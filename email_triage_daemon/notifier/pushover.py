"""Pushover notification sender."""

from __future__ import annotations

import httpx

from email_triage_daemon.models import AlertEvent
from email_triage_daemon.notifier.base import Notifier


class PushoverNotifier(Notifier):
    """Send push notifications through Pushover API."""

    def __init__(self, app_token: str, user_key: str) -> None:
        self._app_token = app_token
        self._user_key = user_key

    def send(self, event: AlertEvent) -> None:
        priority_map = {"critical": 1, "important": 0, "normal": -1, "ignore": -2}

        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": self._app_token,
                    "user": self._user_key,
                    "title": event.title,
                    "message": event.body,
                    "priority": priority_map[event.importance.value],
                },
            )
            resp.raise_for_status()
