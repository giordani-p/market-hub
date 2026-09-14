"""Rota de leitura do Dashboard."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.dashboard.schemas import DashboardResponse
from app.dashboard.service import get_dashboard
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(tags=["dashboard"])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Return the dashboard projection for the authenticated user",
)
def read_dashboard(user: CurrentUser, session: SessionDep) -> DashboardResponse:
    return get_dashboard(session, user)
