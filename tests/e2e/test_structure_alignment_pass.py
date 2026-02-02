"""
T059: E2E tests for structure alignment pass scenario.

Tests the full flow where file changes are WITHIN declared code_home boundaries,
structure validation passes (no violations), and commits are created successfully.

Test cases:
1. test_changes_within_code_home_allowed - Full flow with files in correct location:
   - Make changes WITHIN the declared code_home (src/payments/)
   - Create all artifacts including structure_validation with passed=true
   - Run stop hook
   - Verify commits are created successfully
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from mcp_servers.intention_audit.tools.save_session_record import save_session_record
from mcp_servers.intention_audit.tools.save_structure_validation import (
    save_structure_validation,
)
from tests.e2e.conftest import compute_diff_hash, run_stop_hook


def _create_intentions_for_payments(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
    intent_id: str = "INT-T059-001",
) -> dict:
    """
    Create intentions artifact for changes within payments code_home.

    The structure includes:
    - Root goal: Payment Processing System
    - Functionality child with code_home: ["src/payments/"]
    - Implementation child with specific intent_id
    """
    intentions = {
        "id": "INT-T059-ROOT",
        "title": "Payment Processing System",
        "kind": "goal",
        "status": "in_progress",
        "children": [
            {
                "id": "INT-T059-FUNC",
                "title": "Core Payment Functionality",
                "kind": "functionality",
                "status": "in_progress",
                "code_home": ["src/payments/"],
                "children": [
                    {
                        "id": intent_id,
                        "title": "Enhance payment processing",
                        "kind": "implementation",
                        "status": "planned",
                        "children": [],
                    }
                ],
            }
        ],
    }
    return save_intentions(session_id, diff_hash, str(repo_path), intentions)


def _create_commit_plan_for_payments(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
    files: list[str],
    intent_id: str = "INT-T059-001",
    functionality_intent_id: str = "INT-T059-FUNC",
) -> dict:
    """
    Create commit plan artifact for changes within payments code_home.
    """
    plan = {
        "version": 1,
        "ready": True,
        "commits": [
            {
                "intent_id": intent_id,
                "functionality_intent_id": functionality_intent_id,
                "subject": "feat(payments): enhance payment processing",
                "files": files,
            }
        ],
    }
    return save_commit_plan(session_id, diff_hash, str(repo_path), plan)


def _create_structure_validation_passed(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
) -> dict:
    """
    Create structure validation artifact indicating all files are within code_home.
    """
    validation = {
        "violations": [],
        "passed": True,
        "override_rationale": None,
    }
    return save_structure_validation(session_id, diff_hash, str(repo_path), validation)


def _create_session_record(
    session_id: str,
    diff_hash: str,
    repo_path: Path,
    intent_id: str = "INT-T059-001",
) -> dict:
    """
    Create session record artifact for audit trail.
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
        "notes": "E2E test: structure alignment pass scenario",
    }
    return save_session_record(session_id, str(repo_path), diff_hash, record)


def _create_config_with_disabled_evidence(repo_path: Path) -> None:
    """
    Create config file that disables evidence checking.

    This allows tests to focus on structure validation without
    requiring evidence tests to be run.
    """
    import json

    config = {
        "evidence_checking": False,
        "structure_validation": True,
        "docs_validation": "disabled",
    }
    config_dir = repo_path / ".intent_audit"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2))


@pytest.mark.e2e
class TestStructureAlignmentPass:
    """Test scenarios where structure validation passes (no code_home violations)."""

    def test_changes_within_code_home_allowed(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        Full flow: changes WITHIN code_home should pass structure validation
        and create commits successfully.

        Steps:
        1. Make a change WITHIN the declared code_home (src/payments/)
        2. Create all required artifacts:
           - intentions.yaml with code_home: ["src/payments/"]
           - commit_plan.yaml covering the changed file
           - structure_validation.json with passed=true
           - session_record.json for audit trail
        3. Run stop hook
        4. Verify commits are created successfully
        """
        # Disable evidence checking via config
        _create_config_with_disabled_evidence(structure_repo)

        # Step 1: Make a change WITHIN the code_home (src/payments/)
        processor_file = structure_repo / "src" / "payments" / "processor.py"
        original_content = processor_file.read_text()
        new_content = (
            original_content
            + '\n\ndef refund_payment(amount: float) -> dict:\n    """Refund a payment."""\n    return {"status": "refunded", "amount": amount}\n'
        )
        processor_file.write_text(new_content)

        # Step 2: Create all artifacts
        session_id = "test-t059-001"
        diff_hash = compute_diff_hash(structure_repo)

        # Save intentions (with code_home for payments)
        result = _create_intentions_for_payments(session_id, diff_hash, structure_repo)
        assert result["success"], f"save_intentions failed: {result}"

        # Save commit plan covering the changed file
        result = _create_commit_plan_for_payments(
            session_id,
            diff_hash,
            structure_repo,
            files=["src/payments/processor.py"],
        )
        assert result["success"], f"save_commit_plan failed: {result}"

        # Save structure validation with passed=true
        result = _create_structure_validation_passed(session_id, diff_hash, structure_repo)
        assert result["success"], f"save_structure_validation failed: {result}"

        # Save session record
        result = _create_session_record(session_id, diff_hash, structure_repo)
        assert result["success"], f"save_session_record failed: {result}"

        # Step 3: Run stop hook
        exit_code, stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        # Step 4: Verify commits are created successfully
        assert exit_code == 0, (
            f"Expected exit code 0 (success), got {exit_code}.\nstdout: {stdout}\nstderr: {stderr}"
        )

        # Verify commit was created with Intent-Id trailer
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-2"],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]
        assert len(commits) >= 2, f"Expected at least 2 commits, got: {commits}"

        # Verify Intent-Id trailer is present
        trailer_result = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        intent_id = trailer_result.stdout.strip()
        assert intent_id == "INT-T059-001", (
            f"Expected Intent-Id trailer 'INT-T059-001', got: {intent_id}"
        )

        # Verify no uncommitted changes remain (except .intent_audit/)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(structure_repo),
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

    def test_new_file_within_code_home_allowed(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        Test adding a new file WITHIN the code_home passes structure validation.

        Steps:
        1. Create a NEW file within src/payments/
        2. Create all artifacts with structure_validation.passed=true
        3. Run stop hook
        4. Verify commit is created
        """
        # Disable evidence checking via config
        _create_config_with_disabled_evidence(structure_repo)

        # Step 1: Create a NEW file within the code_home
        new_file = structure_repo / "src" / "payments" / "currency.py"
        new_file.write_text(
            '"""Currency utilities for payment processing."""\n\n'
            'SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]\n\n'
            "def is_supported(currency: str) -> bool:\n"
            '    """Check if currency is supported."""\n'
            "    return currency.upper() in SUPPORTED_CURRENCIES\n"
        )

        session_id = "test-t059-002"
        diff_hash = compute_diff_hash(structure_repo)

        # Create artifacts
        result = _create_intentions_for_payments(
            session_id, diff_hash, structure_repo, intent_id="INT-T059-002"
        )
        assert result["success"]

        result = _create_commit_plan_for_payments(
            session_id,
            diff_hash,
            structure_repo,
            files=["src/payments/currency.py"],
            intent_id="INT-T059-002",
        )
        assert result["success"]

        result = _create_structure_validation_passed(session_id, diff_hash, structure_repo)
        assert result["success"]

        result = _create_session_record(
            session_id, diff_hash, structure_repo, intent_id="INT-T059-002"
        )
        assert result["success"]

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify new file is committed
        show_result = subprocess.run(
            ["git", "show", "--name-only", "--format="],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = show_result.stdout.strip().split("\n")
        assert "src/payments/currency.py" in committed_files, (
            f"Expected src/payments/currency.py to be committed, got: {committed_files}"
        )

    def test_multiple_files_within_code_home_allowed(
        self, structure_repo: Path, project_root: Path
    ) -> None:
        """
        Test modifying multiple files all WITHIN code_home passes structure validation.

        Steps:
        1. Modify multiple files within src/payments/
        2. Create artifacts with all files in commit plan
        3. Run stop hook
        4. Verify single commit with all files
        """
        # Disable evidence checking via config
        _create_config_with_disabled_evidence(structure_repo)

        # Step 1: Modify multiple files within code_home
        processor_file = structure_repo / "src" / "payments" / "processor.py"
        processor_content = processor_file.read_text()
        processor_file.write_text(
            processor_content + "\n# Enhanced with batch processing support\n"
        )

        init_file = structure_repo / "src" / "payments" / "__init__.py"
        init_content = init_file.read_text() if init_file.exists() else ""
        init_file.write_text(init_content + '\n__version__ = "1.1.0"\n')

        session_id = "test-t059-003"
        diff_hash = compute_diff_hash(structure_repo)

        # Create artifacts
        result = _create_intentions_for_payments(
            session_id, diff_hash, structure_repo, intent_id="INT-T059-003"
        )
        assert result["success"]

        result = _create_commit_plan_for_payments(
            session_id,
            diff_hash,
            structure_repo,
            files=["src/payments/processor.py", "src/payments/__init__.py"],
            intent_id="INT-T059-003",
        )
        assert result["success"]

        result = _create_structure_validation_passed(session_id, diff_hash, structure_repo)
        assert result["success"]

        result = _create_session_record(
            session_id, diff_hash, structure_repo, intent_id="INT-T059-003"
        )
        assert result["success"]

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(structure_repo, session_id, project_root)

        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify both files are in the commit
        show_result = subprocess.run(
            ["git", "show", "--name-only", "--format="],
            cwd=str(structure_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = [f for f in show_result.stdout.strip().split("\n") if f]
        assert "src/payments/processor.py" in committed_files
        assert "src/payments/__init__.py" in committed_files
