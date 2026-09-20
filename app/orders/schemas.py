"""Schemas Pydantic do dominio de Order."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.catalog.schemas import Price, format_price

OrderItemStatus = Literal["placed", "preparing", "in_transit", "delivered", "cancelled"]
OrderItemForwardStatus = Literal["placed", "preparing", "in_transit", "delivered"]


class CheckoutItem(BaseModel):
    offer_id: UUID
    quantity: int = Field(ge=1)
    expected_price: Price


class CheckoutRequest(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_offer_ids(self) -> "CheckoutRequest":
        offer_ids = [item.offer_id for item in self.items]
        if len(offer_ids) != len(set(offer_ids)):
            raise ValueError("Duplicate offer_id in checkout")
        return self


class OrderItemStatusUpdate(BaseModel):
    status: OrderItemForwardStatus


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: str
    order_id: UUID
    offer_id: UUID
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("purchase_price", mode="before")
    @classmethod
    def serialize_price(cls, value: object) -> str:
        if isinstance(value, Decimal):
            return format_price(value)
        return str(value)


class BuyerSummary(BaseModel):
    id: UUID
    name: str


class ProductSummary(BaseModel):
    id: UUID
    name: str


class BuyerOrderItem(BaseModel):
    """Order Item na visao do Buyer, com o produto exibido na compra."""

    id: UUID
    number: str
    order_id: UUID
    offer_id: UUID
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    updated_at: datetime
    product: ProductSummary


class OrderResponse(BaseModel):
    id: UUID
    number: int
    buyer_id: UUID
    items: list[BuyerOrderItem]
    created_at: datetime
    updated_at: datetime


class ProductDetailSummary(BaseModel):
    id: UUID
    name: str
    description: str | None


class OrderSummary(BaseModel):
    id: UUID
    number: int
    created_at: datetime


class OrderItemListItem(BaseModel):
    order_item_id: UUID
    number: str
    product: ProductSummary
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    buyer: BuyerSummary
    order_id: UUID


class OrderItemListResponse(BaseModel):
    items: list[OrderItemListItem]
    page: int
    page_size: int
    total: int


class OrderItemDetail(BaseModel):
    id: UUID
    number: str
    offer_id: UUID
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    updated_at: datetime
    product: ProductDetailSummary
    buyer: BuyerSummary
    order: OrderSummary
