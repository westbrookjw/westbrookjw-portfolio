"""Connector interfaces for email providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class FetchResult:
    """Result payload from provider fetch operation."""

    raw_messages: list[dict[str, Any]]
    new_checkpoint: str | None
    fetched_at: datetime


class EmailConnector(ABC):
    """Abstract connector contract for polling new provider messages."""

    @abstractmethod
    def fetch_new(self, checkpoint: str | None) -> FetchResult:
        """Fetch all new messages after the stored checkpoint."""
