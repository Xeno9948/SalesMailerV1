from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ORMBase(BaseModel):
    class Config:
        from_attributes = True


class FeatureBase(BaseModel):
    name: str
    short_description: str
    long_description: Optional[str] = None


class FeatureCreate(FeatureBase):
    pass


class FeatureRead(FeatureBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class BrandBase(BaseModel):
    name: str
    slug: str
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    default_subject: Optional[str] = None
    default_tone: Optional[str] = None
    openai_style_instructions: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    default_subject: Optional[str] = None
    default_tone: Optional[str] = None
    openai_style_instructions: Optional[str] = None


class BrandRead(BrandBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class BrandFeatureBase(BaseModel):
    brand_id: int
    feature_id: int
    asset_label: Optional[str] = None
    asset_url: Optional[str] = None
    cta_text: Optional[str] = None


class BrandFeatureCreate(BrandFeatureBase):
    pass


class BrandFeatureUpdate(BaseModel):
    asset_label: Optional[str] = None
    asset_url: Optional[str] = None
    cta_text: Optional[str] = None


class BrandFeatureRead(BrandFeatureBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime
    feature: FeatureRead


class EmailTemplateBase(BaseModel):
    brand_id: int
    name: str
    subject_template: Optional[str] = None
    html_body: str
    is_default: bool = False


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject_template: Optional[str] = None
    html_body: Optional[str] = None
    is_default: Optional[bool] = None


class EmailTemplateRead(EmailTemplateBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CampaignBase(BaseModel):
    brand_id: int
    name: str
    description: Optional[str] = None
    tone_override: Optional[str] = None
    is_active: bool = False


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tone_override: Optional[str] = None
    is_active: Optional[bool] = None


class CampaignRead(CampaignBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CampaignFeatureBase(BaseModel):
    campaign_id: int
    brand_feature_id: int
    sort_order: int = 0
    highlight_text: Optional[str] = None


class CampaignFeatureCreate(CampaignFeatureBase):
    pass


class CampaignFeatureUpdate(BaseModel):
    sort_order: Optional[int] = None
    highlight_text: Optional[str] = None


class CampaignFeatureRead(CampaignFeatureBase, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime
    brand_feature: BrandFeatureRead


class LeadCreate(BaseModel):
    brand_slug: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    metadata: Optional[dict] = None


class LeadRead(ORMBase):
    id: int
    brand_id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    phone_number: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class GeneratedEmailRead(ORMBase):
    id: int
    lead_id: int
    campaign_id: Optional[int]
    template_id: Optional[int]
    subject: str
    html_body: str
    status: str
    sent_at: Optional[datetime]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class EmailPreview(BaseModel):
    subject: str
    html_body: str
    tone_used: Optional[str] = None
    template_id: Optional[int] = None
    campaign_id: Optional[int] = None


class EmailSendRequest(BaseModel):
    email_id: int

