"""Sender de e-mail simulado: loga no console do Worker, sem SMTP."""

import logging
from typing import Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        entity_id: UUID,
        new_status: str,
    ) -> None:
        """Entrega o alerta. body fica para um provider real."""
        ...


class ConsoleEmailSender:
    """Simula o envio escrevendo no stdout do Worker."""

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        entity_id: UUID,
        new_status: str,
    ) -> None:
        del body
        logger.info(
            "email notification sent to=%s subject=%s entity_id=%s new_status=%s",
            ",".join(to),
            subject,
            entity_id,
            new_status,
        )
