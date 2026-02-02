"""
T048: E2E test for evidence regression scenario.

This test validates the stop hook behavior when evidence tests fail:
1. Make a code change that BREAKS existing tests
2. Create intentions and commit_plan artifacts
3. Run evidence tests (they fail because code is broken)
4. Create evidence_results artifact with failures
5. Run stop hook
6. Verify hook blocks with failure context message

The key scenario is: a developer makes a change that regresses functionality,
and the evidence tests catch this regression before the commit is allowed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_servers.intention_audit.tools.run_evidence_tests import run_evidence_tests
from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from src.intention_audit.models.structure_validation import StructureValidation
from tests.e2e.conftest import compute_diff_hash, run_stop_hook
from tests.e2e.fixtures import (
    intention_tree,
    minimal_commit_plan,
    minimal_intention,
)


def _create_session_record_artifact(
    artifact_dir: Path,
    session_id: str,
    diff_hash: str,
) -> None:
    """Create a minimal session record artifact for test purposes."""
    record = {
        "session_id": session_id,
        "timestamp": "2026-01-30T12:00:00+00:00",
        "transcript_ref": f"transcripts/{session_id}.jsonl",
        "diff_base": "HEAD",
        "diff_hash": diff_hash,
        "planner_tool": "test-runner",
        "intentions_touched": ["INT-REGRESSION-001"],
        "mapping_summary": {"total_files": 1, "commits_planned": 1},
        "notes": "Test session record for evidence regression test",
    }
    record_path = artifact_dir / "session_record.json"
    record_path.write_text(json.dumps(record, indent=2))


def _create_structure_validation_artifact(
    artifact_dir: Path,
) -> None:
    """Create a passing structure validation artifact for test purposes."""
    validation = StructureValidation(
        violations=[],
        passed=True,
    )
    validation.save(artifact_dir / "structure_validation.json")


@pytest.mark.e2e
class TestEvidenceRegressionScenario:
    """
    Test the evidence regression blocking scenario.

    This tests the critical workflow where:
    - Code changes break existing tests
    - Evidence tests catch the regression
    - Stop hook blocks the commit with failure context
    """

    def test_evidence_failure_blocks_commits(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that failing evidence tests block commits.

        Flow:
        1. Make a change that BREAKS tests (modify add() to return wrong value)
        2. Create intentions and commit_plan artifacts
        3. Run evidence tests (they fail)
        4. Create evidence_results artifact with failures
        5. Run stop hook
        6. Verify hook blocks with failure context message
        7. Verify the blocking message includes intention ID, failed tests, etc.
        """
        # Step 1: Make a breaking change to the calculator
        # Change add() to return a - b instead of a + b (this will break tests)
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Introduce a bug: add() now subtracts instead of adds
        broken_content = original_content.replace(
            "return a + b", "return a - b  # BUG: wrong operation"
        )
        operations_file.write_text(broken_content)

        # Verify the change was made
        assert operations_file.read_text() != original_content

        session_id = "test-evidence-regression-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Step 2: Create intentions artifact
        # The intention is to "modify" the add function (ostensibly a bug fix or feature change)
        intentions = intention_tree(
            "INT-REGRESSION-001",
            "Modify calculator operations",
            children=[
                minimal_intention(
                    "INT-REGRESSION-IMPL", "Modify add function", kind="implementation"
                )
            ],
        )
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 3: Create commit plan covering the changed file
        plan = minimal_commit_plan(
            intent_id="INT-REGRESSION-IMPL",
            files=["src/calculator/operations.py"],
            subject="fix: modify add function",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 4: Run evidence tests - they should FAIL because we broke the code
        # The demo_repo has tests that verify add() behavior
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",
            "tests/calculator/test_operations.py::test_add_negative",
            "tests/calculator/test_operations.py::test_add_zero",
        ]

        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=test_selectors,
        )

        # Verify evidence tests failed as expected
        assert evidence_result["success"], (
            f"run_evidence_tests should succeed (even with failures): {evidence_result}"
        )
        assert evidence_result["all_passed"] is False, (
            f"Expected tests to FAIL due to regression bug, but all_passed={evidence_result['all_passed']}"
        )

        # Step 5: Create structure validation artifact (passing, to isolate evidence failure)
        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)

        # Step 6: Create session record artifact (required by stop hook)
        _create_session_record_artifact(artifact_dir, session_id, diff_hash)

        # Step 7: Run stop hook - should BLOCK due to evidence test failures
        exit_code, stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # Verify hook blocked (exit code 2)
        assert exit_code == 2, (
            f"Expected stop hook to block (exit 2) due to evidence failures, "
            f"got exit code {exit_code}.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

        # Step 8: Verify the blocking message contains failure context
        stderr_lower = stderr.lower()

        # Should mention evidence tests failed
        assert "evidence tests failed" in stderr_lower, (
            f"Expected 'evidence tests failed' in stderr, got: {stderr}"
        )

        # Should include action required instructions
        assert "action required" in stderr_lower, (
            f"Expected 'action required' instructions in stderr, got: {stderr}"
        )

        # Should mention options to fix
        assert "options" in stderr_lower or "fix" in stderr_lower, (
            f"Expected fix options in stderr, got: {stderr}"
        )

        # Verify the failure context mentions the specific failed tests
        # At least one of the add tests should be mentioned
        assert "test_add" in stderr.lower() or "test_add_positive" in stderr, (
            f"Expected mention of failed add tests in stderr, got: {stderr}"
        )

    def test_evidence_success_allows_commits(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that passing evidence tests allow commits to proceed.

        This is the counterpoint to the failure test - when evidence tests pass,
        the stop hook should allow the commit.
        """
        # Make a harmless change that doesn't break tests
        # Add a docstring to the module
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Add a comment at the end (doesn't break anything)
        updated_content = original_content + "\n# Additional module documentation\n"
        operations_file.write_text(updated_content)

        session_id = "test-evidence-success-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Create intentions artifact
        intentions = intention_tree(
            "INT-DOCS-001",
            "Document calculator module",
            children=[
                minimal_intention(
                    "INT-DOCS-IMPL", "Add module documentation", kind="implementation"
                )
            ],
        )
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan
        plan = minimal_commit_plan(
            intent_id="INT-DOCS-IMPL",
            files=["src/calculator/operations.py"],
            subject="docs: add module documentation",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run evidence tests - they should PASS because we didn't break anything
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",
            "tests/calculator/test_operations.py::test_add_negative",
            "tests/calculator/test_operations.py::test_add_zero",
            "tests/calculator/test_operations.py::test_subtract_positive",
            "tests/calculator/test_operations.py::test_subtract_negative",
        ]

        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=test_selectors,
        )

        # Verify evidence tests passed
        assert evidence_result["success"], f"run_evidence_tests failed: {evidence_result}"
        assert evidence_result["all_passed"] is True, (
            f"Expected tests to PASS, but got failures: {evidence_result}"
        )

        # Create other required artifacts
        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)
        _create_session_record_artifact(artifact_dir, session_id, diff_hash)

        # Run stop hook - should ALLOW (exit 0) since all evidence passed
        exit_code, stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # Verify hook allowed (exit code 0)
        assert exit_code == 0, (
            f"Expected stop hook to allow (exit 0) since evidence passed, "
            f"got exit code {exit_code}.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_partial_evidence_failure_blocks_commits(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that even partial evidence test failures block commits.

        If some tests pass but others fail, the commit should still be blocked.
        """
        # Break only the add function, subtract tests should still pass
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Introduce a bug: add() returns 0 instead of a + b
        broken_content = original_content.replace(
            "return a + b", "return 0  # BUG: always returns zero"
        )
        operations_file.write_text(broken_content)

        session_id = "test-partial-failure-001"
        diff_hash = compute_diff_hash(demo_repo)

        # Create artifacts
        intentions = intention_tree(
            "INT-PARTIAL-001",
            "Modify calculator",
            children=[
                minimal_intention("INT-PARTIAL-IMPL", "Modify operations", kind="implementation")
            ],
        )
        result = save_intentions(session_id, diff_hash, str(demo_repo), intentions)
        assert result["success"]

        plan = minimal_commit_plan(
            intent_id="INT-PARTIAL-IMPL",
            files=["src/calculator/operations.py"],
            subject="fix: modify operations",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash, str(demo_repo), plan)
        assert result["success"]

        # Run both add and subtract tests
        # add tests should fail, subtract tests should pass
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",  # Will fail
            "tests/calculator/test_operations.py::test_subtract_positive",  # Will pass
        ]

        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash,
            test_selectors=test_selectors,
        )

        # Should report not all passed (mixed results)
        assert evidence_result["success"]
        assert evidence_result["all_passed"] is False, "Expected mixed results (some failures)"

        # Create other artifacts
        artifact_dir = demo_repo / ".intent_audit" / session_id / diff_hash
        _create_structure_validation_artifact(artifact_dir)
        _create_session_record_artifact(artifact_dir, session_id, diff_hash)

        # Stop hook should block due to the partial failure
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        assert exit_code == 2, (
            f"Expected stop hook to block (exit 2) due to partial evidence failure, "
            f"got exit code {exit_code}.\nstderr: {stderr}"
        )
        assert "evidence tests failed" in stderr.lower()
