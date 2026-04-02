"""Configuration loading and validation for the daemon."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PollingConfig(BaseModel):
    """Polling intervals for each provider."""

    model_config = ConfigDict(extra="forbid")

    loop_seconds: int = Field(default=30, ge=5)
    fastmail_seconds: int = Field(default=60, ge=10)
    gmail_seconds: int = Field(default=60, ge=10)


class QuietHoursConfig(BaseModel):
    """Local-time quiet hour window."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    start: str = "22:00"
    end: str = "07:00"
    timezone: str = "America/New_York"
    allow_critical: bool = True


class NotificationConfig(BaseModel):
    """Notification sinks and per-importance policy."""

    model_config = ConfigDict(extra="forbid")

    default_channel: str = "ntfy"
    enabled_for: list[str] = Field(default_factory=lambda: ["critical", "important"])


class RulesConfig(BaseModel):
    """Deterministic sender/domain based policy."""

    model_config = ConfigDict(extra="forbid")

    vip_senders: list[str] = Field(default_factory=list)
    vip_domains: list[str] = Field(default_factory=list)
    ignored_senders: list[str] = Field(default_factory=list)
    ignored_domains: list[str] = Field(default_factory=list)
    always_llm_domains: list[str] = Field(default_factory=list)


class OllamaConfig(BaseModel):
    """Local model settings."""

    model_config = ConfigDict(extra="forbid")

    host: str = "http://127.0.0.1:11434"
    model: str = "llama3.1:8b-instruct"
    timeout_seconds: int = 30


class AppConfig(BaseModel):
    """Root application configuration schema."""

    model_config = ConfigDict(extra="forbid")

    polling: PollingConfig = PollingConfig()
    quiet_hours: QuietHoursConfig = QuietHoursConfig()
    notifications: NotificationConfig = NotificationConfig()
    rules: RulesConfig = RulesConfig()
    ollama: OllamaConfig = OllamaConfig()
    sqlite_path: str = "./state/triage.db"
    log_level: str = "INFO"


def load_config(path: str | Path) -> AppConfig:
    """Load YAML config file into typed model."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration must be a mapping at the top level")

    return AppConfig.model_validate(raw)
