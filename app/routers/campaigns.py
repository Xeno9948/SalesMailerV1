from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Brand, Campaign, CampaignFeature
from app.schemas import (
    CampaignCreate,
    CampaignFeatureCreate,
    CampaignFeatureRead,
    CampaignFeatureUpdate,
    CampaignRead,
    CampaignUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[CampaignRead])
def list_campaigns(session: SessionDep) -> list[Campaign]:
    return session.exec(select(Campaign)).all()


@router.post("/", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, session: SessionDep) -> Campaign:
    brand = session.get(Brand, payload.brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if payload.is_active:
        for active_campaign in session.exec(
            select(Campaign).where(Campaign.brand_id == brand.id, Campaign.is_active == True)
        ):
            active_campaign.is_active = False
            session.add(active_campaign)

    campaign = Campaign(**payload.model_dump())
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignRead)
def update_campaign(campaign_id: int, payload: CampaignUpdate, session: SessionDep) -> Campaign:
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_active"):
        for other in session.exec(
            select(Campaign).where(Campaign.brand_id == campaign.brand_id, Campaign.id != campaign.id)
        ):
            if other.is_active:
                other.is_active = False
                session.add(other)

    for field, value in updates.items():
        setattr(campaign, field, value)

    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/features", response_model=CampaignFeatureRead, status_code=status.HTTP_201_CREATED)
def add_campaign_feature(campaign_id: int, payload: CampaignFeatureCreate, session: SessionDep) -> CampaignFeature:
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if payload.campaign_id != campaign_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign id mismatch")

    campaign_feature = CampaignFeature(**payload.model_dump())
    session.add(campaign_feature)
    session.commit()
    session.refresh(campaign_feature)
    session.refresh(campaign_feature, attribute_names=["brand_feature"])
    if campaign_feature.brand_feature:
        session.refresh(campaign_feature.brand_feature, attribute_names=["feature"])
    return campaign_feature


@router.patch("/features/{campaign_feature_id}", response_model=CampaignFeatureRead)
def update_campaign_feature(
    campaign_feature_id: int, payload: CampaignFeatureUpdate, session: SessionDep
) -> CampaignFeature:
    campaign_feature = session.get(CampaignFeature, campaign_feature_id)
    if not campaign_feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign feature not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign_feature, field, value)

    session.add(campaign_feature)
    session.commit()
    session.refresh(campaign_feature)
    session.refresh(campaign_feature, attribute_names=["brand_feature"])
    if campaign_feature.brand_feature:
        session.refresh(campaign_feature.brand_feature, attribute_names=["feature"])
    return campaign_feature


@router.get("/{campaign_id}/features", response_model=list[CampaignFeatureRead])
def list_campaign_features(campaign_id: int, session: SessionDep) -> list[CampaignFeature]:
    statement = select(CampaignFeature).where(CampaignFeature.campaign_id == campaign_id)
    results = session.exec(statement).all()
    for result in results:
        session.refresh(result, attribute_names=["brand_feature"])
        if result.brand_feature:
            session.refresh(result.brand_feature, attribute_names=["feature"])
    return results


@router.delete("/features/{campaign_feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_feature(campaign_feature_id: int, session: SessionDep) -> None:
    campaign_feature = session.get(CampaignFeature, campaign_feature_id)
    if not campaign_feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign feature not found")

    session.delete(campaign_feature)
    session.commit()
