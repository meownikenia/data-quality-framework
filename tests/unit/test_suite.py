"""Unit tests for the Suite class."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from dq_framework.suite import Suite, SuiteError


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["a", "b", "c", "d", "e"],
        }
    )


def _write_yaml(tmp_path: Path, config: dict) -> Path:
    p = tmp_path / "suite.yaml"
    p.write_text(yaml.safe_dump(config))
    return p


class TestSuiteFromDict:
    def test_minimal_valid_config(self):
        suite = Suite.from_dict(
            {
                "suite": "test",
                "table": "t",
                "checks": [{"type": "not_null", "column": "id"}],
            }
        )
        assert suite.name == "test"
        assert len(suite.checks) == 1

    def test_missing_key_raises(self):
        with pytest.raises(SuiteError, match="Missing required key"):
            Suite.from_dict({"suite": "x", "table": "y"})

    def test_empty_checks_raises(self):
        with pytest.raises(SuiteError, match="at least one check"):
            Suite.from_dict({"suite": "x", "table": "y", "checks": []})

    def test_missing_type_raises(self):
        with pytest.raises(SuiteError, match="missing required field 'type'"):
            Suite.from_dict(
                {
                    "suite": "x",
                    "table": "y",
                    "checks": [{"column": "id"}],
                }
            )

    def test_unknown_type_raises(self):
        with pytest.raises(SuiteError, match="Unknown check type"):
            Suite.from_dict(
                {
                    "suite": "x",
                    "table": "y",
                    "checks": [{"type": "does_not_exist"}],
                }
            )

    def test_invalid_check_config_raises(self):
        """A check whose __init__ raises should be wrapped in SuiteError."""
        with pytest.raises(SuiteError, match="Invalid config"):
            Suite.from_dict(
                {
                    "suite": "x",
                    "table": "y",
                    "checks": [{"type": "range", "column": "amount"}],
                }
            )

class TestSuiteFromYaml:
    def test_load_from_yaml(self, tmp_path: Path):
        path = _write_yaml(
            tmp_path,
            {
                "suite": "yaml_suite",
                "table": "t",
                "checks": [{"type": "not_null", "column": "id"}],
            },
        )
        suite = Suite.from_yaml(path)
        assert suite.name == "yaml_suite"

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(SuiteError, match="not found"):
            Suite.from_yaml(tmp_path / "missing.yaml")


class TestSuiteRun:
    def test_run_all_pass(self):
        suite = Suite.from_dict(
            {
                "suite": "s",
                "table": "t",
                "checks": [
                    {"type": "not_null", "column": "id"},
                    {"type": "unique", "column": "id"},
                ],
            }
        )
        result = suite.run(_sample_df())
        assert result.suite_name == "s"
        assert result.pass_rate == 1.0

    def test_run_detects_failure(self):
        suite = Suite.from_dict(
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "not_null", "column": "id"}],
            }
        )
        df = pd.DataFrame({"id": [1, None, 3]})
        result = suite.run(df)
        assert result.pass_rate < 1.0

    def test_check_exception_becomes_error(self):
        """A check that crashes should become an ERROR result, not break the suite."""
        suite = Suite.from_dict(
            {
                "suite": "s",
                "table": "t",
                "checks": [{"type": "not_null", "column": "id"}],
            }
        )

        # Monkeypatch check.run to raise
        suite.checks[0].run = lambda df: (_ for _ in ()).throw(RuntimeError("boom"))
        result = suite.run(_sample_df())
        assert result.status.value == "error"