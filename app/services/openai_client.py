from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from openai import OpenAI

from app.models import Brand, CampaignFeature, Lead


@dataclass
class OpenAIConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 500


class OpenAIClient:
    """Thin wrapper around the OpenAI client with graceful fallbacks."""

    def __init__(self, *, api_key: str | None = None, config: OpenAIConfig | None = None) -> None:
        self.api_key = api_key
        self.config = config or OpenAIConfig()
        self._client: OpenAI | None = None

        if self.api_key:
            self._client = OpenAI(api_key=self.api_key)

    def _build_prompt(self, brand: Brand, lead: Lead, features: Sequence[CampaignFeature], tone: str | None) -> str:
        feature_lines = []
        for campaign_feature in features:
            bf = campaign_feature.brand_feature
            feature_lines.append(
                f"- {bf.feature.name}: {campaign_feature.highlight_text or bf.feature.short_description}"
            )

        tone_text = tone or brand.default_tone or "professional"

        prompt = (
            "Compose a short paragraph for a confirmation email.\n"
            f"Brand: {brand.name}. Tone: {tone_text}.\n"
            f"Lead: {lead.first_name or ''} {lead.last_name or ''} ({lead.company or 'Unknown company'}).\n"
            "Features to highlight:\n"
            + "\n".join(feature_lines)
            + "\nInclude a warm thank you and mention that further details are attached via the links provided."
        )
        return prompt

    def generate_highlight_copy(
        self,
        *,
        brand: Brand,
        lead: Lead,
        features: Sequence[CampaignFeature],
        tone: str | None,
    ) -> dict[str, Any]:
        if not features:
            return {"summary": "Thank you for your interest!"}

        prompt = self._build_prompt(brand, lead, features, tone)

        if not self._client:
            # Deterministic fallback for development
            return {
                "summary": (
                    f"Hi {lead.first_name or lead.email}, thank you for connecting with {brand.name}. "
                    "Here are the highlights we're excited to share: "
                    + ", ".join(cf.brand_feature.feature.name for cf in features)
                ),
                "model_used": "fallback",
            }

        response = self._client.responses.create(
            model=self.config.model,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            input=prompt,
        )

        text_content = ""
        if response.output and response.output[0].content:
            text_content = "".join(part.text for part in response.output[0].content if hasattr(part, "text"))

        return {
            "summary": text_content.strip(),
            "model_used": self.config.model,
            "prompt_tokens": getattr(response.usage, "input_tokens", None),
            "completion_tokens": getattr(response.usage, "output_tokens", None),
        }
