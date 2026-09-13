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


class ErrorResponse(BaseModel):
    code: str
    message: str


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        body = ErrorResponse(code=exc.code, message=exc.message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())
