"""Daemon entrypoint for local-first email triage."""

from __future__ import annotations

import os
import signal
import time
from datetime import UTC, datetime
from pathlib import Path

import structlog

from email_triage_daemon.classifier.ollama_client import OllamaClassifier
from email_triage_daemon.config import AppConfig, load_config
from email_triage_daemon.connectors.fastmail_jmap import FastmailJmapConnector
from email_triage_daemon.connectors.gmail_api import GmailApiConnector
from email_triage_daemon.logging_config import configure_logging
from email_triage_daemon.models import Provider
from email_triage_daemon.normalization import normalize_fastmail, normalize_gmail
from email_triage_daemon.notifier.ntfy import NtfyNotifier
from email_triage_daemon.notifier.pushover import PushoverNotifier
from email_triage_daemon.orchestrator import TriageEngine
from email_triage_daemon.persistence.db import connect, initialize_schema
from email_triage_daemon.persistence.repository import StateRepository
from email_triage_daemon.utils.retry import retry_with_backoff

logger = structlog.get_logger(__name__)
RUNNING = True


def _handle_signal(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def _build_notifier(config: AppConfig):
    channel = config.notifications.default_channel
    if channel == "pushover":
        return PushoverNotifier(
            app_token=os.environ["PUSHOVER_APP_TOKEN"],
            user_key=os.environ["PUSHOVER_USER_KEY"],
        )
    return NtfyNotifier(
        server=os.environ.get("NTFY_SERVER", "https://ntfy.sh"),
        topic=os.environ["NTFY_TOPIC"],
        token=os.environ.get("NTFY_TOKEN"),
    )


def run(config_path: str = "./config/policy.yaml") -> None:
    """Run daemon loop until termination signal received."""
    config = load_config(config_path)
    configure_logging(config.log_level)

    conn = connect(config.sqlite_path)
    schema_path = str(Path(__file__).parent / "persistence" / "schema.sql")
    initialize_schema(conn, schema_path)
    repo = StateRepository(conn)

    classifier = OllamaClassifier(
        host=config.ollama.host,
        model=config.ollama.model,
        timeout_seconds=config.ollama.timeout_seconds,
    )
    notifier = _build_notifier(config)
    engine = TriageEngine(config, repo, classifier, notifier)

    fastmail = FastmailJmapConnector(api_token=os.environ["FASTMAIL_API_TOKEN"])
    gmail = GmailApiConnector(
        access_token=os.environ["GMAIL_ACCESS_TOKEN"],
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
    )

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("daemon_started", started_at=datetime.now(UTC).isoformat())
    while RUNNING:
        for provider, connector, normalizer in [
            (Provider.FASTMAIL, fastmail, normalize_fastmail),
            (Provider.GMAIL, gmail, normalize_gmail),
        ]:
            checkpoint = repo.get_checkpoint(provider)
            try:
                result = retry_with_backoff(lambda: connector.fetch_new(checkpoint))
            except Exception as exc:  # noqa: BLE001
                logger.error("fetch_failed", provider=provider.value, error=str(exc))
                continue

            for raw in result.raw_messages:
                try:
                    message = normalizer(raw)
                    engine.process_message(message)
                except Exception as exc:  # noqa: BLE001
                    logger.error("message_processing_failed", provider=provider.value, error=str(exc))

            repo.set_checkpoint(provider, result.new_checkpoint)

        time.sleep(config.polling.loop_seconds)

    logger.info("daemon_stopped", stopped_at=datetime.now(UTC).isoformat())


if __name__ == "__main__":
    run()
