"""Rotas de Conversation e Message."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, SellerUser
from app.communication.access import (
    load_participant_conversation,
    load_participant_item,
    load_seller_conversation,
)
from app.communication.lifecycle import (
    add_message,
    close_by_seller,
    get_or_create_conversation,
    maybe_close_inactive,
    message_window,
    utcnow,
    validate_before,
)
from app.communication.models import Conversation, Message
from app.communication.priority import effective_priority
from app.communication.schemas import (
    ConversationResponse,
    CreateConversationRequest,
    CreateMessageRequest,
    MessageListResponse,
    MessageResponse,
)
from app.core.config import Settings, get_settings
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

item_router = APIRouter(tags=["conversations"])
conversation_router = APIRouter(tags=["conversations"])


def _to_conversation_response(conversation: Conversation) -> ConversationResponse:
    """Converte a Conversation persistida, com o `effective_priority` derivado.

    Nao e uma coluna do modelo (so calculated_priority/ops_override sao), por
    isso o Buyer/Seller precisa da mesma conversao explicita que a Ops ja usa
    (`to_ops_conversation`), em vez de `model_validate` direto no ORM.
    """
    return ConversationResponse(
        id=conversation.id,
        order_item_id=conversation.order_item_id,
        reason=conversation.reason,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_interaction_at=conversation.last_interaction_at,
        effective_priority=effective_priority(
            conversation.calculated_priority, conversation.ops_override
        ),
    )


def _conversation_payload(conversation: Conversation) -> dict:
    return _to_conversation_response(conversation).model_dump(mode="json")


def _parse_before(before: datetime | None) -> datetime | None:
    try:
        return validate_before(before)
    except ValueError as exc:
        raise RequestValidationError(
            [{"type": "value_error", "loc": ["query", "before"], "msg": str(exc), "input": before}]
        ) from exc


@item_router.post(
    "/order-items/{item_id}/conversation",
    response_model=ConversationResponse,
    responses={
        200: {"model": ConversationResponse},
        201: {"model": ConversationResponse},
    },
    summary="Open or reuse the OPEN conversation for an order item",
)
def create_conversation(
    item_id: UUID,
    body: CreateConversationRequest,
    session: SessionDep,
    user: CurrentUser,
) -> JSONResponse:
    load_participant_item(session, item_id, user, for_update=True)
    conversation, created = get_or_create_conversation(session, item_id, body.reason)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=_conversation_payload(conversation),
    )


@item_router.get(
    "/order-items/{item_id}/conversations",
    response_model=list[ConversationResponse],
    summary="List conversations of an order item",
)
def list_conversations(
    item_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    settings: SettingsDep,
) -> list[ConversationResponse]:
    load_participant_item(session, item_id, user)
    conversations = list(
        session.scalars(
            select(Conversation)
            .where(Conversation.order_item_id == item_id)
            .order_by(Conversation.last_interaction_at.desc())
        )
    )
    for conversation in conversations:
        if conversation.status == "open":
            locked = session.scalar(
                select(Conversation).where(Conversation.id == conversation.id).with_for_update()
            )
            if locked is not None:
                maybe_close_inactive(session, locked, settings)
    return [
        _to_conversation_response(conversation)
        for conversation in session.scalars(
            select(Conversation)
            .where(Conversation.order_item_id == item_id)
            .order_by(Conversation.last_interaction_at.desc())
        )
    ]


@conversation_router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get a conversation",
)
def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    settings: SettingsDep,
) -> ConversationResponse:
    conversation = load_participant_conversation(session, conversation_id, user, for_update=True)
    maybe_close_inactive(session, conversation, settings)
    return _to_conversation_response(conversation)


@conversation_router.post(
    "/conversations/{conversation_id}/close",
    response_model=ConversationResponse,
    summary="Close a conversation (seller only)",
)
def close_conversation(
    conversation_id: UUID,
    session: SessionDep,
    seller: SellerUser,
    settings: SettingsDep,
) -> ConversationResponse:
    assert seller.seller_id is not None
    conversation = load_seller_conversation(
        session, conversation_id, seller.seller_id, for_update=True
    )
    return _to_conversation_response(close_by_seller(session, conversation, settings))


@conversation_router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
)
def create_message(
    conversation_id: UUID,
    body: CreateMessageRequest,
    session: SessionDep,
    user: CurrentUser,
    settings: SettingsDep,
) -> Message:
    conversation = load_participant_conversation(session, conversation_id, user, for_update=True)
    return add_message(session, conversation, user, body.content, settings)


@conversation_router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="List messages in a 24h window",
)
def list_messages(
    conversation_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    settings: SettingsDep,
    before: Annotated[datetime | None, Query()] = None,
) -> MessageListResponse:
    parsed_before = _parse_before(before)
    conversation = load_participant_conversation(session, conversation_id, user, for_update=True)
    maybe_close_inactive(session, conversation, settings)

    window_from, window_to, exclusive_to = message_window(before=parsed_before, now=utcnow())
    filters = [
        Message.conversation_id == conversation.id,
        Message.created_at >= window_from,
    ]
    if exclusive_to:
        filters.append(Message.created_at < window_to)
    else:
        filters.append(Message.created_at <= window_to)

    items = list(
        session.scalars(select(Message).where(*filters).order_by(Message.created_at.asc()))
    )
    has_older = bool(
        session.scalar(
            select(
                exists().where(
                    Message.conversation_id == conversation.id,
                    Message.created_at < window_from,
                )
            )
        )
    )
    return MessageListResponse(items=items, from_=window_from, to=window_to, has_older=has_older)
