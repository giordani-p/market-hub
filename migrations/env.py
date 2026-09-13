"""Configuracao de runtime do Alembic.

A URL do banco nao fica no alembic.ini: vem de DATABASE_URL, pelas mesmas
Settings que a aplicacao usa.
"""

from logging.config import fileConfig

from alembic import context

from app.auth import models as auth_models  # noqa: F401
from app.catalog import models as catalog_models  # noqa: F401
from app.communication import models as communication_models  # noqa: F401
from app.core.config import get_settings
from app.database import Base, get_engine
from app.orders import models as order_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
