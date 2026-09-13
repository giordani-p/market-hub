import json

import pytest

from app.core.config import Settings
from app.jobs.handlers import default_registry
from app.jobs.models import NOTIFY_STATUS_CHANGE, RECONCILE_PRIORITIES, Job
from app.jobs.queue import sqs_client_kwargs
from app.jobs.registry import JobRegistry, UnknownJobTypeError, parse_job
from app.jobs.worker import process_once
from tests.fakes import InMemoryJobQueue


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
