"""Configuracao minima de logging da API e do Worker."""

import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging() -> None:
    """Mesmo formato na API e no Worker. Nao reconfigura se ja houver handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        stream=sys.stdout,
    )
