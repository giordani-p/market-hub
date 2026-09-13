"""Montagem da aplicacao FastAPI."""

from fastapi import FastAPI

from app import __version__, health
from app.auth import routes as auth_routes
from app.catalog import offers, products
from app.communication.routes import conversation_router, item_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.notifications.routes import router as notifications_router
from app.orders.routes import items_router, orders_router
from app.support.routes import ops_router, seller_comments_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Cria a aplicacao. Recebe settings explicitas nos testes."""
    settings = settings or get_settings()

    app = FastAPI(
        title="Market Hub API",
        version=__version__,
        description="Catalog, Orders, Communication, Support/Ops and Notifications.",
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    app.dependency_overrides[get_settings] = lambda: settings

    register_exception_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth_routes.router, prefix=settings.api_prefix)
    app.include_router(products.router, prefix=settings.api_prefix)
    app.include_router(offers.router, prefix=settings.api_prefix)
    app.include_router(orders_router, prefix=settings.api_prefix)
    app.include_router(items_router, prefix=settings.api_prefix)
    app.include_router(item_router, prefix=settings.api_prefix)
    app.include_router(conversation_router, prefix=settings.api_prefix)
    app.include_router(ops_router, prefix=settings.api_prefix)
    app.include_router(seller_comments_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)

    return app


app = create_app()
