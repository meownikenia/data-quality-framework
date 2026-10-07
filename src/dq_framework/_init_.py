"""Data Quality Framework — production-ready DQ checks for modern data stacks."""

__version__ = "0.1.0"

from dq_framework.models import CheckResult, CheckStatus, Severity, SuiteResult

__all__ = ["CheckResult", "CheckStatus", "Severity", "SuiteResult", "__version__"]