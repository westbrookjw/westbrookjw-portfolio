"""ntfy notification sender."""

from __future__ import annotations

import httpx

from email_triage_daemon.models import AlertEvent
from email_triage_daemon.notifier.base import Notifier


class NtfyNotifier(Notifier):
    """Send push notifications to ntfy topic."""

    def __init__(self, server: str, topic: str, token: str | None = None) -> None:
        self._server = server.rstrip("/")
        self._topic = topic
        self._token = token

    def send(self, event: AlertEvent) -> None:
        headers = {"Title": event.title, "Tags": event.importance.value}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{self._server}/{self._topic}",
                content=event.body.encode("utf-8"),
                headers=headers,
            )
            resp.raise_for_status()
