"""
MCP tool: save_intentions

Persistence endpoint for intention data. Validates and writes
intentions.yaml to the session+diff keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze conversation/trajectory
- It MUST NOT make decisions about intentions
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from intention_audit.models.validation import validate_intentions


def save_intentions(
    session_id: str,
    diff_hash: str,
    cwd: str,
    intentions: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist intention data from a sub-agent.

    This tool is called by the intention-mapper sub-agent AFTER the sub-agent
    has analyzed the conversation and produced structured intention data.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        intentions: Structured intention tree data (already analyzed by sub-agent).
            Must have at minimum: {id, title, kind, children: [...]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate intentions against schema
    validation_errors = validate_intentions(intentions)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid intentions data: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write intentions.yaml
    intentions_path = artifact_dir / "intentions.yaml"
    with open(intentions_path, "w", encoding="utf-8") as f:
        yaml.dump(intentions, f, default_flow_style=False, sort_keys=False)

    return {
        "success": True,
        "path": str(intentions_path),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: save_intentions.py <session_id> <diff_hash> <cwd> <intentions_json>")
        print("\nExample:")
        print('  save_intentions.py abc123 a1b2c3d4e5f6 /path/to/repo \'{"id":"INT-...", "title":"...", "kind":"goal"}\'')
        sys.exit(1)

    try:
        intentions_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = save_intentions(sys.argv[1], sys.argv[2], sys.argv[3], intentions_data)
    print(json.dumps(result, indent=2))
