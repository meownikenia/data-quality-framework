"""Data quality checks and registry."""

from __future__ import annotations

from dq_framework.checks.base import BaseCheck
from dq_framework.checks.completeness import NotNullCheck, UniqueCheck
from dq_framework.checks.validity import RangeCheck, RegexCheck
from dq_framework.checks.volume import FreshnessCheck, RowCountCheck

CHECK_REGISTRY: dict[str, type[BaseCheck]] = {
    "not_null": NotNullCheck,
    "unique": UniqueCheck,
    "range": RangeCheck,
    "regex": RegexCheck,
    "row_count": RowCountCheck,
    "freshness": FreshnessCheck,
}

__all__ = [
    "BaseCheck",
    "NotNullCheck",
    "UniqueCheck",
    "RangeCheck",
    "RegexCheck",
    "RowCountCheck",
    "FreshnessCheck",
    "CHECK_REGISTRY",
]
