"""
MCP tool: compute_drift_score

Persistence endpoint for drift detection results. Validates and writes
drift history and alerts to the session artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT compute semantic similarity or embeddings
- It MUST NOT analyze code for drift patterns
- It ONLY validates schema and writes data passed to it by a sub-agent

Based on research insight: Active drift monitoring with threshold alerts
enables early correction before drift becomes irreversible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_drift_data(data: dict) -> list[str]:
    """Basic validation of drift history data."""
    errors = []

    # Required fields
    if "session_id" not in data:
        errors.append("(root): missing required field 'session_id'")
    elif not isinstance(data["session_id"], str):
        errors.append("session_id: must be a string")

    if "root_intention_id" not in data:
        errors.append("(root): missing required field 'root_intention_id'")
    elif not isinstance(data["root_intention_id"], str):
        errors.append("root_intention_id: must be a string")

    # Validate scores array
    scores = data.get("scores")
    if scores is not None:
        if not isinstance(scores, list):
            errors.append("scores: must be an array")
        else:
            for i, score_entry in enumerate(scores):
                if not isinstance(score_entry, dict):
                    errors.append(f"scores.{i}: must be an object")
                    continue
                if "score" in score_entry:
                    s = score_entry["score"]
                    if not isinstance(s, (int, float)):
                        errors.append(f"scores.{i}.score: must be a number")
                    elif not (0.0 <= s <= 1.0):
                        errors.append(f"scores.{i}.score: must be between 0.0 and 1.0")

    # Validate alerts array
    alerts = data.get("alerts")
    if alerts is not None:
        if not isinstance(alerts, list):
            errors.append("alerts: must be an array")
        else:
            valid_types = {
                "scope_creep",
                "goal_divergence",
                "pattern_drift",
                "context_loss",
                "priority_shift",
            }
            valid_severities = {"low", "medium", "high", "critical"}

            for i, alert in enumerate(alerts):
                if not isinstance(alert, dict):
                    errors.append(f"alerts.{i}: must be an object")
                    continue
                if "id" not in alert:
                    errors.append(f"alerts.{i}: missing required field 'id'")
                if "type" not in alert:
                    errors.append(f"alerts.{i}: missing required field 'type'")
                elif alert["type"] not in valid_types:
                    errors.append(f"alerts.{i}.type: must be one of {sorted(valid_types)}")
                if "severity" not in alert:
                    errors.append(f"alerts.{i}: missing required field 'severity'")
                elif alert["severity"] not in valid_severities:
                    errors.append(f"alerts.{i}.severity: must be one of {sorted(valid_severities)}")
                if "drift_score" in alert:
                    ds = alert["drift_score"]
                    if not isinstance(ds, (int, float)):
                        errors.append(f"alerts.{i}.drift_score: must be a number")
                    elif not (0.0 <= ds <= 1.0):
                        errors.append(f"alerts.{i}.drift_score: must be between 0.0 and 1.0")

    # Validate threshold fields
    for field in [
        "alert_threshold",
        "warning_threshold",
        "current_score",
        "max_score",
        "avg_score",
    ]:
        if field in data:
            val = data[field]
            if not isinstance(val, (int, float)):
                errors.append(f"{field}: must be a number")
            elif not (0.0 <= val <= 1.0):
                errors.append(f"{field}: must be between 0.0 and 1.0")

    # Validate trend
    valid_trends = {"improving", "stable", "worsening", None}
    trend = data.get("trend")
    if trend is not None and trend not in valid_trends:
        errors.append(f"trend: must be one of {sorted(t for t in valid_trends if t)}")

    return errors


def compute_drift_score(
    session_id: str,
    cwd: str,
    drift_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and persist drift detection results from a sub-agent.

    This tool is called by the drift-monitor sub-agent AFTER the sub-agent
    has analyzed code changes for goal drift patterns.

    Args:
        session_id: Unique session identifier.
        cwd: Working directory of the project.
        drift_data: Structured drift history (already analyzed by sub-agent).
            Must have at minimum: {session_id, root_intention_id}

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - current_score: float (current drift score)
        - has_alerts: bool (whether any alerts were triggered)
    """
    project_dir = Path(cwd)

    # Validate drift data
    validation_errors = _validate_drift_data(drift_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid drift data: {'; '.join(validation_errors)}",
        }

    # Create session artifact directory (not diff-keyed, as drift tracks across diffs)
    artifact_dir = project_dir / ".intent_audit" / session_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Write drift_history.json
    drift_path = artifact_dir / "drift_history.json"
    with open(drift_path, "w", encoding="utf-8") as f:
        json.dump(drift_data, f, indent=2)

    # Extract summary for response
    current_score = drift_data.get("current_score", 0.0)
    alerts = drift_data.get("alerts", [])
    has_alerts = len(alerts) > 0
    critical_count = sum(1 for a in alerts if a.get("severity") == "critical")

    return {
        "success": True,
        "path": str(drift_path),
        "current_score": current_score,
        "has_alerts": has_alerts,
        "alert_count": len(alerts),
        "critical_count": critical_count,
        "trend": drift_data.get("trend"),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: compute_drift_score.py <session_id> <cwd> <drift_data_json>")
        print("\nExample:")
        print(
            "  compute_drift_score.py abc123 /path/to/repo "
            '\'{"session_id": "abc123", "root_intention_id": "INT-001"}\''
        )
        sys.exit(1)

    try:
        data = json.loads(sys.argv[3])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = compute_drift_score(sys.argv[1], sys.argv[2], data)
    print(json.dumps(result, indent=2))
