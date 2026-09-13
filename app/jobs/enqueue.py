"""Publica Jobs na fila. Usado pelo Makefile, sem AWS CLI no host."""

import json
import sys

from app.core.config import get_settings
from app.jobs.models import RECONCILE_PRIORITIES
from app.jobs.queue import JobQueue, SqsJobQueue


def enqueue_reconcile(queue: JobQueue | None = None) -> None:
    settings = get_settings()
    target = queue or SqsJobQueue(settings)
    target.send(json.dumps({"job_type": RECONCILE_PRIORITIES}))


def main() -> None:
    enqueue_reconcile()
    print("Enqueued RECONCILE_PRIORITIES", file=sys.stdout)


if __name__ == "__main__":
    main()
