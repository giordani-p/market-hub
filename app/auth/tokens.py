"""Emissao e leitura de JWT."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from app.auth.models import User
from app.core.config import Settings
from app.core.errors import UnauthorizedError

ALGORITHM = "HS256"


def create_access_token(user: User, settings: Settings) -> str:
    if not settings.jwt_secret:
        raise UnauthorizedError("JWT_SECRET is not set")
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expire,
    }
    if user.seller_id is not None:
        payload["seller_id"] = str(user.seller_id)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise UnauthorizedError("Invalid token")
        return UUID(sub)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise UnauthorizedError("Invalid token") from exc
