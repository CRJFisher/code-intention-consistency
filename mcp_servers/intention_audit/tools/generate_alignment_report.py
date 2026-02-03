"""
MCP tool: generate_alignment_report

Persistence endpoint for alignment report data. Validates and writes
alignment_report.json to the session+diff keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze code or infer intents
- It MUST NOT compare declared vs inferred
- It ONLY validates schema and writes data passed to it by a sub-agent

Based on NeuroSync research insight: bidirectional comparison between
user's declared intents and system's inferred intents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_alignment_report(data: dict) -> list[str]:
    """Basic validation of alignment report data."""
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

    # Validate numeric fields
    numeric_fields = [
        "total_declared",
        "total_inferred",
        "aligned_count",
        "partial_count",
        "misaligned_count",
        "missing_declared_count",
        "missing_inferred_count",
    ]
    for field in numeric_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    # Validate score fields
    score_fields = ["alignment_score", "coverage_score", "confidence_avg"]
    for field in score_fields:
        if field in data:
            val = data[field]
            if not isinstance(val, (int, float)):
                errors.append(f"{field}: must be a number")
            elif not (0.0 <= val <= 1.0):
                errors.append(f"{field}: must be between 0.0 and 1.0")

    return errors


def generate_alignment_report(
    session_id: str,
    diff_hash: str,
    cwd: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist alignment report from a sub-agent.

    This tool is called by the alignment-reporter sub-agent AFTER the sub-agent
    has compared declared intentions vs. inferred intentions from code.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        report: Structured alignment report (already analyzed by sub-agent).
            Must have at minimum: {aligned: bool, comparisons: [...]}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - aligned: bool (whether overall alignment is acceptable)
        - alignment_score: float (0.0-1.0)
    """
    project_dir = Path(cwd)

    # Validate report data
    validation_errors = _validate_alignment_report(report)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid alignment report: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write alignment_report.json
    report_path = artifact_dir / "alignment_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {
        "success": True,
        "path": str(report_path),
        "aligned": report.get("aligned", False),
        "alignment_score": report.get("alignment_score", 0.0),
        "misaligned_count": report.get("misaligned_count", 0),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: generate_alignment_report.py <session_id> <diff_hash> <cwd> <report_json>")
        print("\nExample:")
        print(
            "  generate_alignment_report.py abc123 a1b2c3d4e5f6 /path/to/repo "
            '\'{"aligned": true, "comparisons": []}\''
        )
        sys.exit(1)

    try:
        report_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = generate_alignment_report(sys.argv[1], sys.argv[2], sys.argv[3], report_data)
    print(json.dumps(result, indent=2))
