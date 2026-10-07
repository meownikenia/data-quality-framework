"""Core domain models for the Data Quality Framework."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """How serious a check failure is."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    """Result status of a single check."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class CheckResult(BaseModel):
    """Result of running one data quality check."""

    check_name: str
    status: CheckStatus
    severity: Severity
    message: str
    observed_value: Any | None = None
    expected_value: Any | None = None
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED


class SuiteResult(BaseModel):
    """Aggregated result of running a full suite."""

    suite_name: str
    table: str
    results: list[CheckResult]
    started_at: datetime
    finished_at: datetime

    @property
    def status(self) -> CheckStatus:
        if any(r.status == CheckStatus.ERROR for r in self.results):
            return CheckStatus.ERROR
        if any(r.status == CheckStatus.FAILED for r in self.results):
            return CheckStatus.FAILED
        return CheckStatus.PASSED

    @property
    def pass_rate(self) -> float:
        total = len(self.results)
        if total == 0:
            return 0.0
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASSED)
        return passed / total

    @property
    def duration_ms(self) -> float:
        return (self.finished_at - self.started_at).total_seconds() * 1000

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.FAILED]

    @property
    def critical_failures(self) -> list[CheckResult]:
        return [
            r
            for r in self.results
            if r.status == CheckStatus.FAILED and r.severity == Severity.CRITICAL
        ]
