from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.services.email_renderer import EmailRenderer
from app.services.gmail_client import GmailClient, GmailSettings
from app.services.openai_client import OpenAIClient, OpenAIConfig


@lru_cache
def get_renderer() -> EmailRenderer:
    return EmailRenderer()


@lru_cache
def get_openai_service(settings: Settings) -> OpenAIClient:
    if settings.openai_api_key:
        config = OpenAIConfig(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )
        return OpenAIClient(api_key=settings.openai_api_key, config=config)
    return OpenAIClient()


@lru_cache
def get_gmail_service(settings: Settings) -> GmailClient:
    if all(
        [
            settings.gmail_user_id,
            settings.gmail_token,
            settings.gmail_refresh_token,
            settings.gmail_client_id,
            settings.gmail_client_secret,
        ]
    ):
        gmail_settings = GmailSettings(
            user_id=settings.gmail_user_id or "me",
            token=settings.gmail_token or "",
            refresh_token=settings.gmail_refresh_token or "",
            client_id=settings.gmail_client_id or "",
            client_secret=settings.gmail_client_secret or "",
            token_uri=settings.gmail_token_uri,
        )
        return GmailClient(gmail_settings)
    return GmailClient()


def settings_dependency() -> Settings:
    return get_settings()


def renderer_dependency() -> EmailRenderer:
    return get_renderer()


def openai_dependency(settings: Settings = Depends(settings_dependency)) -> OpenAIClient:
    return get_openai_service(settings)


def gmail_dependency(settings: Settings = Depends(settings_dependency)) -> GmailClient:
    return get_gmail_service(settings)
