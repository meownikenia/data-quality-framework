"""Unit tests for volume and freshness checks."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from dq_framework.checks.volume import FreshnessCheck, RowCountCheck
from dq_framework.models import CheckStatus, Severity


class TestRowCountCheck:
    def test_passes_within_range(self):
        df = pd.DataFrame({"x": range(50)})
        result = RowCountCheck(min=10, max=100).run(df)

        assert result.status == CheckStatus.PASSED
        assert result.observed_value == 50

    def test_fails_below_min(self):
        df = pd.DataFrame({"x": range(5)})
        result = RowCountCheck(min=10).run(df)

        assert result.status == CheckStatus.FAILED

    def test_fails_above_max(self):
        df = pd.DataFrame({"x": range(200)})
        result = RowCountCheck(max=100).run(df)

        assert result.status == CheckStatus.FAILED

    def test_requires_min_or_max(self):
        with pytest.raises(ValueError):
            RowCountCheck()

    def test_min_only(self):
        df = pd.DataFrame({"x": range(50)})
        result = RowCountCheck(min=10).run(df)

        assert result.status == CheckStatus.PASSED


class TestFreshnessCheck:
    def test_passes_when_fresh(self):
        now = datetime.now(UTC)
        df = pd.DataFrame({"ts": [now - timedelta(hours=1), now]})
        result = FreshnessCheck(column="ts", max_age_hours=24).run(df)

        assert result.status == CheckStatus.PASSED

    def test_fails_when_stale(self):
        old = datetime.now(UTC) - timedelta(hours=48)
        df = pd.DataFrame({"ts": [old]})
        result = FreshnessCheck(column="ts", max_age_hours=24).run(df)

        assert result.status == CheckStatus.FAILED

    def test_error_when_column_missing(self):
        df = pd.DataFrame({"x": [1]})
        result = FreshnessCheck(column="ts", max_age_hours=24).run(df)

        assert result.status == CheckStatus.ERROR

    def test_error_when_no_valid_timestamps(self):
        df = pd.DataFrame({"ts": ["not-a-date", "also-bad"]})
        result = FreshnessCheck(column="ts", max_age_hours=24).run(df)

        assert result.status == CheckStatus.ERROR

    def test_severity_is_critical(self):
        now = datetime.now(UTC)
        df = pd.DataFrame({"ts": [now]})
        result = FreshnessCheck(column="ts", max_age_hours=24).run(df)

        assert result.severity == Severity.CRITICAL

    def test_handles_naive_datetime(self):
        # Timestamp tanpa timezone → diasumsikan UTC
        df = pd.DataFrame({"ts": [datetime.now()]})
        result = FreshnessCheck(column="ts", max_age_hours=1).run(df)

        assert result.status == CheckStatus.PASSED