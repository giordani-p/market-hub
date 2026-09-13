"""Dependencias de autenticacao e autorizacao."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.models import User, UserRole
from app.auth.tokens import decode_access_token
from app.core.config import Settings, get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.database import get_session

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(
    credentials: CredentialsDep,
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication required")

    user_id = decode_access_token(credentials.credentials, settings)
    user = session.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Authentication required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_buyer(user: CurrentUser) -> User:
    if user.role != UserRole.BUYER:
        raise ForbiddenError("Buyer role required")
    return user


def require_seller(user: CurrentUser) -> User:
    if user.role != UserRole.SELLER or user.seller_id is None:
        raise ForbiddenError("Seller role required")
    return user


def require_ops(user: CurrentUser) -> User:
    if user.role != UserRole.OPS:
        raise ForbiddenError("Ops role required")
    return user


BuyerUser = Annotated[User, Depends(require_buyer)]
SellerUser = Annotated[User, Depends(require_seller)]
OpsUser = Annotated[User, Depends(require_ops)]
