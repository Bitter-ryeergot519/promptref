"""Diff utilities: compute and render unified diffs with Rich colour."""

import difflib
from typing import Tuple

from rich.console import Console
from rich.text import Text

console = Console()


def compute_diff(old_content: str, new_content: str) -> list[str]:
    """Return unified diff lines between two prompt strings."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    return list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm="",
        )
    )


def render_diff(diff_lines: list[str], hash1: str, hash2: str) -> None:
    """Print a coloured unified diff to the terminal using Rich."""
    console.print(f"\nDiffing [bold cyan]{hash1}[/] → [bold cyan]{hash2}[/]")
    console.print("─" * 45)

    if not diff_lines:
        console.print("[dim]No differences found.[/dim]")
        return

    for line in diff_lines:
        # Skip the --- / +++ header lines produced by unified_diff
        if line.startswith("---") or line.startswith("+++"):
            console.print(Text(line, style="dim"))
        elif line.startswith("@@"):
            console.print(Text(line, style="cyan"))
        elif line.startswith("+"):
            console.print(Text(line, style="bold green"))
        elif line.startswith("-"):
            console.print(Text(line, style="bold red"))
        else:
            console.print(Text(line, style="default"))
