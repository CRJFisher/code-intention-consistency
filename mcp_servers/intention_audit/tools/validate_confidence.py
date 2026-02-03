"""
MCP tool: validate_confidence

Persistence endpoint for confidence-based validation results.
Validates and writes confidence_validation.json to the session+diff keyed artifact directory.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze confidence or determine validation requirements
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_confidence_result(data: dict) -> list[str]:
    """Basic validation of confidence validation data."""
    errors = []

    # passed must be a boolean
    if "passed" not in data:
        errors.append("(root): missing required field 'passed'")
    elif not isinstance(data["passed"], bool):
        errors.append("passed: must be a boolean")

    # Validate checks array
    checks = data.get("checks")
    if checks is not None:
        if not isinstance(checks, list):
            errors.append("checks: must be an array")
        else:
            valid_tiers = {"high", "medium", "low"}
            valid_requirements = {"standard", "additional_evidence", "human_confirmation"}

            for i, check in enumerate(checks):
                if not isinstance(check, dict):
                    errors.append(f"checks.{i}: must be an object")
                    continue

                required = ["intent_id", "confidence", "tier", "requirement"]
                for field in required:
                    if field not in check:
                        errors.append(f"checks.{i}: missing required field '{field}'")

                if "confidence" in check:
                    conf = check["confidence"]
                    if not isinstance(conf, (int, float)):
                        errors.append(f"checks.{i}.confidence: must be a number")
                    elif not (0.0 <= conf <= 1.0):
                        errors.append(f"checks.{i}.confidence: must be between 0.0 and 1.0")

                if "tier" in check and check["tier"] not in valid_tiers:
                    errors.append(f"checks.{i}.tier: must be one of {sorted(valid_tiers)}")

                if "requirement" in check and check["requirement"] not in valid_requirements:
                    errors.append(
                        f"checks.{i}.requirement: must be one of {sorted(valid_requirements)}"
                    )

    # Validate thresholds
    thresholds = data.get("thresholds")
    if thresholds is not None:
        if not isinstance(thresholds, dict):
            errors.append("thresholds: must be an object")
        else:
            for field in ["high_threshold", "medium_threshold"]:
                if field in thresholds:
                    val = thresholds[field]
                    if not isinstance(val, (int, float)):
                        errors.append(f"thresholds.{field}: must be a number")
                    elif not (0.0 <= val <= 1.0):
                        errors.append(f"thresholds.{field}: must be between 0.0 and 1.0")

    # Validate count fields
    count_fields = [
        "total_checked",
        "high_confidence_count",
        "medium_confidence_count",
        "low_confidence_count",
    ]
    for field in count_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    # Validate array fields
    array_fields = ["needs_additional_evidence", "needs_human_confirmation"]
    for field in array_fields:
        if field in data and not isinstance(data[field], list):
            errors.append(f"{field}: must be an array")

    # override_rationale is optional
    override = data.get("override_rationale")
    if override is not None and not isinstance(override, str):
        errors.append("override_rationale: must be a string or null")

    return errors


def validate_confidence(
    session_id: str,
    diff_hash: str,
    cwd: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist confidence validation results from a sub-agent.

    This tool is called after confidence-based validation has been performed
    by the evidence-checker or a dedicated confidence-validator sub-agent.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        validation: Structured confidence validation results.
            Must have at minimum: {passed: bool}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - passed: bool (whether validation passed)
        - needs_confirmation: list[str] (intent_ids needing human confirmation)
    """
    project_dir = Path(cwd)

    # Validate data
    validation_errors = _validate_confidence_result(validation)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid confidence validation: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write confidence_validation.json
    validation_path = artifact_dir / "confidence_validation.json"
    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

    # Extract summary for response
    needs_confirmation = validation.get("needs_human_confirmation", [])
    needs_evidence = validation.get("needs_additional_evidence", [])

    return {
        "success": True,
        "path": str(validation_path),
        "passed": validation.get("passed", False),
        "needs_confirmation": needs_confirmation,
        "needs_additional_evidence": needs_evidence,
        "total_checked": validation.get("total_checked", 0),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: validate_confidence.py <session_id> <diff_hash> <cwd> <validation_json>")
        sys.exit(1)

    try:
        validation_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = validate_confidence(sys.argv[1], sys.argv[2], sys.argv[3], validation_data)
    print(json.dumps(result, indent=2))
