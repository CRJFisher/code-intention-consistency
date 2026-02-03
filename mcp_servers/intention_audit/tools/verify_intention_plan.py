"""
MCP tool: verify_intention_plan

Plan verification endpoint that validates plan coherence before coding.
Based on LPW (Language-Model-Powered Workflow) research insight.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze conversation/trajectory
- It MUST NOT make decisions about plan quality
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_verification_data(data: dict) -> list[str]:
    """Basic validation of plan verification data."""
    errors = []

    # passed must be a boolean
    if "passed" not in data:
        errors.append("(root): missing required field 'passed'")
    elif not isinstance(data["passed"], bool):
        errors.append("passed: must be a boolean")

    # issues must be an array
    issues = data.get("issues")
    if issues is None:
        errors.append("(root): missing required field 'issues'")
    elif not isinstance(issues, list):
        errors.append("issues: must be an array")
    else:
        for i, issue in enumerate(issues):
            if not isinstance(issue, dict):
                errors.append(f"issues.{i}: must be an object")
                continue
            if "type" not in issue:
                errors.append(f"issues.{i}: missing required field 'type'")
            if "severity" not in issue:
                errors.append(f"issues.{i}: missing required field 'severity'")
            if "intent_id" not in issue:
                errors.append(f"issues.{i}: missing required field 'intent_id'")
            if "message" not in issue:
                errors.append(f"issues.{i}: missing required field 'message'")

    return errors


def verify_intention_plan(
    session_id: str,
    diff_hash: str,
    cwd: str,
    verification: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist plan verification results from a sub-agent.

    This tool is called by the plan-verifier sub-agent AFTER the sub-agent
    has analyzed the intention plan for coherence and achievability.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        verification: Structured verification results (already analyzed by sub-agent).
            Must have at minimum: {passed: bool, issues: [...]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate verification data
    validation_errors = _validate_verification_data(verification)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid verification data: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write plan_verification.json
    verification_path = artifact_dir / "plan_verification.json"
    with open(verification_path, "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2)

    return {
        "success": True,
        "path": str(verification_path),
        "passed": verification.get("passed", False),
        "error_count": verification.get("error_count", 0),
        "warning_count": verification.get("warning_count", 0),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: verify_intention_plan.py <session_id> <diff_hash> <cwd> <verification_json>")
        print("\nExample:")
        print(
            "  verify_intention_plan.py abc123 a1b2c3d4e5f6 /path/to/repo "
            '\'{"passed": true, "issues": []}\''
        )
        sys.exit(1)

    try:
        verification_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = verify_intention_plan(sys.argv[1], sys.argv[2], sys.argv[3], verification_data)
    print(json.dumps(result, indent=2))
