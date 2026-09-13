"""Rotas de login e perfil. Sem cadastro publico."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.passwords import verify_password
from app.auth.schemas import LoginRequest, TokenResponse, UserResponse
from app.auth.tokens import create_access_token
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse, summary="Authenticate a seeded user")
def login(payload: LoginRequest, session: SessionDep, settings: SettingsDep) -> TokenResponse:
    email = payload.email.lower()
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    return TokenResponse(access_token=create_access_token(user, settings))


@router.get("/auth/me", response_model=UserResponse, summary="Return the authenticated user")
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
