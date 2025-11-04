from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Brand
from app.schemas import BrandCreate, BrandRead, BrandUpdate

router = APIRouter()


@router.get("/", response_model=list[BrandRead])
def list_brands(session: SessionDep) -> list[Brand]:
    return session.exec(select(Brand)).all()


@router.post("/", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, session: SessionDep) -> Brand:
    brand = Brand(**payload.model_dump())
    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: int, session: SessionDep) -> Brand:
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand


@router.patch("/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: int, payload: BrandUpdate, session: SessionDep) -> Brand:
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, value)

    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, session: SessionDep) -> None:
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    session.delete(brand)
    session.commit()
