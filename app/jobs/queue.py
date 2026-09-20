"""Fila de Jobs: contrato minimo e adapter SQS."""

import time
from dataclasses import dataclass
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError

from app.core.config import Settings, get_settings

# Credenciais dummy aceitas pelo LocalStack. Nao sao segredos reais.
_LOCALSTACK_ACCESS_KEY = "test"
_LOCALSTACK_SECRET_KEY = "test"

# Enqueue e efeito secundario: nao pode segurar o request HTTP.
_ENQUEUE_SQS_CONFIG = Config(
    connect_timeout=2,
    read_timeout=5,
    retries={"max_attempts": 2},
)


def _consume_sqs_config(settings: Settings) -> Config:
    """HTTP read precisa ultrapassar o WaitTimeSeconds do long poll."""
    return Config(
        connect_timeout=2,
        read_timeout=settings.jobs_wait_time_seconds + 5,
        retries={"max_attempts": 2},
    )


@dataclass(frozen=True)
class ReceivedMessage:
    receipt_handle: str
    body: str


class JobQueue(Protocol):
    def receive(self) -> ReceivedMessage | None: ...

    def delete(self, receipt_handle: str) -> None: ...

    def send(self, body: str) -> None: ...


def sqs_client_kwargs(settings: Settings, *, long_poll: bool = False) -> dict[str, object]:
    """Usa dummy keys no endpoint local para nao herdar ~/.aws contra a AWS real."""
    endpoint = settings.aws_endpoint_url or None
    kwargs: dict[str, object] = {
        "region_name": settings.aws_region,
        "endpoint_url": endpoint,
        "config": _consume_sqs_config(settings) if long_poll else _ENQUEUE_SQS_CONFIG,
    }
    if endpoint:
        kwargs["aws_access_key_id"] = _LOCALSTACK_ACCESS_KEY
        kwargs["aws_secret_access_key"] = _LOCALSTACK_SECRET_KEY
        kwargs["aws_session_token"] = ""
    return kwargs


class SqsJobQueue:
    """Adapter SQS. Sem endpoint, usa o default da AWS."""

    def __init__(
        self,
        settings: Settings,
        client: object | None = None,
        *,
        long_poll: bool = False,
    ) -> None:
        self._settings = settings
        self._client = client or boto3.client(
            "sqs", **sqs_client_kwargs(settings, long_poll=long_poll)
        )
        self._queue_url: str | None = None

    def queue_url(self) -> str:
        if self._queue_url is None:
            self._queue_url = self._client.get_queue_url(QueueName=self._settings.jobs_queue_name)[
                "QueueUrl"
            ]
        return self._queue_url

    def receive(self) -> ReceivedMessage | None:
        try:
            response = self._client.receive_message(
                QueueUrl=self.queue_url(),
                MaxNumberOfMessages=1,
                WaitTimeSeconds=self._settings.jobs_wait_time_seconds,
                VisibilityTimeout=self._settings.jobs_visibility_timeout_seconds,
            )
        except ReadTimeoutError:
            return None
        messages = response.get("Messages") or []
        if not messages:
            return None
        message = messages[0]
        return ReceivedMessage(receipt_handle=message["ReceiptHandle"], body=message["Body"])

    def delete(self, receipt_handle: str) -> None:
        self._client.delete_message(QueueUrl=self.queue_url(), ReceiptHandle=receipt_handle)

    def send(self, body: str) -> None:
        self._client.send_message(QueueUrl=self.queue_url(), MessageBody=body)


_job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    """Fila compartilhada no processo. Testes substituem via set_job_queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = SqsJobQueue(get_settings())
    return _job_queue


def set_job_queue(queue: JobQueue | None) -> None:
    global _job_queue
    _job_queue = queue


def wait_for_queue(queue: SqsJobQueue, *, attempts: int = 30) -> None:
    """Espera a fila existir apos o provisionamento do LocalStack."""
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            queue.queue_url()
            return
        except ClientError as exc:
            last_error = exc
            time.sleep(1)
    if last_error is not None:
        raise last_error
