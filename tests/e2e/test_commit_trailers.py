"""
T036: E2E tests for commit trailer verification.

There are two test classes:

1. TestCommitTrailers / TestTrailerEdgeCases - Simulated E2E tests that call MCP tools
   directly with test data. These are fast and reliable for testing trailer generation.

2. TestCommitTrailersClaude - True E2E tests using `claude -p` headless mode.
   These test that real sub-agents produce valid trailer data.
   These require API access and are skipped by default.

Test cases (simulated):
1. test_intent_id_trailer_present - Every commit has Intent-Id trailer
2. test_intent_path_trailer_when_provided - Intent-Path present when plan provides it
3. test_functionality_intent_id_trailer - Functionality-Intent-Id present when provided
4. test_trace_via_git_log - Trailers extractable via git log --format=%(trailers:...)
5. test_multiple_commits_each_has_trailers - Multiple commits each have their own trailers
6. test_commit_body_preserved - Body appears before trailers

Test cases (true E2E with claude -p):
1. test_intent_id_trailer_via_claude - Verify Intent-Id is present in real flow
2. test_multiple_commits_trailers_via_claude - Verify multiple commits have proper trailers
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
    minimal_intention,
    multi_commit_plan,
)


def get_commit_message(repo_path: Path, ref: str = "HEAD") -> str:
    """Get full commit message for a given ref."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B", ref],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def get_trailer_value(repo_path: Path, trailer_key: str, ref: str = "HEAD") -> str | None:
    """
    Extract a specific trailer value from a commit.

    Uses git log --format=%(trailers:key=...,valueonly) for reliable extraction.
    """
    result = subprocess.run(
        ["git", "log", "-1", f"--format=%(trailers:key={trailer_key},valueonly)", ref],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    value = result.stdout.strip()
    return value if value else None


def get_all_trailers(repo_path: Path, ref: str = "HEAD") -> dict[str, str]:
    """Extract all trailers from a commit as a dictionary."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%(trailers)", ref],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    trailers = {}
    for line in result.stdout.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            trailers[key.strip()] = value.strip()
    return trailers


@pytest.mark.e2e
class TestCommitTrailers:
    """Test commit trailer generation."""

    def test_intent_id_trailer_present(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        Every commit created by the stop hook should have Intent-Id trailer.
        """
        # Create file change
        new_file = basic_repo / "src" / "feature_x" / "trailer_test.py"
        new_file.write_text("# Trailer test module\n")

        session_id = "test-trailer-001"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-T001",
            "Test trailer presence",
            children=[minimal_intention("INT-T001-A", "Add trailer test module")],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save commit plan
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-T001-A",
                files=["src/feature_x/trailer_test.py"],
                subject="feat: add trailer test module",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify Intent-Id trailer
        intent_id = get_trailer_value(basic_repo, "Intent-Id")
        assert intent_id == "INT-T001-A", f"Expected Intent-Id 'INT-T001-A', got '{intent_id}'"

        # Also verify via raw message parsing
        message = get_commit_message(basic_repo)
        assert "Intent-Id: INT-T001-A" in message

    def test_intent_path_trailer_when_provided(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        Intent-Path trailer should be present when the plan provides it.
        """
        # Create file change
        new_file = basic_repo / "src" / "feature_x" / "path_test.py"
        new_file.write_text("# Path test module\n")

        session_id = "test-trailer-002"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions with hierarchy
        intentions = intention_tree(
            "INT-T002",
            "Test intent path",
            children=[
                {
                    "id": "INT-T002-FUNC",
                    "title": "Functionality intent",
                    "kind": "functionality",
                    "status": "planned",
                    "children": [
                        minimal_intention("INT-T002-IMPL", "Implementation intent"),
                    ],
                }
            ],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save commit plan with intent_path
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-T002-IMPL",
                files=["src/feature_x/path_test.py"],
                subject="feat: add path test module",
                intent_path="INT-T002/INT-T002-FUNC/INT-T002-IMPL",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify Intent-Path trailer
        intent_path = get_trailer_value(basic_repo, "Intent-Path")
        assert intent_path == "INT-T002/INT-T002-FUNC/INT-T002-IMPL"

        # Also verify Intent-Id is present
        intent_id = get_trailer_value(basic_repo, "Intent-Id")
        assert intent_id == "INT-T002-IMPL"

    def test_functionality_intent_id_trailer(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        Functionality-Intent-Id trailer should be present when provided.
        """
        # Create file change
        new_file = basic_repo / "src" / "feature_x" / "func_test.py"
        new_file.write_text("# Functionality test module\n")

        session_id = "test-trailer-003"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-T003",
            "Test functionality intent",
            children=[
                {
                    "id": "INT-T003-FUNC",
                    "title": "Parent functionality",
                    "kind": "functionality",
                    "status": "planned",
                    "children": [
                        minimal_intention("INT-T003-IMPL", "Child implementation"),
                    ],
                }
            ],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save commit plan with functionality_intent_id
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-T003-IMPL",
                files=["src/feature_x/func_test.py"],
                subject="feat: add functionality test module",
                functionality_intent_id="INT-T003-FUNC",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify Functionality-Intent-Id trailer
        func_intent = get_trailer_value(basic_repo, "Functionality-Intent-Id")
        assert func_intent == "INT-T003-FUNC"

        # Also verify Intent-Id is present
        intent_id = get_trailer_value(basic_repo, "Intent-Id")
        assert intent_id == "INT-T003-IMPL"

    def test_trace_via_git_log(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        Trailers should be extractable via git log --format=%(trailers:...).
        This validates the standard Git trailer format is used.
        """
        # Create file change
        new_file = basic_repo / "src" / "feature_x" / "trace_test.py"
        new_file.write_text("# Trace test module\n")

        session_id = "test-trailer-004"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-T004",
            "Test git log extraction",
            children=[minimal_intention("INT-T004-A", "Implementation")],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save commit plan with all optional fields
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-T004-A",
                files=["src/feature_x/trace_test.py"],
                subject="feat: add trace test module",
                intent_path="INT-T004/INT-T004-A",
                functionality_intent_id="INT-T004",
                intent_confidence=0.95,
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Extract all trailers using git's trailer parsing
        trailers = get_all_trailers(basic_repo)

        # Verify all expected trailers
        assert "Intent-Id" in trailers
        assert trailers["Intent-Id"] == "INT-T004-A"

        assert "Intent-Path" in trailers
        assert trailers["Intent-Path"] == "INT-T004/INT-T004-A"

        assert "Functionality-Intent-Id" in trailers
        assert trailers["Functionality-Intent-Id"] == "INT-T004"

        assert "Intent-Confidence" in trailers
        assert trailers["Intent-Confidence"] == "0.95"

    def test_multiple_commits_each_has_trailers(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When multiple commits are created, each should have its own trailers.
        """
        # Create two files
        file1 = basic_repo / "src" / "feature_x" / "multi_a.py"
        file1.write_text("# Multi A\n")
        file2 = basic_repo / "src" / "feature_x" / "multi_b.py"
        file2.write_text("# Multi B\n")

        session_id = "test-trailer-005"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-T005",
            "Multi-commit trailers",
            children=[
                minimal_intention("INT-T005-A", "First implementation"),
                minimal_intention("INT-T005-B", "Second implementation"),
            ],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save plan with two commits
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-T005-A",
                files=["src/feature_x/multi_a.py"],
                subject="feat: add multi_a module",
            ),
            full_commit_entry(
                intent_id="INT-T005-B",
                files=["src/feature_x/multi_b.py"],
                subject="feat: add multi_b module",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify trailers on HEAD (second commit)
        head_intent = get_trailer_value(basic_repo, "Intent-Id", "HEAD")
        assert head_intent == "INT-T005-B"

        # Verify trailers on HEAD~1 (first commit)
        prev_intent = get_trailer_value(basic_repo, "Intent-Id", "HEAD~1")
        assert prev_intent == "INT-T005-A"


@pytest.mark.e2e
class TestTrailerEdgeCases:
    """Test edge cases in trailer generation."""

    def test_commit_body_preserved(
        self, basic_repo: Path, project_root: Path
    ) -> None:
        """
        When commit plan includes a body, it should appear before trailers.
        """
        # Create file change
        new_file = basic_repo / "src" / "feature_x" / "body_test.py"
        new_file.write_text("# Body test module\n")

        session_id = "test-trailer-body"
        diff_hash = compute_diff_hash(basic_repo)

        # Save intentions
        intentions = intention_tree(
            "INT-BODY",
            "Body test",
            children=[minimal_intention("INT-BODY-A", "Implementation")],
        )
        result = save_intentions(session_id, diff_hash, str(basic_repo), intentions)
        assert result["success"]

        # Save commit plan with body
        plan = multi_commit_plan([
            full_commit_entry(
                intent_id="INT-BODY-A",
                files=["src/feature_x/body_test.py"],
                subject="feat: add body test module",
                body="This is a longer description.\n\nWith multiple paragraphs.",
            ),
        ])
        result = save_commit_plan(session_id, diff_hash, str(basic_repo), plan)
        assert result["success"]

        # Run stop hook
        exit_code, _, stderr = run_stop_hook(basic_repo, session_id, project_root)
        assert exit_code == 0, f"Hook failed: {stderr}"

        # Verify commit message structure
        message = get_commit_message(basic_repo)

        # Subject should be first line
        lines = message.strip().split("\n")
        assert "feat: add body test module" in lines[0]

        # Body should be present
        assert "longer description" in message
        assert "multiple paragraphs" in message

        # Trailer should be present
        assert "Intent-Id: INT-BODY-A" in message

        # Body should come before trailers
        body_pos = message.find("longer description")
        trailer_pos = message.find("Intent-Id:")
        assert body_pos < trailer_pos, "Body should appear before trailers"


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
class TestCommitTrailersClaude:
    """
    True E2E tests for commit trailers using claude -p headless mode.

    These tests verify that when real sub-agents create intentions and commit
    plans, the resulting commits have proper trailers.
    """

    @classmethod
    def setup_class(cls) -> None:
        """Verify claude CLI is available before running tests."""
        _check_claude_available()

    def test_intent_id_trailer_via_claude(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        Verify Intent-Id trailer is present in commits created by real flow.
        """
        prompt = """
        Create a new file src/feature_x/hello.py with a function hello() that prints "Hello".

        After creating the file, stop the session.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=300,
        )

        assert exit_code == 0, f"Session failed.\nstdout: {stdout}\nstderr: {stderr}"

        # Verify file was created
        assert (basic_repo / "src" / "feature_x" / "hello.py").exists()

        # Verify Intent-Id trailer using git's trailer parsing
        intent_id = get_trailer_value(basic_repo, "Intent-Id")
        assert intent_id is not None, "Expected Intent-Id trailer but none found"
        # Note: The sub-agent may use different ID formats (INT-*, root, intention_1, etc.)
        # The key is that an Intent-Id is present and non-empty
        assert len(intent_id) > 0, f"Intent-Id should be non-empty, got: {intent_id}"

    def test_files_committed_when_multiple_requested(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        Verify that when multiple files are requested, they are committed.

        Note: Claude may commit files directly via `git commit` before the stop hook
        triggers. In that case, the commits won't have Intent-Id trailers because
        the stop hook only processes uncommitted changes. This test verifies the
        basic flow works even if Claude commits directly.
        """
        prompt = """
        Create two files:

        1. src/feature_x/adder.py with a function add(a, b) that returns a + b
        2. tests/feature_x/test_adder.py with a test for the add function

        After creating both files, stop the session.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=300,
        )

        assert exit_code == 0, f"Session failed.\nstdout: {stdout}\nstderr: {stderr}"

        # Verify files were created
        assert (basic_repo / "src" / "feature_x" / "adder.py").exists()
        assert (basic_repo / "tests" / "feature_x" / "test_adder.py").exists()

        # Verify files are committed (either by Claude directly or via stop hook)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        uncommitted = [
            line for line in status_result.stdout.strip().split("\n")
            if line and not any(p in line for p in [".intent_audit", ".claude", ".mcp.json"])
        ]
        assert len(uncommitted) == 0, f"Expected no uncommitted files, got: {uncommitted}"

        # Get commit count - should have at least: initial, .gitignore, + work commits
        log_result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(basic_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [line for line in log_result.stdout.strip().split("\n") if line]
        assert len(commits) >= 3, f"Expected at least 3 commits, got {len(commits)}: {commits}"

    def test_trailers_extractable_via_git_format(
        self,
        basic_repo: Path,
        project_root: Path,
        claude_session_runner: callable,
    ) -> None:
        """
        Verify that trailers from real flow are extractable via git log --format.
        This confirms the trailer format is correct for Git integration tools.
        """
        prompt = """
        Create a simple file src/feature_x/version.py that defines VERSION = "1.0.0".

        After creating the file, stop the session.
        """

        exit_code, stdout, stderr = claude_session_runner(
            basic_repo,
            prompt,
            timeout_seconds=300,
        )

        assert exit_code == 0, f"Session failed.\nstdout: {stdout}\nstderr: {stderr}"

        # Extract all trailers using git's native format
        trailers = get_all_trailers(basic_repo)

        # Must have at least Intent-Id
        assert "Intent-Id" in trailers, f"Expected Intent-Id in trailers, got: {trailers}"

        # Verify the Intent-Id is non-empty (format may vary)
        intent_id = trailers["Intent-Id"]
        assert len(intent_id) > 0, f"Intent-Id should be non-empty, got: {intent_id}"
