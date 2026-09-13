"""Worker SQS: um Job por vez, delete so apos sucesso."""

import logging
import signal
import sys
import time

from app.core.config import Settings, get_settings
from app.jobs.handlers import default_registry
from app.jobs.queue import JobQueue, SqsJobQueue, wait_for_queue
from app.jobs.registry import JobRegistry, parse_job

logger = logging.getLogger(__name__)

_stop = False


def process_once(queue: JobQueue, registry: JobRegistry) -> bool:
    """Processa no maximo uma mensagem. True se havia mensagem."""
    message = queue.receive()
    if message is None:
        return False
    try:
        job = parse_job(message.body)
        logger.info("job started type=%s", job.job_type)
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
) -> None:
    settings = settings or get_settings()
    registry = registry or default_registry()
    if queue is None:
        sqs = SqsJobQueue(settings)
        wait_for_queue(sqs)
        queue = sqs
    logger.info("worker started queue=%s", settings.jobs_queue_name)
    while not _stop:
        try:
            process_once(queue, registry)
        except Exception:
            logger.exception("worker loop error")
            time.sleep(1)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    run_worker()


if __name__ == "__main__":
    main()
