"""
MCP tool: verify_intention_tree

Persistence endpoint for verified intention tree from bootstrap mining.
Validates and writes final intentions.yaml to the bootstrap artifact directory.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT verify or analyze intentions
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def _validate_verified_intentions(data: dict) -> list[str]:
    """Basic validation of verified intentions data."""
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

            # Verified intentions should have linkage
            if "code_home" in intent and not isinstance(intent["code_home"], list):
                errors.append(f"intentions.{i}.code_home: must be an array")

            if "evidence_tests" in intent and not isinstance(intent["evidence_tests"], list):
                errors.append(f"intentions.{i}.evidence_tests: must be an array")

    # evidence_mappings is optional but must be valid if present
    mappings = data.get("evidence_mappings")
    if mappings is not None:
        if not isinstance(mappings, list):
            errors.append("evidence_mappings: must be an array")
        else:
            for i, mapping in enumerate(mappings):
                if not isinstance(mapping, dict):
                    errors.append(f"evidence_mappings.{i}: must be an object")
                    continue
                if "intent_id" not in mapping:
                    errors.append(f"evidence_mappings.{i}: missing required field 'intent_id'")
                if "test_path" not in mapping:
                    errors.append(f"evidence_mappings.{i}: missing required field 'test_path'")

    # verification_summary is optional
    summary = data.get("verification_summary")
    if summary is not None and not isinstance(summary, dict):
        errors.append("verification_summary: must be an object")

    return errors


def verify_intention_tree(
    cwd: str,
    verified_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist verified intention tree from a sub-agent.

    This tool is called by the intent-verifier sub-agent AFTER the sub-agent
    has validated and linked the synthesized intentions to code.

    Args:
        cwd: Working directory of the project.
        verified_data: Verified intention tree with linkage.
            Must have: {intentions: [{intent_id, title, type, code_home?, evidence_tests?, ...}]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - intention_count: int (number of verified intentions)
        - linked_tests: int (number of evidence test mappings)
    """
    project_dir = Path(cwd)

    # Validate verified data
    validation_errors = _validate_verified_intentions(verified_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid verified intentions: {'; '.join(validation_errors)}",
        }

    # Create bootstrap artifact directory
    artifact_dir = project_dir / ".intent_audit" / "bootstrap"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write intentions.yaml (final verified output)
    intentions_path = artifact_dir / "intentions.yaml"
    with open(intentions_path, "w", encoding="utf-8") as f:
        yaml.dump(verified_data, f, default_flow_style=False, sort_keys=False)

    # Write evidence_mappings.json if present
    mappings = verified_data.get("evidence_mappings", [])
    if mappings:
        mappings_path = artifact_dir / "evidence_mappings.json"
        with open(mappings_path, "w", encoding="utf-8") as f:
            json.dump({"mappings": mappings}, f, indent=2)

    # Extract summary for response
    intentions = verified_data.get("intentions", [])

    return {
        "success": True,
        "path": str(intentions_path),
        "intention_count": len(intentions),
        "linked_tests": len(mappings),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: verify_intention_tree.py <cwd> <verified_json>")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = verify_intention_tree(sys.argv[1], data)
    print(json.dumps(result, indent=2))
