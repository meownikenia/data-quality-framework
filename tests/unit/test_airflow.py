"""Unit tests for Airflow integration core logic."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from dq_framework.integrations import DQSuiteError, run_suite


def _write_yaml(tmp_path: Path, config: dict) -> Path:
    p = tmp_path / "suite.yaml"
    p.write_text(yaml.safe_dump(config))
    return p


def _write_csv(tmp_path: Path, df: pd.DataFrame) -> Path:
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    return p


class TestRunSuite:
    def test_returns_summary_on_pass(self, tmp_path: Path):
        suite_path = _write_yaml(
            tmp_path,
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "not_null", "column": "id"}],
            },
        )
        data_path = _write_csv(tmp_path, pd.DataFrame({"id": [1, 2, 3]}))

        summary = run_suite(str(suite_path), str(data_path))

        assert summary["status"] == "passed"
        assert summary["pass_rate"] == 1.0
        assert summary["total_checks"] == 1
        assert summary["critical_failures"] == 0

    def test_raises_on_critical_failure(self, tmp_path: Path):
        suite_path = _write_yaml(
            tmp_path,
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "unique", "column": "id"}],
            },
        )
        # Duplicate ID → unique check fails with CRITICAL severity
        data_path = _write_csv(tmp_path, pd.DataFrame({"id": [1, 1, 2]}))

        with pytest.raises(DQSuiteError, match="Critical DQ checks failed"):
            run_suite(str(suite_path), str(data_path))

    def test_no_raise_when_fail_on_critical_false(self, tmp_path: Path):
        suite_path = _write_yaml(
            tmp_path,
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "unique", "column": "id"}],
            },
        )
        data_path = _write_csv(tmp_path, pd.DataFrame({"id": [1, 1, 2]}))

        summary = run_suite(str(suite_path), str(data_path), fail_on_critical=False)

        assert summary["status"] == "failed"
        assert summary["critical_failures"] >= 1

    def test_summary_keys(self, tmp_path: Path):
        suite_path = _write_yaml(
            tmp_path,
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "row_count", "min": 1}],
            },
        )
        data_path = _write_csv(tmp_path, pd.DataFrame({"x": [1, 2]}))

        summary = run_suite(str(suite_path), str(data_path))

        expected = {
            "suite_name", "table", "status", "pass_rate",
            "duration_ms", "total_checks", "failed_checks", "critical_failures",
        }
        assert set(summary.keys()) == expected