"""Local Ollama classifier client."""

from __future__ import annotations

import json

import httpx

from email_triage_daemon.classifier.prompt import SYSTEM_PROMPT, build_user_prompt
from email_triage_daemon.models import LLMClassification, NormalizedMessage


class OllamaClassifier:
    """Calls Ollama chat API and validates strict JSON output."""

    def __init__(self, host: str, model: str, timeout_seconds: int = 30) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    def classify(self, message: NormalizedMessage) -> LLMClassification:
        """Classify message importance with local model response validation."""
        payload = {
            "model": self._model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(message)},
            ],
        }

        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{self._host}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            content = data["message"]["content"]
            parsed = json.loads(content)
            return LLMClassification.model_validate(parsed)
        except (KeyError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid response from Ollama: {data}") from exc
