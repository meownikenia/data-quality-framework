"""Unit tests for completeness checks."""

import pandas as pd
from dq_framework.checks.completeness import NotNullCheck, UniqueCheck
from dq_framework.models import CheckStatus, Severity

# --------------------------------------------------------------------- #
# NotNullCheck
# --------------------------------------------------------------------- #


class TestNotNullCheck:
    def test_passes_when_no_nulls(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = NotNullCheck(column="id").run(df)

        assert result.status == CheckStatus.PASSED
        assert result.observed_value == 0
        assert result.expected_value == 0
        assert result.check_name == "not_null"
        assert result.severity == Severity.CRITICAL

    def test_fails_when_nulls_present(self):
        df = pd.DataFrame({"id": [1, None, 3, None]})
        result = NotNullCheck(column="id").run(df)

        assert result.status == CheckStatus.FAILED
        assert result.observed_value == 2
        assert "2/4" in result.message

    def test_error_when_column_missing(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = NotNullCheck(column="nonexistent").run(df)

        assert result.status == CheckStatus.ERROR
        assert "not found" in result.message.lower()

    def test_duration_is_positive(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = NotNullCheck(column="id").run(df)

        assert result.duration_ms >= 0

    def test_metadata_contains_column(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = NotNullCheck(column="id").run(df)

        assert result.metadata["column"] == "id"


# --------------------------------------------------------------------- #
# UniqueCheck
# --------------------------------------------------------------------- #


class TestUniqueCheck:
    def test_passes_when_unique(self):
        df = pd.DataFrame({"id": [1, 2, 3, 4]})
        result = UniqueCheck(column="id").run(df)

        assert result.status == CheckStatus.PASSED
        assert result.observed_value == 0

    def test_fails_when_duplicates(self):
        df = pd.DataFrame({"id": [1, 1, 2, 3, 3, 3]})
        result = UniqueCheck(column="id").run(df)

        assert result.status == CheckStatus.FAILED
        # id=1 muncul 2x → 1 duplicate
        # id=3 muncul 3x → 2 duplicates
        # total 3 duplicates
        assert result.observed_value == 3
        assert "3 duplicate" in result.message

    def test_error_when_column_missing(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = UniqueCheck(column="missing").run(df)

        assert result.status == CheckStatus.ERROR

    def test_severity_is_critical(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        result = UniqueCheck(column="id").run(df)

        assert result.severity == Severity.CRITICAL


# --------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------- #


class TestCheckRegistry:
    def test_registry_contains_known_checks(self):
        from dq_framework.checks import CHECK_REGISTRY

        assert "not_null" in CHECK_REGISTRY
        assert "unique" in CHECK_REGISTRY
        assert CHECK_REGISTRY["not_null"] is NotNullCheck
        assert CHECK_REGISTRY["unique"] is UniqueCheck
