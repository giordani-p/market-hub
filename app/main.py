"""Montagem da aplicacao FastAPI."""

from fastapi import FastAPI

from app import __version__, health
from app.catalog import offers, products
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Cria a aplicacao. Recebe settings explicitas nos testes."""
    settings = settings or get_settings()

    app = FastAPI(
        title="Marketplace API",
        version=__version__,
        description="Marketplace backend. Catalog domain.",
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    register_exception_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(products.router, prefix=settings.api_prefix)
    app.include_router(offers.router, prefix=settings.api_prefix)

    return app


app = create_app()
