"""End-to-end triage orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parseaddr

import structlog

from email_triage_daemon.classifier.ollama_client import OllamaClassifier
from email_triage_daemon.config import AppConfig
from email_triage_daemon.models import AlertEvent, Importance, LLMClassification, NormalizedMessage, Provider
from email_triage_daemon.notifier.base import Notifier
from email_triage_daemon.persistence.repository import StateRepository
from email_triage_daemon.rules import apply_pre_rules

logger = structlog.get_logger(__name__)


def _domain(address: str) -> str:
    return parseaddr(address)[1].split("@")[-1].lower()


def _can_notify(config: AppConfig, importance: Importance, now: datetime) -> bool:
    if importance.value not in config.notifications.enabled_for:
        return False

    qh = config.quiet_hours
    if not qh.enabled:
        return True

    # Naive local comparison for v1; timezone conversion can be added in v2.
    current = now.strftime("%H:%M")
    in_quiet_window = qh.start <= current or current <= qh.end
    if in_quiet_window and importance != Importance.CRITICAL:
        return False

    return True


def _build_alert(message: NormalizedMessage, importance: Importance, tags: list[str]) -> AlertEvent:
    title = f"{importance.value.upper()}: {message.subject[:80]}"
    body = f"From: {message.from_email}\nSnippet: {(message.snippet or '')[:280]}"
    dedupe_key = f"{message.provider.value}:{message.provider_message_id}:{importance.value}"
    return AlertEvent(
        dedupe_key=dedupe_key,
        importance=importance,
        title=title,
        body=body,
        source_message_id=message.provider_message_id,
        source_provider=message.provider,
        policy_tags=tags,
        created_at=datetime.now(UTC),
    )


class TriageEngine:
    """Coordinates rules, optional LLM, persistence, and notifications."""

    def __init__(
        self,
        config: AppConfig,
        repo: StateRepository,
        classifier: OllamaClassifier,
        notifier: Notifier,
    ) -> None:
        self._config = config
        self._repo = repo
        self._classifier = classifier
        self._notifier = notifier

    def process_message(self, message: NormalizedMessage) -> None:
        """Run pipeline for a single normalized message."""
        if self._repo.message_exists(message.provider, message.provider_message_id):
            logger.debug("duplicate_message_skip", message_id=message.provider_message_id)
            return

        rule_decision = apply_pre_rules(message, self._config.rules)
        llm_result: LLMClassification | None = None

        if rule_decision.needs_llm:
            llm_result = self._classifier.classify(message)
            importance = llm_result.importance
            reason_codes = [*rule_decision.reason_codes, "llm"]
        else:
            importance = rule_decision.forced_importance or Importance.NORMAL
            reason_codes = rule_decision.reason_codes

        self._repo.save_message(message, importance, reason_codes, llm_result)
        now = datetime.now(UTC)

        if not _can_notify(self._config, importance, now):
            logger.info("notification_suppressed", importance=importance.value, message_id=message.provider_message_id)
            return

        if importance in {Importance.IGNORE, Importance.NORMAL}:
            return

        alert = _build_alert(message, importance, reason_codes)
        if self._repo.alert_already_sent(alert.dedupe_key):
            logger.debug("duplicate_alert_skip", dedupe_key=alert.dedupe_key)
            return

        self._notifier.send(alert)
        self._repo.save_alert(alert, self._config.notifications.default_channel)
        logger.info("alert_sent", dedupe_key=alert.dedupe_key, importance=importance.value)
