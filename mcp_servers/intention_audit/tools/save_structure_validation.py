"""
MCP tool: save_structure_validation

Persistence endpoint for structure validation data. Validates and writes
structure_validation.json to the session+diff keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT check code_home boundaries (sub-agent does this)
- It MUST NOT analyze file paths (sub-agent does this)
- It MUST NOT suggest fixes (sub-agent does this)
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from intention_audit.models.structure_validation import (
    StructureValidation,
    StructureViolation,
)
from intention_audit.models.validation import validate_structure_validation


def save_structure_validation(
    session_id: str,
    diff_hash: str,
    cwd: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist structure validation data from a sub-agent.

    This tool is called by a sub-agent AFTER the sub-agent has analyzed
    the code_home boundaries and produced structure validation results.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        validation: Structured validation data (already analyzed by sub-agent).
            Must have: {violations: [...], passed: bool, override_rationale: str|null}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
    """
    project_dir = Path(cwd)

    # Validate structure validation against schema
    validation_errors = validate_structure_validation(validation)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid structure validation data: {'; '.join(validation_errors)}",
        }

    # Convert to StructureValidation model
    try:
        violations = [
            StructureViolation(
                type=v["type"],
                intent_id=v["intent_id"],
                functionality_intent_id=v.get("functionality_intent_id"),
                violating_paths=v.get("violating_paths", []),
                expected_prefixes=v.get("expected_prefixes", []),
                details=v.get("details", {}),
                suggested_fix=v.get("suggested_fix", ""),
            )
            for v in validation.get("violations", [])
        ]
        structure_validation = StructureValidation(
            violations=violations,
            passed=validation.get("passed", True),
            override_rationale=validation.get("override_rationale"),
        )
    except (KeyError, TypeError) as e:
        return {
            "success": False,
            "error": f"Failed to construct StructureValidation model: {e}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write structure_validation.json
    validation_path = artifact_dir / "structure_validation.json"
    structure_validation.save(validation_path)

    return {
        "success": True,
        "path": str(validation_path),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print(
            "Usage: save_structure_validation.py <session_id> <diff_hash> <cwd> <validation_json>"
        )
        print("\nExample:")
        print(
            '  save_structure_validation.py abc123 a1b2c3d4e5f6 /path/to/repo \'{"violations":[], "passed":true}\''
        )
        sys.exit(1)

    try:
        validation_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = save_structure_validation(
        sys.argv[1], sys.argv[2], sys.argv[3], validation_data
    )
    print(json.dumps(result, indent=2))
