"""
Schema validation utilities for intention audit models.

Validates the audit artifacts (intentions, commit plans, session records,
structure/plan/alignment reports) with structural checks. The canonical JSON
schemas for these artifacts live as reference docs in
``backlog/docs/contracts/``.
"""

from __future__ import annotations


def validate_intentions(data: dict) -> list[str]:
    """
    Validate intentions data.

    Args:
        data: Dictionary to validate (should have 'root' key or be root intention directly).

    Returns:
        List of validation error messages. Empty list means valid.
    """
    errors = []

    # Accept either a {"root": {...}} wrapper or a direct intention.
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
    Validate commit plan data.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
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
    Validate session record data.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
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
    Validate structure validation data.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
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
            # Optional fields type checks - combined conditions
            func_id = violation.get("functionality_intent_id")
            if func_id is not None and not isinstance(func_id, str):
                errors.append(f"violations.{i}.functionality_intent_id: must be a string or null")
            viol_paths = violation.get("violating_paths")
            if viol_paths is not None and not isinstance(viol_paths, list):
                errors.append(f"violations.{i}.violating_paths: must be an array or null")
            exp_prefixes = violation.get("expected_prefixes")
            if exp_prefixes is not None and not isinstance(exp_prefixes, list):
                errors.append(f"violations.{i}.expected_prefixes: must be an array or null")
            details = violation.get("details")
            if details is not None and not isinstance(details, dict):
                errors.append(f"violations.{i}.details: must be an object or null")
            suggested = violation.get("suggested_fix")
            if suggested is not None and not isinstance(suggested, str):
                errors.append(f"violations.{i}.suggested_fix: must be a string or null")

    # override_rationale is optional but must be string or null
    override = data.get("override_rationale")
    if override is not None and not isinstance(override, str):
        errors.append("override_rationale: must be a string or null")

    return errors


def validate_plan_verification(data: dict) -> list[str]:
    """
    Validate plan verification data.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
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
        valid_types = {
            "code_home_conflict",
            "missing_evidence",
            "orphan_intention",
            "circular_dependency",
            "scope_overlap",
            "pattern_mismatch",
            "confidence_low",
        }
        valid_severities = {"error", "warning", "info"}

        for i, issue in enumerate(issues):
            if not isinstance(issue, dict):
                errors.append(f"issues.{i}: must be an object")
                continue
            if "type" not in issue:
                errors.append(f"issues.{i}: missing required field 'type'")
            elif issue["type"] not in valid_types:
                errors.append(f"issues.{i}.type: must be one of {sorted(valid_types)}")
            if "severity" not in issue:
                errors.append(f"issues.{i}: missing required field 'severity'")
            elif issue["severity"] not in valid_severities:
                errors.append(f"issues.{i}.severity: must be one of {sorted(valid_severities)}")
            if "intent_id" not in issue:
                errors.append(f"issues.{i}: missing required field 'intent_id'")
            elif not isinstance(issue["intent_id"], str):
                errors.append(f"issues.{i}.intent_id: must be a string")
            if "message" not in issue:
                errors.append(f"issues.{i}: missing required field 'message'")
            elif not isinstance(issue["message"], str):
                errors.append(f"issues.{i}.message: must be a string")

    # Optional numeric counts
    for count_field in ["error_count", "warning_count", "info_count"]:
        if count_field in data and not isinstance(data[count_field], int):
            errors.append(f"{count_field}: must be an integer")

    # override_rationale is optional but must be string or null
    override = data.get("override_rationale")
    if override is not None and not isinstance(override, str):
        errors.append("override_rationale: must be a string or null")

    return errors


def validate_alignment_report(data: dict) -> list[str]:
    """
    Validate alignment report data.

    Args:
        data: Dictionary to validate.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    errors = []

    # aligned must be a boolean
    if "aligned" not in data:
        errors.append("(root): missing required field 'aligned'")
    elif not isinstance(data["aligned"], bool):
        errors.append("aligned: must be a boolean")

    # comparisons must be an array
    comparisons = data.get("comparisons")
    if comparisons is None:
        errors.append("(root): missing required field 'comparisons'")
    elif not isinstance(comparisons, list):
        errors.append("comparisons: must be an array")
    else:
        valid_statuses = {
            "aligned",
            "partial",
            "misaligned",
            "missing_declared",
            "missing_inferred",
        }
        for i, comp in enumerate(comparisons):
            if not isinstance(comp, dict):
                errors.append(f"comparisons.{i}: must be an object")
                continue
            if "status" not in comp:
                errors.append(f"comparisons.{i}: missing required field 'status'")
            elif comp["status"] not in valid_statuses:
                errors.append(f"comparisons.{i}.status: must be one of {sorted(valid_statuses)}")
            if "confidence" in comp:
                conf = comp["confidence"]
                if not isinstance(conf, (int, float)):
                    errors.append(f"comparisons.{i}.confidence: must be a number")
                elif not (0.0 <= conf <= 1.0):
                    errors.append(f"comparisons.{i}.confidence: must be between 0.0 and 1.0")

    # Validate numeric count fields
    count_fields = [
        "total_declared",
        "total_inferred",
        "aligned_count",
        "partial_count",
        "misaligned_count",
        "missing_declared_count",
        "missing_inferred_count",
    ]
    for field in count_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    # Validate score fields (0.0-1.0)
    score_fields = ["alignment_score", "coverage_score", "confidence_avg"]
    for field in score_fields:
        if field in data:
            val = data[field]
            if not isinstance(val, (int, float)):
                errors.append(f"{field}: must be a number")
            elif not (0.0 <= val <= 1.0):
                errors.append(f"{field}: must be between 0.0 and 1.0")

    # override_rationale is optional but must be string or null
    override = data.get("override_rationale")
    if override is not None and not isinstance(override, str):
        errors.append("override_rationale: must be a string or null")

    return errors
