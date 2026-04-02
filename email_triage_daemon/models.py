"""Domain models for normalized messages, classification, and notifications."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Provider(StrEnum):
    """Supported mail providers."""

    FASTMAIL = "fastmail"
    GMAIL = "gmail"


class Importance(StrEnum):
    """Final importance category assigned by the pipeline."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    NORMAL = "normal"
    IGNORE = "ignore"


class NormalizedMessage(BaseModel):
    """Provider-agnostic email message representation."""

    model_config = ConfigDict(extra="forbid")

    provider: Provider
    provider_message_id: str
    thread_id: str | None = None
    received_at: datetime
    sent_at: datetime | None = None
    subject: str
    from_name: str | None = None
    from_email: str
    to_emails: list[str] = Field(default_factory=list)
    cc_emails: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    snippet: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    has_attachments: bool = False
    message_hash: str


class RuleDecision(BaseModel):
    """Deterministic rules outcome before/without LLM."""

    model_config = ConfigDict(extra="forbid")

    needs_llm: bool
    reason_codes: list[str] = Field(default_factory=list)
    forced_importance: Importance | None = None


class LLMClassification(BaseModel):
    """Structured result returned by local LLM."""

    model_config = ConfigDict(extra="forbid")

    importance: Importance
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=3, max_length=280)
    categories: list[str] = Field(default_factory=list)
    action_deadline: Literal["immediate", "today", "this_week", "none"] = "none"


class AlertEvent(BaseModel):
    """Event to be sent to notification providers."""

    model_config = ConfigDict(extra="forbid")

    dedupe_key: str
    importance: Importance
    title: str
    body: str
    source_message_id: str
    source_provider: Provider
    policy_tags: list[str] = Field(default_factory=list)
    created_at: datetime
