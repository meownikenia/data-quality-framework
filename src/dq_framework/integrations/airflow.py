"""Apache Airflow integration.

The Airflow imports are deferred so that the rest of the framework can be
used without Airflow installed. Import this module only when you actually
have Airflow in your environment.
"""

from __future__ import annotations

from typing import Any, cast

import pandas as pd
from dq_framework.suite import Suite


class DQSuiteError(Exception):
    """Raised when a DQ suite fails during an Airflow task."""


def _require_airflow() -> Any:
    """Import BaseOperator lazily, with a helpful error message."""
    try:
        from airflow.models import BaseOperator  # type: ignore[import-not-found]
        from airflow.utils.decorators import apply_defaults  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "apache-airflow is required for the Airflow integration. "
            "Install it with: pip install 'dq-framework[airflow]'"
        ) from exc
    return BaseOperator, apply_defaults


# --------------------------------------------------------------------- #
# Core logic (testable without Airflow installed)
# --------------------------------------------------------------------- #


def run_suite(
    suite_path: str,
    data_path: str,
    *,
    fail_on_critical: bool = True,
) -> dict[str, Any]:
    """Run a DQ suite and return a summary dict.

    This function contains the business logic — testable without Airflow.
    The operator below simply wraps it.
    """
    suite = Suite.from_yaml(suite_path)
    df = pd.read_csv(data_path)
    result = suite.run(df)

    summary = {
        "suite_name": result.suite_name,
        "table": result.table,
        "status": result.status.value,
        "pass_rate": result.pass_rate,
        "duration_ms": result.duration_ms,
        "total_checks": len(result.results),
        "failed_checks": len(result.failed_checks),
        "critical_failures": len(result.critical_failures),
    }

    if fail_on_critical and result.critical_failures:
        raise DQSuiteError(
            f"Critical DQ checks failed for suite '{result.suite_name}': "
            f"{len(result.critical_failures)} critical failure(s). "
            f"Pass rate: {result.pass_rate:.1%}"
        )

    return summary


# --------------------------------------------------------------------- #
# Airflow Operator (lazy — only instantiated if Airflow is installed)
# --------------------------------------------------------------------- #


def make_airflow_operator() -> type:
    """Factory that builds the DataQualityOperator class.

    Called lazily so that importing this module doesn't require Airflow.
    """
    BaseOperator, apply_defaults = _require_airflow()

    class DataQualityOperator(BaseOperator):  # type: ignore[misc, valid-type]
        """Run a DQ suite as an Airflow task.

        Pushes the suite summary to XCom under key ``dq_result``.
        Fails the task if any critical check fails (when ``fail_on_critical=True``).
        """

        template_fields = ("suite_path", "data_path")

        @apply_defaults
        def __init__(
            self,
            suite_path: str,
            data_path: str,
            fail_on_critical: bool = True,
            **kwargs: Any,
        ) -> None:
            super().__init__(**kwargs)
            self.suite_path = suite_path
            self.data_path = data_path
            self.fail_on_critical = fail_on_critical

        def execute(self, context: dict[str, Any]) -> dict[str, Any]:
            summary = run_suite(
                self.suite_path,
                self.data_path,
                fail_on_critical=self.fail_on_critical,
            )
            # Push to XCom for downstream tasks
            ti = context.get("ti")
            if ti is not None:
                ti.xcom_push(key="dq_result", value=summary)
            self.log.info("DQ suite completed: %s", summary)
            return summary

    return cast(type, DataQualityOperator)
