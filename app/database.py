"""Engine, sessao e base declarativa do SQLAlchemy."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada pelos modelos dos dominios."""


@lru_cache
def get_engine() -> Engine:
    """Engine unica por processo. Criada sob demanda, nao no import."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Dependencia do FastAPI: uma sessao por request, com commit ao final."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
