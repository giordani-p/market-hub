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
            raise ValueError("Content cannot be empty")
        if len(stripped) > 2000:
            raise ValueError("Content cannot exceed 2000 characters")
        return stripped


class ApplyCriticalRequest(BaseModel):
    justification: str = Field(min_length=1, max_length=2000)

    @field_validator("justification")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Justification cannot be empty")
        if len(stripped) > 2000:
            raise ValueError("Justification cannot exceed 2000 characters")
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


class OpsConversation(BaseModel):
    id: UUID
    order_item_id: UUID
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_interaction_at: datetime
    calculated_priority: str
    ops_override: str | None
    effective_priority: str


class OpsConversationQueueItem(OpsConversation):
    seller: SellerSummary
    product: ProductSummary
    buyer: BuyerSummary
    order_item_status: str
    purchase_price: str


class OpsConversationQueueResponse(BaseModel):
    items: list[OpsConversationQueueItem]
    page: int
    page_size: int
    total: int
