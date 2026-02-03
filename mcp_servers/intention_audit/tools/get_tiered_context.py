"""
MCP tool: get_tiered_context

Retrieves hierarchical memory context for sub-agents.
Implements HiAgent-inspired tiered memory management.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a RETRIEVAL ENDPOINT.
- It reads tiered_context.json from the session artifact directory
- It does NOT compute the context itself
- Context is computed by the main agent and saved separately
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_tiered_context(data: dict) -> list[str]:
    """Basic validation of tiered context data."""
    errors = []

    # session_id must be present
    if "session_id" not in data:
        errors.append("(root): missing required field 'session_id'")
    elif not isinstance(data["session_id"], str):
        errors.append("session_id: must be a string")

    # active_intention_path must be an array
    path = data.get("active_intention_path")
    if path is not None:
        if not isinstance(path, list):
            errors.append("active_intention_path: must be an array")
        elif not all(isinstance(p, str) for p in path):
            errors.append("active_intention_path: all elements must be strings")

    # Validate active context
    active = data.get("active")
    if active is not None:
        if not isinstance(active, dict):
            errors.append("active: must be an object")
        else:
            required = ["intent_id", "title", "type"]
            for field in required:
                if field not in active:
                    errors.append(f"active: missing required field '{field}'")

    # Validate recent array
    recent = data.get("recent")
    if recent is not None:
        if not isinstance(recent, list):
            errors.append("recent: must be an array")
        else:
            for i, summary in enumerate(recent):
                if not isinstance(summary, dict):
                    errors.append(f"recent.{i}: must be an object")
                    continue
                required = ["intent_id", "title", "type"]
                for field in required:
                    if field not in summary:
                        errors.append(f"recent.{i}: missing required field '{field}'")

    # Validate archive array
    archive = data.get("archive")
    if archive is not None:
        if not isinstance(archive, list):
            errors.append("archive: must be an array")
        else:
            for i, summary in enumerate(archive):
                if not isinstance(summary, dict):
                    errors.append(f"archive.{i}: must be an object")
                    continue
                required = ["intent_id", "title", "type"]
                for field in required:
                    if field not in summary:
                        errors.append(f"archive.{i}: missing required field '{field}'")

    # Validate size fields
    size_fields = ["total_intentions", "active_tier_size", "recent_tier_size", "archive_tier_size"]
    for field in size_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    return errors


def get_tiered_context(
    session_id: str,
    cwd: str,
    intent_id: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve tiered memory context for a sub-agent.

    This tool retrieves the pre-computed tiered context from the session
    artifact directory. If intent_id is provided, it returns context
    focused on that specific intention.

    Args:
        session_id: Unique session identifier.
        cwd: Working directory of the project.
        intent_id: Optional specific intention to focus context on.

    Returns:
        Dictionary with:
        - success: bool
        - context: dict (tiered context data) if success
        - error: str (error message) if not success
        - active_intention: str (current active intention ID)
        - context_size: int (total context size)
    """
    project_dir = Path(cwd)

    # Find the latest tiered context file
    session_dir = project_dir / ".intent_audit" / session_id
    if not session_dir.exists():
        return {
            "success": False,
            "error": f"Session directory not found: {session_id}",
        }

    # Look for tiered_context.json in session directory
    context_path = session_dir / "tiered_context.json"
    if not context_path.exists():
        # Check in diff subdirectories for latest
        diff_dirs = sorted(session_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for diff_dir in diff_dirs:
            if diff_dir.is_dir():
                candidate = diff_dir / "tiered_context.json"
                if candidate.exists():
                    context_path = candidate
                    break

    if not context_path.exists():
        return {
            "success": False,
            "error": "No tiered context found for session",
        }

    # Load and validate
    try:
        with open(context_path, encoding="utf-8") as f:
            context_data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in tiered_context.json: {e}",
        }

    validation_errors = _validate_tiered_context(context_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid tiered context: {'; '.join(validation_errors)}",
        }

    # If intent_id specified, filter context
    if intent_id:
        # Check if intent is in active path
        active_path = context_data.get("active_intention_path", [])
        if intent_id not in active_path:
            # Intent is not active, return archived view
            archive = context_data.get("archive", [])
            matching = [a for a in archive if a.get("intent_id") == intent_id]
            if matching:
                return {
                    "success": True,
                    "context": {
                        "session_id": session_id,
                        "focused_intention": matching[0],
                        "tier": "archive",
                    },
                    "active_intention": active_path[-1] if active_path else None,
                    "context_size": context_data.get("archive_tier_size", 0),
                }

    # Return full tiered context
    active_path = context_data.get("active_intention_path", [])
    total_size = (
        context_data.get("active_tier_size", 0)
        + context_data.get("recent_tier_size", 0)
        + context_data.get("archive_tier_size", 0)
    )

    return {
        "success": True,
        "context": context_data,
        "active_intention": active_path[-1] if active_path else None,
        "context_size": total_size,
        "path": str(context_path),
    }


def save_tiered_context(
    session_id: str,
    cwd: str,
    context: dict[str, Any],
    diff_hash: str | None = None,
) -> dict[str, Any]:
    """
    Save tiered memory context to the session artifact directory.

    Args:
        session_id: Unique session identifier.
        cwd: Working directory of the project.
        context: Tiered context data to save.
        diff_hash: Optional diff hash for diff-specific storage.

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate context data
    validation_errors = _validate_tiered_context(context)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid tiered context: {'; '.join(validation_errors)}",
        }

    # Determine save location
    if diff_hash:
        artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    else:
        artifact_dir = project_dir / ".intent_audit" / session_id

    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write tiered_context.json
    context_path = artifact_dir / "tiered_context.json"
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)

    return {
        "success": True,
        "path": str(context_path),
        "active_intention": context.get("active_intention_path", [])[-1]
        if context.get("active_intention_path")
        else None,
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: get_tiered_context.py <session_id> <cwd> [intent_id]")
        print("\nExample:")
        print("  get_tiered_context.py abc123 /path/to/repo")
        print("  get_tiered_context.py abc123 /path/to/repo INT-001")
        sys.exit(1)

    intent_id_arg = sys.argv[3] if len(sys.argv) > 3 else None
    result = get_tiered_context(sys.argv[1], sys.argv[2], intent_id_arg)
    print(json.dumps(result, indent=2))
