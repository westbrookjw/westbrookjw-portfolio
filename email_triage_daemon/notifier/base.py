"""Notification interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from email_triage_daemon.models import AlertEvent


class Notifier(ABC):
    """Abstract notifier transport."""

    @abstractmethod
    def send(self, event: AlertEvent) -> None:
        """Send a single alert event."""
