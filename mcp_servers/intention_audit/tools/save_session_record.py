"""
MCP tool: save_session_record

Persistence endpoint for session record data. Validates and writes
session record to the .intent_audit/sessions/<session_id>.json file.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT generate session metadata (sub-agent provides this)
- It MUST NOT analyze the session (sub-agent does this)
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from intention_audit.models.session_record import SessionRecord
from intention_audit.models.validation import validate_session_record


def save_session_record(
    session_id: str,
    cwd: str,
    diff_hash: str,
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist session record data from a sub-agent.

    This tool is called by a sub-agent AFTER the sub-agent has analyzed
    the session and produced structured session record data.

    Args:
        session_id: Unique session identifier.
        cwd: Working directory of the project.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        record: Structured session record data (already analyzed by sub-agent).
            Must have:
            - session_id: str
            - timestamp: str (ISO format)
            - transcript_ref: str
            - diff_base: str
            - diff_hash: str
            - planner_tool: str
            - intentions_touched: list[str]
            - mapping_summary: dict
            - notes: str | None (optional)

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate session record against schema
    validation_errors = validate_session_record(record)
    if validation_errors:
        return {
            "success": False,
            "path": None,
            "error": f"Invalid session record data: {'; '.join(validation_errors)}",
        }

    # Validate that session_id in record matches the provided session_id
    if record.get("session_id") != session_id:
        return {
            "success": False,
            "path": None,
            "error": f"session_id mismatch: provided '{session_id}' but record contains '{record.get('session_id')}'",
        }

    # Validate that diff_hash in record matches the provided diff_hash
    if record.get("diff_hash") != diff_hash:
        return {
            "success": False,
            "path": None,
            "error": f"diff_hash mismatch: provided '{diff_hash}' but record contains '{record.get('diff_hash')}'",
        }

    # Convert to SessionRecord model (validates structure)
    try:
        session_record = SessionRecord.from_dict(record)
    except (KeyError, TypeError, ValueError) as e:
        return {
            "success": False,
            "path": None,
            "error": f"Failed to create SessionRecord: {e}",
        }

    # Create sessions directory
    sessions_dir = project_dir / ".intent_audit" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Write session record as JSON
    record_path = sessions_dir / f"{session_id}.json"
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(session_record.to_dict(), f, indent=2)

    return {
        "success": True,
        "path": str(record_path),
        "error": None,
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: save_session_record.py <session_id> <cwd> <diff_hash> <record_json>")
        print("\nExample:")
        print(
            '  save_session_record.py abc123 /path/to/repo a1b2c3d4e5f6 '
            '\'{"session_id":"abc123", "timestamp":"...", ...}\''
        )
        sys.exit(1)

    try:
        record_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "path": None, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = save_session_record(sys.argv[1], sys.argv[2], sys.argv[3], record_data)
    print(json.dumps(result, indent=2))
