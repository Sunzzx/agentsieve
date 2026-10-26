"""
AgentSieve CLI - High-speed semantic distillation interface.
"""

from __future__ import annotations
import sys
import subprocess
from typing import Sequence
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from agentsieve.core import AgentSieve, ContentKind
from agentsieve.token_budget import estimate_tokens

console = Console(stderr=True)


@click.group()
@click.version_option()
def cli():
    """AgentSieve: Zero-LLM Tool Output Distiller for AI Coding Agents."""
    pass


@cli.command()
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option("--kind", "-k", type=click.Choice([k.value for k in ContentKind]), default=None, help="Force content type")
@click.option("--focus", "-f", multiple=True, help="Focal symbol name to preserve in full")
@click.option("--focus-line", "-l", multiple=True, type=int, help="Focal line number to preserve in full")
@click.option("--max-tokens", "-m", type=int, default=2000, help="Maximum token budget")
@click.option("--stats/--no-stats", default=True, help="Print token metrics to stderr")
def distill(
    file: str | None,
    kind: str | None,
    focus: tuple[str, ...],
    focus_line: tuple[int, ...],
    max_tokens: int,
    stats: bool,
):
    """Distill tool output from a file or stdin."""
    if file:
        with open(file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    if not content:
        return

    sieve = AgentSieve(default_max_tokens=max_tokens)
    content_kind = ContentKind(kind) if kind else None
    
    res = sieve.distill(
        text=content,
        kind=content_kind,
        focus_symbols=list(focus),
        focus_lines=list(focus_line),
        max_tokens=max_tokens,
    )

    if stats:
        console.print(
            f"[bold green]✓ Distilled ({res.kind.value})[/bold green]: "
            f"{res.original_tokens} → {res.distilled_tokens} tokens "
            f"([bold cyan]-{res.savings_percent}%[/bold cyan] / saved ~{res.saved_tokens} tokens)"
        )

    sys.stdout.write(res.distilled_text)
    if not res.distilled_text.endswith("\n"):
        sys.stdout.write("\n")


@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
@click.option("--max-tokens", "-m", type=int, default=2000, help="Maximum token budget")
def run(ctx: click.Context, max_tokens: int):
    """
    Execute any shell command, intercept output, distill it, and stream the clean result.
    Usage: agentsieve run -- pytest -v
    """
    cmd = ctx.args
    if not cmd:
        console.print("[red]Error: No command specified to run.[/red]")
        sys.exit(1)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw_output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

    sieve = AgentSieve(default_max_tokens=max_tokens)
    res = sieve.distill(raw_output, max_tokens=max_tokens)

    console.print(
        f"[dim][agentsieve: executed '{' '.join(cmd)}' | exit code {proc.returncode} | "
        f"compressed {res.original_tokens} -> {res.distilled_tokens} tokens (-{res.savings_percent}%)] [/dim]"
    )

    sys.stdout.write(res.distilled_text)
    if not res.distilled_text.endswith("\n"):
        sys.stdout.write("\n")
    sys.exit(proc.returncode)


@cli.command()
@click.argument("file", type=click.Path(exists=True))
def inspect(file: str):
    """Inspect token weight and structure of a file or output dump."""
    with open(file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    sieve = AgentSieve()
    kind = sieve.detect_kind(content)
    tokens = estimate_tokens(content)
    
    res = sieve.distill(content)
    
    table = Table(title=f"AgentSieve Analysis: {file}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Detected Kind", kind.value)
    table.add_row("Original Tokens (est)", str(tokens))
    table.add_row("Distilled Tokens (est)", str(res.distilled_tokens))
    table.add_row("Savings", f"{res.savings_percent}% (~{res.saved_tokens} tokens)")
    
    console.print(table)
