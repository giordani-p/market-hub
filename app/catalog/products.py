"""Rotas de Produto."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog.models import Product
from app.catalog.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.core.errors import ResourceInUseError, ResourceNotFoundError
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductResponse], summary="List products")
def list_products(session: SessionDep) -> list[Product]:
    return list(session.scalars(select(Product)).all())


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(payload: ProductCreate, session: SessionDep) -> Product:
    product = Product(name=payload.name, description=payload.description)
    session.add(product)
    session.flush()
    return product


@router.get("/products/{product_id}", response_model=ProductResponse, summary="Get a product")
def get_product(product_id: UUID, session: SessionDep) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise ResourceNotFoundError("Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductResponse, summary="Update a product")
def update_product(product_id: UUID, payload: ProductUpdate, session: SessionDep) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise ResourceNotFoundError("Product not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)
    session.flush()
    return product


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
def delete_product(product_id: UUID, session: SessionDep) -> None:
    product = session.get(Product, product_id)
    if product is None:
        raise ResourceNotFoundError("Product not found")

    try:
        session.delete(product)
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ResourceInUseError("Product has associated offers") from exc
