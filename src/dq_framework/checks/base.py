"""Base class for all data quality checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from dq_framework.models import CheckResult, CheckStatus, Severity


class BaseCheck(ABC):
    """Abstract base for data quality checks."""

    name: str = "base_check"
    severity: Severity = Severity.WARNING

    def __init__(self, column: str | None = None, **config: Any) -> None:
        self.column = column
        self.config = config

    @abstractmethod
    def run(self, df: pd.DataFrame) -> CheckResult:
        """Execute the check against a pandas DataFrame."""

    def _result(
        self,
        status: CheckStatus,
        message: str,
        *,
        observed: Any = None,
        expected: Any = None,
        duration_ms: float = 0.0,
        **metadata: Any,
    ) -> CheckResult:
        return CheckResult(
            check_name=self.name,
            status=status,
            severity=self.severity,
            message=message,
            observed_value=observed,
            expected_value=expected,
            duration_ms=duration_ms,
            metadata={"column": self.column, **self.config, **metadata},
        )

    def _error_result(self, message: str, duration_ms: float = 0.0) -> CheckResult:
        return self._result(
            CheckStatus.ERROR,
            f"Check crashed: {message}",
            duration_ms=duration_ms,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} column={self.column!r}>"
