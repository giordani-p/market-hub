"""Schemas Pydantic do dominio Support/Ops."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.orders.schemas import BuyerSummary, OrderSummary, ProductDetailSummary, ProductSummary

InternalCommentAuthorType = Literal["ops", "seller"]


class CreateInternalCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Comment content cannot be empty")
        if len(stripped) > 2000:
            raise ValueError("Comment content cannot exceed 2000 characters")
        return stripped


class InternalCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_item_id: UUID
    author_id: UUID
    author_type: str
    content: str
    created_at: datetime


class SellerSummary(BaseModel):
    id: UUID
    name: str


class OpsOrderItemListItem(BaseModel):
    order_item_id: UUID
    product: ProductSummary
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    buyer: BuyerSummary
    seller: SellerSummary
    order_id: UUID


class OpsOrderItemListResponse(BaseModel):
    items: list[OpsOrderItemListItem]
    page: int
    page_size: int
    total: int


class OpsOrderItemDetail(BaseModel):
    id: UUID
    offer_id: UUID
    quantity: int
    purchase_price: str
    status: str
    created_at: datetime
    updated_at: datetime
    product: ProductDetailSummary
    buyer: BuyerSummary
    seller: SellerSummary
    order: OrderSummary
