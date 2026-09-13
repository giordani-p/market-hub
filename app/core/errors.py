"""Erros de negocio e sua traducao para respostas HTTP."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class DomainError(Exception):
    """Base das violacoes de regra de negocio.

    Nao define status nem codigo: cada subclasse declara os seus. Validacao de
    campo nao passa por aqui, fica com o Pydantic, que responde 422.
    """

    status_code: int
    code: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(DomainError):
    """Recurso referenciado nao existe."""

    status_code = 404
    code = "resource_not_found"


class ResourceInUseError(DomainError):
    """Exclusao bloqueada por integridade referencial."""

    status_code = 409
    code = "resource_in_use"


class UnauthorizedError(DomainError):
    """Credenciais ausentes ou invalidas."""

    status_code = 401
    code = "unauthorized"


class ForbiddenError(DomainError):
    """Usuario autenticado sem permissao para a operacao."""

    status_code = 403
    code = "forbidden"


class InvalidTransitionError(DomainError):
    """Mudanca de status fora do fluxo permitido."""

    status_code = 409
    code = "invalid_transition"


class CheckoutRejectedItem(BaseModel):
    offer_id: str
    reason: str
    expected_price: str | None = None
    current_price: str | None = None
    available: bool | None = None
    stock: int | None = None


class CheckoutRejectedError(DomainError):
    """Compra nao efetivada: um ou mais itens precisam de revisao."""

    status_code = 409
    code = "checkout_rejected"

    def __init__(self, items: list[CheckoutRejectedItem]) -> None:
        super().__init__("One or more items require review")
        self.items = items


class ErrorResponse(BaseModel):
    code: str
    message: str


class CheckoutRejectedResponse(BaseModel):
    code: str
    message: str
    items: list[CheckoutRejectedItem]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CheckoutRejectedError)
    async def handle_checkout_rejected(_: Request, exc: CheckoutRejectedError) -> JSONResponse:
        body = CheckoutRejectedResponse(
            code=exc.code,
            message=exc.message,
            items=exc.items,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        body = ErrorResponse(code=exc.code, message=exc.message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())
