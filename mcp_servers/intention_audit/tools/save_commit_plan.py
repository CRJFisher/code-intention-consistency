"""
MCP tool: save_commit_plan

Persistence endpoint for commit plan data. Validates and writes
commit_plan.yaml to the session+diff keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT map diff hunks to intentions (sub-agent does this)
- It MUST NOT analyze the diff (sub-agent does this)
- It MUST NOT decide which files go in which commit (sub-agent does this)
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from intention_audit.models.validation import validate_commit_plan


def save_commit_plan(
    session_id: str,
    diff_hash: str,
    cwd: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist commit plan data from a sub-agent.

    This tool is called by the commit-planner sub-agent AFTER the sub-agent
    has analyzed the diff and intentions and produced a structured commit plan.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        plan: Structured commit plan data (already analyzed by sub-agent).
            Must have: {version: 1, ready: bool, commits: [{intent_id, subject, files, ...}]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate commit plan against schema
    validation_errors = validate_commit_plan(plan)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid commit plan data: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write commit_plan.yaml (as JSON for MVP compatibility)
    plan_path = artifact_dir / "commit_plan.yaml"
    with open(plan_path, "w", encoding="utf-8") as f:
        # Use JSON for MVP (stop hook requires JSON parsing)
        json.dump(plan, f, indent=2)

    return {
        "success": True,
        "path": str(plan_path),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: save_commit_plan.py <session_id> <diff_hash> <cwd> <plan_json>")
        print("\nExample:")
        print('  save_commit_plan.py abc123 a1b2c3d4e5f6 /path/to/repo \'{"version":1, "ready":true, "commits":[...]}\'')
        sys.exit(1)

    try:
        plan_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = save_commit_plan(sys.argv[1], sys.argv[2], sys.argv[3], plan_data)
    print(json.dumps(result, indent=2))
