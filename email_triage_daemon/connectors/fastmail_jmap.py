"""Fastmail JMAP polling connector."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from email_triage_daemon.connectors.base import EmailConnector, FetchResult


class FastmailJmapConnector(EmailConnector):
    """Fetch email from Fastmail using the JMAP API."""

    def __init__(self, api_token: str, *, timeout_seconds: int = 20) -> None:
        self._api_token = api_token
        self._base_url = "https://api.fastmail.com/jmap/api/"
        self._timeout = timeout_seconds

    def fetch_new(self, checkpoint: str | None) -> FetchResult:
        """Retrieve message metadata newer than checkpoint state token."""
        with httpx.Client(timeout=self._timeout) as client:
            payload = {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    [
                        "Email/query",
                        {
                            "accountId": "u0",
                            "filter": {"inMailbox": "inbox"},
                            "sort": [{"property": "receivedAt", "isAscending": False}],
                            "limit": 25,
                            **({"sinceQueryState": checkpoint} if checkpoint else {}),
                        },
                        "q1",
                    ],
                    [
                        "Email/get",
                        {
                            "accountId": "u0",
                            "#ids": {
                                "resultOf": "q1",
                                "name": "Email/query",
                                "path": "/ids",
                            },
                            "properties": [
                                "id",
                                "threadId",
                                "receivedAt",
                                "sentAt",
                                "from",
                                "to",
                                "cc",
                                "subject",
                                "preview",
                                "hasAttachment",
                                "mailboxIds",
                                "bodyValues",
                                "textBody",
                            ],
                        },
                        "g1",
                    ],
                ],
            }
            resp = client.post(
                self._base_url,
                headers={"Authorization": f"Bearer {self._api_token}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        method_responses = data.get("methodResponses", [])
        query_state: str | None = None
        messages: list[dict[str, Any]] = []

        for name, body, _tag in method_responses:
            if name == "Email/query":
                query_state = body.get("queryState")
            if name == "Email/get":
                messages = body.get("list", [])

        return FetchResult(
            raw_messages=messages,
            new_checkpoint=query_state,
            fetched_at=datetime.now(UTC),
        )
