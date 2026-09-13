"""Rotas de Support/Ops e comments do Seller."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import OpsUser, SellerUser
from app.database import get_session
from app.orders.access import load_seller_item
from app.orders.schemas import OrderItemStatus
from app.support.access import load_ops_conversation, load_ops_item
from app.support.comments import create_comment, list_comments
from app.support.listing import get_ops_order_item, list_ops_order_items
from app.support.models import InternalComment
from app.support.priority_ops import (
    apply_critical,
    list_item_conversations,
    list_open_queue,
    refresh_calculated_priority,
    remove_critical,
    to_ops_conversation,
)
from app.support.schemas import (
    ApplyCriticalRequest,
    CreateInternalCommentRequest,
    InternalCommentResponse,
    OpsConversation,
    OpsConversationQueueResponse,
    OpsOrderItemDetail,
    OpsOrderItemListResponse,
)

SessionDep = Annotated[Session, Depends(get_session)]

ops_router = APIRouter(prefix="/ops", tags=["ops"])
seller_comments_router = APIRouter(tags=["order-items"])


@ops_router.get(
    "/order-items",
    response_model=OpsOrderItemListResponse,
    summary="List all order items for Ops",
)
def list_order_items_for_ops(
    _ops: OpsUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[OrderItemStatus | None, Query(alias="status")] = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    order_item_id: UUID | None = None,
    seller_id: UUID | None = None,
) -> OpsOrderItemListResponse:
    return list_ops_order_items(
        session,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        from_=from_,
        to=to,
        order_item_id=order_item_id,
        seller_id=seller_id,
    )


@ops_router.get(
    "/order-items/{item_id}",
    response_model=OpsOrderItemDetail,
    summary="Get an order item for Ops",
)
def get_order_item_for_ops(item_id: UUID, _ops: OpsUser, session: SessionDep) -> OpsOrderItemDetail:
    return get_ops_order_item(session, item_id)


@ops_router.get(
    "/order-items/{item_id}/internal-comments",
    response_model=list[InternalCommentResponse],
    summary="List internal comments of an order item for Ops",
)
def list_ops_internal_comments(
    item_id: UUID, _ops: OpsUser, session: SessionDep
) -> list[InternalComment]:
    load_ops_item(session, item_id)
    return list_comments(session, item_id)


@ops_router.post(
    "/order-items/{item_id}/internal-comments",
    response_model=InternalCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an internal comment as Ops",
)
def create_ops_internal_comment(
    item_id: UUID,
    body: CreateInternalCommentRequest,
    ops: OpsUser,
    session: SessionDep,
) -> InternalComment:
    load_ops_item(session, item_id)
    return create_comment(session, item_id, ops, body.content)


@ops_router.get(
    "/order-items/{item_id}/conversations",
    response_model=list[OpsConversation],
    summary="List conversations of an order item for Ops",
)
def list_ops_item_conversations(
    item_id: UUID, _ops: OpsUser, session: SessionDep
) -> list[OpsConversation]:
    return [to_ops_conversation(row) for row in list_item_conversations(session, item_id)]


@ops_router.get(
    "/conversations",
    response_model=OpsConversationQueueResponse,
    summary="List OPEN conversations ordered by effective priority",
)
def list_ops_conversation_queue(
    _ops: OpsUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    seller_id: UUID | None = None,
    order_item_id: UUID | None = None,
    effective: Annotated[
        Literal["critical", "high", "medium", "low"] | None, Query(alias="effective_priority")
    ] = None,
) -> OpsConversationQueueResponse:
    return list_open_queue(
        session,
        page=page,
        page_size=page_size,
        seller_id=seller_id,
        order_item_id=order_item_id,
        effective=effective,
    )


@ops_router.get(
    "/conversations/{conversation_id}",
    response_model=OpsConversation,
    summary="Get a conversation for Ops",
)
def get_ops_conversation(
    conversation_id: UUID, _ops: OpsUser, session: SessionDep
) -> OpsConversation:
    return to_ops_conversation(load_ops_conversation(session, conversation_id))


@ops_router.post(
    "/conversations/{conversation_id}/priority/refresh",
    response_model=OpsConversation,
    summary="Recalculate calculated_priority without changing ops_override",
)
def refresh_ops_conversation_priority(
    conversation_id: UUID, _ops: OpsUser, session: SessionDep
) -> OpsConversation:
    conversation = load_ops_conversation(session, conversation_id, for_update=True)
    return to_ops_conversation(refresh_calculated_priority(session, conversation))


@ops_router.post(
    "/conversations/{conversation_id}/critical",
    response_model=OpsConversation,
    summary="Mark a conversation as critical",
)
def mark_conversation_critical(
    conversation_id: UUID,
    body: ApplyCriticalRequest,
    ops: OpsUser,
    session: SessionDep,
) -> OpsConversation:
    conversation = load_ops_conversation(session, conversation_id, for_update=True)
    return to_ops_conversation(apply_critical(session, conversation, ops, body.justification))


@ops_router.post(
    "/conversations/{conversation_id}/critical/remove",
    response_model=OpsConversation,
    summary="Remove the critical override",
)
def remove_conversation_critical(
    conversation_id: UUID, _ops: OpsUser, session: SessionDep
) -> OpsConversation:
    conversation = load_ops_conversation(session, conversation_id, for_update=True)
    return to_ops_conversation(remove_critical(session, conversation))


@seller_comments_router.get(
    "/order-items/{item_id}/internal-comments",
    response_model=list[InternalCommentResponse],
    summary="List internal comments of the authenticated seller's order item",
)
def list_seller_internal_comments(
    item_id: UUID, seller: SellerUser, session: SessionDep
) -> list[InternalComment]:
    assert seller.seller_id is not None
    load_seller_item(session, item_id, seller.seller_id)
    return list_comments(session, item_id)


@seller_comments_router.post(
    "/order-items/{item_id}/internal-comments",
    response_model=InternalCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an internal comment on the authenticated seller's order item",
)
def create_seller_internal_comment(
    item_id: UUID,
    body: CreateInternalCommentRequest,
    seller: SellerUser,
    session: SessionDep,
) -> InternalComment:
    assert seller.seller_id is not None
    load_seller_item(session, item_id, seller.seller_id)
    return create_comment(session, item_id, seller, body.content)
