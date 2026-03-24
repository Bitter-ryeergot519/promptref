"""Lightweight dataclass models that wrap sqlite3.Row results."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """Represents a prompt project."""

    id: int
    name: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "Project":
        """Construct a Project from a sqlite3.Row."""
        return cls(
            id=row["id"],
            name=row["name"],
            created_at=_parse_ts(row["created_at"]),
        )


@dataclass
class Version:
    """Represents a single saved version of a prompt."""

    id: int
    project_id: int
    content: str
    hash: str
    message: Optional[str]
    branch: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "Version":
        """Construct a Version from a sqlite3.Row."""
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            content=row["content"],
            hash=row["hash"],
            message=row["message"],
            branch=row["branch"],
            created_at=_parse_ts(row["created_at"]),
        )


@dataclass
class Branch:
    """Represents a branch within a project."""

    id: int
    project_id: int
    name: str
    head_hash: Optional[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "Branch":
        """Construct a Branch from a sqlite3.Row."""
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            head_hash=row["head_hash"],
            created_at=_parse_ts(row["created_at"]),
        )


def _parse_ts(value) -> datetime:
    """Parse a SQLite timestamp string into a datetime object."""
    if isinstance(value, datetime):
        return value
    # SQLite stores as 'YYYY-MM-DD HH:MM:SS' or with fractional seconds
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return datetime.utcnow()
