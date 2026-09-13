"""Rotas de Oferta."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import SellerUser
from app.auth.models import User
from app.catalog.models import Offer, Product
from app.catalog.schemas import OfferCreate, OfferResponse, OfferUpdate
from app.core.errors import ForbiddenError, ResourceInUseError, ResourceNotFoundError
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(tags=["offers"])


def _require_owned_offer(offer: Offer | None, seller: User) -> Offer:
    if offer is None:
        raise ResourceNotFoundError("Offer not found")
    if offer.seller_id != seller.seller_id:
        raise ForbiddenError("Offer does not belong to the authenticated seller")
    return offer


@router.get("/offers", response_model=list[OfferResponse], summary="List offers")
def list_offers(session: SessionDep, seller_id: UUID | None = None) -> list[Offer]:
    stmt = select(Offer)
    if seller_id is not None:
        stmt = stmt.where(Offer.seller_id == seller_id)
    return list(session.scalars(stmt).all())


@router.post(
    "/offers",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an offer",
)
def create_offer(payload: OfferCreate, seller: SellerUser, session: SessionDep) -> Offer:
    if session.get(Product, payload.product_id) is None:
        raise ResourceNotFoundError("Product not found")

    offer = Offer(
        product_id=payload.product_id,
        seller_id=seller.seller_id,
        price=Decimal(payload.price),
        stock=payload.stock,
        available=payload.available,
    )
    session.add(offer)
    session.flush()
    return offer


@router.get("/offers/{offer_id}", response_model=OfferResponse, summary="Get an offer")
def get_offer(offer_id: UUID, session: SessionDep) -> Offer:
    offer = session.get(Offer, offer_id)
    if offer is None:
        raise ResourceNotFoundError("Offer not found")
    return offer


@router.patch("/offers/{offer_id}", response_model=OfferResponse, summary="Update an offer")
def update_offer(
    offer_id: UUID, payload: OfferUpdate, seller: SellerUser, session: SessionDep
) -> Offer:
    offer = _require_owned_offer(session.get(Offer, offer_id), seller)

    updates = payload.model_dump(exclude_unset=True)
    if "price" in updates:
        updates["price"] = Decimal(updates["price"])
    for field, value in updates.items():
        setattr(offer, field, value)
    session.flush()
    return offer


@router.delete(
    "/offers/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an offer",
)
def delete_offer(offer_id: UUID, seller: SellerUser, session: SessionDep) -> None:
    offer = _require_owned_offer(session.get(Offer, offer_id), seller)
    try:
        session.delete(offer)
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceInUseError("Offer has associated order items") from exc
