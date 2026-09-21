"""Schemas Pydantic da capability Dashboard."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.schemas import Price, SellerSummary
from app.orders.schemas import BuyerSummary, ProductSummary

_FORBID = ConfigDict(extra="forbid")


class OrderItemsByStatus(BaseModel):
    model_config = _FORBID

    placed: int = Field(ge=0)
    preparing: int = Field(ge=0)
    in_transit: int = Field(ge=0)
    delivered: int = Field(ge=0)
    cancelled: int = Field(ge=0)


class ConversationsByPriority(BaseModel):
    model_config = _FORBID

    critical: int = Field(ge=0)
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)


class OpenConversationsAttention(BaseModel):
    model_config = _FORBID

    open_conversations: int = Field(ge=0)


class SellerDashboardSummary(BaseModel):
    model_config = _FORBID

    total_order_items: int = Field(ge=0)
    active_order_items: int = Field(ge=0)
    order_items_by_status: OrderItemsByStatus


class SellerRecentOrderItem(BaseModel):
    model_config = _FORBID

    order_item_id: UUID
    number: str
    order_id: UUID
    product: ProductSummary
    buyer: BuyerSummary
    quantity: int = Field(ge=1)
    purchase_price: Price
    status: str
    created_at: datetime


class SellerRecent(BaseModel):
    model_config = _FORBID

    order_items: list[SellerRecentOrderItem]


class SellerDashboard(BaseModel):
    model_config = _FORBID

    role: Literal["seller"]
    summary: SellerDashboardSummary
    attention: OpenConversationsAttention
    recent: SellerRecent


class BuyerDashboardSummary(BaseModel):
    model_config = _FORBID

    active_orders: int = Field(ge=0)
    completed_orders: int = Field(ge=0)


class BuyerRecentOrderItem(BaseModel):
    model_config = _FORBID

    order_item_id: UUID
    number: str
    product: ProductSummary
    seller: SellerSummary
    quantity: int = Field(ge=1)
    status: str


class BuyerRecentOrder(BaseModel):
    model_config = _FORBID

    order_id: UUID
    number: int
    created_at: datetime
    status: Literal["in_progress", "completed", "cancelled"]
    total_amount: Price
    items: list[BuyerRecentOrderItem]


class BuyerRecent(BaseModel):
    model_config = _FORBID

    orders: list[BuyerRecentOrder]


class BuyerDashboard(BaseModel):
    model_config = _FORBID

    role: Literal["buyer"]
    summary: BuyerDashboardSummary
    attention: OpenConversationsAttention
    recent: BuyerRecent


class OpsDashboardSummary(BaseModel):
    model_config = _FORBID

    open_conversations: int = Field(ge=0)
    conversations_by_priority: ConversationsByPriority


class OpsQueuePreviewItem(BaseModel):
    model_config = _FORBID

    conversation_id: UUID
    order_item_id: UUID
    number: str
    effective_priority: str
    calculated_priority: str
    ops_override: str | None
    reason: str
    last_interaction_at: datetime
    seller: SellerSummary
    buyer: BuyerSummary
    product: ProductSummary
    order_item_status: str
    purchase_price: Price


class OpsAttention(BaseModel):
    model_config = _FORBID

    priority_queue_preview: list[OpsQueuePreviewItem]


class OpsRecent(BaseModel):
    model_config = _FORBID


class OpsDashboard(BaseModel):
    model_config = _FORBID

    role: Literal["ops"]
    summary: OpsDashboardSummary
    attention: OpsAttention
    recent: OpsRecent


DashboardResponse = Annotated[
    SellerDashboard | BuyerDashboard | OpsDashboard,
    Field(discriminator="role"),
]
