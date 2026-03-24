"""CLI entry point for promptref — Git-like version control for LLM prompts."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import promptref.db as db
from promptref.diff import compute_diff, render_diff
from promptref.models import Branch, Project, Version
from promptref.utils import (
    fmt_ts,
    get_active_branch,
    make_hash,
    set_active_branch,
)

app = typer.Typer(
    name="promptref",
    help="Git-like version control for LLM prompts.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _abort(msg: str) -> None:
    """Print a red error message and exit with code 1."""
    err_console.print(f"[bold red]Error:[/bold red] {msg}")
    raise typer.Exit(code=1)


def _require_project(name: str) -> Project:
    """Fetch a project or abort with a helpful message."""
    row = db.get_project(name)
    if row is None:
        _abort(f"Project '{name}' not found. Run: promptref init {name}")
    return Project.from_row(row)


def _require_version(hash_prefix: str) -> Version:
    """Fetch a version by hash prefix or abort."""
    row = db.get_version_by_hash(hash_prefix)
    if row is None:
        _abort(f"Version '{hash_prefix}' not found.")
    return Version.from_row(row)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def init(project_name: str = typer.Argument(..., help="Name of the new project")) -> None:
    """Create a new prompt project with a default 'main' branch."""
    db.init_db()
    if db.get_project(project_name) is not None:
        _abort(f"Project '{project_name}' already exists.")
    project_id = db.create_project(project_name)
    db.create_branch(project_id, "main")
    set_active_branch(project_name, "main")

    store_path = Path.home() / ".promptref" / "store.db"
    console.print(f"[bold green]✓[/bold green] Initialized prompt project '[cyan]{project_name}[/cyan]'")
    console.print(f"  Branch : [cyan]main[/cyan]")
    console.print(f"  Store  : [dim]{store_path}[/dim]")


@app.command()
def save(
    project_name: str = typer.Argument(..., help="Target project name"),
    content: str = typer.Argument(..., help="Prompt content to save"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Version message"),
) -> None:
    """Save a new prompt version and update the branch HEAD."""
    db.init_db()
    project = _require_project(project_name)
    branch = get_active_branch(project_name)

    # Ensure branch exists (handles projects pre-dating branch support)
    if db.get_branch(project.id, branch) is None:
        db.create_branch(project.id, branch)

    hash_ = make_hash(content)
    db.save_version(project.id, content, hash_, branch, message)
    db.update_branch_head(project.id, branch, hash_)

    console.print(f"[bold green]✓[/bold green] Saved version [cyan]{hash_}[/cyan]")
    console.print(f"  Project : [cyan]{project_name}[/cyan]")
    console.print(f"  Branch  : [cyan]{branch}[/cyan]")
    if message:
        console.print(f"  Message : {message}")


@app.command()
def log(project_name: str = typer.Argument(..., help="Project to show history for")) -> None:
    """Display version history for the active branch using Rich."""
    db.init_db()
    project = _require_project(project_name)
    branch = get_active_branch(project_name)
    rows = db.list_versions(project.id, branch)

    if not rows:
        console.print(f"[dim]No versions found for '{project_name}' on branch '{branch}'.[/dim]")
        return

    console.print(f"\n[bold]History[/bold] — [cyan]{project_name}[/cyan] / [cyan]{branch}[/cyan]\n")
    for row in rows:
        v = Version.from_row(row)
        msg_display = v.message or "[dim](no message)[/dim]"
        console.print(
            f"[bold cyan]●[/bold cyan] [bold]{v.hash}[/bold]  "
            f"[dim]{fmt_ts(v.created_at)}[/dim]  {msg_display}"
        )


@app.command()
def diff(
    project_name: str = typer.Argument(..., help="Project name"),
    hash1: str = typer.Argument(..., help="First version hash (older)"),
    hash2: str = typer.Argument(..., help="Second version hash (newer)"),
) -> None:
    """Show a line-by-line diff between two prompt versions."""
    db.init_db()
    _require_project(project_name)
    v1 = _require_version(hash1)
    v2 = _require_version(hash2)
    diff_lines = compute_diff(v1.content, v2.content)
    render_diff(diff_lines, v1.hash, v2.hash)


@app.command()
def show(
    project_name: str = typer.Argument(..., help="Project name"),
    hash_: str = typer.Argument(..., metavar="HASH", help="Version hash to display"),
) -> None:
    """Display full content and metadata for a specific version."""
    db.init_db()
    _require_project(project_name)
    v = _require_version(hash_)
    header = (
        f"[bold]Hash:[/bold]    [cyan]{v.hash}[/cyan]\n"
        f"[bold]Branch:[/bold]  {v.branch}\n"
        f"[bold]Saved:[/bold]   {fmt_ts(v.created_at)}\n"
        f"[bold]Message:[/bold] {v.message or '(none)'}"
    )
    console.print(Panel(header, title="[bold]Version Metadata[/bold]", expand=False))
    console.print(Panel(v.content, title="[bold]Prompt Content[/bold]"))


@app.command()
def rollback(
    project_name: str = typer.Argument(..., help="Project name"),
    hash_: str = typer.Argument(..., metavar="HASH", help="Hash to roll back to"),
) -> None:
    """Set branch HEAD to a previous version without deleting history."""
    db.init_db()
    project = _require_project(project_name)
    v = _require_version(hash_)
    branch = get_active_branch(project_name)
    db.update_branch_head(project.id, branch, v.hash)
    console.print(
        f"[bold green]✓[/bold green] Rolled back '[cyan]{project_name}[/cyan]' "
        f"to version [cyan]{v.hash}[/cyan]"
    )


@app.command()
def branch(
    project_name: str = typer.Argument(..., help="Project name"),
    branch_name: str = typer.Argument(..., help="New branch name"),
) -> None:
    """Create a new branch from the current HEAD."""
    db.init_db()
    project = _require_project(project_name)
    current_branch = get_active_branch(project_name)

    if db.get_branch(project.id, branch_name) is not None:
        _abort(f"Branch '{branch_name}' already exists in project '{project_name}'.")

    branch_row = db.get_branch(project.id, current_branch)
    head_hash = branch_row["head_hash"] if branch_row else None
    db.create_branch(project.id, branch_name, head_hash)

    head_display = head_hash or "[dim]no commits[/dim]"
    console.print(
        f"[bold green]✓[/bold green] Created branch '[cyan]{branch_name}[/cyan]' "
        f"from {current_branch} ([cyan]{head_display}[/cyan])"
    )


@app.command()
def switch(
    project_name: str = typer.Argument(..., help="Project name"),
    branch_name: str = typer.Argument(..., help="Branch to switch to"),
) -> None:
    """Switch the active branch for a project."""
    db.init_db()
    project = _require_project(project_name)
    if db.get_branch(project.id, branch_name) is None:
        _abort(f"Branch '{branch_name}' does not exist in project '{project_name}'.")
    set_active_branch(project_name, branch_name)
    console.print(
        f"[bold green]✓[/bold green] Switched '[cyan]{project_name}[/cyan]' "
        f"to branch [cyan]{branch_name}[/cyan]"
    )


@app.command(name="list")
def list_projects() -> None:
    """List all projects with their active branch and latest version hash."""
    db.init_db()
    projects = db.list_projects()
    if not projects:
        console.print("[dim]No projects found. Run: promptref init <name>[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("PROJECT", style="cyan", min_width=16)
    table.add_column("BRANCH", min_width=12)
    table.add_column("LATEST", min_width=10)
    table.add_column("UPDATED", min_width=16)

    for row in projects:
        p = Project.from_row(row)
        branch_name = get_active_branch(p.name)
        latest = db.get_latest_version(p.id, branch_name)
        if latest:
            v = Version.from_row(latest)
            hash_display = v.hash
            updated = fmt_ts(v.created_at)
        else:
            hash_display = "[dim]—[/dim]"
            updated = "[dim]—[/dim]"
        table.add_row(p.name, branch_name, hash_display, updated)

    console.print(table)


@app.command()
def export(
    project_name: str = typer.Argument(..., help="Project to export"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json | txt | yaml"),
) -> None:
    """Export full version history to json, txt, or yaml."""
    db.init_db()
    project = _require_project(project_name)
    rows = db.list_all_versions(project.id)

    if not rows:
        console.print(f"[dim]No versions to export for '{project_name}'.[/dim]")
        return

    versions_data = [
        {
            "hash": row["hash"],
            "branch": row["branch"],
            "message": row["message"],
            "created_at": str(row["created_at"]),
            "content": row["content"],
        }
        for row in rows
    ]

    fmt = format.lower()
    filename = f"{project_name}-export.{fmt}"
    out_path = Path(filename)

    if fmt == "json":
        out_path.write_text(json.dumps(versions_data, indent=2))
    elif fmt == "yaml":
        out_path.write_text(yaml.dump(versions_data, allow_unicode=True, sort_keys=False))
    elif fmt == "txt":
        lines = []
        for v in versions_data:
            lines.append(f"Hash: {v['hash']}")
            lines.append(f"Branch: {v['branch']}")
            lines.append(f"Message: {v['message'] or ''}")
            lines.append(f"Created: {v['created_at']}")
            lines.append(f"Content:\n{v['content']}")
            lines.append("─" * 50)
        out_path.write_text("\n".join(lines))
    else:
        _abort(f"Unknown format '{format}'. Choose from: json, txt, yaml")

    console.print(
        f"[bold green]✓[/bold green] Exported [cyan]{len(versions_data)}[/cyan] "
        f"version(s) to [cyan]{out_path}[/cyan]"
    )
