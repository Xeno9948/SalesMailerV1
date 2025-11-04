from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import BrandFeature, Feature
from app.schemas import (
    BrandFeatureCreate,
    BrandFeatureRead,
    BrandFeatureUpdate,
    FeatureCreate,
    FeatureRead,
)

router = APIRouter()


@router.get("/", response_model=list[FeatureRead])
def list_features(session: SessionDep) -> list[Feature]:
    return session.exec(select(Feature)).all()


@router.post("/", response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
def create_feature(payload: FeatureCreate, session: SessionDep) -> Feature:
    feature = Feature(**payload.model_dump())
    session.add(feature)
    session.commit()
    session.refresh(feature)
    return feature


@router.post("/brand", response_model=BrandFeatureRead, status_code=status.HTTP_201_CREATED)
def attach_feature_to_brand(payload: BrandFeatureCreate, session: SessionDep) -> BrandFeature:
    brand_feature = BrandFeature(**payload.model_dump())
    session.add(brand_feature)
    session.commit()
    session.refresh(brand_feature)
    session.refresh(brand_feature, attribute_names=["feature"])
    return brand_feature


@router.patch("/brand/{brand_feature_id}", response_model=BrandFeatureRead)
def update_brand_feature(brand_feature_id: int, payload: BrandFeatureUpdate, session: SessionDep) -> BrandFeature:
    brand_feature = session.get(BrandFeature, brand_feature_id)
    if not brand_feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand feature not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand_feature, field, value)

    session.add(brand_feature)
    session.commit()
    session.refresh(brand_feature)
    session.refresh(brand_feature, attribute_names=["feature"])
    return brand_feature


@router.get("/brand/{brand_id}", response_model=list[BrandFeatureRead])
def list_brand_features(brand_id: int, session: SessionDep) -> list[BrandFeature]:
    statement = select(BrandFeature).where(BrandFeature.brand_id == brand_id)
    results = session.exec(statement).all()
    for result in results:
        session.refresh(result, attribute_names=["feature"])
    return results


@router.delete("/brand/{brand_feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand_feature(brand_feature_id: int, session: SessionDep) -> None:
    brand_feature = session.get(BrandFeature, brand_feature_id)
    if not brand_feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand feature not found")

    session.delete(brand_feature)
    session.commit()
