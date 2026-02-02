"""
T049: E2E test for evidence repair path scenario.

This test validates the stop hook behavior when evidence tests fail and the developer
repairs the code to make them pass:

1. Make a code change that BREAKS existing tests
2. Create artifacts with failing evidence
3. Verify stop hook blocks
4. FIX the code to restore evidence tests
5. Recompute diff_hash (it changed because code changed)
6. Create NEW artifacts with passing evidence for new diff_hash
7. Run stop hook again
8. Verify commits are created successfully

The key insight: when code is fixed, the diff_hash changes. A new set of artifacts
must be created for the new diff_hash.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mcp_servers.intention_audit.tools.run_evidence_tests import run_evidence_tests
from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from mcp_servers.intention_audit.tools.save_session_record import save_session_record
from mcp_servers.intention_audit.tools.save_structure_validation import (
    save_structure_validation,
)
from tests.e2e.conftest import compute_diff_hash, run_stop_hook
from tests.e2e.fixtures import (
    intention_tree,
    minimal_commit_plan,
    minimal_intention,
)


def _create_session_record_artifact(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
    intent_id: str = "INT-REPAIR-IMPL",
) -> dict:
    """
    Create a session record artifact using the MCP tool.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes.
        repo_path: Path to the repository.
        intent_id: Intent ID being worked on.

    Returns:
        Result dict from save_session_record.
    """
    record = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "transcript_ref": f"~/.claude/transcripts/{session_id}.jsonl",
        "diff_base": "HEAD",
        "diff_hash": diff_hash,
        "planner_tool": "commit-planner",
        "intentions_touched": [intent_id],
        "mapping_summary": {
            "total_files": 1,
            "mapped_files": 1,
            "unmapped_files": 0,
        },
        "notes": "E2E test: evidence repair scenario",
    }
    return save_session_record(session_id, str(repo_path), diff_hash, record)


def _create_structure_validation_passed(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
) -> dict:
    """
    Create a passing structure validation artifact.

    Args:
        session_id: Unique session identifier.
        diff_hash: Hash of the current uncommitted changes.
        repo_path: Path to the repository.

    Returns:
        Result dict from save_structure_validation.
    """
    validation = {
        "violations": [],
        "passed": True,
        "override_rationale": None,
    }
    return save_structure_validation(session_id, diff_hash, str(repo_path), validation)


def _create_config_with_structure_disabled(repo_path: Path) -> None:
    """
    Create config file that disables structure validation but keeps evidence checking.

    This allows tests to focus on evidence validation workflow.

    Args:
        repo_path: Path to the repository.
    """
    config = {
        "evidence_checking": True,
        "structure_validation": False,
        "docs_validation": "disabled",
    }
    config_dir = repo_path / ".intent_audit"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2))


@pytest.mark.e2e
class TestEvidenceRepairScenario:
    """
    Test the evidence repair workflow: failing tests -> fix code -> new artifacts -> commit.

    This tests the critical developer experience where:
    - Code changes break existing tests
    - Evidence tests catch the regression
    - Stop hook blocks the commit
    - Developer fixes the code
    - New artifacts are created for the new diff_hash
    - Stop hook allows the commit
    """

    def test_evidence_repair_allows_commits(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Full repair flow: break code -> fail -> fix code -> new artifacts -> success.

        This is the "repair" path that follows the regression scenario:

        Phase 1 - Regression (blocked):
        1. Make a change that BREAKS tests (modify add() to return wrong value)
        2. Create artifacts with failing evidence
        3. Verify stop hook blocks

        Phase 2 - Repair (allowed):
        4. FIX the code (restore correct implementation but keep original intent)
        5. Recompute diff_hash (it changed because code changed)
        6. Create NEW artifacts with passing evidence for new diff_hash
        7. Run stop hook again
        8. Verify commits are created successfully

        Key insight: When code is fixed, the diff_hash changes. A new set of
        artifacts must be created for the new diff_hash - you cannot reuse
        the old artifacts.
        """
        # Create config to focus on evidence checking
        _create_config_with_structure_disabled(demo_repo)

        # ============================================
        # PHASE 1: REGRESSION - Make breaking change
        # ============================================

        # Step 1: Make a breaking change to the calculator
        # Change add() to return a - b instead of a + b (this will break tests)
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        # Introduce a bug: add() now subtracts instead of adds
        broken_content = original_content.replace(
            "return a + b", "return a - b  # BUG: wrong operation"
        )
        operations_file.write_text(broken_content)

        session_id = "test-evidence-repair-001"
        diff_hash_broken = compute_diff_hash(demo_repo)

        # Step 2: Create intentions artifact
        intentions = intention_tree(
            "INT-REPAIR-001",
            "Modify calculator operations",
            children=[
                minimal_intention("INT-REPAIR-IMPL", "Modify add function", kind="implementation")
            ],
        )
        result = save_intentions(session_id, diff_hash_broken, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan
        plan = minimal_commit_plan(
            intent_id="INT-REPAIR-IMPL",
            files=["src/calculator/operations.py"],
            subject="fix: modify add function",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash_broken, str(demo_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 3: Run evidence tests - they should FAIL
        test_selectors = [
            "tests/calculator/test_operations.py::test_add_positive",
            "tests/calculator/test_operations.py::test_add_negative",
            "tests/calculator/test_operations.py::test_add_zero",
        ]

        evidence_result = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash_broken,
            test_selectors=test_selectors,
        )

        # Verify evidence tests failed
        assert evidence_result["success"], f"run_evidence_tests error: {evidence_result}"
        assert evidence_result["all_passed"] is False, (
            f"Expected tests to FAIL due to regression, but all_passed={evidence_result['all_passed']}"
        )

        # Create supporting artifacts
        result = _create_structure_validation_passed(session_id, diff_hash_broken, demo_repo)
        assert result["success"], f"save_structure_validation failed: {result}"

        result = _create_session_record_artifact(session_id, diff_hash_broken, demo_repo)
        assert result["success"], f"save_session_record failed: {result}"

        # Step 4: Run stop hook - should BLOCK due to evidence failures
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        assert exit_code == 2, (
            f"Expected stop hook to block (exit 2) due to evidence failures, "
            f"got exit code {exit_code}.\nstderr: {stderr}"
        )
        assert "evidence tests failed" in stderr.lower(), (
            f"Expected 'evidence tests failed' in stderr, got: {stderr}"
        )

        # ============================================
        # PHASE 2: REPAIR - Fix the code
        # ============================================

        # Step 5: FIX the code - restore correct behavior but with a twist
        # Add functionality that keeps original intent visible
        fixed_content = original_content.replace(
            "return a + b", "return a + b  # Fixed: correct addition with logging potential"
        )
        operations_file.write_text(fixed_content)

        # Step 6: Recompute diff_hash - IT CHANGED because the code changed
        diff_hash_fixed = compute_diff_hash(demo_repo)

        # CRITICAL: The diff_hash must be different after fixing
        assert diff_hash_fixed != diff_hash_broken, (
            "After fixing code, diff_hash should change. "
            f"broken={diff_hash_broken}, fixed={diff_hash_fixed}"
        )

        # Step 7: Create NEW artifacts for the new diff_hash
        # We use the same session_id but new diff_hash - this creates a new artifact set

        # New intentions (same structure, new diff_hash key)
        result = save_intentions(session_id, diff_hash_fixed, str(demo_repo), intentions)
        assert result["success"], f"save_intentions failed for fixed code: {result}"

        # New commit plan (same content, new diff_hash key)
        plan_fixed = minimal_commit_plan(
            intent_id="INT-REPAIR-IMPL",
            files=["src/calculator/operations.py"],
            subject="fix: modify add function with improved documentation",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash_fixed, str(demo_repo), plan_fixed)
        assert result["success"], f"save_commit_plan failed for fixed code: {result}"

        # Run evidence tests again - they should PASS now
        evidence_result_fixed = run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash_fixed,
            test_selectors=test_selectors,
        )

        assert evidence_result_fixed["success"], (
            f"run_evidence_tests error: {evidence_result_fixed}"
        )
        assert evidence_result_fixed["all_passed"] is True, (
            f"Expected tests to PASS after fix, but got failures: {evidence_result_fixed}"
        )

        # Create new supporting artifacts for the fixed diff_hash
        result = _create_structure_validation_passed(session_id, diff_hash_fixed, demo_repo)
        assert result["success"], f"save_structure_validation failed: {result}"

        result = _create_session_record_artifact(session_id, diff_hash_fixed, demo_repo)
        assert result["success"], f"save_session_record failed: {result}"

        # Step 8: Run stop hook again - should ALLOW now
        exit_code, stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        assert exit_code == 0, (
            f"Expected stop hook to allow (exit 0) after repair, "
            f"got exit code {exit_code}.\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

        # Verify commit was created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-2"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]
        assert len(commits) >= 2, f"Expected at least 2 commits, got: {commits}"

        # Verify Intent-Id trailer is present
        trailer_result = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        intent_id = trailer_result.stdout.strip()
        assert intent_id == "INT-REPAIR-IMPL", (
            f"Expected Intent-Id trailer 'INT-REPAIR-IMPL', got: {intent_id}"
        )

        # Verify no uncommitted changes remain (except .intent_audit/)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(demo_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        uncommitted = [
            line
            for line in status_result.stdout.strip().split("\n")
            if line and ".intent_audit" not in line
        ]
        assert len(uncommitted) == 0, f"Unexpected uncommitted files: {uncommitted}"

    def test_repair_without_new_artifacts_still_blocked(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that fixing code but not creating new artifacts still blocks.

        This validates that the diff_hash keying mechanism works correctly:
        if you fix the code but try to reuse the old artifacts, the stop hook
        will not find matching artifacts for the new diff_hash.

        Steps:
        1. Make a breaking change
        2. Create artifacts with failing evidence for that diff_hash
        3. Fix the code (diff_hash changes)
        4. Run stop hook WITHOUT creating new artifacts
        5. Verify hook blocks (missing artifacts for new diff_hash)
        """
        # Create config to focus on evidence checking
        _create_config_with_structure_disabled(demo_repo)

        # Make a breaking change
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()

        broken_content = original_content.replace(
            "return a + b", "return 0  # BUG: always returns zero"
        )
        operations_file.write_text(broken_content)

        session_id = "test-no-new-artifacts-001"
        diff_hash_broken = compute_diff_hash(demo_repo)

        # Create artifacts for the broken state
        intentions = intention_tree(
            "INT-NOARTIFACT-001",
            "Test artifact keying",
            children=[
                minimal_intention(
                    "INT-NOARTIFACT-IMPL", "Test implementation", kind="implementation"
                )
            ],
        )
        result = save_intentions(session_id, diff_hash_broken, str(demo_repo), intentions)
        assert result["success"]

        plan = minimal_commit_plan(
            intent_id="INT-NOARTIFACT-IMPL",
            files=["src/calculator/operations.py"],
            subject="test: artifact keying test",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash_broken, str(demo_repo), plan)
        assert result["success"]

        # Run evidence tests (they will fail, but that's expected)
        test_selectors = ["tests/calculator/test_operations.py::test_add_positive"]
        run_evidence_tests(
            session_id=session_id,
            cwd=str(demo_repo),
            diff_hash=diff_hash_broken,
            test_selectors=test_selectors,
        )

        # Create supporting artifacts
        _create_structure_validation_passed(session_id, diff_hash_broken, demo_repo)
        _create_session_record_artifact(
            session_id, diff_hash_broken, demo_repo, intent_id="INT-NOARTIFACT-IMPL"
        )

        # Now fix the code
        fixed_content = original_content.replace("return a + b", "return a + b  # Fixed")
        operations_file.write_text(fixed_content)

        # The diff_hash has changed
        diff_hash_fixed = compute_diff_hash(demo_repo)
        assert diff_hash_fixed != diff_hash_broken, "diff_hash should change after fix"

        # Run stop hook WITHOUT creating new artifacts
        # The hook should block because there are no artifacts for diff_hash_fixed
        exit_code, _stdout, stderr = run_stop_hook(demo_repo, session_id, project_root)

        # Should block with missing artifacts message
        assert exit_code == 2, (
            f"Expected stop hook to block (exit 2) due to missing artifacts, "
            f"got exit code {exit_code}.\nstderr: {stderr}"
        )

        # The error should indicate missing intentions artifact for the new diff_hash
        stderr_lower = stderr.lower()
        assert "intentions" in stderr_lower or "artifact" in stderr_lower, (
            f"Expected message about missing intentions artifact, got: {stderr}"
        )

    def test_repair_with_different_session_id_is_independent(
        self,
        demo_repo: Path,
        project_root: Path,
    ) -> None:
        """
        Test that using a different session_id creates independent artifact sets.

        This validates that session_id + diff_hash creates unique artifact paths.

        Steps:
        1. Make a change
        2. Create artifacts with session_id A
        3. Create artifacts with session_id B (same diff_hash)
        4. Both sessions have independent artifact sets
        """
        # Create config
        _create_config_with_structure_disabled(demo_repo)

        # Make a harmless change
        operations_file = demo_repo / "src" / "calculator" / "operations.py"
        original_content = operations_file.read_text()
        operations_file.write_text(original_content + "\n# Session independence test\n")

        diff_hash = compute_diff_hash(demo_repo)

        # Create artifacts for session A
        session_a = "test-session-a-001"
        intentions = intention_tree(
            "INT-SESSA-001",
            "Session A Test",
            children=[
                minimal_intention(
                    "INT-SESSA-IMPL", "Session A implementation", kind="implementation"
                )
            ],
        )
        result = save_intentions(session_a, diff_hash, str(demo_repo), intentions)
        assert result["success"]

        # Create artifacts for session B with different intent IDs
        session_b = "test-session-b-001"
        intentions_b = intention_tree(
            "INT-SESSB-001",
            "Session B Test",
            children=[
                minimal_intention(
                    "INT-SESSB-IMPL", "Session B implementation", kind="implementation"
                )
            ],
        )
        result = save_intentions(session_b, diff_hash, str(demo_repo), intentions_b)
        assert result["success"]

        # Verify both artifact directories exist independently
        artifact_dir_a = demo_repo / ".intent_audit" / session_a / diff_hash
        artifact_dir_b = demo_repo / ".intent_audit" / session_b / diff_hash

        assert artifact_dir_a.exists(), f"Session A artifacts should exist at {artifact_dir_a}"
        assert artifact_dir_b.exists(), f"Session B artifacts should exist at {artifact_dir_b}"

        # Verify they contain different intentions
        intentions_a_yaml = (artifact_dir_a / "intentions.yaml").read_text()
        intentions_b_yaml = (artifact_dir_b / "intentions.yaml").read_text()

        assert "INT-SESSA-001" in intentions_a_yaml
        assert "INT-SESSB-001" in intentions_b_yaml
        assert "INT-SESSA-001" not in intentions_b_yaml
        assert "INT-SESSB-001" not in intentions_a_yaml
