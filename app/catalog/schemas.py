"""Schemas Pydantic do Catalogo, alinhados ao contrato."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Price = Annotated[str, Field(pattern=r"^\d+\.\d{2}$")]


def format_price(value: Decimal) -> str:
    return f"{value:.2f}"


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None


class SellerSummary(BaseModel):
    """Identidade publica da loja, reusada em Offer, pedido do Buyer e Ops."""

    id: UUID
    name: str


class OfferCreate(BaseModel):
    product_id: UUID
    price: Price
    stock: int = Field(ge=0)
    available: bool = True


class OfferUpdate(BaseModel):
    price: Price | None = None
    stock: int | None = Field(default=None, ge=0)
    available: bool | None = None


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    seller_id: UUID
    seller: SellerSummary
    price: str
    stock: int
    available: bool

    @field_validator("price", mode="before")
    @classmethod
    def serialize_price(cls, value: object) -> str:
        if isinstance(value, Decimal):
            return format_price(value)
        return str(value)
