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


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    buyer_id: UUID
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class BuyerSummary(BaseModel):
    id: UUID
    name: str


class ProductSummary(BaseModel):
    id: UUID
    name: str


class ProductDetailSummary(BaseModel):
    id: UUID
    name: str
    description: str | None


class OrderSummary(BaseModel):
    id: UUID
    created_at: datetime


class OrderItemListItem(BaseModel):
    order_item_id: UUID
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
    offer_id: UUID
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    updated_at: datetime
    product: ProductDetailSummary
    buyer: BuyerSummary
    order: OrderSummary
