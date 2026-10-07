"""Unit tests for core domain models."""

from datetime import UTC, datetime, timedelta

import pytest
from dq_framework.models import (
    CheckResult,
    CheckStatus,
    Severity,
    SuiteResult,
)


def make_result(status: CheckStatus, severity: Severity = Severity.WARNING) -> CheckResult:
    return CheckResult(
        check_name="dummy",
        status=status,
        severity=severity,
        message="dummy message",
    )


class TestCheckResult:
    def test_passed_property(self):
        assert make_result(CheckStatus.PASSED).passed is True
        assert make_result(CheckStatus.FAILED).passed is False

    def test_default_duration_is_zero(self):
        assert make_result(CheckStatus.PASSED).duration_ms == 0.0

    def test_metadata_defaults_to_empty_dict(self):
        assert make_result(CheckStatus.PASSED).metadata == {}


class TestSuiteResult:
    def _make_suite(self, results: list[CheckResult]) -> SuiteResult:
        now = datetime.now(UTC)
        return SuiteResult(
            suite_name="test_suite",
            table="test_table",
            results=results,
            started_at=now,
            finished_at=now + timedelta(milliseconds=100),
        )

    def test_status_passed_when_all_pass(self):
        suite = self._make_suite([make_result(CheckStatus.PASSED)] * 3)
        assert suite.status == CheckStatus.PASSED

    def test_status_failed_when_any_fails(self):
        suite = self._make_suite([make_result(CheckStatus.PASSED), make_result(CheckStatus.FAILED)])
        assert suite.status == CheckStatus.FAILED

    def test_status_error_takes_priority(self):
        suite = self._make_suite([make_result(CheckStatus.FAILED), make_result(CheckStatus.ERROR)])
        assert suite.status == CheckStatus.ERROR

    def test_pass_rate(self):
        suite = self._make_suite(
            [
                make_result(CheckStatus.PASSED),
                make_result(CheckStatus.PASSED),
                make_result(CheckStatus.FAILED),
                make_result(CheckStatus.PASSED),
            ]
        )
        assert suite.pass_rate == pytest.approx(0.75)

    def test_pass_rate_empty(self):
        assert self._make_suite([]).pass_rate == 0.0

    def test_critical_failures_filter(self):
        suite = self._make_suite(
            [
                make_result(CheckStatus.FAILED, Severity.CRITICAL),
                make_result(CheckStatus.FAILED, Severity.WARNING),
                make_result(CheckStatus.PASSED, Severity.CRITICAL),
            ]
        )
        assert len(suite.critical_failures) == 1

    def test_duration_ms(self):
        suite = self._make_suite([make_result(CheckStatus.PASSED)])
        assert suite.duration_ms == pytest.approx(100.0)
        # Di tests/unit/test_models.py, dalam class TestSuiteResult:

    def test_failed_checks_filter(self):
        suite = self._make_suite(
            [
                make_result(CheckStatus.PASSED),
                make_result(CheckStatus.FAILED),
                make_result(CheckStatus.ERROR),
            ]
        )
        assert len(suite.failed_checks) == 1
