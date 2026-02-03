"""
MCP tool: extract_implementation_requirements

Persistence endpoint for implementation requirements extracted from commit clusters.
Validates and writes implementation_requirements.json to the bootstrap artifact directory.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze diffs or extract requirements
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_implementation_requirements(data: dict) -> list[str]:
    """Basic validation of implementation requirements data."""
    errors = []

    # requirements must be an array
    requirements = data.get("requirements")
    if requirements is None:
        errors.append("(root): missing required field 'requirements'")
    elif not isinstance(requirements, list):
        errors.append("requirements: must be an array")
    else:
        for i, req in enumerate(requirements):
            if not isinstance(req, dict):
                errors.append(f"requirements.{i}: must be an object")
                continue

            required = ["ir_id", "cluster_id", "description"]
            for field in required:
                if field not in req:
                    errors.append(f"requirements.{i}: missing required field '{field}'")

            # Validate array fields
            array_fields = [
                "functions_modified",
                "classes_modified",
                "tests_added",
                "patterns_detected",
            ]
            for field in array_fields:
                if field in req and not isinstance(req[field], list):
                    errors.append(f"requirements.{i}.{field}: must be an array")

            if "confidence" in req:
                conf = req["confidence"]
                if not isinstance(conf, (int, float)):
                    errors.append(f"requirements.{i}.confidence: must be a number")
                elif not (0.0 <= conf <= 1.0):
                    errors.append(f"requirements.{i}.confidence: must be between 0.0 and 1.0")

    # Validate count fields
    if "irs_extracted" in data and not isinstance(data["irs_extracted"], int):
        errors.append("irs_extracted: must be an integer")

    return errors


def extract_implementation_requirements(
    cwd: str,
    requirements_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist implementation requirements from a sub-agent.

    This tool is called by the code-reviewer sub-agent AFTER the sub-agent
    has analyzed commit clusters and extracted implementation-level rationale.

    Args:
        cwd: Working directory of the project.
        requirements_data: Structured implementation requirements.
            Must have: {requirements: [{ir_id, cluster_id, description, ...}]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - ir_count: int (number of implementation requirements)
    """
    project_dir = Path(cwd)

    # Validate requirements data
    validation_errors = _validate_implementation_requirements(requirements_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid implementation requirements: {'; '.join(validation_errors)}",
        }

    # Create bootstrap artifact directory
    artifact_dir = project_dir / ".intent_audit" / "bootstrap"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write implementation_requirements.json
    requirements_path = artifact_dir / "implementation_requirements.json"
    with open(requirements_path, "w", encoding="utf-8") as f:
        json.dump(requirements_data, f, indent=2)

    # Extract summary for response
    requirements = requirements_data.get("requirements", [])

    return {
        "success": True,
        "path": str(requirements_path),
        "ir_count": len(requirements),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: extract_implementation_requirements.py <cwd> <requirements_json>")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = extract_implementation_requirements(sys.argv[1], data)
    print(json.dumps(result, indent=2))
