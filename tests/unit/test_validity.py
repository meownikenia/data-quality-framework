"""Unit tests for validity checks."""

import pandas as pd
import pytest
from dq_framework.checks.validity import RangeCheck, RegexCheck
from dq_framework.models import CheckStatus


class TestRangeCheck:
    def test_passes_when_all_in_range(self):
        df = pd.DataFrame({"age": [18, 25, 30, 65]})
        result = RangeCheck(column="age", min=0, max=100).run(df)

        assert result.status == CheckStatus.PASSED
        assert result.observed_value == 0

    def test_fails_when_out_of_range(self):
        df = pd.DataFrame({"age": [18, -5, 150, 30]})
        result = RangeCheck(column="age", min=0, max=100).run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 2

    def test_min_only(self):
        df = pd.DataFrame({"score": [10, 20, 5]})
        result = RangeCheck(column="score", min=10).run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 1

    def test_max_only(self):
        df = pd.DataFrame({"score": [10, 20, 5]})
        result = RangeCheck(column="score", max=15).run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 1

    def test_exclusive_bounds(self):
        df = pd.DataFrame({"score": [10, 20]})
        # exclusive min=10 → 10 should fail
        result = RangeCheck(column="score", min=10, inclusive=False).run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 1

    def test_requires_min_or_max(self):
        with pytest.raises(ValueError):
            RangeCheck(column="x")

    def test_error_when_column_missing(self):
        df = pd.DataFrame({"a": [1]})
        result = RangeCheck(column="x", min=0).run(df)

        assert result.status == CheckStatus.ERROR

    def test_error_when_not_numeric(self):
        df = pd.DataFrame({"name": ["alice", "bob"]})
        result = RangeCheck(column="name", min=0).run(df)

        assert result.status == CheckStatus.ERROR

    def test_nulls_ignored(self):
        df = pd.DataFrame({"age": [18, None, 30]})
        result = RangeCheck(column="age", min=0, max=100).run(df)

        assert result.status == CheckStatus.PASSED


class TestRegexCheck:
    def test_passes_when_all_match(self):
        df = pd.DataFrame({"email": ["a@x.com", "b@y.com"]})
        result = RegexCheck(column="email", pattern=r"^[\w.]+@[\w.]+\.\w+$").run(df)

        assert result.status == CheckStatus.PASSED

    def test_fails_when_some_dont_match(self):
        df = pd.DataFrame({"email": ["a@x.com", "invalid", "b@y.com"]})
        result = RegexCheck(column="email", pattern=r"^[\w.]+@[\w.]+\.\w+$").run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 1

    def test_error_when_column_missing(self):
        df = pd.DataFrame({"a": ["x"]})
        result = RegexCheck(column="email", pattern=r".*").run(df)

        assert result.status == CheckStatus.ERROR

    def test_metadata_contains_pattern(self):
        df = pd.DataFrame({"code": ["ABC123"]})
        result = RegexCheck(column="code", pattern=r"^[A-Z]+\d+$").run(df)

        assert result.metadata["pattern"] == r"^[A-Z]+\d+$"
