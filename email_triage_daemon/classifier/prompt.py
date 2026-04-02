"""Prompt templates and strict JSON contract for Ollama classification."""

from __future__ import annotations

from textwrap import dedent

from email_triage_daemon.models import NormalizedMessage

SYSTEM_PROMPT = dedent(
    """
    You are an email triage classifier.
    Return ONLY valid JSON (no markdown, no extra keys).
    Classify message importance as one of: critical, important, normal, ignore.
    """
).strip()

JSON_CONTRACT = {
    "importance": "critical|important|normal|ignore",
    "confidence": "float 0.0..1.0",
    "rationale": "short reason <= 280 chars",
    "categories": ["billing", "security", "calendar", "legal", "personal", "marketing", "ops"],
    "action_deadline": "immediate|today|this_week|none",
}


def build_user_prompt(message: NormalizedMessage) -> str:
    """Build constrained prompt containing normalized email content."""
    return dedent(
        f"""
        Schema:
        {JSON_CONTRACT}

        Message fields:
        provider: {message.provider}
        from_email: {message.from_email}
        subject: {message.subject}
        snippet: {message.snippet or ''}
        body_text: {(message.body_text or '')[:1500]}
        has_attachments: {message.has_attachments}

        Rules:
        - critical: legal deadlines, security incidents, fraud, urgent family emergency
        - important: actionable work/personal matters worth near-term attention
        - normal: informational but not urgent
        - ignore: newsletters/promotions/no action needed
        """
    ).strip()
