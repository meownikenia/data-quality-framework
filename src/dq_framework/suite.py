"""Suite: load and run a collection of checks defined in YAML."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from dq_framework.checks import CHECK_REGISTRY
from dq_framework.checks.base import BaseCheck
from dq_framework.models import CheckResult, CheckStatus, Severity, SuiteResult


class SuiteError(Exception):
    """Raised when a suite config is invalid."""


class Suite:
    """A collection of data quality checks run against a DataFrame."""

    def __init__(
        self,
        name: str,
        table: str,
        checks: list[BaseCheck],
        description: str = "",
    ) -> None:
        self.name = name
        self.table = table
        self.checks = checks
        self.description = description

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> Suite:
        """Build a Suite from a parsed YAML/dict config."""
        try:
            name = config["suite"]
            table = config["table"]
            checks_raw = config["checks"]
        except KeyError as exc:
            raise SuiteError(f"Missing required key in suite config: {exc}") from exc

        if not isinstance(checks_raw, list) or not checks_raw:
            raise SuiteError("Suite must contain at least one check")

        checks: list[BaseCheck] = []
        for i, spec in enumerate(checks_raw):
            spec = dict(spec)  # copy biar tidak mutate input
            check_type = spec.pop("type", None)
            if check_type is None:
                raise SuiteError(f"Check #{i} is missing required field 'type'")
            check_cls = CHECK_REGISTRY.get(check_type)
            if check_cls is None:
                raise SuiteError(
                    f"Unknown check type '{check_type}'. " f"Available: {sorted(CHECK_REGISTRY)}"
                )
            try:
                checks.append(check_cls(**spec))
            except (TypeError, ValueError) as exc:
                raise SuiteError(f"Invalid config for check '{check_type}': {exc}") from exc

        return cls(
            name=name,
            table=table,
            checks=checks,
            description=config.get("description", ""),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Suite:
        """Load a Suite from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise SuiteError(f"Suite file not found: {path}")
        with path.open() as fh:
            config = yaml.safe_load(fh)
        if not isinstance(config, dict):
            raise SuiteError(f"Invalid YAML in {path}: expected a mapping")
        return cls.from_dict(config)

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #

    def run(self, df: pd.DataFrame) -> SuiteResult:
        """Run all checks against the DataFrame."""
        started = datetime.now(UTC)
        results: list[CheckResult] = []

        for check in self.checks:
            try:
                results.append(check.run(df))
            except Exception as exc:  # noqa: BLE001
                results.append(
                    CheckResult(
                        check_name=check.name,
                        status=CheckStatus.ERROR,
                        severity=Severity.CRITICAL,
                        message=f"Check crashed: {exc}",
                        metadata={"column": check.column},
                    )
                )

        return SuiteResult(
            suite_name=self.name,
            table=self.table,
            results=results,
            started_at=started,
            finished_at=datetime.now(UTC),
        )

    def __repr__(self) -> str:
        return f"<Suite name={self.name!r} checks={len(self.checks)}>"
