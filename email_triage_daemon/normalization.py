"""Normalization from provider-specific payloads to common model."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from email.utils import parseaddr
from typing import Any

from email_triage_daemon.connectors.gmail_api import decode_b64url
from email_triage_daemon.models import NormalizedMessage, Provider


def _hash_for_message(parts: list[str]) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_fastmail(raw: dict[str, Any]) -> NormalizedMessage:
    """Convert a Fastmail/JMAP message to NormalizedMessage."""
    from_field = raw.get("from", [{}])[0]
    from_email = from_field.get("email", "unknown@example.com")
    received = datetime.fromisoformat(raw.get("receivedAt", datetime.now(UTC).isoformat()))

    return NormalizedMessage(
        provider=Provider.FASTMAIL,
        provider_message_id=raw["id"],
        thread_id=raw.get("threadId"),
        received_at=received,
        sent_at=datetime.fromisoformat(raw["sentAt"]) if raw.get("sentAt") else None,
        subject=raw.get("subject", "(no subject)"),
        from_name=from_field.get("name"),
        from_email=from_email.lower(),
        to_emails=[x.get("email", "") for x in raw.get("to", []) if x.get("email")],
        cc_emails=[x.get("email", "") for x in raw.get("cc", []) if x.get("email")],
        labels=list(raw.get("mailboxIds", {}).keys()),
        snippet=raw.get("preview"),
        body_text=raw.get("preview"),
        has_attachments=bool(raw.get("hasAttachment", False)),
        message_hash=_hash_for_message([raw["id"], from_email, raw.get("subject", "")]),
    )


def normalize_gmail(raw: dict[str, Any]) -> NormalizedMessage:
    """Convert a Gmail API message payload to NormalizedMessage."""
    payload = raw.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    from_name, from_email = parseaddr(headers.get("from", ""))

    text_body: str | None = None
    if "parts" in payload:
        for part in payload.get("parts", []):
            mime_type = part.get("mimeType")
            data = part.get("body", {}).get("data")
            if mime_type == "text/plain" and data:
                text_body = decode_b64url(data)
                break
    else:
        text_body = decode_b64url(payload.get("body", {}).get("data"))

    internal_date_ms = int(raw.get("internalDate", "0") or "0")
    received = datetime.fromtimestamp(internal_date_ms / 1000, tz=UTC) if internal_date_ms else datetime.now(UTC)

    return NormalizedMessage(
        provider=Provider.GMAIL,
        provider_message_id=raw["id"],
        thread_id=raw.get("threadId"),
        received_at=received,
        sent_at=None,
        subject=headers.get("subject", "(no subject)"),
        from_name=from_name or None,
        from_email=(from_email or "unknown@example.com").lower(),
        to_emails=[x.strip() for x in headers.get("to", "").split(",") if x.strip()],
        cc_emails=[x.strip() for x in headers.get("cc", "").split(",") if x.strip()],
        labels=raw.get("labelIds", []),
        snippet=raw.get("snippet"),
        body_text=text_body,
        has_attachments=any(p.get("filename") for p in payload.get("parts", [])),
        message_hash=_hash_for_message([raw["id"], from_email, headers.get("subject", "")]),
    )
