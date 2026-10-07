"""Data quality checks and registry."""

from __future__ import annotations

from dq_framework.checks.base import BaseCheck
from dq_framework.checks.completeness import NotNullCheck, UniqueCheck

# Registry: maps YAML `type` field to check class.
# Ini yang dipakai suite.py nanti untuk auto-instantiate check dari config.
CHECK_REGISTRY: dict[str, type[BaseCheck]] = {
    "not_null": NotNullCheck,
    "unique": UniqueCheck,
}

__all__ = [
    "BaseCheck",
    "NotNullCheck",
    "UniqueCheck",
    "CHECK_REGISTRY",
]