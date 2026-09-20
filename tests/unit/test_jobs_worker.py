import json
import logging
from collections.abc import Callable

import pytest
from botocore.config import Config
from botocore.exceptions import ReadTimeoutError

from app.core.config import Settings
from app.jobs.handlers import default_registry
from app.jobs.models import NOTIFY_STATUS_CHANGE, RECONCILE_PRIORITIES, Job
from app.jobs.queue import ReceivedMessage, SqsJobQueue, sqs_client_kwargs
from app.jobs.registry import JobRegistry, UnknownJobTypeError, parse_job
from app.jobs.worker import process_once, run_worker
from tests.fakes import InMemoryJobQueue


class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


class SendOnlyQueue(InMemoryJobQueue):
    """Aceita send, mas receive nunca entrega — simula backlog nao consumido."""

    def receive(self) -> ReceivedMessage | None:
        return None


def _stop_after(cycles: int, on_cycle: Callable[[int], None] | None = None) -> Callable[[], bool]:
    state = {"n": 0}

    def should_stop() -> bool:
        state["n"] += 1
        if on_cycle is not None:
            on_cycle(state["n"])
        return state["n"] > cycles

    return should_stop


def test_parse_job_plain_and_eventbridge_envelope() -> None:
    plain = parse_job(json.dumps({"job_type": RECONCILE_PRIORITIES}))
    assert plain.job_type == RECONCILE_PRIORITIES
    assert plain.params == {}
    nested = parse_job(
        json.dumps({"detail": {"job_type": RECONCILE_PRIORITIES, "params": {"page": 1}}})
    )
    assert nested.job_type == RECONCILE_PRIORITIES
    assert nested.params == {"page": 1}


def test_unknown_job_type_raises() -> None:
    registry = JobRegistry({})
    with pytest.raises(UnknownJobTypeError):
        registry.resolve("NOPE")


def test_worker_calls_handler_and_deletes_on_success() -> None:
    queue = InMemoryJobQueue()
    queue.send(json.dumps({"job_type": RECONCILE_PRIORITIES}))
    called: list[Job] = []
    registry = JobRegistry({RECONCILE_PRIORITIES: called.append})
    assert process_once(queue, registry) is True
    assert [job.job_type for job in called] == [RECONCILE_PRIORITIES]
    assert queue.pending == []
    assert queue.deleted == ["1"]


def test_worker_does_not_delete_when_handler_fails() -> None:
    queue = InMemoryJobQueue()
    queue.send(json.dumps({"job_type": RECONCILE_PRIORITIES}))

    def fail(_job: Job) -> None:
        raise RuntimeError("boom")

    registry = JobRegistry({RECONCILE_PRIORITIES: fail})
    assert process_once(queue, registry) is True
    assert queue.pending == [("1", json.dumps({"job_type": RECONCILE_PRIORITIES}))]
    assert queue.deleted == []


def test_worker_does_not_delete_unknown_or_invalid_payload() -> None:
    queue = InMemoryJobQueue()
    registry = JobRegistry({RECONCILE_PRIORITIES: lambda job: None})
    queue.send(json.dumps({"job_type": "NOPE"}))
    assert process_once(queue, registry) is True
    assert queue.deleted == []
    queue.delete("1")
    queue.send("not-json")
    assert process_once(queue, registry) is True
    assert queue.deleted == ["1"]
    assert queue.pending[0][0] == "2"


def test_worker_logs_job_completed_with_type(caplog: pytest.LogCaptureFixture) -> None:
    queue = InMemoryJobQueue()
    queue.send(json.dumps({"job_type": NOTIFY_STATUS_CHANGE, "params": {}}))
    registry = JobRegistry({NOTIFY_STATUS_CHANGE: lambda job: None})
    with caplog.at_level(logging.INFO, logger="app.jobs.worker"):
        assert process_once(queue, registry) is True
    assert "job completed type=NOTIFY_STATUS_CHANGE" in caplog.text


def test_worker_notify_handler_deletes_on_success() -> None:
    queue = InMemoryJobQueue()
    queue.send(json.dumps({"job_type": NOTIFY_STATUS_CHANGE, "params": {}}))
    called: list[Job] = []
    registry = JobRegistry({NOTIFY_STATUS_CHANGE: called.append})
    assert process_once(queue, registry) is True
    assert [job.job_type for job in called] == [NOTIFY_STATUS_CHANGE]
    assert queue.deleted == ["1"]


def test_worker_notify_does_not_delete_when_handler_fails() -> None:
    queue = InMemoryJobQueue()
    queue.send(json.dumps({"job_type": NOTIFY_STATUS_CHANGE, "params": {}}))

    def fail(_job: Job) -> None:
        raise RuntimeError("boom")

    registry = JobRegistry({NOTIFY_STATUS_CHANGE: fail})
    assert process_once(queue, registry) is True
    assert queue.pending == [("1", json.dumps({"job_type": NOTIFY_STATUS_CHANGE, "params": {}}))]
    assert queue.deleted == []


def test_default_registry_resolves_notify_job() -> None:
    assert default_registry().resolve(NOTIFY_STATUS_CHANGE) is not None


def test_local_sqs_client_ignores_host_aws_credentials() -> None:
    kwargs = sqs_client_kwargs(Settings(_env_file=None))
    assert kwargs["endpoint_url"] == "http://localhost:4566"
    assert kwargs["aws_access_key_id"] == "test"
    assert kwargs["aws_secret_access_key"] == "test"
    assert kwargs["aws_session_token"] == ""
    config = kwargs["config"]
    assert isinstance(config, Config)
    assert config.connect_timeout == 2
    assert config.read_timeout == 5
    assert config.retries["max_attempts"] == 2


def test_long_poll_client_read_timeout_exceeds_wait() -> None:
    settings = Settings(_env_file=None)
    kwargs = sqs_client_kwargs(settings, long_poll=True)
    config = kwargs["config"]
    assert isinstance(config, Config)
    assert config.read_timeout == settings.jobs_wait_time_seconds + 5
    assert config.connect_timeout == 2
    assert config.retries["max_attempts"] == 2


def test_receive_returns_none_on_read_timeout() -> None:
    class FakeClient:
        def get_queue_url(self, **kwargs: object) -> dict[str, str]:
            del kwargs
            return {"QueueUrl": "http://sqs.local/queue"}

        def receive_message(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            raise ReadTimeoutError(endpoint_url="http://localstack:4566/")

    queue = SqsJobQueue(Settings(_env_file=None), client=FakeClient())
    assert queue.receive() is None


def test_ticker_enqueues_reconcile_after_interval() -> None:
    queue = InMemoryJobQueue()
    clock = FakeClock(0.0)
    called: list[Job] = []
    registry = JobRegistry({RECONCILE_PRIORITIES: called.append})
    settings = Settings(_env_file=None, jobs_reconcile_interval_seconds=60)

    def on_cycle(n: int) -> None:
        if n == 3:
            clock.t = 60.0

    run_worker(
        settings=settings,
        queue=queue,
        registry=registry,
        now=clock,
        should_stop=_stop_after(5, on_cycle),
    )
    assert [job.job_type for job in called] == [RECONCILE_PRIORITIES, RECONCILE_PRIORITIES]


def test_ticker_disabled_when_interval_is_zero() -> None:
    queue = InMemoryJobQueue()
    settings = Settings(_env_file=None, jobs_reconcile_interval_seconds=0)
    registry = JobRegistry({RECONCILE_PRIORITIES: lambda job: None})
    run_worker(
        settings=settings,
        queue=queue,
        registry=registry,
        now=FakeClock(0.0),
        should_stop=_stop_after(3),
    )
    assert queue.pending == []


def test_ticker_does_not_pile_up_while_reconcile_is_pending() -> None:
    queue = SendOnlyQueue()
    clock = FakeClock(0.0)
    settings = Settings(_env_file=None, jobs_reconcile_interval_seconds=60)
    registry = JobRegistry({RECONCILE_PRIORITIES: lambda job: None})

    def on_cycle(n: int) -> None:
        if n == 2:
            clock.t = 60.0

    run_worker(
        settings=settings,
        queue=queue,
        registry=registry,
        now=clock,
        should_stop=_stop_after(2, on_cycle),
    )
    bodies = [body for _, body in queue.pending]
    assert bodies == [json.dumps({"job_type": RECONCILE_PRIORITIES})]
