from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON, event
from sqlmodel import Field, Relationship, SQLModel


class TimestampMixin(SQLModel, table=False):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Brand(TimestampMixin, SQLModel, table=True):
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    slug: str = Field(index=True, unique=True)
    sender_email: Optional[str] = Field(default=None, index=True)
    sender_name: Optional[str] = Field(default=None)
    default_subject: Optional[str] = Field(default=None)
    default_tone: Optional[str] = Field(default=None)
    openai_style_instructions: Optional[str] = Field(default=None)

    templates: list[EmailTemplate] = Relationship(back_populates="brand")
    brand_features: list[BrandFeature] = Relationship(back_populates="brand")
    campaigns: list[Campaign] = Relationship(back_populates="brand")


class Feature(TimestampMixin, SQLModel, table=True):
    __tablename__ = "features"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    short_description: str
    long_description: Optional[str] = Field(default=None)

    brand_links: list[BrandFeature] = Relationship(back_populates="feature")


class BrandFeature(TimestampMixin, SQLModel, table=True):
    __tablename__ = "brand_features"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id")
    feature_id: int = Field(foreign_key="features.id")
    asset_label: Optional[str] = Field(default=None)
    asset_url: Optional[str] = Field(default=None)
    cta_text: Optional[str] = Field(default=None)

    brand: Brand = Relationship(back_populates="brand_features")
    feature: Feature = Relationship(back_populates="brand_links")
    campaign_links: list[CampaignFeature] = Relationship(back_populates="brand_feature")


class EmailTemplate(TimestampMixin, SQLModel, table=True):
    __tablename__ = "email_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id")
    name: str
    subject_template: Optional[str] = Field(default=None)
    html_body: str
    is_default: bool = Field(default=False)

    brand: Brand = Relationship(back_populates="templates")


class Campaign(TimestampMixin, SQLModel, table=True):
    __tablename__ = "campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id")
    name: str
    description: Optional[str] = Field(default=None)
    tone_override: Optional[str] = Field(default=None)
    is_active: bool = Field(default=False, index=True)

    brand: Brand = Relationship(back_populates="campaigns")
    features: list[CampaignFeature] = Relationship(back_populates="campaign")
    generated_emails: list[GeneratedEmail] = Relationship(back_populates="campaign")


class CampaignFeature(TimestampMixin, SQLModel, table=True):
    __tablename__ = "campaign_features"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id")
    brand_feature_id: int = Field(foreign_key="brand_features.id")
    sort_order: int = Field(default=0, index=True)
    highlight_text: Optional[str] = Field(default=None)

    campaign: Campaign = Relationship(back_populates="features")
    brand_feature: BrandFeature = Relationship(back_populates="campaign_links")


class Lead(TimestampMixin, SQLModel, table=True):
    __tablename__ = "leads"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id")
    email: str = Field(index=True)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None)
    job_title: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))

    generated_emails: list[GeneratedEmail] = Relationship(back_populates="lead")


class GeneratedEmail(TimestampMixin, SQLModel, table=True):
    __tablename__ = "generated_emails"

    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id")
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id")
    template_id: Optional[int] = Field(default=None, foreign_key="email_templates.id")
    subject: str
    html_body: str
    status: str = Field(default="draft")
    sent_at: Optional[datetime] = Field(default=None)
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))

    lead: Lead = Relationship(back_populates="generated_emails")
    campaign: Optional[Campaign] = Relationship(back_populates="generated_emails")


def _set_timestamp(mapper, connection, target) -> None:  # type: ignore[no-untyped-def]
    if isinstance(target, TimestampMixin):
        target.updated_at = datetime.utcnow()


for model in (Brand, Feature, BrandFeature, EmailTemplate, Campaign, CampaignFeature, Lead, GeneratedEmail):
    event.listen(model, "before_update", _set_timestamp)

