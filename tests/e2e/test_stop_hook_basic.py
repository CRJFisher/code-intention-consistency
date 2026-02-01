"""
T035: E2E tests for basic stop-gate blocking behavior.

There are two test classes:

1. TestStopHookBasic - Simulated E2E tests that call MCP tools directly with test data.
   These are fast and reliable for testing the hook logic itself.

2. TestStopHookBasicClaude - True E2E tests using `claude -p` headless mode.
   These test the complete flow: hook → sub-agent → MCP tool → artifact → hook → commit.
   These require API access and are skipped by default.

Test cases (simulated):
1. test_blocks_missing_intentions - No artifacts → blocks with intention-mapper instructions
2. test_blocks_missing_commit_plan - Has intentions but no plan → blocks with commit-planner instructions
3. test_creates_commits_with_full_coverage - Valid artifacts → creates commits and allows stop
4. test_blocks_incomplete_coverage - Plan missing files → blocks with coverage error
5. test_allows_stop_no_changes - No uncommitted changes → allows stop immediately

Test cases (true E2E with claude -p):
1. test_full_flow_single_file - Create file → stop blocked → sub-agents run → commits created
2. test_full_flow_multiple_files - Create multiple files → grouped commits
3. test_no_changes_allows_stop - No changes → exits cleanly
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path for MCP tool imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.intention_audit.tools.save_commit_plan import save_commit_plan
from mcp_servers.intention_audit.tools.save_intentions import save_intentions
from tests.e2e.conftest import compute_diff_hash, run_stop_hook
from tests.e2e.fixtures import (
    full_commit_entry,
    intention_tree,
    minimal_commit_plan,
    minimal_intention,
    multi_commit_plan,
)


@pytest.mark.e2e
class TestStopHookBasic:
    """Test basic stop-gate blocking scenarios."""

    def test_blocks_missing_intentions(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When uncommitted changes exist but no intentions artifact,
        hook should block with intention-mapper instructions.
        """
        # Create a file change
        new_file = basic_repo / "src" / "feature_x" / "new_module.py"
        new_file.write_text("# New module\n")

        session_id = "test-session-001"
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)

        # Hook should block (exit code 2)
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}. stderr: {stderr}"

        # Should mention missing intentions and intention-mapper
        assert "missing intentions artifact" in stderr.lower()
        assert "intention-mapper" in stderr

    def test_blocks_missing_commit_plan(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When intentions exist but no commit plan,
        hook should block with commit-planner instructions.
        """
        # Create a file change
        new_file = basic_repo / "src" / "feature_x" / "new_module.py"
        new_file.write_text("# New module for commit plan test\n")

        session_id = "test-session-002"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions artifact (simulating intention-mapper sub-agent)
        intentions = intention_tree(
            "INT-001",
            "Add new module",
            children=[minimal_intention("INT-001-A", "Implement new_module.py")],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Run stop hook WITHOUT commit plan
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)

        # Hook should block (exit code 2)
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}. stderr: {stderr}"

        # Should mention missing commit plan and commit-planner
        assert "missing commit plan" in stderr.lower()
        assert "commit-planner" in stderr

    def test_creates_commits_with_full_coverage(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When valid intentions and commit plan exist with full coverage,
        hook should create commits and allow stop (exit 0).
        """
        # Create a file change
        new_file = basic_repo / "src" / "feature_x" / "covered_module.py"
        new_file.write_text("# Covered module\ndef covered(): pass\n")

        session_id = "test-session-003"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions artifact
        intentions = intention_tree(
            "INT-002",
            "Add covered module",
            children=[minimal_intention("INT-002-A", "Implement covered_module.py")],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Save commit plan covering the changed file
        plan = minimal_commit_plan(
            intent_id="INT-002-A",
            files=["src/feature_x/covered_module.py"],
            subject="feat: add covered_module implementation",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)

        # Hook should allow stop (exit code 0)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"

        # Verify commit was created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "covered_module" in log_result.stdout or "INT-002" in log_result.stdout

        # Verify no uncommitted changes remain
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        # Filter out .intent_audit/ from status
        uncommitted = [
            line for line in status_result.stdout.strip().split("\n")
            if line and ".intent_audit" not in line
        ]
        assert len(uncommitted) == 0, f"Unexpected uncommitted files: {uncommitted}"

    def test_blocks_incomplete_coverage(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When commit plan doesn't cover all changed files,
        hook should block with coverage error.
        """
        # Create TWO file changes
        file1 = basic_repo / "src" / "feature_x" / "module_a.py"
        file1.write_text("# Module A\n")
        file2 = basic_repo / "src" / "feature_x" / "module_b.py"
        file2.write_text("# Module B\n")

        session_id = "test-session-004"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions artifact
        intentions = intention_tree(
            "INT-003",
            "Add modules",
            children=[
                minimal_intention("INT-003-A", "Implement module_a"),
                minimal_intention("INT-003-B", "Implement module_b"),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"], f"save_intentions failed: {result}"

        # Save commit plan covering ONLY ONE file (incomplete)
        plan = minimal_commit_plan(
            intent_id="INT-003-A",
            files=["src/feature_x/module_a.py"],  # Missing module_b.py!
            subject="feat: add module_a",
            ready=True,
        )
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"], f"save_commit_plan failed: {result}"

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)

        # Hook should block (exit code 2)
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}. stderr: {stderr}"

        # Should mention coverage issue and unassigned file
        assert "unassigned" in stderr.lower() or "does not exactly cover" in stderr.lower()
        assert "module_b.py" in stderr

    def test_allows_stop_no_changes(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When there are no uncommitted changes,
        hook should allow stop immediately (exit 0).
        """
        session_id = "test-session-005"

        # Ensure clean working directory (should already be clean after fixture setup)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        # Only .intent_audit/ might be present, which is gitignored
        assert status_result.stdout.strip() == "", "Repo should have no changes"

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)

        # Hook should allow stop (exit code 0)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"


@pytest.mark.e2e
class TestStopHookMultipleCommits:
    """Test scenarios with multiple commits."""

    def test_creates_multiple_commits(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When plan specifies multiple commits,
        hook should create each commit separately.
        """
        # Create two file changes for different intentions
        file1 = basic_repo / "src" / "feature_x" / "api.py"
        file1.write_text("# API module\ndef api_call(): pass\n")
        file2 = basic_repo / "tests" / "feature_x" / "test_api.py"
        file2.write_text("# API tests\ndef test_api(): pass\n")

        session_id = "test-session-multi"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-MULTI",
            "Add API feature",
            children=[
                minimal_intention("INT-MULTI-IMPL", "Implement API", kind="implementation"),
                minimal_intention("INT-MULTI-TEST", "Add API tests", kind="tests"),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save plan with two commits
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-MULTI-IMPL",
                files=["src/feature_x/api.py"],
                subject="feat: add API module",
            ),
            full_commit_entry(
                intent_id="INT-MULTI-TEST",
                files=["tests/feature_x/test_api.py"],
                subject="test: add API tests",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _stdout, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Expected exit 0, got {exit_code}. stderr: {stderr}"

        # Verify two commits were created
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-3"],  # Get last 3 commits
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]

        # Should have at least 2 new commits plus the initial
        assert len(commits) >= 3, f"Expected at least 3 commits, got: {commits}"


# =============================================================================
# TRUE E2E TESTS WITH claude -p
# =============================================================================


def _check_claude_available() -> None:
    """Check if claude CLI is available, raise error if not."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"claude CLI returned non-zero exit code: {result.returncode}\n"
                f"stderr: {result.stderr}"
            )
    except FileNotFoundError:
        raise RuntimeError(
            "claude CLI not found. Install Claude Code to run E2E tests: "
            "https://docs.anthropic.com/en/docs/claude-code"
        ) from None
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude CLI timed out during version check") from None




@pytest.mark.e2e
class TestStopHookBasicClaude:
    """
    True E2E tests using claude -p headless mode.

    These tests invoke the actual Claude CLI and test the complete flow:
    1. Create file changes
    2. Try to stop → hook blocks
    3. Claude spawns intention-mapper sub-agent
    4. Sub-agent calls save_intentions MCP tool
    5. Retry stop → hook blocks (missing commit plan)
    6. Claude spawns commit-planner sub-agent
    7. Sub-agent calls save_commit_plan MCP tool
    8. Retry stop → hook creates commits → allows stop

    These tests require:
    - claude CLI installed and configured
    - API access (uses haiku for cost efficiency)
    - Network access
    """

    @classmethod
    def setup_class(cls) -> None:
        """Verify claude CLI is available before running tests."""
        _check_claude_available()

    def test_full_flow_single_file(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        Test complete flow: create file → stop blocked → sub-agents run → commit created.

        This is the canonical test for the full intention audit trail flow.
        """
        prompt = """
        Create a new file src/feature_x/greet.py with a simple greeting function that returns "Hello, World!".

        After creating the file, stop the session.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=300,  # Allow more time for full flow
        )

        # Collect diagnostic info for debugging
        greet_file = basic_repo / "src" / "feature_x" / "greet.py"
        file_exists = greet_file.exists()

        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
        )
        git_log = log_result.stdout

        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
        )
        git_status = status_result.stdout

        # Check for .intent_audit artifacts
        intent_audit_dir = basic_repo / ".intent_audit"
        intent_artifacts = list(intent_audit_dir.rglob("*")) if intent_audit_dir.exists() else []

        debug_info = (
            f"\n=== DEBUG INFO ===\n"
            f"Exit code: {exit_code}\n"
            f"File exists: {file_exists}\n"
            f"Git log:\n{git_log}\n"
            f"Git status:\n{git_status}\n"
            f"Intent artifacts: {[str(a) for a in intent_artifacts]}\n"
            f"\n=== STDOUT ===\n{stdout}\n"
            f"\n=== STDERR ===\n{stderr}\n"
        )

        # Session should complete successfully
        assert exit_code == 0, f"Session failed with exit code {exit_code}.{debug_info}"

        # Verify file was created
        assert file_exists, f"Expected greet.py to be created, but it doesn't exist.{debug_info}"

        # Verify commit was created (at least 2: initial + new file commit)
        commits = [line for line in git_log.strip().split("\n") if line]
        assert len(commits) >= 2, f"Expected at least 2 commits.{debug_info}"

        # Verify Intent-Id trailer is present
        trailer_result = subprocess.run(
            ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        intent_id = trailer_result.stdout.strip()
        assert intent_id, f"Expected Intent-Id trailer, but none found.{debug_info}"

    def test_full_flow_multiple_files(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        Test flow with multiple files: should create intention-scoped commits.
        """
        prompt = """
        Create two new files:
        1. src/feature_x/math_utils.py with add() and subtract() functions
        2. tests/feature_x/test_math_utils.py with tests for those functions

        After creating both files, stop the session.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=300,
        )

        assert exit_code == 0, f"Session failed.\nstdout: {stdout}\nstderr: {stderr}"

        # Verify files were created
        math_file = basic_repo / "src" / "feature_x" / "math_utils.py"
        test_file = basic_repo / "tests" / "feature_x" / "test_math_utils.py"
        assert math_file.exists(), "math_utils.py not created"
        assert test_file.exists(), "test_math_utils.py not created"

        # Verify commits were created (could be 1 grouped commit or multiple)
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-4"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]
        # At minimum: initial commit + .gitignore commit + at least 1 new commit
        assert len(commits) >= 3, f"Expected at least 3 commits, got: {commits}"

        # Verify all new commits have Intent-Id trailers
        for i in range(len(commits) - 2):  # Skip initial and .gitignore commits
            ref = f"HEAD~{i}"
            trailer_result = subprocess.run(
                ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)", ref],
                cwd=str(basic_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            intent_id = trailer_result.stdout.strip()
            assert intent_id, f"Expected Intent-Id trailer at {ref}, but none found"

    def test_no_changes_allows_stop(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        When there are no changes, stop should be allowed immediately.
        """
        # Count commits before running claude
        log_before = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits_before = len([line for line in log_before.stdout.strip().split("\n") if line])

        prompt = """
        Do not make any changes. Just stop the session immediately.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=60,  # Should be quick
        )

        assert exit_code == 0, f"Session failed.\nstdout: {stdout}\nstderr: {stderr}"

        # Verify no new intention-tagged commits were created
        log_result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits_after = len([line for line in log_result.stdout.strip().split("\n") if line])

        # Allow for at most 1 new commit (possible .gitignore update)
        new_commits = commits_after - commits_before
        assert new_commits <= 1, f"Expected at most 1 new commit (optional .gitignore), got {new_commits}"

        # If there's a new commit, it shouldn't have Intent-Id (it's just .gitignore)
        if new_commits == 1:
            intent_id = subprocess.run(
                ["git", "log", "-1", "--format=%(trailers:key=Intent-Id,valueonly)"],
                cwd=str(basic_repo),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            assert not intent_id, f"Unexpected Intent-Id on .gitignore commit: {intent_id}"
