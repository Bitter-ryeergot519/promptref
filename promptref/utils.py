"""Utility helpers: hashing, config read/write, timestamp formatting."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path.home() / ".promptref" / "config.json"


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def make_hash(content: str) -> str:
    """Return an 8-character SHA-256 hash derived from content + current UTC time."""
    timestamp = datetime.now(timezone.utc).isoformat()
    raw = f"{content}{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Config (active branch per project)
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    """Load ~/.promptref/config.json, returning an empty dict if absent."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(data: dict) -> None:
    """Persist config dict to ~/.promptref/config.json."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def get_active_branch(project_name: str) -> str:
    """Return the active branch for a project, defaulting to 'main'."""
    config = _load_config()
    return config.get("active_branches", {}).get(project_name, "main")


def set_active_branch(project_name: str, branch_name: str) -> None:
    """Persist the active branch for a project in config."""
    config = _load_config()
    config.setdefault("active_branches", {})[project_name] = branch_name
    _save_config(config)


# ---------------------------------------------------------------------------
# Timestamp display
# ---------------------------------------------------------------------------


def fmt_ts(dt: datetime) -> str:
    """Format a UTC datetime for display in local time (YYYY-MM-DD HH:MM)."""
    # SQLite stores UTC; convert to local for display
    utc_dt = dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M")
