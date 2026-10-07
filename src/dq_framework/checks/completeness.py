"""Completeness checks: not-null and uniqueness."""

from __future__ import annotations

import time

import pandas as pd
from dq_framework.checks.base import BaseCheck
from dq_framework.models import CheckResult, CheckStatus, Severity


class NotNullCheck(BaseCheck):
    """Verify that a column contains no null values."""

    name = "not_null"
    severity = Severity.CRITICAL

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()

        if self.column not in df.columns:
            return self._error_result(
                f"Column '{self.column}' not found",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        total = len(df)
        null_count = int(df[self.column].isna().sum())
        duration = (time.perf_counter() - start) * 1000

        if null_count == 0:
            return self._result(
                CheckStatus.PASSED,
                f"Column '{self.column}' has no nulls ({total} rows)",
                observed=null_count,
                expected=0,
                duration_ms=duration,
            )

        return self._result(
            CheckStatus.FAILED,
            f"Column '{self.column}' has {null_count}/{total} nulls " f"({null_count / total:.1%})",
            observed=null_count,
            expected=0,
            duration_ms=duration,
        )


class UniqueCheck(BaseCheck):
    """Verify that a column contains no duplicate values."""

    name = "unique"
    severity = Severity.CRITICAL

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()

        if self.column not in df.columns:
            return self._error_result(
                f"Column '{self.column}' not found",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        total = len(df)
        # dropna=False supaya null tetap dihitung sebagai duplicate kalau ada >1
        dup_count = int(df[self.column].duplicated(keep="first").sum())
        duration = (time.perf_counter() - start) * 1000

        if dup_count == 0:
            return self._result(
                CheckStatus.PASSED,
                f"Column '{self.column}' is unique ({total} rows)",
                observed=dup_count,
                expected=0,
                duration_ms=duration,
            )

        return self._result(
            CheckStatus.FAILED,
            f"Column '{self.column}' has {dup_count} duplicate(s) out of {total}",
            observed=dup_count,
            expected=0,
            duration_ms=duration,
        )
