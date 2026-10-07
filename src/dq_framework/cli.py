"""Command-line interface for the Data Quality Framework."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from dq_framework.models import CheckStatus, SuiteResult
from dq_framework.suite import Suite, SuiteError

app = typer.Typer(
    name="dq",
    help="Data Quality Framework CLI",
    add_completion=False,
)
console = Console()


_STATUS_ICONS = {
    CheckStatus.PASSED: "[green]✅[/green]",
    CheckStatus.FAILED: "[red]❌[/red]",
    CheckStatus.ERROR: "[yellow]💥[/yellow]",
    CheckStatus.SKIPPED: "[dim]⏭️[/dim]",
}

_SEVERITY_COLORS = {
    "info": "blue",
    "warning": "yellow",
    "critical": "red",
}


def _render_result(result: SuiteResult) -> None:
    """Print a SuiteResult to the console."""
    status_color = {
        CheckStatus.PASSED: "green",
        CheckStatus.FAILED: "red",
        CheckStatus.ERROR: "yellow",
    }.get(result.status, "white")

    console.print()
    console.rule(f"[bold]DQ Suite: {result.suite_name}[/bold]")
    console.print(f"Table:      [cyan]{result.table}[/cyan]")
    console.print(
        f"Status:     [{status_color}][bold]{result.status.value.upper()}[/bold][/{status_color}]"
    )
    console.print(f"Pass rate:  {result.pass_rate:.1%}")
    console.print(f"Duration:   {result.duration_ms:.1f} ms")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("", width=3)
    table.add_column("Check", style="cyan")
    table.add_column("Column", style="magenta")
    table.add_column("Severity")
    table.add_column("Message")
    table.add_column("Time (ms)", justify="right")

    for r in result.results:
        sev_color = _SEVERITY_COLORS.get(r.severity.value, "white")
        table.add_row(
            _STATUS_ICONS.get(r.status, "❓"),
            r.check_name,
            str(r.metadata.get("column", "-")),
            f"[{sev_color}]{r.severity.value}[/{sev_color}]",
            r.message,
            f"{r.duration_ms:.1f}",
        )

    console.print(table)
    console.print()


def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load a DataFrame from CSV or Parquet based on file extension."""
    if not path.exists():
        console.print(f"[red]Data file not found: {path}[/red]")
        raise typer.Exit(code=2)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    console.print(f"[red]Unsupported data format: {suffix}[/red]")
    raise typer.Exit(code=2)


@app.command()
def run(
    suite_path: Path = typer.Argument(..., help="Path to suite YAML file"),
    data_path: Path = typer.Argument(..., help="Path to data file (CSV/Parquet)"),
    fail_on_critical: bool = typer.Option(
        True,
        "--fail-on-critical/--no-fail-on-critical",
        help="Exit with code 1 if any critical check fails",
    ),
    output_json: Path | None = typer.Option(
        None, "--output-json", help="Write result as JSON to this path"
    ),
) -> None:
    """Run a data quality suite against a data file."""
    try:
        suite = Suite.from_yaml(suite_path)
    except SuiteError as exc:
        console.print(f"[red]Suite error: {exc}[/red]")
        raise typer.Exit(code=2) from exc

    df = _load_dataframe(data_path)
    result = suite.run(df)
    _render_result(result)

    if output_json is not None:
        output_json.write_text(result.model_dump_json(indent=2))
        console.print(f"[dim]JSON written to {output_json}[/dim]")

    if fail_on_critical and result.critical_failures:
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show the DQ Framework version."""
    from dq_framework import __version__

    console.print(f"dq-framework [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()