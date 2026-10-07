"""Slack alerting for data quality failures."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from dq_framework.models import SuiteResult


class SlackAlertError(Exception):
    """Raised when the Slack webhook call fails."""


class SlackAlerter:
    """Send a formatted DQ failure notification to a Slack webhook."""

    def __init__(
        self,
        webhook_url: str,
        *,
        channel: str | None = None,
        max_failures: int = 5,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not webhook_url:
            raise ValueError("webhook_url is required")
        self.webhook_url = webhook_url
        self.channel = channel
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------ #
    # Payload construction (pure — easy to unit-test)
    # ------------------------------------------------------------------ #

    def build_payload(self, result: SuiteResult) -> dict[str, Any]:
        """Build the Slack message payload from a SuiteResult."""
        failed = [r for r in result.results if not r.passed and r.status.value != "skipped"]
        critical = [r for r in result.results if r.severity.value == "critical" and not r.passed]

        emoji = "🚨" if critical else "⚠️"
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} DQ Failure: {result.suite_name}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Table:*\n`{result.table}`"},
                    {"type": "mrkdwn", "text": f"*Status:*\n`{result.status.value.upper()}`"},
                    {"type": "mrkdwn", "text": f"*Pass rate:*\n{result.pass_rate:.1%}"},
                    {"type": "mrkdwn", "text": f"*Failures:*\n{len(failed)}"},
                ],
            },
        ]

        for r in failed[: self.max_failures]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"• *`{r.check_name}`* "
                            f"[{r.severity.value}] — {r.message}"
                        ),
                    },
                }
            )

        if len(failed) > self.max_failures:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_...and {len(failed) - self.max_failures} more failure(s)_",
                        }
                    ],
                }
            )

        payload: dict[str, Any] = {"blocks": blocks}
        if self.channel:
            payload["channel"] = self.channel
        return payload

    # ------------------------------------------------------------------ #
    # Sending
    # ------------------------------------------------------------------ #

    def send(self, result: SuiteResult) -> None:
        """Send the alert. Raises SlackAlertError on network/HTTP failure."""
        payload = self.build_payload(result)
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status >= 400:
                    raise SlackAlertError(f"Slack returned HTTP {resp.status}")
        except urllib.error.URLError as exc:
            raise SlackAlertError(f"Failed to reach Slack: {exc}") from exc