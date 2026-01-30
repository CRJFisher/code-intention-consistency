"""
E2E test fixtures for sample repository setup and product artifact installation.

These fixtures handle:
- Creating temporary copies of sample repos with git initialized
- Installing PRODUCT artifacts (hooks, agents) into sample repos
- Setting up .intent_audit/ runtime state directory
- Cleanup after tests complete
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from tests.e2e.setup_intent_audit import cleanup_intent_audit_dir, setup_intent_audit_dir


@pytest.fixture
def basic_repo(sample_repos_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary copy of basic_repo with git initialized.

    Yields the path to the temporary repo, then cleans up.
    """
    source = sample_repos_path / "basic_repo"
    if not source.exists():
        pytest.skip("basic_repo fixture not populated yet")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "basic_repo"
        shutil.copytree(source, repo_path)

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path

        # Cleanup is automatic with TemporaryDirectory


@pytest.fixture
def demo_repo(sample_repos_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary copy of demo_repo with git initialized.

    Yields the path to the temporary repo, then cleans up.
    """
    source = sample_repos_path / "demo_repo"
    if not source.exists():
        pytest.skip("demo_repo fixture not populated yet")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "demo_repo"
        shutil.copytree(source, repo_path)

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def install_product_artifacts(product_src_path: Path) -> callable:
    """
    Factory fixture that installs PRODUCT artifacts into a sample repo.

    Returns a function that can be called with a repo path to install:
    - src/intention_audit/hooks/stop_hook.py → .claude/hooks/
    - src/intention_audit/agents/*.yaml → .claude/agents/
    - Creates .intent_audit/ directory structure
    """

    def _install(repo_path: Path) -> None:
        # Create .claude directories
        claude_hooks_dir = repo_path / ".claude" / "hooks"
        claude_agents_dir = repo_path / ".claude" / "agents"
        claude_hooks_dir.mkdir(parents=True, exist_ok=True)
        claude_agents_dir.mkdir(parents=True, exist_ok=True)

        # Copy stop hook
        stop_hook_src = product_src_path / "hooks" / "stop_hook.py"
        if stop_hook_src.exists():
            shutil.copy(stop_hook_src, claude_hooks_dir / "stop_hook.py")

        # Copy agent definitions
        agents_src_dir = product_src_path / "agents"
        if agents_src_dir.exists():
            for yaml_file in agents_src_dir.glob("*.yaml"):
                shutil.copy(yaml_file, claude_agents_dir / yaml_file.name)

        # Setup .intent_audit/ directory
        setup_intent_audit_dir(repo_path)

    return _install


@pytest.fixture
def cleanup_sample_repo() -> callable:
    """
    Factory fixture that cleans up runtime state from a sample repo.

    Returns a function that removes:
    - .git/
    - .claude/
    - .intent_audit/
    """

    def _cleanup(repo_path: Path) -> None:
        git_dir = repo_path / ".git"
        claude_dir = repo_path / ".claude"

        if git_dir.exists():
            shutil.rmtree(git_dir)
        if claude_dir.exists():
            shutil.rmtree(claude_dir)
        cleanup_intent_audit_dir(repo_path)

    return _cleanup


def run_mcp_tool(tool_name: str, repo_path: Path, **kwargs) -> dict:
    """
    Helper to call real MCP tools for E2E testing.

    This simulates what sub-agents would do when calling MCP tools.
    For now, returns a placeholder - will be implemented when MCP tools exist.

    Args:
        tool_name: Name of the MCP tool (e.g., "map_intentions")
        repo_path: Path to the repository
        **kwargs: Tool-specific arguments

    Returns:
        Tool result as a dictionary
    """
    # Placeholder - will be implemented in Phase 3+
    raise NotImplementedError(f"MCP tool {tool_name} not yet implemented")
