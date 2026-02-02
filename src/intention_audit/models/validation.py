"""
Schema validation utilities for intention audit models.

Uses JSON schemas from specs/001-intent-audit-trail/contracts/.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

# Schema directory relative to this module
_SCHEMA_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "specs"
    / "001-intent-audit-trail"
    / "contracts"
)


def _load_schema(name: str) -> dict:
    """Load a JSON schema from the contracts directory."""
    schema_path = _SCHEMA_DIR / f"{name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_against_schema(data: dict, schema: dict) -> list[str]:
    """
    Validate data against a JSON schema.

    Returns a list of validation error messages.
    """
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
        path = ".".join(str(p) for p in error.path) if error.path else "(root)"
        errors.append(f"{path}: {error.message}")
    return errors


def validate_intentions(data: dict) -> list[str]:
    """
    Validate intentions data against the schema.

    Args:
        data: Dictionary to validate (should have 'root' key or be root intention directly).

    Returns:
        List of validation error messages. Empty list means valid.
    """
    try:
        schema = _load_schema("intentions")
    except FileNotFoundError:
        # If schema not found, perform basic validation
        return _validate_intentions_basic(data)

    # The schema expects {"root": {...}}, but we might get the root intention directly
    if "root" not in data and "id" in data:
        data = {"root": data}

    return _validate_against_schema(data, schema)


def _validate_intentions_basic(data: dict) -> list[str]:
    """Basic validation without JSON schema."""
    errors = []

    # Check for root or direct intention
    intention = data.get("root", data)
    if not isinstance(intention, dict):
        errors.append("(root): must be an object")
        return errors

    required = ["id", "title", "kind"]
    for field in required:
        if field not in intention:
            errors.append(f"(root): missing required field '{field}'")

    kind = intention.get("kind", "")
    valid_kinds = {"goal", "functionality", "implementation", "tests", "docs", "observability"}
    if kind and kind not in valid_kinds:
        errors.append(f"kind: must be one of {sorted(valid_kinds)}")

    status = intention.get("status", "planned")
    valid_statuses = {"planned", "in_progress", "implemented", "superseded", "deprecated"}
    if status not in valid_statuses:
        errors.append(f"status: must be one of {sorted(valid_statuses)}")

    return errors


def validate_commit_plan(data: dict) -> list[str]:
    """
    Validate commit plan data against the schema.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    try:
        schema = _load_schema("commit_plan")
    except FileNotFoundError:
        return _validate_commit_plan_basic(data)

    return _validate_against_schema(data, schema)


def _validate_commit_plan_basic(data: dict) -> list[str]:
    """Basic validation without JSON schema."""
    errors = []

    if data.get("version") != 1:
        errors.append("version: must be 1")

    if not isinstance(data.get("ready"), bool):
        errors.append("ready: must be a boolean")

    commits = data.get("commits")
    if not isinstance(commits, list):
        errors.append("commits: must be an array")
    elif len(commits) == 0:
        errors.append("commits: must have at least 1 item")
    else:
        for i, entry in enumerate(commits):
            if not isinstance(entry, dict):
                errors.append(f"commits.{i}: must be an object")
                continue
            if "intent_id" not in entry:
                errors.append(f"commits.{i}: missing required field 'intent_id'")
            if "subject" not in entry:
                errors.append(f"commits.{i}: missing required field 'subject'")

    return errors


def validate_session_record(data: dict) -> list[str]:
    """
    Validate session record data against the schema.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    try:
        schema = _load_schema("session_record")
    except FileNotFoundError:
        return _validate_session_record_basic(data)

    return _validate_against_schema(data, schema)


def _validate_session_record_basic(data: dict) -> list[str]:
    """Basic validation without JSON schema."""
    errors = []

    required = [
        "session_id",
        "timestamp",
        "transcript_ref",
        "diff_base",
        "diff_hash",
        "planner_tool",
        "intentions_touched",
        "mapping_summary",
    ]
    for field in required:
        if field not in data:
            errors.append(f"(root): missing required field '{field}'")

    if "intentions_touched" in data and not isinstance(data["intentions_touched"], list):
        errors.append("intentions_touched: must be an array")

    if "mapping_summary" in data and not isinstance(data["mapping_summary"], dict):
        errors.append("mapping_summary: must be an object")

    return errors


def validate_structure_validation(data: dict) -> list[str]:
    """
    Validate structure validation data against the schema.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    try:
        schema = _load_schema("structure_validation")
    except FileNotFoundError:
        return _validate_structure_validation_basic(data)

    return _validate_against_schema(data, schema)


def _validate_structure_validation_basic(data: dict) -> list[str]:
    """Basic validation without JSON schema."""
    errors = []

    # passed must be a boolean
    if "passed" not in data:
        errors.append("(root): missing required field 'passed'")
    elif not isinstance(data["passed"], bool):
        errors.append("passed: must be a boolean")

    # violations must be an array
    violations = data.get("violations")
    if violations is None:
        errors.append("(root): missing required field 'violations'")
    elif not isinstance(violations, list):
        errors.append("violations: must be an array")
    else:
        for i, violation in enumerate(violations):
            if not isinstance(violation, dict):
                errors.append(f"violations.{i}: must be an object")
                continue
            if "type" not in violation:
                errors.append(f"violations.{i}: missing required field 'type'")
            elif not isinstance(violation["type"], str):
                errors.append(f"violations.{i}.type: must be a string")
            if "intent_id" not in violation:
                errors.append(f"violations.{i}: missing required field 'intent_id'")
            elif not isinstance(violation["intent_id"], str):
                errors.append(f"violations.{i}.intent_id: must be a string")
            # Optional fields type checks
            if (
                "functionality_intent_id" in violation
                and violation["functionality_intent_id"] is not None
            ):
                if not isinstance(violation["functionality_intent_id"], str):
                    errors.append(
                        f"violations.{i}.functionality_intent_id: must be a string or null"
                    )
            if "violating_paths" in violation and violation["violating_paths"] is not None:
                if not isinstance(violation["violating_paths"], list):
                    errors.append(f"violations.{i}.violating_paths: must be an array or null")
            if "expected_prefixes" in violation and violation["expected_prefixes"] is not None:
                if not isinstance(violation["expected_prefixes"], list):
                    errors.append(f"violations.{i}.expected_prefixes: must be an array or null")
            if "details" in violation and violation["details"] is not None:
                if not isinstance(violation["details"], dict):
                    errors.append(f"violations.{i}.details: must be an object or null")
            if "suggested_fix" in violation and violation["suggested_fix"] is not None:
                if not isinstance(violation["suggested_fix"], str):
                    errors.append(f"violations.{i}.suggested_fix: must be a string or null")

    # override_rationale is optional but must be string or null
    if "override_rationale" in data and data["override_rationale"] is not None:
        if not isinstance(data["override_rationale"], str):
            errors.append("override_rationale: must be a string or null")

    return errors
