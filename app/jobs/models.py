"""Unidade de trabalho assincrona, sem regra de negocio."""

from dataclasses import dataclass, field

RECONCILE_PRIORITIES = "RECONCILE_PRIORITIES"
NOTIFY_STATUS_CHANGE = "NOTIFY_STATUS_CHANGE"


@dataclass(frozen=True)
class Job:
    """Identifica o tipo de Job e parametros pequenos para o handler."""

    job_type: str
    params: dict[str, object] = field(default_factory=dict)
