"""Gmail API polling connector."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email_triage_daemon.connectors.base import EmailConnector, FetchResult


class GmailApiConnector(EmailConnector):
    """Fetch unread/INBOX Gmail messages using OAuth access token."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        *,
        timeout_seconds: int = 20,
    ) -> None:
        self._creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
        self._timeout = timeout_seconds

    def fetch_new(self, checkpoint: str | None) -> FetchResult:
        """Read messages after a history checkpoint; fallback to recent inbox fetch."""
        if self._creds.expired and self._creds.refresh_token:
            self._creds.refresh(Request())

        service = build("gmail", "v1", credentials=self._creds, cache_discovery=False)

        message_ids: list[str] = []
        new_checkpoint = checkpoint

        if checkpoint:
            hist = (
                service.users()
                .history()
                .list(userId="me", startHistoryId=checkpoint, historyTypes=["messageAdded"])
                .execute()
            )
            for item in hist.get("history", []):
                for msg in item.get("messagesAdded", []):
                    message_ids.append(msg["message"]["id"])
            if hist.get("historyId"):
                new_checkpoint = str(hist["historyId"])
        else:
            response = (
                service.users()
                .messages()
                .list(userId="me", q="in:inbox newer_than:2d", maxResults=20)
                .execute()
            )
            message_ids = [m["id"] for m in response.get("messages", [])]
            profile = service.users().getProfile(userId="me").execute()
            new_checkpoint = str(profile.get("historyId"))

        raw_messages: list[dict[str, Any]] = []
        for msg_id in message_ids:
            payload = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            raw_messages.append(payload)

        return FetchResult(
            raw_messages=raw_messages,
            new_checkpoint=new_checkpoint,
            fetched_at=datetime.now(UTC),
        )


def decode_b64url(data: str | None) -> str | None:
    """Decode base64url body to UTF-8 text when present."""
    if not data:
        return None
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
