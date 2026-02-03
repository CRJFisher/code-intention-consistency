"""
MCP tool: cluster_commits

Persistence endpoint for commit clustering results from bootstrap mining.
Validates and writes commit_clusters.json to the bootstrap artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.

CRITICAL: This tool is a PERSISTENCE ENDPOINT.
- It MUST NOT analyze git history or cluster commits
- It MUST NOT perform semantic analysis
- It ONLY validates schema and writes data passed to it by a sub-agent
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_commit_clusters(data: dict) -> list[str]:
    """Basic validation of commit clusters data."""
    errors = []

    # clusters must be an array
    clusters = data.get("clusters")
    if clusters is None:
        errors.append("(root): missing required field 'clusters'")
    elif not isinstance(clusters, list):
        errors.append("clusters: must be an array")
    else:
        for i, cluster in enumerate(clusters):
            if not isinstance(cluster, dict):
                errors.append(f"clusters.{i}: must be an object")
                continue

            required = ["cluster_id", "commits", "semantic_label"]
            for field in required:
                if field not in cluster:
                    errors.append(f"clusters.{i}: missing required field '{field}'")

            if "commits" in cluster and not isinstance(cluster["commits"], list):
                errors.append(f"clusters.{i}.commits: must be an array")

            if "confidence" in cluster:
                conf = cluster["confidence"]
                if not isinstance(conf, (int, float)):
                    errors.append(f"clusters.{i}.confidence: must be a number")
                elif not (0.0 <= conf <= 1.0):
                    errors.append(f"clusters.{i}.confidence: must be between 0.0 and 1.0")

    # Validate count fields
    count_fields = ["commits_analyzed", "clusters_created"]
    for field in count_fields:
        if field in data and not isinstance(data[field], int):
            errors.append(f"{field}: must be an integer")

    return errors


def cluster_commits(
    cwd: str,
    clusters_data: dict[str, Any],
    since_date: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """
    Validate and persist commit clustering results from a sub-agent.

    This tool is called by the commit-searcher sub-agent AFTER the sub-agent
    has analyzed git history and grouped commits semantically.

    Args:
        cwd: Working directory of the project.
        clusters_data: Structured commit clusters (already analyzed by sub-agent).
            Must have: {clusters: [{cluster_id, commits, semantic_label, ...}]}
        since_date: Optional date filter used during mining.
        branch: Optional branch filter used during mining.

    Returns:
        Dictionary with:
        - success: bool
        - path: str (path to created file) if success
        - error: str (error message) if not success
        - cluster_count: int (number of clusters)
        - commits_analyzed: int (total commits analyzed)
    """
    project_dir = Path(cwd)

    # Validate clusters data
    validation_errors = _validate_commit_clusters(clusters_data)
    if validation_errors:
        return {
            "success": False,
            "error": f"Invalid commit clusters: {'; '.join(validation_errors)}",
        }

    # Create bootstrap artifact directory
    artifact_dir = project_dir / ".intent_audit" / "bootstrap"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Add metadata
    clusters_data["since_date"] = since_date
    clusters_data["branch"] = branch

    # Write commit_clusters.json
    clusters_path = artifact_dir / "commit_clusters.json"
    with open(clusters_path, "w", encoding="utf-8") as f:
        json.dump(clusters_data, f, indent=2)

    # Extract summary for response
    clusters = clusters_data.get("clusters", [])

    return {
        "success": True,
        "path": str(clusters_path),
        "cluster_count": len(clusters),
        "commits_analyzed": clusters_data.get("commits_analyzed", 0),
    }


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: cluster_commits.py <cwd> <clusters_json> [since_date] [branch]")
        print("\nExample:")
        print("  cluster_commits.py /path/to/repo '{\"clusters\": [...]}'")
        sys.exit(1)

    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    since = sys.argv[3] if len(sys.argv) > 3 else None
    branch_arg = sys.argv[4] if len(sys.argv) > 4 else None

    result = cluster_commits(sys.argv[1], data, since, branch_arg)
    print(json.dumps(result, indent=2))
