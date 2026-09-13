import json

import pytest

from app.core.config import Settings
from app.jobs.models import RECONCILE_PRIORITIES, Job
from app.jobs.queue import ReceivedMessage, sqs_client_kwargs
from app.jobs.registry import JobRegistry, UnknownJobTypeError, parse_job
from app.jobs.worker import process_once


class InMemoryJobQueue:
    def __init__(self) -> None:
        self.pending: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self._n = 0

    def send(self, body: str) -> None:
        self._n += 1
        self.pending.append((str(self._n), body))

    def receive(self) -> ReceivedMessage | None:
        if not self.pending:
            return None
        handle, body = self.pending[0]
        return ReceivedMessage(receipt_handle=handle, body=body)

    def delete(self, receipt_handle: str) -> None:
        self.deleted.append(receipt_handle)
        self.pending = [(handle, body) for handle, body in self.pending if handle != receipt_handle]


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


def test_local_sqs_client_ignores_host_aws_credentials() -> None:
    kwargs = sqs_client_kwargs(Settings(_env_file=None))
    assert kwargs["endpoint_url"] == "http://localhost:4566"
    assert kwargs["aws_access_key_id"] == "test"
    assert kwargs["aws_secret_access_key"] == "test"
    assert kwargs["aws_session_token"] == ""
