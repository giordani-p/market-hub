"""Rotas de Oferta."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Offer, Product, Seller
from app.catalog.schemas import OfferCreate, OfferResponse, OfferUpdate
from app.core.errors import ResourceNotFoundError
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(tags=["offers"])


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
def create_offer(payload: OfferCreate, session: SessionDep) -> Offer:
    if session.get(Product, payload.product_id) is None:
        raise ResourceNotFoundError("Product not found")
    if session.get(Seller, payload.seller_id) is None:
        raise ResourceNotFoundError("Seller not found")

    offer = Offer(
        product_id=payload.product_id,
        seller_id=payload.seller_id,
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
def update_offer(offer_id: UUID, payload: OfferUpdate, session: SessionDep) -> Offer:
    offer = session.get(Offer, offer_id)
    if offer is None:
        raise ResourceNotFoundError("Offer not found")

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
def delete_offer(offer_id: UUID, session: SessionDep) -> None:
    offer = session.get(Offer, offer_id)
    if offer is None:
        raise ResourceNotFoundError("Offer not found")
    session.delete(offer)
    session.flush()
