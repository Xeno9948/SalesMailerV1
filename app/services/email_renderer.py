from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, StrictUndefined

from app.models import Campaign, CampaignFeature, EmailTemplate, GeneratedEmail, Lead


def _environment() -> Environment:
    return Environment(autoescape=True, undefined=StrictUndefined)


@dataclass
class RenderContext:
    lead: Lead
    brand: Any
    campaign: Campaign | None
    features: list[CampaignFeature]
    tone: str | None
    openai_notes: dict[str, Any] | None = None


class EmailRenderer:
    """Render templated emails using a Jinja2 environment."""

    def __init__(self) -> None:
        self.env = _environment()

    def render(self, template: EmailTemplate, context: RenderContext, *, subject_override: str | None = None) -> GeneratedEmail:
        template_obj = self.env.from_string(template.html_body)
        subject_template = subject_override or template.subject_template

        template_context = {
            "lead": context.lead,
            "brand": context.brand,
            "campaign": context.campaign,
            "features": [
                {
                    "name": c.brand_feature.feature.name,
                    "short_description": c.brand_feature.feature.short_description,
                    "long_description": c.brand_feature.feature.long_description,
                    "asset_label": c.brand_feature.asset_label,
                    "asset_url": c.brand_feature.asset_url,
                    "cta_text": c.brand_feature.cta_text,
                    "highlight_text": c.highlight_text,
                }
                for c in sorted(context.features, key=lambda c: c.sort_order)
            ],
            "tone": context.tone,
            "openai": context.openai_notes or {},
        }

        html_body = template_obj.render(**template_context)

        if subject_template:
            subject = self.env.from_string(subject_template).render(**template_context)
        else:
            subject = context.brand.default_subject or "Confirmation from {brand_name}".format(brand_name=context.brand.name)

        return GeneratedEmail(
            lead_id=context.lead.id,
            campaign_id=context.campaign.id if context.campaign else None,
            template_id=template.id,
            subject=subject,
            html_body=html_body,
            status="draft",
            metadata={"tone": context.tone, "openai": context.openai_notes},
        )
