"""Dispatcher de Jobs: tipo -> handler."""

import json
from collections.abc import Callable

from app.jobs.models import Job

JobHandler = Callable[[Job], None]


class UnknownJobTypeError(Exception):
    """Job type sem handler registrado."""

    def __init__(self, job_type: str) -> None:
        super().__init__(f"unknown job type: {job_type}")
        self.job_type = job_type


def parse_job(body: str) -> Job:
    """Aceita JSON puro ou envelope EventBridge com detail."""
    payload = _extract_payload(json.loads(body))
    job_type = payload.get("job_type")
    if not isinstance(job_type, str) or not job_type:
        raise ValueError("job_type is required")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("params must be an object")
    return Job(job_type=job_type, params=params)


def _extract_payload(raw: object) -> dict:
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        raise ValueError("job payload must be an object")
    if "job_type" in raw:
        return raw
    detail = raw.get("detail")
    if detail:
        return _extract_payload(detail)
    raise ValueError("job_type is required")


class JobRegistry:
    def __init__(self, handlers: dict[str, JobHandler]) -> None:
        self._handlers = handlers

    def resolve(self, job_type: str) -> JobHandler:
        handler = self._handlers.get(job_type)
        if handler is None:
            raise UnknownJobTypeError(job_type)
        return handler
