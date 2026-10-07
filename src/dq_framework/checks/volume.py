"""Volume and freshness checks."""

from __future__ import annotations

import time
import warnings
from datetime import UTC, datetime, timedelta

import pandas as pd

from dq_framework.checks.base import BaseCheck
from dq_framework.models import CheckResult, CheckStatus, Severity


class RowCountCheck(BaseCheck):
    """Verify that the DataFrame has a row count within [min, max]."""

    name = "row_count"
    severity = Severity.WARNING

    def __init__(
        self,
        min: int | None = None,
        max: int | None = None,
        **config,
    ) -> None:
        super().__init__(**config)
        if min is None and max is None:
            raise ValueError("RowCountCheck requires at least 'min' or 'max'")
        self.min = min
        self.max = max

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()
        count = len(df)
        duration = (time.perf_counter() - start) * 1000

        bounds = []
        if self.min is not None:
            bounds.append(f">={self.min}")
        if self.max is not None:
            bounds.append(f"<={self.max}")
        bounds_str = " and ".join(bounds)

        in_range = True
        if self.min is not None and count < self.min:
            in_range = False
        if self.max is not None and count > self.max:
            in_range = False

        status = CheckStatus.PASSED if in_range else CheckStatus.FAILED
        return self._result(
            status,
            f"Row count is {count} (expected {bounds_str})",
            observed=count,
            expected=bounds_str,
            duration_ms=duration,
        )


class FreshnessCheck(BaseCheck):
    """Verify that the most recent timestamp is not older than max_age_hours."""

    name = "freshness"
    severity = Severity.CRITICAL

    def __init__(self, column: str, max_age_hours: float, **config) -> None:
        super().__init__(column=column, **config)
        self.max_age_hours = max_age_hours

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()

        if self.column not in df.columns:
            return self._error_result(
                f"Column '{self.column}' not found",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        # Suppress pandas' UserWarning when it can't infer a single datetime format
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(df[self.column], errors="coerce")

        series = pd.Series(parsed).dropna()

        if series.empty:
            return self._error_result(
                f"Column '{self.column}' has no valid timestamps",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        latest = series.max()
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)

        age = datetime.now(UTC) - latest
        age_hours = age.total_seconds() / 3600
        duration = (time.perf_counter() - start) * 1000

        threshold = timedelta(hours=self.max_age_hours)
        status = CheckStatus.PASSED if age <= threshold else CheckStatus.FAILED

        return self._result(
            status,
            f"Data is {age_hours:.1f}h old (max allowed: {self.max_age_hours}h)",
            observed=f"{age_hours:.1f}h",
            expected=f"<={self.max_age_hours}h",
            duration_ms=duration,
        )