"""Handlers de Job. Delegam para a aplicacao; nao contem regra de negocio."""

import logging

from app.communication.reconcile import run_reconcile
from app.database import get_session_factory
from app.jobs.models import NOTIFY_STATUS_CHANGE, RECONCILE_PRIORITIES, Job
from app.jobs.registry import JobRegistry
from app.notifications.service import process_notify_job

logger = logging.getLogger(__name__)


def handle_reconcile_priorities(job: Job) -> None:
    del job
    result = run_reconcile()
    logger.info(
        "job finished type=%s found=%s processed=%s updated=%s unchanged=%s",
        RECONCILE_PRIORITIES,
        result.found,
        result.processed,
        result.updated,
        result.unchanged,
    )


def handle_notify_status_change(job: Job) -> None:
    factory = get_session_factory()
    session = factory()
    try:
        process_notify_job(session, job)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def default_registry() -> JobRegistry:
    return JobRegistry(
        {
            RECONCILE_PRIORITIES: handle_reconcile_priorities,
            NOTIFY_STATUS_CHANGE: handle_notify_status_change,
        }
    )
