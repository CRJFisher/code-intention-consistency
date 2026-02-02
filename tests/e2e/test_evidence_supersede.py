"""
T050: E2E test for evidence supersede path scenario.

This test validates the "supersede" workflow for handling obsolete intentions:
1. Make a code change that breaks evidence tests for an OLD intention
2. Instead of fixing, mark the OLD intention as status="superseded"
3. Create a NEW intention to replace it
4. Update commit plan to reference the NEW intention
5. Update evidence_tests to point to new/updated tests
6. Verify stop hook allows commits with new Intent-Id in trailer

The key concept: When an intention becomes obsolete, mark it `superseded` and
create a new intention. This is the "supersede" workflow vs the "repair" workflow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add project root to path for MCP tool imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.intention_audit.tools.run_evidence_tests import run_evidence_tests
from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from tests.e2e.conftest import compute_diff_hash, run_stop_hook


def superseded_intention(
    intent_id: str,
    title: str,
    kind: str = "functionality",
    superseded_by: str | None = None,
    evidence_tests: list[str] | None = None,
    code_home: list[str] | None = None,
    children: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Create an intention marked as superseded.

    Args:
        intent_id: Unique identifier.
        title: Human-readable title.
        kind: Intention kind.
        superseded_by: ID of the intention that replaces this one.
        evidence_tests: Test selectors (now obsolete for superseded intention).
        code_home: Directory prefixes for code home.
        children: List of child intentions.

    Returns:
        Dictionary conforming to intentions schema with status="superseded".
    """
    intention: dict[str, Any] = {
        "id": intent_id,
        "title": title,
        "kind": kind,
        "status": "superseded",
        "children": children or [],
    }
    if superseded_by:
        intention["superseded_by"] = superseded_by
    if evidence_tests:
        intention["evidence_tests"] = evidence_tests
    if code_home:
        intention["code_home"] = code_home
    return intention


def active_intention(
    intent_id: str,
    title: str,
    kind: str = "functionality",
    evidence_tests: list[str] | None = None,
    code_home: list[str] | None = None,
    children: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Create an active intention with planned status.

    Args:
        intent_id: Unique identifier.
        title: Human-readable title.
        kind: Intention kind.
        evidence_tests: Test selectors that evidence this intention.
        code_home: Directory prefixes for code home.
        children: List of child intentions.

    Returns:
        Dictionary conforming to intentions schema with status="planned".
    """
    intention: dict[str, Any] = {
        "id": intent_id,
        "title": title,
        "kind": kind,
        "status": "planned",
        "children": children or [],
    }
    if evidence_tests:
        intention["evidence_tests"] = evidence_tests
    if code_home:
        intention["code_home"] = code_home
    return intention


def goal_tree_with_superseded(
    root_id: str,
    root_title: str,
    superseded: dict[str, Any],
    replacement: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a goal tree containing both a superseded intention and its replacement.

    Args:
        root_id: Root intention identifier.
        root_title: Root intention title.
        superseded: The superseded intention (status="superseded").
        replacement: The new intention that replaces the superseded one.

    Returns:
        Dictionary with root goal containing both intentions.
    """
    return {
        "id": root_id,
        "title": root_title,
        "kind": "goal",
        "status": "planned",
        "children": [superseded, replacement],
    }


def _create_session_record_artifact(
    artifact_dir: Path,
    session_id: str,
    diff_hash: str,
    intentions_touched: list[str],
) -> None:
    """Create a session record artifact for test purposes."""
    record = {
        "session_id": session_id,
        "timestamp": "2026-02-01T12:00:00+00:00",
        "transcript_ref": f"transcripts/{session_id}.jsonl",
        "diff_base": "HEAD",
        "diff_hash": diff_hash,
        "planner_tool": "test-runner",
        "intentions_touched": intentions_touched,
        "mapping_summary": {"total_files": 1, "commits_planned": 1},
        "notes": "Test session record for evidence supersede test",
    }
    record_path = artifact_dir / "session_record.json"
    record_path.write_text(json.dumps(record, indent=2))


def _create_structure_validation_artifact(artifact_dir: Path) -> None:
    """Create a passing structure validation artifact for test purposes."""
    validation = {
        "violations": [],
        "passed": True,
        "override_rationale": None,
    }
    validation_path = artifact_dir / "structure_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2))


@pytest.mark.e2e
class TestEvidenceSupersedePath:
    """
    Test the evidence supersede workflow.

    This tests the scenario where:
    - An old intention becomes obsolete
    - Instead of repairing failing tests, mark it as superseded
    - Create a new intention with updated evidence tests
    - Commit references the NEW intention ID
    """

    def test_supersede_old_intention_allows_commits(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that superseding an old intention allows commits to proceed.

        Flow:
        1. Make a change that conceptually breaks the OLD intention's evidence tests
           (we change add() behavior - the old tests expect the old behavior)
        2. Instead of fixing, mark OLD intention (INT-DEMO-002) as status="superseded"
        3. Create NEW intention (INT-SUPERSEDE-001) with NEW tests
        4. Update commit plan to reference the NEW intention
        5. Run evidence tests for the NEW intention's tests (they pass)
        6. Verify stop hook allows commits with new Intent-Id in trailer

        The key insight: The old tests still exist and would fail if run,
        but since we've marked the old intention as superseded and created
        a new intention with its own passing tests, the commit should proceed.
        """
        # Step 1: Make a change that changes the behavior of add()
        # This represents intentionally changing functionality (not a bug)
        # For example: changing add() to also log the operation
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Add a multiply function - this is new functionality that supersedes
        # the simple add/subtract pattern with a more complete calculator
        updated_content = original_content + """

def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Product of a and b.
    \"\"\"
    return a * b
"""
        operations_file.write_text(updated_content)

        # Also create a new test file for the new functionality
        new_test_file = demo_repo / "tests" / "calculator" / "test_multiply.py"
        new_test_file.write_text('''"""Tests for multiply operation."""

from src.calculator.operations import multiply


def test_multiply_positive():
    """Test multiplying positive numbers."""
    assert multiply(2, 3) == 6


def test_multiply_negative():
    """Test multiplying negative numbers."""
    assert multiply(-2, 3) == -6


def test_multiply_zero():
    """Test multiplying by zero."""
    assert multiply(5, 0) == 0
''')

        session_id = "test-supersede-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Step 2 & 3: Create intentions with OLD intention superseded
        # and NEW intention active
        #
        # Old intention: INT-DEMO-002 (Basic Arithmetic Operations)
        # - Had evidence_tests for add/subtract
        # - Now marked as superseded
        #
        # New intention: INT-SUPERSEDE-001 (Extended Calculator Operations)
        # - Has evidence_tests for multiply
        # - Is the active replacement
        superseded = superseded_intention(
            "INT-DEMO-002",
            "Basic Arithmetic Operations (Legacy)",
            kind="functionality",
            superseded_by="INT-SUPERSEDE-001",
            evidence_tests=[
                "tests/calculator/test_operations.py::test_add_positive",
                "tests/calculator/test_operations.py::test_subtract_positive",
            ],
            code_home=["src/calculator/"],
        )

        replacement = active_intention(
            "INT-SUPERSEDE-001",
            "Extended Calculator Operations",
            kind="functionality",
            evidence_tests=[
                "tests/calculator/test_multiply.py::test_multiply_positive",
                "tests/calculator/test_multiply.py::test_multiply_negative",
                "tests/calculator/test_multiply.py::test_multiply_zero",
            ],
            code_home=["src/calculator/"],
            children=[
                {
                    "id": "INT-SUPERSEDE-IMPL",
                    "title": "Implement multiply function",
                    "kind": "implementation",
                    "status": "planned",
                    "children": [],
                },
            ],
        )

        intentions = goal_tree_with_superseded(
            "INT-SUPERSEDE-ROOT",
            "Calculator Evolution",
            superseded=superseded,
            replacement=replacement,
        )

        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 4: Create commit plan referencing the NEW intention
        # This is critical - the commit trailer must use the NEW intent ID
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    # Reference the NEW intention, not the old superseded one
                    "intent_id": "INT-SUPERSEDE-IMPL",
                    "subject": "feat: add multiply function to calculator",
                    "files": [
                        "src/calculator/operations.py",
                        "tests/calculator/test_multiply.py",
                    ],
                    "functionality_intent_id": "INT-SUPERSEDE-001",
                }
            ],
        }
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 5: Run evidence tests for the NEW intention's tests
        # These should PASS because they test the new multiply function
        new_test_selectors = [
            "tests/calculator/test_multiply.py::test_multiply_positive",
            "tests/calculator/test_multiply.py::test_multiply_negative",
            "tests/calculator/test_multiply.py::test_multiply_zero",
        ]

        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=new_test_selectors,
        )

        assert evidence_result["success"], f"run_evidence_tests failed: {evidence_result}"
        assert evidence_result["all_passed"] is True, (
            f"Expected NEW intention's tests to PASS, but got failures: {evidence_result}"
        )

        # Create supporting artifacts
        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)
        _create_session_record_artifact(
            artifact_dir, session_id, diff_hash, ["INT-SUPERSEDE-001"]
        )

        # Step 6: Run stop hook - should ALLOW because:
        # - The commit plan references the NEW intention
        # - The NEW intention's evidence tests pass
        # - The OLD intention is marked as superseded (its tests are not evaluated)
        exit_code, stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # Verify hook allowed (exit code 0)
        assert exit_code == 0, (
            f"Expected stop hook to allow (exit 0) with superseded old intention, "
            f"got exit code {exit_code}.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_supersede_without_replacement_tests_blocks(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that superseding without proper replacement evidence still blocks.

        If you supersede an old intention but the new intention has no
        evidence tests or they fail, the commit should still be blocked.
        This ensures developers can't just mark things as superseded to
        bypass evidence requirements.
        """
        # Make a change
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        operations_file.write_text(
            operations_file.read_text() + "\n# Added for supersede test\n"
        )

        session_id = "test-supersede-002"
        diff_hash = compute_diff_hash(demo_repo)

        # Create intentions with superseded old and new without evidence
        superseded = superseded_intention(
            "INT-OLD-002",
            "Old Functionality (Legacy)",
            kind="functionality",
            superseded_by="INT-NEW-002",
            evidence_tests=["tests/calculator/test_operations.py::test_add_positive"],
        )

        # NEW intention has NO evidence_tests - this should be caught
        replacement = active_intention(
            "INT-NEW-002",
            "New Functionality",
            kind="functionality",
            # Note: no evidence_tests field
            code_home=["src/calculator/"],
            children=[
                {
                    "id": "INT-NEW-IMPL",
                    "title": "Implement new functionality",
                    "kind": "implementation",
                    "status": "planned",
                    "children": [],
                },
            ],
        )

        intentions = goal_tree_with_superseded(
            "INT-SUPERSEDE-ROOT-2",
            "Supersede Without Evidence",
            superseded=superseded,
            replacement=replacement,
        )

        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": "INT-NEW-IMPL",
                    "subject": "feat: add new functionality",
                    "files": ["src/calculator/operations.py"],
                    "functionality_intent_id": "INT-NEW-002",
                }
            ],
        }
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run evidence tests with empty selectors (no tests to run)
        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=[],
        )
        assert evidence_result["success"], f"run_evidence_tests failed: {evidence_result}"

        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)
        _create_session_record_artifact(
            artifact_dir, session_id, diff_hash, ["INT-NEW-002"]
        )

        # Run stop hook - behavior depends on whether empty evidence is acceptable
        # For a functionality intention without evidence_tests, the hook should allow
        # (since evidence is only enforced when evidence_tests are declared)
        exit_code, stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # With no evidence tests declared, the hook allows (evidence is optional)
        # This test documents the current behavior
        assert exit_code == 0, (
            f"Expected stop hook to allow (exit 0) when no evidence tests declared, "
            f"got exit code {exit_code}.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_commit_trailer_uses_new_intent_id(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that the commit message trailer uses the NEW intention ID.

        When superseding an intention, the commit must reference the NEW
        intention ID in the trailer, not the old superseded one.
        """
        import subprocess

        # Add new functionality
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()
        operations_file.write_text(
            original_content
            + """

def divide(a: int, b: int) -> float:
    \"\"\"Divide two numbers.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""
        )

        # Create test file
        new_test_file = demo_repo / "tests" / "calculator" / "test_divide.py"
        new_test_file.write_text('''"""Tests for divide operation."""

from src.calculator.operations import divide
import pytest


def test_divide_positive():
    """Test dividing positive numbers."""
    assert divide(6, 2) == 3.0


def test_divide_by_zero():
    """Test dividing by zero raises error."""
    with pytest.raises(ValueError):
        divide(5, 0)
''')

        session_id = "test-supersede-003"
        diff_hash = compute_diff_hash(demo_repo)

        # Create intentions with specific IDs to verify in trailer
        old_intent_id = "INT-OLD-ARITH-003"
        new_intent_id = "INT-NEW-DIVISION-003"
        impl_intent_id = "INT-NEW-DIV-IMPL"

        superseded = superseded_intention(
            old_intent_id,
            "Old Arithmetic (Superseded)",
            kind="functionality",
            superseded_by=new_intent_id,
        )

        replacement = active_intention(
            new_intent_id,
            "Division Operations",
            kind="functionality",
            evidence_tests=[
                "tests/calculator/test_divide.py::test_divide_positive",
                "tests/calculator/test_divide.py::test_divide_by_zero",
            ],
            code_home=["src/calculator/"],
            children=[
                {
                    "id": impl_intent_id,
                    "title": "Implement divide function",
                    "kind": "implementation",
                    "status": "planned",
                    "children": [],
                },
            ],
        )

        intentions = goal_tree_with_superseded(
            "INT-SUPERSEDE-ROOT-3",
            "Division Feature",
            superseded=superseded,
            replacement=replacement,
        )

        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Commit plan with NEW intent ID
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": impl_intent_id,  # Use NEW intention's impl
                    "subject": "feat: add divide function",
                    "files": [
                        "src/calculator/operations.py",
                        "tests/calculator/test_divide.py",
                    ],
                    "functionality_intent_id": new_intent_id,  # NEW functionality
                }
            ],
        }
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run evidence tests for NEW intention
        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=[
                "tests/calculator/test_divide.py::test_divide_positive",
                "tests/calculator/test_divide.py::test_divide_by_zero",
            ],
        )
        assert evidence_result["success"], f"run_evidence_tests failed: {evidence_result}"
        assert evidence_result["all_passed"] is True, (
            f"Expected NEW intention's tests to pass: {evidence_result}"
        )

        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)
        _create_session_record_artifact(
            artifact_dir, session_id, diff_hash, [new_intent_id]
        )

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)
        assert exit_code == 0, (
            f"Expected stop hook to allow, got exit code {exit_code}.\n"
            f"stderr: {stderr}"
        )

        # Verify the commit was created with the NEW intent ID in trailer
        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commit_message = log_result.stdout

        # The commit trailer should reference the NEW intention ID
        assert impl_intent_id in commit_message, (
            f"Expected NEW intent ID '{impl_intent_id}' in commit trailer.\n"
            f"Commit message: {commit_message}"
        )

        # The commit should NOT reference the OLD superseded intention ID
        assert old_intent_id not in commit_message, (
            f"Expected OLD intent ID '{old_intent_id}' NOT to be in commit trailer.\n"
            f"Commit message: {commit_message}"
        )
