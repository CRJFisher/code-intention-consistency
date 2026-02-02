"""
T060: E2E tests for structure alignment blocking behavior.

Tests the stop hook's structure validation phase, verifying that:
- Changes outside declared code_home boundaries are blocked
- Structure violations include suggested fixes in the blocking message
- Evidence results are separate from structure validation (can pass while structure fails)

Test scenario:
1. Repository has intentions.yaml with code_home: ["src/payments/"] for payments functionality
2. Changes are made OUTSIDE this boundary (in src/other_domain/)
3. Structure validation fails due to boundary violation
4. Stop hook blocks with structure violation report
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
from tests.e2e.fixtures import (
    full_commit_entry,
    minimal_intention,
    multi_commit_plan,
)


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
        "intentions_touched": ["INT-TEST-STRUCT"],
        "mapping_summary": {
            "total_files": 1,
            "mapped_files": 1,
            "unmapped_files": 0,
        },
        "notes": "Test session for structure validation",
    }


@pytest.mark.e2e
class TestStructureAlignmentBlock:
    """Test structure alignment blocking scenarios."""

    def test_changes_outside_code_home_blocked(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When file changes are outside declared code_home boundaries,
        hook should block with structure violation message.

        Flow:
        1. Make a change OUTSIDE the declared code_home (src/other_domain/)
           but assign it to payments functionality
        2. Create intentions with code_home for payments
        3. Create commit_plan artifact mapping the file to payments intention
        4. Create evidence_results artifact (passing - evidence is separate)
        5. Create structure_validation artifact with violations (passed=false)
        6. Run stop hook
        7. Verify hook blocks with structure violation message
        8. Verify suggested fixes are included
        """
        # Create a file change OUTSIDE the payments code_home boundary
        # The payments functionality has code_home: ["src/payments/"]
        # But we're modifying a file in src/other_domain/
        violation_file = structure_repo / "src" / "other_domain" / "payment_leak.py"
        violation_file.write_text(
            "# This file implements payment logic but is in wrong domain\n"
            "def leaked_payment_function():\n"
            "    return 'should be in src/payments/'\n"
        )

        session_id = "test-struct-001"
        diff_hash = compute_diff_hash(structure_repo)

        # Step 2: Create intentions artifact with code_home boundary
        intentions = goal_intention_tree(
            "INT-STRUCT-ROOT",
            "Test Structure Validation",
            children=[
                intention_with_code_home(
                    "INT-STRUCT-PAYMENTS",
                    "Payment Processing",
                    code_home=["src/payments/"],
                    children=[
                        minimal_intention(
                            "INT-STRUCT-IMPL",
                            "Implement payment leak function",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Step 3: Create commit plan that maps the file to the payments intention
        # This creates the boundary violation - file is in src/other_domain/
        # but commit is assigned to an intention under payments functionality
        plan = multi_commit_plan(
            [
                full_commit_entry(
                    intent_id="INT-STRUCT-IMPL",
                    files=["src/other_domain/payment_leak.py"],
                    subject="feat: add payment leak function",
                    functionality_intent_id="INT-STRUCT-PAYMENTS",
                ),
            ]
        )
        result = save_commit_plan(session_id, diff_hash, str(structure_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Step 4: Create evidence results (passing - evidence is independent of structure)
        # Use empty test selectors since we're not testing evidence here
        result = run_evidence_tests(
            session_id,
            str(structure_repo),
            diff_hash,
            ["tests/payments/test_processor.py::test_process_payment"],
        )
        assert result["success"], f"run_evidence_tests failed: {result}"

        # Step 5: Create structure validation with violations (passed=false)
        validation = {
            "violations": [
                structure_violation(
                    violation_type="code_home_boundary",
                    intent_id="INT-STRUCT-IMPL",
                    violating_paths=["src/other_domain/payment_leak.py"],
                    expected_prefixes=["src/payments/"],
                    functionality_intent_id="INT-STRUCT-PAYMENTS",
                    suggested_fix="Move file to src/payments/payment_leak.py",
                ),
            ],
            "passed": False,
            "override_rationale": None,
        }
        result = save_structure_validation(session_id, diff_hash, str(structure_repo), validation)
        assert result["success"], f"save_structure_validation failed: {result}"

        # Step 6: Create session record (required by hook)
        record = minimal_session_record(session_id, diff_hash)
        result = save_session_record(session_id, str(structure_repo), diff_hash, record)
        assert result["success"], f"save_session_record failed: {result}"

        # Step 7: Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        # Step 8: Verify hook blocks with exit code 2
        assert exit_code == 2, f"Expected exit code 2 (blocked), got {exit_code}.\nstderr: {stderr}"

        # Step 9: Verify structure violation message is present
        assert "structure validation failed" in stderr.lower(), (
            f"Expected 'structure validation failed' in stderr.\nstderr: {stderr}"
        )

        # Verify the violation report is included
        assert "code_home_boundary" in stderr.lower() or "boundary" in stderr.lower(), (
            f"Expected boundary violation type in stderr.\nstderr: {stderr}"
        )

        # Verify violating path is mentioned
        assert "other_domain" in stderr or "payment_leak" in stderr, (
            f"Expected violating path in stderr.\nstderr: {stderr}"
        )

        # Step 10: Verify suggested fixes are included
        # The structure_renderer.py generates suggested fixes for code_home_boundary
        assert "suggested fix" in stderr.lower() or "move" in stderr.lower(), (
            f"Expected suggested fixes in stderr.\nstderr: {stderr}"
        )

    def test_structure_override_allows_proceed(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When structure violations exist but override rationale is provided,
        hook should allow proceeding (no block).

        This tests the override mechanism for intentional cross-boundary changes.
        """
        # Create a file change outside code_home
        violation_file = structure_repo / "src" / "other_domain" / "intentional_cross.py"
        violation_file.write_text(
            "# Intentionally cross-boundary utility\n"
            "def shared_utility():\n"
            "    return 'used by multiple domains'\n"
        )

        session_id = "test-struct-002"
        diff_hash = compute_diff_hash(structure_repo)

        # Create intentions
        intentions = goal_intention_tree(
            "INT-STRUCT-ROOT2",
            "Test Structure Override",
            children=[
                intention_with_code_home(
                    "INT-STRUCT-SHARED",
                    "Shared Utilities",
                    code_home=["src/shared/"],
                    children=[
                        minimal_intention(
                            "INT-STRUCT-UTIL",
                            "Add shared utility",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan WITH override rationale
        plan = {
            "version": 1,
            "ready": True,
            "commits": [
                {
                    "intent_id": "INT-STRUCT-UTIL",
                    "subject": "feat: add shared utility",
                    "files": ["src/other_domain/intentional_cross.py"],
                    "functionality_intent_id": "INT-STRUCT-SHARED",
                }
            ],
            "structure_override_rationale": (
                "Cross-boundary placement is intentional: "
                "this utility serves multiple domains and will be "
                "refactored into src/shared/ in a follow-up PR."
            ),
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

        # Create structure validation with violations but hook will use override from plan
        validation = {
            "violations": [
                structure_violation(
                    violation_type="code_home_boundary",
                    intent_id="INT-STRUCT-UTIL",
                    violating_paths=["src/other_domain/intentional_cross.py"],
                    expected_prefixes=["src/shared/"],
                    functionality_intent_id="INT-STRUCT-SHARED",
                ),
            ],
            "passed": False,
            "override_rationale": None,  # Hook reads override from commit_plan
        }
        result = save_structure_validation(session_id, diff_hash, str(structure_repo), validation)
        assert result["success"], f"save_structure_validation failed: {result}"

        # Create session record
        record = minimal_session_record(session_id, diff_hash)
        result = save_session_record(session_id, str(structure_repo), diff_hash, record)
        assert result["success"], f"save_session_record failed: {result}"

        # Run stop hook - should succeed due to override rationale
        exit_code, _stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        # Should NOT block - override rationale allows proceeding
        assert exit_code == 0, (
            f"Expected exit code 0 (allowed with override), got {exit_code}.\nstderr: {stderr}"
        )

        # Verify commit was created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "shared utility" in log_result.stdout.lower() or "INT-STRUCT" in log_result.stdout, (
            f"Expected commit with intent ID.\nGit log: {log_result.stdout}"
        )

    def test_missing_structure_validation_blocks(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        When structure_validation artifact is missing,
        hook should block with instructions to run structure-validator.
        """
        # Create a file change
        new_file = structure_repo / "src" / "payments" / "new_payment.py"
        new_file.write_text("# New payment module\n")

        session_id = "test-struct-003"
        diff_hash = compute_diff_hash(structure_repo)

        # Create intentions
        intentions = goal_intention_tree(
            "INT-STRUCT-ROOT3",
            "Test Missing Structure Validation",
            children=[
                intention_with_code_home(
                    "INT-STRUCT-PAY",
                    "Payment Processing",
                    code_home=["src/payments/"],
                    children=[
                        minimal_intention(
                            "INT-STRUCT-NEW",
                            "Add new payment module",
                            kind="implementation",
                        ),
                    ],
                ),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(structure_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Create commit plan
        plan = multi_commit_plan(
            [
                full_commit_entry(
                    intent_id="INT-STRUCT-NEW",
                    files=["src/payments/new_payment.py"],
                    subject="feat: add new payment module",
                    functionality_intent_id="INT-STRUCT-PAY",
                ),
            ]
        )
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

        # DO NOT create structure_validation artifact

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        # Should block due to missing structure_validation
        assert exit_code == 2, f"Expected exit code 2 (blocked), got {exit_code}.\nstderr: {stderr}"

        # Should mention missing structure validation
        assert "structure validation" in stderr.lower(), (
            f"Expected 'structure validation' in stderr.\nstderr: {stderr}"
        )

        # Should mention structure-validator sub-agent
        assert "structure-validator" in stderr, (
            f"Expected 'structure-validator' sub-agent in stderr.\nstderr: {stderr}"
        )
