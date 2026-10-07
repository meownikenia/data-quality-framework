"""JSON reporter."""

from __future__ import annotations

import json

from dq_framework.models import SuiteResult
from dq_framework.reporters.base import Reporter


class JSONReporter(Reporter):
    """Serialize a SuiteResult to JSON."""

    format_name = "json"

    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def render(self, result: SuiteResult) -> str:
        payload = {
            "suite_name": result.suite_name,
            "table": result.table,
            "status": result.status.value,
            "pass_rate": result.pass_rate,
            "duration_ms": result.duration_ms,
            "started_at": result.started_at.isoformat(),
            "finished_at": result.finished_at.isoformat(),
            "results": [r.model_dump(mode="json") for r in result.results],
        }
        return json.dumps(payload, indent=self.indent, default=str)
