from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


@dataclass
class GmailSettings:
    user_id: str
    token: str
    refresh_token: str
    client_id: str
    client_secret: str
    token_uri: str = "https://oauth2.googleapis.com/token"


class GmailClient:
    """Wrapper around the Gmail API with structured logging."""

    def __init__(self, settings: GmailSettings | None = None) -> None:
        self.settings = settings
        self._service = None
        if settings:
            self._service = self._build_service(settings)

    def _build_service(self, settings: GmailSettings):  # type: ignore[no-untyped-def]
        creds = Credentials(
            token=settings.token,
            refresh_token=settings.refresh_token,
            token_uri=settings.token_uri,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        return build("gmail", "v1", credentials=creds)

    def send_html_email(
        self,
        *,
        to_address: str,
        subject: str,
        html_body: str,
        from_address: str,
        from_name: Optional[str] = None,
    ) -> dict[str, Any]:
        if not self._service:
            logger.warning("Gmail service not configured; skipping send.")
            return {"status": "skipped", "reason": "gmail_not_configured"}

        message = EmailMessage()
        message["To"] = to_address
        message["From"] = f"{from_name} <{from_address}>" if from_name else from_address
        message["Subject"] = subject
        message.set_content("This email requires an HTML capable client.")
        message.add_alternative(html_body, subtype="html")

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_data = {"raw": encoded_message}

        response = (
            self._service.users().messages().send(userId=self.settings.user_id, body=send_data).execute()
        )
        logger.info("Email sent via Gmail API", extra={"response": response})
        return {"status": "sent", "response": response}
