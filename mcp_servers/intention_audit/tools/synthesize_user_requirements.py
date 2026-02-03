"""
MCP tool: synthesize_user_requirements

Persistence endpoint for synthesized user requirements (draft intentions).
Validates and writes draft_intentions.yaml to the bootstrap artifact directory.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT synthesize or analyze requirements
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def _validate_synthesized_intentions(data: dict) -> list[str]:
    """Basic validation of synthesized intentions data."""
    errors = []

    # intentions must be an array
    intentions = data.get("intentions")
    if intentions is None:
        errors.append("(root): missing required field 'intentions'")
    elif not isinstance(intentions, list):
        errors.append("intentions: must be an array")
    else:
        valid_types = {"goal", "functionality", "implementation"}

        for i, intent in enumerate(intentions):
            if not isinstance(intent, dict):
                errors.append(f"intentions.{i}: must be an object")
                continue

            required = ["intent_id", "title", "type"]
            for field in required:
                if field not in intent:
                    errors.append(f"intentions.{i}: missing required field '{field}'")

            if "type" in intent and intent["type"] not in valid_types:
                errors.append(f"intentions.{i}.type: must be one of {sorted(valid_types)}")

            # Validate array fields
            array_fields = [
                "source_ir_ids",
                "source_clusters",
                "child_ids",
                "code_home",
                "evidence_tests",
            ]
            for field in array_fields:
                if field in intent and not isinstance(intent[field], list):
                    errors.append(f"intentions.{i}.{field}: must be an array")

            if "confidence" in intent:
                conf = intent["confidence"]
                if not isinstance(conf, (int, float)):
                    errors.append(f"intentions.{i}.confidence: must be a number")
                elif not (0.0 <= conf <= 1.0):
                    errors.append(f"intentions.{i}.confidence: must be between 0.0 and 1.0")

    # Validate count fields
    if "intentions_synthesized" in data and not isinstance(data["intentions_synthesized"], int):
        errors.append("intentions_synthesized: must be an integer")

    return errors


def synthesize_user_requirements(
    cwd: str,
    intentions_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist synthesized user requirements from a sub-agent.

    This tool is called by the intent-writer sub-agent AFTER the sub-agent
    has synthesized user-level intentions from implementation requirements.

    Args:
        cwd: Working directory of the project.
        intentions_data: Structured synthesized intentions.
            Must have: {intentions: [{intent_id, title, type, ...}]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - intention_count: int (number of intentions synthesized)
        - goal_count: int (number of goal-level intentions)
    """
    project_dir = Path(cwd)

    # Validate intentions data
    validation_errors = _validate_synthesized_intentions(intentions_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid synthesized intentions: {'; '.join(validation_errors)}",
        }

    # Create bootstrap artifact directory
    artifact_dir = project_dir / ".intent_audit" / "bootstrap"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write draft_intentions.yaml (YAML for human readability)
    draft_path = artifact_dir / "draft_intentions.yaml"
    with open(draft_path, "w", encoding="utf-8") as f:
        yaml.dump(intentions_data, f, default_flow_style=False, sort_keys=False)

    # Also write JSON version for programmatic access
    json_path = artifact_dir / "draft_intentions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(intentions_data, f, indent=2)

    # Extract summary for response
    intentions = intentions_data.get("intentions", [])
    goal_count = sum(1 for i in intentions if i.get("type") == "goal")

    return {
        "success": True,
        "path": str(draft_path),
        "json_path": str(json_path),
        "intention_count": len(intentions),
        "goal_count": goal_count,
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: synthesize_user_requirements.py <cwd> <intentions_json>")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = synthesize_user_requirements(sys.argv[1], data)
    print(json.dumps(result, indent=2))
