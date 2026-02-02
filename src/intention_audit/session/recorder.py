"""
Session recorder for capturing audit trail records.

This module creates session records that document the intention mapping
process for a given session, capturing transcript references and mapping summaries.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from intention_audit.models.session_record import MappingSummary, SessionRecord


def record_session(
    project_dir: Path,
    session_id: str,
    diff_hash: str,
    transcript_ref: str = "",
    intentions_touched: list[str] | None = None,
    total_files: int = 0,
    total_commits: int = 0,
    notes: str | None = None,
) -> SessionRecord:
    """
    Create and save a session record.

    Args:
        project_dir: Path to the project directory.
        session_id: Unique session identifier.
        diff_hash: Hash of the diff.
        transcript_ref: Reference to the transcript.
        intentions_touched: List of intention IDs referenced.
        total_files: Total number of files mapped.
        total_commits: Total number of commits.
        notes: Optional notes.

    Returns:
        The created SessionRecord.
    """
    mapping = MappingSummary(
        total_intentions=len(intentions_touched or []),
        commits_planned=total_commits,
        files_covered=total_files,
    )

    record = SessionRecord(
        session_id=session_id,
        timestamp=datetime.now(UTC).isoformat(),
        transcript_ref=transcript_ref,
        diff_base="HEAD",
        diff_hash=diff_hash,
        planner_tool="intention-audit/1.0",
        intentions_touched=intentions_touched or [],
        mapping_summary=mapping,
        notes=notes,
    )

    # Save to sessions directory
    sessions_dir = project_dir / ".intent_audit" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    record_path = sessions_dir / f"{session_id}.json"
    record_path.write_text(
        json.dumps(record.to_dict(), indent=2),
        encoding="utf-8",
    )

    return record


def load_session_record(project_dir: Path, session_id: str) -> SessionRecord | None:
    """
    Load a session record.

    Args:
        project_dir: Path to the project directory.
        session_id: Session ID to load.

    Returns:
        SessionRecord if found, None otherwise.
    """
    record_path = project_dir / ".intent_audit" / "sessions" / f"{session_id}.json"
    if not record_path.exists():
        return None

    data: dict[str, Any] = json.loads(record_path.read_text(encoding="utf-8"))
    return SessionRecord.from_dict(data)


def list_session_records(project_dir: Path) -> list[str]:
    """
    List all session IDs in the project.

    Args:
        project_dir: Path to the project directory.

    Returns:
        List of session IDs (without .json extension).
    """
    sessions_dir = project_dir / ".intent_audit" / "sessions"
    if not sessions_dir.exists():
        return []

    return [f.stem for f in sessions_dir.glob("*.json") if f.is_file()]
