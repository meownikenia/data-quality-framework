"""Abstract base class for reporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from dq_framework.models import SuiteResult


class Reporter(ABC):
    """Renders a SuiteResult into some output format."""

    format_name: str = "base"

    @abstractmethod
    def render(self, result: SuiteResult) -> str:
        """Return the serialized result as a string."""

    def write(self, result: SuiteResult, path: str | Path) -> Path:
        """Render and write to a file. Returns the written path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(result), encoding="utf-8")
        return path