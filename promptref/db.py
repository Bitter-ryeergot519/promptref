"""Database layer for promptref — all SQLite operations live here."""

import sqlite3
from pathlib import Path
from typing import Optional

DB_DIR = Path.home() / ".promptref"
DB_PATH = DB_DIR / "store.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    content TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE,
    message TEXT,
    branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    name TEXT NOT NULL,
    head_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, name)
);
"""


def get_connection() -> sqlite3.Connection:
    """Open (and lazily create) the SQLite database, returning a connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def create_project(name: str) -> int:
    """Insert a new project and return its id."""
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        return cur.lastrowid


def get_project(name: str) -> Optional[sqlite3.Row]:
    """Fetch a project row by name, or None if not found."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects WHERE name = ?", (name,)
        ).fetchone()


def list_projects() -> list:
    """Return all project rows."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        ).fetchall()


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------


def create_branch(project_id: int, name: str, head_hash: Optional[str] = None) -> None:
    """Insert a new branch for the given project."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO branches (project_id, name, head_hash) VALUES (?, ?, ?)",
            (project_id, name, head_hash),
        )


def get_branch(project_id: int, name: str) -> Optional[sqlite3.Row]:
    """Fetch a branch row, or None if not found."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM branches WHERE project_id = ? AND name = ?",
            (project_id, name),
        ).fetchone()


def update_branch_head(project_id: int, branch_name: str, head_hash: str) -> None:
    """Set the HEAD hash for a branch."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE branches SET head_hash = ? WHERE project_id = ? AND name = ?",
            (head_hash, project_id, branch_name),
        )


def list_branches(project_id: int) -> list:
    """Return all branches for a project."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM branches WHERE project_id = ? ORDER BY created_at",
            (project_id,),
        ).fetchall()


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------


def save_version(
    project_id: int,
    content: str,
    hash_: str,
    branch: str,
    message: Optional[str] = None,
) -> None:
    """Insert a new version record."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO versions (project_id, content, hash, message, branch) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_id, content, hash_, message, branch),
        )


def get_version_by_hash(hash_prefix: str) -> Optional[sqlite3.Row]:
    """Fetch a version by exact hash or 8-char prefix."""
    with get_connection() as conn:
        # Try exact match first, then prefix
        row = conn.execute(
            "SELECT * FROM versions WHERE hash = ?", (hash_prefix,)
        ).fetchone()
        if row:
            return row
        return conn.execute(
            "SELECT * FROM versions WHERE hash LIKE ?", (hash_prefix + "%",)
        ).fetchone()


def list_versions(project_id: int, branch: str) -> list:
    """Return all versions for a project/branch ordered newest-first."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM versions WHERE project_id = ? AND branch = ? "
            "ORDER BY created_at DESC",
            (project_id, branch),
        ).fetchall()


def list_all_versions(project_id: int) -> list:
    """Return all versions for a project across all branches, newest-first."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM versions WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()


def get_latest_version(project_id: int, branch: str) -> Optional[sqlite3.Row]:
    """Return the most recent version on a branch."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM versions WHERE project_id = ? AND branch = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (project_id, branch),
        ).fetchone()
