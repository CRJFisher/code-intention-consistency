"""
MCP tool: analyze_hunk_intents

Persistence endpoint for hunk-level tangled commit detection results.
Validates and writes hunk_analysis.json to the session+diff keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze diffs or detect tangles
- It MUST NOT perform AST or semantic analysis
- It ONLY validates schema and writes data passed to it by a sub-agent

Based on ColaUntangle research: dual-worker (explicit + implicit) analysis
for detecting when changes serve multiple intentions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_hunk_analysis(data: dict) -> list[str]:
    """Basic validation of hunk analysis data."""
    errors = []

    # passed must be a boolean
    if "passed" not in data:
        errors.append("(root): missing required field 'passed'")
    elif not isinstance(data["passed"], bool):
        errors.append("passed: must be a boolean")

    # Validate hunk_mappings array
    mappings = data.get("hunk_mappings")
    if mappings is not None:
        if not isinstance(mappings, list):
            errors.append("hunk_mappings: must be an array")
        else:
            for i, mapping in enumerate(mappings):
                if not isinstance(mapping, dict):
                    errors.append(f"hunk_mappings.{i}: must be an object")
                    continue
                required = ["file_path", "hunk_index", "start_line", "end_line", "intent_id"]
                for field in required:
                    if field not in mapping:
                        errors.append(f"hunk_mappings.{i}: missing required field '{field}'")
                if "intent_confidence" in mapping:
                    conf = mapping["intent_confidence"]
                    if not isinstance(conf, (int, float)):
                        errors.append(f"hunk_mappings.{i}.intent_confidence: must be a number")
                    elif not (0.0 <= conf <= 1.0):
                        errors.append(
                            f"hunk_mappings.{i}.intent_confidence: must be between 0.0 and 1.0"
                        )

    # Validate tangles array
    tangles = data.get("tangles")
    if tangles is not None:
        if not isinstance(tangles, list):
            errors.append("tangles: must be an array")
        else:
            valid_types = {"semantic", "functional", "structural", "dependency"}
            valid_severities = {"low", "medium", "high"}

            for i, tangle in enumerate(tangles):
                if not isinstance(tangle, dict):
                    errors.append(f"tangles.{i}: must be an object")
                    continue
                if "file_path" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'file_path'")
                if "type" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'type'")
                elif tangle["type"] not in valid_types:
                    errors.append(f"tangles.{i}.type: must be one of {sorted(valid_types)}")
                if "severity" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'severity'")
                elif tangle["severity"] not in valid_severities:
                    errors.append(
                        f"tangles.{i}.severity: must be one of {sorted(valid_severities)}"
                    )
                if "hunk_indices" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'hunk_indices'")
                elif not isinstance(tangle["hunk_indices"], list):
                    errors.append(f"tangles.{i}.hunk_indices: must be an array")
                if "intent_ids" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'intent_ids'")
                elif not isinstance(tangle["intent_ids"], list):
                    errors.append(f"tangles.{i}.intent_ids: must be an array")
                if "message" not in tangle:
                    errors.append(f"tangles.{i}: missing required field 'message'")

    # Validate count fields
    count_fields = [
        "total_hunks",
        "files_analyzed",
        "clean_files",
        "tangled_files",
        "low_tangles",
        "medium_tangles",
        "high_tangles",
    ]
    for field in count_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    # override_rationale is optional
    override = data.get("override_rationale")
    if override is not None and not isinstance(override, str):
        errors.append("override_rationale: must be a string or null")

    return errors


def analyze_hunk_intents(
    session_id: str,
    diff_hash: str,
    cwd: str,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist hunk analysis results from a sub-agent.

    This tool is called by the tangle-analyzer sub-agent AFTER the sub-agent
    has analyzed hunks for intent mixing using dual-worker approach.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        cwd: Working directory of the project.
        analysis: Structured hunk analysis (already analyzed by sub-agent).
            Must have at minimum: {passed: bool}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - passed: bool (whether no high-severity tangles)
        - tangle_count: int (number of tangles detected)
    """
    project_dir = Path(cwd)

    # Validate analysis data
    validation_errors = _validate_hunk_analysis(analysis)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid hunk analysis: {'; '.join(validation_errors)}",
        }

    # Create session+diff keyed artifact directory
    artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write hunk_analysis.json
    analysis_path = artifact_dir / "hunk_analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    # Extract summary for response
    tangles = analysis.get("tangles", [])
    high_tangles = sum(1 for t in tangles if t.get("severity") == "high")

    return {
        "success": True,
        "path": str(analysis_path),
        "passed": analysis.get("passed", False),
        "tangle_count": len(tangles),
        "high_tangle_count": high_tangles,
        "files_analyzed": analysis.get("files_analyzed", 0),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: analyze_hunk_intents.py <session_id> <diff_hash> <cwd> <analysis_json>")
        print("\nExample:")
        print("  analyze_hunk_intents.py abc123 a1b2c3d4e5f6 /path/to/repo '{\"passed\": true}'")
        sys.exit(1)

    try:
        analysis_data = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = analyze_hunk_intents(sys.argv[1], sys.argv[2], sys.argv[3], analysis_data)
    print(json.dumps(result, indent=2))
