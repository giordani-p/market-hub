"""Handlers de Job. Delegam para a aplicacao; nao contem regra de negocio."""

import logging

from app.communication.reconcile import run_reconcile
from app.jobs.models import RECONCILE_PRIORITIES, Job
from app.jobs.registry import JobRegistry

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


def default_registry() -> JobRegistry:
    return JobRegistry({RECONCILE_PRIORITIES: handle_reconcile_priorities})
