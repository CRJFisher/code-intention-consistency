"""
T047: E2E tests for evidence passing scenario.

This test verifies the complete flow where:
1. A change is made that doesn't break tests (e.g., add a docstring)
2. All artifacts are created (intentions, commit_plan, evidence_results, structure_validation, session_record)
3. Evidence tests PASS
4. Stop hook allows commits to be created

Test cases:
1. test_evidence_passing_allows_commits - Full flow where evidence tests pass
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from mcp_servers.intention_audit.tools.run_evidence_tests import run_evidence_tests
from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from mcp_servers.intention_audit.tools.save_structure_validation import (
    save_structure_validation,
)
from tests.e2e.conftest import compute_diff_hash, run_stop_hook
from tests.e2e.fixtures import (
    full_commit_entry,
    multi_commit_plan,
)


def _create_evidence_passing_intentions(
    intent_id: str,
    title: str,
    child_id: str,
    child_title: str,
    code_home: list[str] | None = None,
    evidence_tests: list[str] | None = None,
) -> dict:
    """
    Create an intention tree for a functionality change with evidence tests.

    Args:
        intent_id: Root intention identifier.
        title: Root intention title.
        child_id: Child implementation intention ID.
        child_title: Child intention title.
        code_home: List of code home prefixes (for structure validation).
        evidence_tests: List of pytest selectors for evidence tests.

    Returns:
        Dictionary conforming to intentions schema with functionality node.
    """
    functionality_child = {
        "id": child_id,
        "title": child_title,
        "kind": "functionality",
        "status": "implemented",
        "children": [],
    }

    if code_home:
        functionality_child["code_home"] = code_home

    if evidence_tests:
        functionality_child["evidence_tests"] = evidence_tests

    return {
        "id": intent_id,
        "title": title,
        "kind": "goal",
        "status": "implemented",
        "children": [functionality_child],
    }


def _create_passing_structure_validation() -> dict:
    """Create a structure validation result with no violations."""
    return {
        "violations": [],
        "passed": True,
        "override_rationale": None,
    }


def _save_session_record_to_artifact_dir(
    repo_path: Path,
    session_id: str,
    diff_hash: str,
    intent_ids: list[str],
    total_files: int = 1,
    total_commits: int = 1,
) -> dict[str, Any]:
    """
    Create and save a session record to the artifact directory.

    The stop hook expects session_record.json in the artifact directory
    (.intent_audit/<session_id>/<diff_hash>/session_record.json), not in the
    sessions directory that the save_session_record MCP tool uses.

    Args:
        repo_path: Path to the repository.
        session_id: Unique session identifier.
        diff_hash: Hash of uncommitted changes.
        intent_ids: List of intention IDs touched in this session.
        total_files: Number of files in the commit plan.
        total_commits: Number of commits in the commit plan.

    Returns:
        Dictionary with success status and path.
    """
    session_record = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "transcript_ref": f"claude://sessions/{session_id}",
        "diff_base": "HEAD",
        "diff_hash": diff_hash,
        "planner_tool": "test-harness",
        "intentions_touched": intent_ids,
        "mapping_summary": {
            "total_files": total_files,
            "total_commits": total_commits,
            "intentions_mapped": len(intent_ids),
        },
        "notes": "Test session for evidence passing scenario",
    }

    # Write to artifact directory (where stop hook expects it)
    artifact_dir = repo_path / ".intent_audit" / session_id / diff_hash
    artifact_dir.mkdir(parents=True, exist_ok=True)
    record_path = artifact_dir / "session_record.json"
    record_path.write_text(json.dumps(session_record, indent=2))

    return {
        "success": True,
        "path": str(record_path),
    }


@pytest.mark.e2e
class TestEvidencePassingScenario:
    """Test scenarios where evidence tests pass and commits are allowed."""

    def test_evidence_passing_allows_commits(self, demo_repo: Path, project_root: Path) -> None:
        """
        Full flow where evidence tests pass and commits are created.

        This test:
        1. Makes a non-breaking change (adds a docstring to operations.py)
        2. Creates all required artifacts using MCP tools
        3. Runs evidence tests (which should pass)
        4. Runs stop hook
        5. Verifies commits are created with Intent-Id trailers
        """
        # Step 1: Make a non-breaking change (add a docstring)
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Add a module-level docstring enhancement (non-breaking)
        enhanced_content = original_content.replace(
            '"""Arithmetic operations with intentional bug potential."""',
            '"""Arithmetic operations with intentional bug potential.\n\nThis module provides basic arithmetic functions for the calculator.\n"""',
        )
        operations_file.write_text(enhanced_content)

        session_id = "test-evidence-passing-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Step 2: Create intentions artifact
        intentions = _create_evidence_passing_intentions(
            intent_id="INT-EVIDENCE-001",
            title="Improve calculator documentation",
            child_id="INT-EVIDENCE-001-A",
            child_title="Enhance operations module docstring",
            code_home=["src/calculator/"],
            evidence_tests=[
                "tests/calculator/test_operations.py::test_add_positive",
                "tests/calculator/test_operations.py::test_add_negative",
                "tests/calculator/test_operations.py::test_subtract_positive",
            ],
        )
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 3: Create commit plan artifact
        plan = multi_commit_plan(
            [
                full_commit_entry(
                    intent_id="INT-EVIDENCE-001-A",
                    files=["src/calculator/operations.py"],
                    subject="docs: enhance operations module docstring",
                    functionality_intent_id="INT-EVIDENCE-001-A",
                ),
            ]
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 4: Run evidence tests via MCP tool
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",
            "tests/calculator/test_operations.py::test_add_negative",
            "tests/calculator/test_operations.py::test_subtract_positive",
        ]
        result = run_evidence_tests(session_id, str(demo_repo), diff_hash, test_selectors)
        assert result["success"], f"run_evidence_tests failed: {result}"
        assert result["all_passed"], f"Evidence tests did not pass: {result}"

        # Step 5: Create structure validation artifact (no violations)
        structure_validation = _create_passing_structure_validation()
        result = save_structure_validation(
            session_id, diff_hash, str(demo_repo), structure_validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        # Step 6: Create session record artifact in artifact directory
        # Note: We write directly to artifact directory where stop hook expects it
        result = _save_session_record_to_artifact_dir(
            repo_path=demo_repo,
            session_id=session_id,
            diff_hash=diff_hash,
            intent_ids=["INT-EVIDENCE-001", "INT-EVIDENCE-001-A"],
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Step 7: Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # Hook should allow stop (exit code 0)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"

        # Step 8: Verify commit was created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "docstring" in log_result.stdout.lower() or "INT-EVIDENCE" in log_result.stdout

        # Step 9: Verify Intent-Id trailer is present
        trailer_result = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        intent_id = trailer_result.stdout.strip()
        assert intent_id == "INT-EVIDENCE-001-A", (
            f"Expected Intent-Id 'INT-EVIDENCE-001-A', got '{intent_id}'"
        )

        # Step 10: Verify no uncommitted changes remain
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        # Filter out .intent_audit/ from status
        uncommitted = [
            line
            for line in status_result.stdout.strip().split("\n")
            if line and ".intent_audit" not in line
        ]
        assert len(uncommitted) == 0, f"Unexpected uncommitted files: {uncommitted}"

    def test_evidence_passing_with_multiple_commits(
        self, demo_repo: Path, project_root: Path
    ) -> None:
        """
        Test evidence passing with multiple commits in a single session.

        This test:
        1. Makes two non-breaking changes (docstrings to operations.py and test file)
        2. Creates artifacts with two-commit plan
        3. Verifies both commits are created
        """
        # Step 1: Make non-breaking changes to two files
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_ops = operations_file.read_text()
        enhanced_ops = original_ops.replace(
            "def add(a: int, b: int) -> int:",
            "def add(a: int, b: int) -> int:\n    # Enhanced implementation",
        )
        operations_file.write_text(enhanced_ops)

        test_file = demo_repo / "tests" / "calculator" / "test_operations.py"
        original_test = test_file.read_text()
        enhanced_test = original_test.replace(
            '"""Tests for calculator operations.',
            '"""Tests for calculator operations.\n\nComprehensive test suite for arithmetic functions.',
        )
        test_file.write_text(enhanced_test)

        session_id = "test-evidence-multi-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Step 2: Create intentions with two children
        intentions = {
            "id": "INT-MULTI-001",
            "title": "Improve calculator codebase",
            "kind": "goal",
            "status": "implemented",
            "children": [
                {
                    "id": "INT-MULTI-001-IMPL",
                    "title": "Enhance operations implementation",
                    "kind": "functionality",
                    "status": "implemented",
                    "code_home": ["src/calculator/"],
                    "evidence_tests": [
                        "tests/calculator/test_operations.py::test_add_positive",
                    ],
                    "children": [],
                },
                {
                    "id": "INT-MULTI-001-TEST",
                    "title": "Enhance test documentation",
                    "kind": "tests",
                    "status": "implemented",
                    "children": [],
                },
            ],
        }
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 3: Create two-commit plan
        plan = multi_commit_plan(
            [
                full_commit_entry(
                    intent_id="INT-MULTI-001-IMPL",
                    files=["src/calculator/operations.py"],
                    subject="refactor: enhance operations implementation",
                    functionality_intent_id="INT-MULTI-001-IMPL",
                ),
                full_commit_entry(
                    intent_id="INT-MULTI-001-TEST",
                    files=["tests/calculator/test_operations.py"],
                    subject="docs: enhance test documentation",
                ),
            ]
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 4: Run evidence tests
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",
        ]
        result = run_evidence_tests(session_id, str(demo_repo), diff_hash, test_selectors)
        assert result["success"], f"run_evidence_tests failed: {result}"
        assert result["all_passed"], f"Evidence tests did not pass: {result}"

        # Step 5: Create structure validation
        structure_validation = _create_passing_structure_validation()
        result = save_structure_validation(
            session_id, diff_hash, str(demo_repo), structure_validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        # Step 6: Create session record in artifact directory
        result = _save_session_record_to_artifact_dir(
            repo_path=demo_repo,
            session_id=session_id,
            diff_hash=diff_hash,
            intent_ids=["INT-MULTI-001", "INT-MULTI-001-IMPL", "INT-MULTI-001-TEST"],
            total_files=2,
            total_commits=2,
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Step 7: Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"

        # Step 8: Verify two commits were created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-3"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]
        # Should have at least 3 commits: initial + 2 new commits
        assert len(commits) >= 3, f"Expected at least 3 commits, got: {commits}"

        # Step 9: Verify Intent-Id trailers on both new commits
        for i in range(2):
            ref = f"HEAD~{i}"
            trailer_result = subprocess.run(
                ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)", ref],
                cwd=str(demo_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            intent_id = trailer_result.stdout.strip()
            assert intent_id, f"Expected Intent-Id trailer at {ref}, but none found"
            assert intent_id.startswith("INT-MULTI-001"), f"Unexpected Intent-Id: {intent_id}"

    def test_evidence_passing_with_all_tests_in_file(
        self, demo_repo: Path, project_root: Path
    ) -> None:
        """
        Test running evidence tests on an entire test file (file-level selector).

        This verifies the evidence runner handles file-level selectors correctly.
        """
        # Make a trivial non-breaking change
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()
        enhanced_content = original_content + "\n# End of file marker\n"
        operations_file.write_text(enhanced_content)

        session_id = "test-evidence-file-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Create intentions
        intentions = _create_evidence_passing_intentions(
            intent_id="INT-FILE-001",
            title="Add file marker",
            child_id="INT-FILE-001-A",
            child_title="Add end of file marker",
            code_home=["src/calculator/"],
            evidence_tests=["tests/calculator/test_operations.py"],  # File-level selector
        )
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan
        plan = multi_commit_plan(
            [
                full_commit_entry(
                    intent_id="INT-FILE-001-A",
                    files=["src/calculator/operations.py"],
                    subject="chore: add end of file marker",
                    functionality_intent_id="INT-FILE-001-A",
                ),
            ]
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run evidence tests with FILE-LEVEL selector
        test_selectors = ["tests/calculator/test_operations.py"]
        result = run_evidence_tests(session_id, str(demo_repo), diff_hash, test_selectors)
        assert result["success"], f"run_evidence_tests failed: {result}"
        assert result["all_passed"], f"Evidence tests did not pass: {result}"

        # Verify multiple tests were run (file contains multiple test functions)
        assert result["results"], "Expected multiple test results"
        assert len(result["results"]) >= 5, (
            f"Expected at least 5 tests from file, got {len(result['results'])}"
        )

        # Create remaining artifacts
        structure_validation = _create_passing_structure_validation()
        result = save_structure_validation(
            session_id, diff_hash, str(demo_repo), structure_validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        result = _save_session_record_to_artifact_dir(
            repo_path=demo_repo,
            session_id=session_id,
            diff_hash=diff_hash,
            intent_ids=["INT-FILE-001", "INT-FILE-001-A"],
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"

        # Verify commit was created
        trailer_result = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        assert trailer_result.stdout.strip() == "INT-FILE-001-A"
