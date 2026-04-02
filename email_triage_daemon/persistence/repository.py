"""Persistence repository for checkpoints, messages, and alerts."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from email_triage_daemon.models import AlertEvent, Importance, LLMClassification, NormalizedMessage, Provider


class StateRepository:
    """Data access layer for daemon state in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_checkpoint(self, provider: Provider) -> str | None:
        row = self._conn.execute(
            "SELECT checkpoint FROM checkpoints WHERE provider = ?",
            (provider.value,),
        ).fetchone()
        return str(row["checkpoint"]) if row else None

    def set_checkpoint(self, provider: Provider, checkpoint: str | None) -> None:
        self._conn.execute(
            """
            INSERT INTO checkpoints(provider, checkpoint, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(provider)
            DO UPDATE SET checkpoint = excluded.checkpoint, updated_at = excluded.updated_at
            """,
            (provider.value, checkpoint, datetime.now(UTC).isoformat()),
        )
        self._conn.commit()

    def message_exists(self, provider: Provider, provider_message_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM messages WHERE provider = ? AND provider_message_id = ?",
            (provider.value, provider_message_id),
        ).fetchone()
        return row is not None

    def save_message(
        self,
        message: NormalizedMessage,
        importance: Importance,
        reason_codes: list[str],
        llm: LLMClassification | None,
    ) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO messages(
              provider, provider_message_id, message_hash, received_at, from_email,
              subject, snippet, importance, confidence, reason_codes, llm_rationale, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.provider.value,
                message.provider_message_id,
                message.message_hash,
                message.received_at.isoformat(),
                message.from_email,
                message.subject,
                message.snippet,
                importance.value,
                llm.confidence if llm else None,
                json.dumps(reason_codes),
                llm.rationale if llm else None,
                datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()

    def alert_already_sent(self, dedupe_key: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM alerts WHERE dedupe_key = ?", (dedupe_key,)).fetchone()
        return row is not None

    def save_alert(self, event: AlertEvent, channel: str) -> None:
        self._conn.execute(
            """
            INSERT INTO alerts(dedupe_key, provider, provider_message_id, importance, channel, sent_at, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.dedupe_key,
                event.source_provider.value,
                event.source_message_id,
                event.importance.value,
                channel,
                datetime.now(UTC).isoformat(),
                event.model_dump_json(),
            ),
        )
        self._conn.commit()
