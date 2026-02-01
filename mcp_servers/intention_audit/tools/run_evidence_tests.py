"""
MCP tool: run_evidence_tests

Runs pytest tests that a sub-agent requests and persists results to the session+diff
keyed artifact directory.

IMPORTANT: Target repositories MUST add `.intent_audit/` to their .gitignore.
If not gitignored, artifact files will appear as untracked changes, changing
the diff hash and creating an infinite loop where the stop hook never unblocks.

CRITICAL: This tool is a TEST EXECUTION ENDPOINT.
- It MUST NOT decide which tests to run (sub-agent does this)
- It MUST NOT analyze test failures (sub-agent does this)
- It ONLY runs the specified tests and saves results
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from intention_audit.evidence.runner import EvidenceResults
from intention_audit.evidence.runner import run_evidence_tests as _run_tests


def run_evidence_tests(
    session_id: str,
    cwd: str,
    diff_hash: str,
    test_selectors: list[str],
) -> dict[str, Any]:
    """
    Run evidence tests via pytest and persist results.

    This tool is called by a sub-agent AFTER the sub-agent has decided
    which tests to run. This tool only executes tests and saves results.

    Args:
        session_id: Unique session identifier.
        cwd: Working directory of the project.
        diff_hash: Hash of the current uncommitted changes (16-char hex).
        test_selectors: List of pytest test selectors (e.g., ["tests/test_foo.py::test_bar"]).

    Returns:
        Dictionary with:
        - success: bool
        - all_passed: bool | None (None if error)
        - results: list of test result dicts (selector, passed, output, duration) | None
        - error: str | None
        - path: str (path to saved results file)
    """
    project_dir = Path(cwd)

    # Validate inputs
    if not test_selectors:
        return {
            "success": False,
            "all_passed": None,
            "results": None,
            "error": "No test selectors provided",
            "path": "",
        }

    if not project_dir.exists():
        return {
            "success": False,
            "all_passed": None,
            "results": None,
            "error": f"Project directory does not exist: {cwd}",
            "path": "",
        }

    try:
        # Run the tests
        evidence_results: EvidenceResults = _run_tests(project_dir, test_selectors)

        # Convert to output format
        results = _convert_results(evidence_results)

        # Create session+diff keyed artifact directory
        artifact_dir = project_dir / ".intent_audit" / session_id / diff_hash
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Write evidence_results.json
        results_path = artifact_dir / "evidence_results.json"
        output_data = {
            "success": True,
            "all_passed": evidence_results.all_passed,
            "summary": evidence_results.summary,
            "results": results,
            "raw_output": evidence_results.raw_output,
        }

        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        return {
            "success": True,
            "all_passed": evidence_results.all_passed,
            "results": results,
            "error": None,
            "path": str(results_path),
        }

    except Exception as e:
        return {
            "success": False,
            "all_passed": None,
            "results": None,
            "error": f"Error running tests: {e}",
            "path": "",
        }


def _convert_results(evidence_results: EvidenceResults) -> list[dict[str, Any]]:
    """Convert EvidenceResults to list of result dicts."""
    results: list[dict[str, Any]] = []

    for test_output in evidence_results.passed:
        results.append(asdict(test_output))

    for test_output in evidence_results.failed:
        results.append(asdict(test_output))

    for test_output in evidence_results.errors:
        results.append(asdict(test_output))

    return results


# For direct execution in tests
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: run_evidence_tests.py <session_id> <cwd> <diff_hash> <test_selectors_json>")
        print("\nExample:")
        print(
            '  run_evidence_tests.py abc123 /path/to/repo a1b2c3d4e5f6 '
            '\'["tests/test_foo.py::test_bar"]\''
        )
        sys.exit(1)

    try:
        selectors = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = run_evidence_tests(sys.argv[1], sys.argv[2], sys.argv[3], selectors)
    print(json.dumps(result, indent=2))
