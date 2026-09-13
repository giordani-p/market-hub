"""Rotas de Support/Ops e comments do Seller."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import OpsUser, SellerUser
from app.database import get_session
from app.orders.access import load_seller_item
from app.orders.schemas import OrderItemStatus
from app.support.access import load_ops_item
from app.support.comments import create_comment, list_comments
from app.support.listing import get_ops_order_item, list_ops_order_items
from app.support.models import InternalComment
from app.support.schemas import (
    CreateInternalCommentRequest,
    InternalCommentResponse,
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
