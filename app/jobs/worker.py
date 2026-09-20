"""Worker SQS: um Job por vez, delete so apos sucesso."""

import logging
import signal
import time
from collections.abc import Callable

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.jobs.enqueue import enqueue_reconcile
from app.jobs.handlers import default_registry
from app.jobs.models import RECONCILE_PRIORITIES, Job
from app.jobs.queue import JobQueue, SqsJobQueue, wait_for_queue
from app.jobs.registry import JobRegistry, parse_job

logger = logging.getLogger(__name__)

_stop = False


def process_once(
    queue: JobQueue,
    registry: JobRegistry,
    on_job: Callable[[Job], None] | None = None,
) -> bool:
    """Processa no maximo uma mensagem. True se havia mensagem."""
    message = queue.receive()
    if message is None:
        return False
    try:
        job = parse_job(message.body)
        logger.info("job started type=%s", job.job_type)
        if on_job is not None:
            on_job(job)
        registry.resolve(job.job_type)(job)
    except Exception:
        logger.exception("job failed")
        return True
    queue.delete(message.receipt_handle)
    logger.info("job completed")
    return True


def _request_stop(signum: int, frame: object) -> None:
    del signum, frame
    global _stop
    _stop = True
    logger.info("worker stopping after current job")


def run_worker(
    settings: Settings | None = None,
    queue: JobQueue | None = None,
    registry: JobRegistry | None = None,
    now: Callable[[], float] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    settings = settings or get_settings()
    registry = registry or default_registry()
    clock = now or time.monotonic
    stop = should_stop or (lambda: _stop)
    if queue is None:
        sqs = SqsJobQueue(settings, long_poll=True)
        wait_for_queue(sqs)
        queue = sqs

    pending_reconcile = False
    interval = settings.jobs_reconcile_interval_seconds
    last_enqueued_at = clock() - max(interval, 0)

    def on_job(job: Job) -> None:
        nonlocal pending_reconcile
        if job.job_type == RECONCILE_PRIORITIES:
            pending_reconcile = False

    logger.info("worker started queue=%s", settings.jobs_queue_name)
    while not stop():
        try:
            process_once(queue, registry, on_job=on_job)
            if interval > 0 and not pending_reconcile and clock() - last_enqueued_at >= interval:
                enqueue_reconcile(queue)
                pending_reconcile = True
                last_enqueued_at = clock()
                logger.info("reconcile job enqueued by worker ticker")
        except Exception:
            logger.exception("worker loop error")
            time.sleep(1)


def main() -> None:
    configure_logging()
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    run_worker()


if __name__ == "__main__":
    main()
