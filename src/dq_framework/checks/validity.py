"""Validity checks: range and regex validation."""

from __future__ import annotations

import re
import time

import pandas as pd

from dq_framework.checks.base import BaseCheck
from dq_framework.models import CheckResult, CheckStatus, Severity


class RangeCheck(BaseCheck):
    """Verify that numeric values fall within [min, max]."""

    name = "range"
    severity = Severity.WARNING

    def __init__(
        self,
        column: str,
        min: float | None = None,
        max: float | None = None,
        inclusive: bool = True,
        **config,
    ) -> None:
        super().__init__(column=column, **config)
        if min is None and max is None:
            raise ValueError("RangeCheck requires at least 'min' or 'max'")
        self.min = min
        self.max = max
        self.inclusive = inclusive

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()

        if self.column not in df.columns:
            return self._error_result(
                f"Column '{self.column}' not found",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        series = df[self.column].dropna()
        if not pd.api.types.is_numeric_dtype(series):
            return self._error_result(
                f"Column '{self.column}' is not numeric",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        mask = pd.Series(True, index=series.index)
        if self.min is not None:
            mask &= series >= self.min if self.inclusive else series > self.min
        if self.max is not None:
            mask &= series <= self.max if self.inclusive else series < self.max

        out_of_range = int((~mask).sum())
        duration = (time.perf_counter() - start) * 1000

        bounds = []
        if self.min is not None:
            bounds.append(f">={self.min}" if self.inclusive else f">{self.min}")
        if self.max is not None:
            bounds.append(f"<={self.max}" if self.inclusive else f"<{self.max}")
        bounds_str = " and ".join(bounds)

        if out_of_range == 0:
            return self._result(
                CheckStatus.PASSED,
                f"Column '{self.column}' all within range {bounds_str}",
                observed=out_of_range,
                expected=0,
                duration_ms=duration,
            )

        return self._result(
            CheckStatus.FAILED,
            f"Column '{self.column}' has {out_of_range} value(s) outside range {bounds_str}",
            observed=out_of_range,
            expected=0,
            duration_ms=duration,
        )


class RegexCheck(BaseCheck):
    """Verify that string values match a regular expression pattern."""

    name = "regex"
    severity = Severity.WARNING

    def __init__(self, column: str, pattern: str, **config) -> None:
        super().__init__(column=column, **config)
        self.pattern = pattern
        self._compiled = re.compile(pattern)

    def run(self, df: pd.DataFrame) -> CheckResult:
        start = time.perf_counter()

        if self.column not in df.columns:
            return self._error_result(
                f"Column '{self.column}' not found",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        series = df[self.column].dropna().astype(str)
        non_matching = int((~series.str.match(self._compiled)).sum())
        duration = (time.perf_counter() - start) * 1000

        if non_matching == 0:
            return self._result(
                CheckStatus.PASSED,
                f"Column '{self.column}' all match pattern",
                observed=non_matching,
                expected=0,
                duration_ms=duration,
                pattern=self.pattern,
            )

        return self._result(
            CheckStatus.FAILED,
            f"Column '{self.column}' has {non_matching} value(s) not matching pattern",
            observed=non_matching,
            expected=0,
            duration_ms=duration,
            pattern=self.pattern,
        )