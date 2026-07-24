"""`claim-chart` CLI — build a grounded claim chart against a prior-art reference.

    claim-chart chart --claim "A method comprising: ..." --reference "The prior art teaches ..."
    claim-chart chart --claim-file claim.txt --reference-file ref.txt
    claim-chart demo
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .chart import chart as build_chart
from .client import LLMClient
from .config import Settings
from .data import SAMPLE_CASES
from .models import ChartResult

app = typer.Typer(add_completion=False, help="AI patent claim-chart / prior-art anticipation tool (not legal advice).")
console = Console()


def _print(result: ChartResult) -> None:
    disclosed = sum(1 for m in result.mappings if m.disclosed)
    total = len(result.mappings)
    anticipated = result.verdict.startswith("anticipated")
    style = "red" if anticipated else "green"
    verdict_label = "ANTICIPATED" if anticipated else "NOVEL OVER THE REFERENCE"
    console.print(
        Panel(
            f"[bold]{verdict_label}[/]\n{disclosed}/{total} limitations disclosed by the reference.\n{result.verdict}",
            title="Claim chart",
            border_style=style,
        )
    )

    table = Table(show_lines=True, expand=True)
    table.add_column("#", justify="right", width=3)
    table.add_column("Limitation")
    table.add_column("Disclosed", width=13)
    table.add_column("Quote from reference")
    for lim, m in zip(result.limitations, result.mappings):
        if m.disclosed:
            mark = "[green]✓ disclosed[/]"
            quote = f"[dim]“{m.quote}”[/]"
        else:
            mark = "[red]✗ not disclosed[/]"
            quote = "[red]—[/]"
        table.add_row(str(lim.index), lim.text, mark, quote)
    console.print(table)

    if result.novel_because:
        console.print("\n[bold]Novel because these limitations are not disclosed:[/]")
        for t in result.novel_because:
            console.print(f"  [red]•[/] {t}")

    console.print(f"\n[dim]{result.disclaimer}[/]")


def _run(claim: str, reference: str) -> None:
    settings = Settings.from_env()
    with console.status("Building claim chart…"):
        result = build_chart(claim, reference, LLMClient(settings))
    _print(result)


@app.callback()
def _root() -> None:
    """AI patent claim-chart / prior-art anticipation tool (educational, not legal advice)."""


@app.command()
def chart(
    claim: str = typer.Option(None, "--claim", help="Inline independent patent claim text."),
    reference: str = typer.Option(None, "--reference", help="Inline prior-art reference text."),
    claim_file: Path = typer.Option(None, "--claim-file", help="Path to a file with the claim text."),
    reference_file: Path = typer.Option(None, "--reference-file", help="Path to a file with the reference text."),
) -> None:
    """Build a claim chart for a CLAIM against a prior-art REFERENCE."""
    claim_text = claim_file.read_text(encoding="utf-8") if claim_file else claim
    ref_text = reference_file.read_text(encoding="utf-8") if reference_file else reference
    if not claim_text or not ref_text:
        console.print("[red]Provide the claim (--claim/--claim-file) and the reference (--reference/--reference-file), or run `claim-chart demo`.[/]")
        raise typer.Exit(1)
    _run(claim_text, ref_text)


@app.command()
def demo(
    case: str = typer.Option(
        None,
        "--case",
        help=f"Which sample case to run. One of: {', '.join(c.name for c in SAMPLE_CASES)}.",
    ),
) -> None:
    """Build a claim chart for a baked-in synthetic claim + reference pair."""
    chosen = next((c for c in SAMPLE_CASES if c.name == case), None) if case else SAMPLE_CASES[0]
    if chosen is None:
        console.print(f"[red]Unknown case '{case}'. Choose one of: {', '.join(c.name for c in SAMPLE_CASES)}.[/]")
        raise typer.Exit(1)
    console.print(f"[dim]Sample case: {chosen.name} — {chosen.note}[/]\n")
    _run(chosen.claim, chosen.reference)


if __name__ == "__main__":
    app()
