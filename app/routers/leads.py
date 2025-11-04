from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import gmail_dependency, openai_dependency, renderer_dependency
from app.models import Brand, BrandFeature, Campaign, CampaignFeature, EmailTemplate, GeneratedEmail, Lead
from app.schemas import EmailPreview, EmailSendRequest, GeneratedEmailRead, LeadCreate, LeadRead
from app.services.gmail_client import GmailClient
from app.services.openai_client import OpenAIClient
from app.services.email_renderer import EmailRenderer, RenderContext

router = APIRouter()


DEFAULT_TEMPLATE = """
<h1>{{ brand.name }} - Confirmation</h1>
<p>Hi {{ lead.first_name or lead.email }},</p>
<p>Thank you for reaching out to {{ brand.name }}. We're excited to highlight the following:</p>
<ul>
{% for feature in features %}
    <li><strong>{{ feature.name }}</strong>: {{ feature.highlight_text or feature.short_description }}{% if feature.asset_url %} - <a href="{{ feature.asset_url }}">{{ feature.asset_label or 'Learn more' }}</a>{% endif %}</li>
{% endfor %}
</ul>
<p>{{ openai.summary if openai.summary else '' }}</p>
<p>Warm regards,<br>{{ brand.sender_name or brand.name }}</p>
"""


def _get_brand(session: SessionDep, slug: str) -> Brand:
    statement = select(Brand).where(Brand.slug == slug)
    brand = session.exec(statement).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand


def _get_active_campaign(session: SessionDep, brand: Brand) -> Optional[Campaign]:
    statement = (
        select(Campaign)
        .where(Campaign.brand_id == brand.id)
        .order_by(Campaign.is_active.desc(), Campaign.updated_at.desc())
    )
    return session.exec(statement).first()


def _get_campaign_features(session: SessionDep, campaign: Campaign | None) -> list[CampaignFeature]:
    if not campaign:
        return []
    statement = (
        select(CampaignFeature)
        .where(CampaignFeature.campaign_id == campaign.id)
        .options(
            selectinload(CampaignFeature.brand_feature).selectinload(BrandFeature.feature)
        )
        .order_by(CampaignFeature.sort_order)
    )
    return session.exec(statement).all()


def _get_brand_template(session: SessionDep, brand: Brand) -> EmailTemplate:
    statement = (
        select(EmailTemplate)
        .where(EmailTemplate.brand_id == brand.id)
        .order_by(EmailTemplate.is_default.desc(), EmailTemplate.updated_at.desc())
    )
    template = session.exec(statement).first()
    if template:
        return template
    return EmailTemplate(brand_id=brand.id, name="Default", html_body=DEFAULT_TEMPLATE, is_default=True)


def _generate_email(
    *,
    session: SessionDep,
    lead: Lead,
    brand: Brand,
    campaign: Campaign | None,
    renderer: EmailRenderer,
    openai_client: OpenAIClient,
) -> GeneratedEmail:
    campaign_features = _get_campaign_features(session, campaign)

    openai_notes = openai_client.generate_highlight_copy(
        brand=brand,
        lead=lead,
        features=campaign_features,
        tone=campaign.tone_override if campaign else brand.default_tone,
    )

    template = _get_brand_template(session, brand)
    if template.id is None:
        session.add(template)
        session.commit()
        session.refresh(template)

    context = RenderContext(
        lead=lead,
        brand=brand,
        campaign=campaign,
        features=campaign_features,
        tone=campaign.tone_override if campaign else brand.default_tone,
        openai_notes=openai_notes,
    )

    generated = renderer.render(template, context)
    session.add(generated)
    session.commit()
    session.refresh(generated)
    return generated


@router.post("/", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def ingest_lead(
    payload: LeadCreate,
    session: SessionDep,
    renderer: EmailRenderer = Depends(renderer_dependency),
    openai_client: OpenAIClient = Depends(openai_dependency),
) -> Lead:
    brand = _get_brand(session, payload.brand_slug)

    lead = Lead(
        brand_id=brand.id,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        company=payload.company,
        job_title=payload.job_title,
        phone_number=payload.phone_number,
        metadata=payload.metadata,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    campaign = _get_active_campaign(session, brand)
    _generate_email(
        session=session,
        lead=lead,
        brand=brand,
        campaign=campaign,
        renderer=renderer,
        openai_client=openai_client,
    )

    return lead


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, session: SessionDep) -> Lead:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.get("/{lead_id}/emails", response_model=list[GeneratedEmailRead])
def list_lead_emails(lead_id: int, session: SessionDep) -> list[GeneratedEmail]:
    statement = select(GeneratedEmail).where(GeneratedEmail.lead_id == lead_id)
    return session.exec(statement).all()


@router.post("/{lead_id}/preview", response_model=EmailPreview)
def regenerate_preview(
    lead_id: int,
    session: SessionDep,
    renderer: EmailRenderer = Depends(renderer_dependency),
    openai_client: OpenAIClient = Depends(openai_dependency),
) -> EmailPreview:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    brand = session.get(Brand, lead.brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand missing for lead")

    campaign = _get_active_campaign(session, brand)
    generated = _generate_email(
        session=session,
        lead=lead,
        brand=brand,
        campaign=campaign,
        renderer=renderer,
        openai_client=openai_client,
    )
    return EmailPreview(
        subject=generated.subject,
        html_body=generated.html_body,
        tone_used=campaign.tone_override if campaign else brand.default_tone,
        template_id=generated.template_id,
        campaign_id=generated.campaign_id,
    )


@router.post("/send", response_model=dict)
def send_generated_email(
    payload: EmailSendRequest,
    session: SessionDep,
    gmail_client: GmailClient = Depends(gmail_dependency),
) -> dict:
    generated = session.get(GeneratedEmail, payload.email_id)
    if not generated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated email not found")

    lead = session.get(Lead, generated.lead_id)
    brand = session.get(Brand, lead.brand_id) if lead else None
    if not lead or not brand:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email missing lead or brand context")

    result = gmail_client.send_html_email(
        to_address=lead.email,
        subject=generated.subject,
        html_body=generated.html_body,
        from_address=brand.sender_email or f"info@{brand.slug}.com",
        from_name=brand.sender_name or brand.name,
    )

    if result.get("status") == "sent":
        generated.status = "sent"
        generated.sent_at = datetime.utcnow()
        session.add(generated)
        session.commit()

    return result
