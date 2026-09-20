"""Endpoint de health check."""

import logging
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.database import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        503: {
            "model": HealthResponse,
            "description": "Service cannot reach PostgreSQL",
        }
    },
    summary="Service health check",
)
def get_health(response: Response) -> HealthResponse:
    try:
        with get_engine().begin() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "Health check failed: database unreachable (%s)",
            type(exc).__name__,
        )
        response.status_code = 503
        return HealthResponse(status="error", version=__version__)
    return HealthResponse(status="ok", version=__version__)
