"""
T061: E2E tests for structure override rationale scenario.

Tests that when `structure_override_rationale` is provided in the commit plan,
the stop hook allows commits even when structure validation has violations.

This validates the override mechanism for intentional cross-boundary changes
where developers have explicitly documented why the boundary violation is acceptable.

Test scenario:
1. Repository has intentions.yaml with code_home: ["src/payments/"] for payments functionality
2. Changes are made OUTSIDE this boundary (in src/other_domain/)
3. Structure validation has violations (passed=false)
4. commit_plan.yaml includes `structure_override_rationale` field
5. Stop hook ALLOWS commits despite structure violations
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path for MCP tool imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.intention_audit.tools.run_evidence_tests import run_evidence_tests
from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from mcp_servers.intention_audit.tools.save_session_record import save_session_record
from mcp_servers.intention_audit.tools.save_structure_validation import (
    save_structure_validation,
)
from tests.e2e.conftest import compute_diff_hash, run_stop_hook
from tests.e2e.fixtures import minimal_intention


def intention_with_code_home(
    intent_id: str,
    title: str,
    code_home: list[str],
    children: list[dict] | None = None,
) -> dict:
    """
    Create a functionality intention with code_home defined.

    Args:
        intent_id: Unique identifier.
        title: Human-readable title.
        code_home: List of directory prefixes where implementation should reside.
        children: List of child intentions.

    Returns:
        Dictionary conforming to intentions schema.
    """
    return {
        "id": intent_id,
        "title": title,
        "kind": "functionality",
        "status": "planned",
        "code_home": code_home,
        "children": children or [],
    }


def goal_intention_tree(
    root_id: str,
    root_title: str,
    children: list[dict] | None = None,
) -> dict:
    """
    Create a goal intention tree with optional children.

    Args:
        root_id: Root intention identifier.
        root_title: Root intention title.
        children: List of child intentions.

    Returns:
        Dictionary with root goal intention containing children.
    """
    return {
        "id": root_id,
        "title": root_title,
        "kind": "goal",
        "status": "planned",
        "children": children or [],
    }


def structure_violation(
    violation_type: str,
    intent_id: str,
    violating_paths: list[str],
    expected_prefixes: list[str],
    functionality_intent_id: str | None = None,
    suggested_fix: str = "",
) -> dict:
    """
    Create a structure violation entry.

    Args:
        violation_type: Type of violation (e.g., "code_home_boundary").
        intent_id: Intent ID that has the violation.
        violating_paths: List of file paths that violate the boundary.
        expected_prefixes: List of expected directory prefixes.
        functionality_intent_id: Optional parent functionality intent ID.
        suggested_fix: Optional suggested fix text.

    Returns:
        Dictionary conforming to structure_validation violation schema.
    """
    return {
        "type": violation_type,
        "intent_id": intent_id,
        "functionality_intent_id": functionality_intent_id,
        "violating_paths": violating_paths,
        "expected_prefixes": expected_prefixes,
        "details": {},
        "suggested_fix": suggested_fix,
    }


def minimal_session_record(session_id: str, diff_hash: str) -> dict:
    """
    Create a minimal valid session record.

    Args:
        session_id: Session identifier.
        diff_hash: Diff hash for the session.

    Returns:
        Dictionary conforming to session_record schema.
    """
    return {
        "session_id": session_id,
        "timestamp": "2026-02-01T12:00:00Z",
        "transcript_ref": f"transcripts/{session_id}.jsonl",
        "diff_base": "HEAD",
        "diff_hash": diff_hash,
        "planner_tool": "claude-code",
        "intentions_touched": ["INT-OVERRIDE-TEST"],
        "mapping_summary": {
            "total_files": 1,
            "mapped_files": 1,
            "unmapped_files": 0,
        },
        "notes": "Test session for structure override rationale",
    }


@pytest.mark.e2e
class TestStructureOverrideScenario:
    """Test structure override rationale allows commits despite violations."""

    def test_override_rationale_allows_commits(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When structure violations exist but override rationale is provided in commit_plan,
        hook should allow commits despite structure validation failures.

        Flow:
        1. Make a change OUTSIDE the declared code_home (src/other_domain/)
           but assign it to payments functionality
        2. Create intentions with code_home for payments (src/payments/)
        3. Create commit_plan with `structure_override_rationale` field
        4. Create structure_validation with violations (passed=false)
        5. Run stop hook
        6. Verify hook ALLOWS commits (exit code 0)
        7. Verify commit was created with proper trailers
        """
        # Step 1: Create a file change OUTSIDE the payments code_home boundary
        # The payments functionality has code_home: ["src/payments/"]
        # But we're creating a file in src/other_domain/
        violation_file = (
            structure_repo / "src" / "other_domain" / "cross_boundary_util.py"
        )
        violation_file.write_text(
            "# Cross-boundary utility - intentionally placed here\n"
            "# This module serves both payments and other_domain\n"
            "def shared_payment_utility():\n"
            "    '''Utility used by multiple domains.'''\n"
            "    return 'cross-domain shared logic'\n"
        )

        session_id = "test-override-001"
        diff_hash = compute_diff_hash(structure_repo)

        # Step 2: Create intentions artifact with code_home boundary
        intentions = goal_intention_tree(
            "INT-OVERRIDE-ROOT",
            "Test Structure Override Rationale",
            children=[
                intention_with_code_home(
                    "INT-OVERRIDE-PAYMENTS",
                    "Payment Processing",
                    code_home=["src/payments/"],
                    children=[
                        minimal_intention(
                            "INT-OVERRIDE-IMPL",
                            "Implement shared payment utility",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 3: Create commit plan WITH structure_override_rationale
        # This is the key feature being tested - the override should allow commits
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": "INT-OVERRIDE-IMPL",
                    "subject": "feat: add shared payment utility",
                    "files": ["src/other_domain/cross_boundary_util.py"],
                    "functionality_intent_id": "INT-OVERRIDE-PAYMENTS",
                }
            ],
            "structure_override_rationale": (
                "Cross-boundary placement is intentional: "
                "this utility module serves both payments and other_domain. "
                "The file will be moved to src/shared/ in a follow-up refactoring PR. "
                "This temporary placement avoids code duplication."
            ),
        }
        result = save_commit_plan(session_id, diff_hash, str(structure_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 4: Create evidence results (passing - evidence is independent)
        result = run_evidence_tests(
            session_id,
            str(structure_repo),
            diff_hash,
            ["tests/payments/test_processor.py::test_process_payment"],
        )
        assert result["success"], f"run_evidence_tests failed: {result}"

        # Step 5: Create structure validation with violations (passed=false)
        # This simulates what the structure-validator sub-agent would produce
        validation = {
            "violations": [
                structure_violation(
                    violation_type="code_home_boundary",
                    intent_id="INT-OVERRIDE-IMPL",
                    violating_paths=["src/other_domain/cross_boundary_util.py"],
                    expected_prefixes=["src/payments/"],
                    functionality_intent_id="INT-OVERRIDE-PAYMENTS",
                    suggested_fix="Move file to src/payments/cross_boundary_util.py",
                ),
            ],
            "passed": False,
            "override_rationale": None,  # Hook reads override from commit_plan
        }
        result = save_structure_validation(
            session_id, diff_hash, str(structure_repo), validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        # Step 6: Create session record (required by hook)
        record = minimal_session_record(session_id, diff_hash)
        result = save_session_record(
            session_id, str(structure_repo), diff_hash, record
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Step 7: Run stop hook - should succeed due to override rationale
        exit_code, _stdout, stderr = run_stop_hook(
            structure_repo, session_id, project_root
        )

        # Step 8: Verify hook ALLOWS commits (exit code 0)
        assert exit_code == 0, (
            f"Expected exit code 0 (allowed with override), got {exit_code}.\n"
            f"stderr: {stderr}"
        )

        # Step 9: Verify commit was created with proper trailers
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-1", "--format=%s%n%b"],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )

        # Check commit subject contains expected text
        assert "shared payment utility" in log_result.stdout.lower(), (
            f"Expected commit subject to contain 'shared payment utility'.\n"
            f"Git log: {log_result.stdout}"
        )

        # Check Intent-Id trailer is present
        log_with_trailers = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers)"],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "INT-OVERRIDE" in log_with_trailers.stdout, (
            f"Expected Intent-Id trailer with INT-OVERRIDE.\n"
            f"Trailers: {log_with_trailers.stdout}"
        )

    def test_override_rationale_missing_still_blocks(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When structure violations exist and NO override rationale is provided,
        hook should still block commits.

        This is the control case to ensure override mechanism only works when
        rationale is explicitly provided.
        """
        # Create a file change outside code_home
        violation_file = (
            structure_repo / "src" / "other_domain" / "no_override_util.py"
        )
        violation_file.write_text(
            "# File without override rationale\n"
            "def utility_without_justification():\n"
            "    return 'should be blocked'\n"
        )

        session_id = "test-override-002"
        diff_hash = compute_diff_hash(structure_repo)

        # Create intentions
        intentions = goal_intention_tree(
            "INT-NO-OVERRIDE-ROOT",
            "Test No Override",
            children=[
                intention_with_code_home(
                    "INT-NO-OVERRIDE-FUNC",
                    "Payment Processing",
                    code_home=["src/payments/"],
                    children=[
                        minimal_intention(
                            "INT-NO-OVERRIDE-IMPL",
                            "Implement utility",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan WITHOUT structure_override_rationale
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": "INT-NO-OVERRIDE-IMPL",
                    "subject": "feat: add utility without justification",
                    "files": ["src/other_domain/no_override_util.py"],
                    "functionality_intent_id": "INT-NO-OVERRIDE-FUNC",
                }
            ],
            # NO structure_override_rationale field!
        }
        result = save_commit_plan(session_id, diff_hash, str(structure_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Create evidence results
        result = run_evidence_tests(
            session_id,
            str(structure_repo),
            diff_hash,
            ["tests/payments/test_processor.py::test_process_payment"],
        )
        assert result["success"], f"run_evidence_tests failed: {result}"

        # Create structure validation with violations (passed=false)
        validation = {
            "violations": [
                structure_violation(
                    violation_type="code_home_boundary",
                    intent_id="INT-NO-OVERRIDE-IMPL",
                    violating_paths=["src/other_domain/no_override_util.py"],
                    expected_prefixes=["src/payments/"],
                    functionality_intent_id="INT-NO-OVERRIDE-FUNC",
                    suggested_fix="Move file to src/payments/no_override_util.py",
                ),
            ],
            "passed": False,
            "override_rationale": None,
        }
        result = save_structure_validation(
            session_id, diff_hash, str(structure_repo), validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        # Create session record
        record = minimal_session_record(session_id, diff_hash)
        record["session_id"] = session_id
        result = save_session_record(
            session_id, str(structure_repo), diff_hash, record
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Run stop hook - should BLOCK without override
        exit_code, _stdout, stderr = run_stop_hook(
            structure_repo, session_id, project_root
        )

        # Verify hook blocks with exit code 2
        assert exit_code == 2, (
            f"Expected exit code 2 (blocked), got {exit_code}.\n"
            f"stderr: {stderr}"
        )

        # Verify structure violation message
        assert "structure validation failed" in stderr.lower(), (
            f"Expected 'structure validation failed' in stderr.\n"
            f"stderr: {stderr}"
        )

    def test_override_rationale_empty_string_still_blocks(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When structure_override_rationale is present but empty string,
        hook should still block commits.

        Empty rationale should not bypass the structure check.
        """
        # Create a file change outside code_home
        violation_file = (
            structure_repo / "src" / "other_domain" / "empty_override_util.py"
        )
        violation_file.write_text(
            "# File with empty override rationale\n"
            "def utility_with_empty_rationale():\n"
            "    return 'should be blocked'\n"
        )

        session_id = "test-override-003"
        diff_hash = compute_diff_hash(structure_repo)

        # Create intentions
        intentions = goal_intention_tree(
            "INT-EMPTY-OVERRIDE-ROOT",
            "Test Empty Override",
            children=[
                intention_with_code_home(
                    "INT-EMPTY-OVERRIDE-FUNC",
                    "Payment Processing",
                    code_home=["src/payments/"],
                    children=[
                        minimal_intention(
                            "INT-EMPTY-OVERRIDE-IMPL",
                            "Implement utility",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan with EMPTY structure_override_rationale
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": "INT-EMPTY-OVERRIDE-IMPL",
                    "subject": "feat: add utility with empty rationale",
                    "files": ["src/other_domain/empty_override_util.py"],
                    "functionality_intent_id": "INT-EMPTY-OVERRIDE-FUNC",
                }
            ],
            "structure_override_rationale": "",  # Empty string!
        }
        result = save_commit_plan(session_id, diff_hash, str(structure_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Create evidence results
        result = run_evidence_tests(
            session_id,
            str(structure_repo),
            diff_hash,
            ["tests/payments/test_processor.py::test_process_payment"],
        )
        assert result["success"], f"run_evidence_tests failed: {result}"

        # Create structure validation with violations
        validation = {
            "violations": [
                structure_violation(
                    violation_type="code_home_boundary",
                    intent_id="INT-EMPTY-OVERRIDE-IMPL",
                    violating_paths=["src/other_domain/empty_override_util.py"],
                    expected_prefixes=["src/payments/"],
                    functionality_intent_id="INT-EMPTY-OVERRIDE-FUNC",
                    suggested_fix="Move file to src/payments/empty_override_util.py",
                ),
            ],
            "passed": False,
            "override_rationale": None,
        }
        result = save_structure_validation(
            session_id, diff_hash, str(structure_repo), validation
        )
        assert result["success"], f"save_structure_validation failed: {result}"

        # Create session record
        record = minimal_session_record(session_id, diff_hash)
        record["session_id"] = session_id
        result = save_session_record(
            session_id, str(structure_repo), diff_hash, record
        )
        assert result["success"], f"save_session_record failed: {result}"

        # Run stop hook - should BLOCK with empty override
        exit_code, _stdout, stderr = run_stop_hook(
            structure_repo, session_id, project_root
        )

        # Verify hook blocks with exit code 2
        assert exit_code == 2, (
            f"Expected exit code 2 (blocked with empty override), got {exit_code}.\n"
            f"stderr: {stderr}"
        )

        # Verify structure violation message
        assert "structure validation failed" in stderr.lower(), (
            f"Expected 'structure validation failed' in stderr.\n"
            f"stderr: {stderr}"
        )
