"""Unit tests for Slack alerter."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from dq_framework.alerting import SlackAlertError, SlackAlerter
from dq_framework.models import CheckResult, CheckStatus, Severity, SuiteResult


def _result(*, with_critical: bool = False) -> SuiteResult:
    now = datetime.now(UTC)
    results = [
        CheckResult(
            check_name="not_null",
            status=CheckStatus.PASSED,
            severity=Severity.CRITICAL,
            message="ok",
        ),
        CheckResult(
            check_name="range",
            status=CheckStatus.FAILED,
            severity=Severity.WARNING,
            message="2 values out of range",
        ),
    ]
    if with_critical:
        results.append(
            CheckResult(
                check_name="unique",
                status=CheckStatus.FAILED,
                severity=Severity.CRITICAL,
                message="3 duplicates found",
            )
        )
    return SuiteResult(
        suite_name="orders_quality",
        table="analytics.orders",
        results=results,
        started_at=now,
        finished_at=now,
    )


class TestSlackAlerterConstruction:
    def test_requires_webhook(self):
        with pytest.raises(ValueError, match="webhook_url"):
            SlackAlerter(webhook_url="")


class TestSlackPayload:
    def test_payload_contains_header(self):
        alert = SlackAlerter("https://hooks.slack.com/x")
        payload = alert.build_payload(_result())

        assert payload["blocks"][0]["type"] == "header"
        assert "orders_quality" in payload["blocks"][0]["text"]["text"]

    def test_warning_emoji_when_no_critical(self):
        payload = SlackAlerter("https://x").build_payload(_result(with_critical=False))
        header_text = payload["blocks"][0]["text"]["text"]
        assert "⚠️" in header_text

    def test_critical_emoji_when_critical_present(self):
        payload = SlackAlerter("https://x").build_payload(_result(with_critical=True))
        header_text = payload["blocks"][0]["text"]["text"]
        assert "🚨" in header_text

    def test_only_failed_checks_listed(self):
        payload = SlackAlerter("https://x").build_payload(_result())
        section_texts = [
            b["text"]["text"] for b in payload["blocks"] if b["type"] == "section" and "text" in b
        ]
        # "not_null" passed → shouldn't appear as bullet
        bullets = [t for t in section_texts if t.startswith("•")]
        assert all("not_null" not in b for b in bullets)

    def test_max_failures_truncates(self):
        now = datetime.now(UTC)
        results = [
            CheckResult(
                check_name=f"check_{i}",
                status=CheckStatus.FAILED,
                severity=Severity.WARNING,
                message="fail",
            )
            for i in range(10)
        ]
        result = SuiteResult(
            suite_name="s",
            table="t",
            results=results,
            started_at=now,
            finished_at=now,
        )
        payload = SlackAlerter("https://x", max_failures=3).build_payload(result)

        bullets = [
            b for b in payload["blocks"]
            if b["type"] == "section" and b.get("text", {}).get("text", "").startswith("•")
        ]
        assert len(bullets) == 3

    def test_channel_included_when_set(self):
        alert = SlackAlerter("https://x", channel="#alerts")
        payload = alert.build_payload(_result())
        assert payload["channel"] == "#alerts"


class TestSlackSend:
    def test_send_success(self):
        alert = SlackAlerter("https://hooks.slack.com/x")
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            alert.send(_result())  # should not raise

    def test_send_network_error_raises(self):
        import urllib.error

        alert = SlackAlerter("https://hooks.slack.com/x")
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            with pytest.raises(SlackAlertError, match="Failed to reach Slack"):
                alert.send(_result())