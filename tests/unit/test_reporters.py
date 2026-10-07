"""Unit tests for reporters."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from dq_framework.models import CheckResult, CheckStatus, Severity, SuiteResult
from dq_framework.reporters import HTMLReporter, JSONReporter


def _sample_result() -> SuiteResult:
    now = datetime.now(UTC)
    results = [
        CheckResult(
            check_name="not_null",
            status=CheckStatus.PASSED,
            severity=Severity.CRITICAL,
            message="Column 'id' has no nulls (3 rows)",
            observed_value=0,
            expected_value=0,
            metadata={"column": "id"},
        ),
        CheckResult(
            check_name="range",
            status=CheckStatus.FAILED,
            severity=Severity.WARNING,
            message="Column 'amount' has 2 values out of range",
            observed_value=2,
            expected_value=0,
            metadata={"column": "amount"},
        ),
    ]
    return SuiteResult(
        suite_name="orders_quality",
        table="analytics.orders",
        results=results,
        started_at=now,
        finished_at=now + timedelta(milliseconds=42),
    )


class TestJSONReporter:
    def test_render_returns_valid_json(self):
        reporter = JSONReporter()
        payload = json.loads(reporter.render(_sample_result()))

        assert payload["suite_name"] == "orders_quality"
        assert payload["status"] == "failed"
        assert len(payload["results"]) == 2

    def test_render_contains_status_per_check(self):
        payload = json.loads(JSONReporter().render(_sample_result()))
        statuses = [r["status"] for r in payload["results"]]
        assert "passed" in statuses
        assert "failed" in statuses

    def test_write_creates_file(self, tmp_path: Path):
        path = tmp_path / "out.json"
        written = JSONReporter().write(_sample_result(), path)

        assert written == path
        assert path.exists()
        assert json.loads(path.read_text())["suite_name"] == "orders_quality"

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "deep" / "nested" / "out.json"
        JSONReporter().write(_sample_result(), path)
        assert path.exists()


class TestHTMLReporter:
    def test_render_returns_html(self):
        html = HTMLReporter().render(_sample_result())

        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "orders_quality" in html
        assert "analytics.orders" in html

    def test_render_shows_pass_rate(self):
        html = HTMLReporter().render(_sample_result())
        # 1 passed out of 2 = 50.0%
        assert "50.0%" in html

    def test_render_shows_status_classes(self):
        html = HTMLReporter().render(_sample_result())
        assert 'class="badge badge-passed"' in html
        assert 'class="badge badge-failed"' in html

    def test_escaping_is_applied(self):
        """HTML in message should be escaped."""
        now = datetime.now(UTC)
        result = SuiteResult(
            suite_name="xss_test",
            table="t",
            results=[
                CheckResult(
                    check_name="evil",
                    status=CheckStatus.FAILED,
                    severity=Severity.WARNING,
                    message="<script>alert('xss')</script>",
                )
            ],
            started_at=now,
            finished_at=now,
        )
        html = HTMLReporter().render(result)

        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_write_creates_file(self, tmp_path: Path):
        path = tmp_path / "report.html"
        HTMLReporter().write(_sample_result(), path)

        assert path.exists()
        assert "<!DOCTYPE html>" in path.read_text()