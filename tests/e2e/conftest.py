"""
E2E test fixtures for sample repository setup and product artifact installation.

These fixtures handle:
- Creating temporary copies of sample repos with git initialized
- Installing PRODUCT artifacts (hooks, agents) into sample repos
- Setting up .intent_audit/ runtime state directory
- Running claude -p sessions for true E2E tests
- Cleanup after tests complete
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.output_capture import copy_artifacts, create_output_dir, save_component
from tests.e2e.setup_intent_audit import cleanup_intent_audit_dir, setup_intent_audit_dir


def compute_diff_hash(repo_path: Path) -> str:
    """
    Compute diff hash matching stop_hook._compute_diff_hash().

    Combines git diff HEAD (staged + unstaged changes) and git status
    (to capture untracked files) into a deterministic hash.

    Args:
        repo_path: Path to the git repository.

    Returns:
        16-character hex string (truncated SHA-256).
    """
    # Get diff of all changes (staged and unstaged) against HEAD
    diff_result = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    diff_output = diff_result.stdout

    # Get status to capture untracked files (which don't appear in diff)
    status_result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    status_output = status_result.stdout

    # Combine and hash (same as stop_hook)
    combined = f"{diff_output}\n---STATUS---\n{status_output}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def run_stop_hook(
    repo_path: Path, session_id: str, project_root: Path
) -> tuple[int, str, str]:
    """
    Run stop hook as subprocess, return (exit_code, stdout, stderr).

    Args:
        repo_path: Path to the repository.
        session_id: Session ID to pass to the hook.
        project_root: Path to the project root (for finding the hook).

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    hook_path = project_root / "src" / "intention_audit" / "hooks" / "stop_hook.py"

    # Prepare hook input JSON (what Claude Code would send)
    hook_input = json.dumps({
        "session_id": session_id,
        "cwd": str(repo_path),
    })

    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(repo_path)

    result = subprocess.run(
        ["python", str(hook_path)],
        cwd=str(repo_path),
        input=hook_input,
        capture_output=True,
        text=True,
        env=env,
    )

    return result.returncode, result.stdout, result.stderr


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

        # Copy agent definitions (markdown format with YAML frontmatter)
        agents_src_dir = product_src_path / "agents"
        if agents_src_dir.exists():
            for md_file in agents_src_dir.glob("*.md"):
                shutil.copy(md_file, claude_agents_dir / md_file.name)

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


def run_mcp_tool(tool_name: str, repo_path: Path, **kwargs: Any) -> dict[str, Any]:
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


def setup_claude_config(
    repo_path: Path,
    project_root: Path,
) -> Path:
    """
    Set up MCP config and hook settings for a test repository.

    Args:
        repo_path: Path to the test repository.
        project_root: Path to the project root (for finding MCP server and hooks).

    Returns:
        Path to the created MCP config file.
    """
    # Create MCP config for this test
    mcp_config = {
        "mcpServers": {
            "intention-audit": {
                "command": "python",
                "args": [str(project_root / "mcp_servers" / "intention_audit" / "server.py")],
            }
        }
    }
    mcp_config_path = repo_path / ".mcp.json"
    mcp_config_path.write_text(json.dumps(mcp_config, indent=2))

    # Configure hooks in test repo using correct format
    # Hooks need to be nested: hooks.Stop[].hooks[].command
    claude_dir = repo_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    settings = {
        "hooks": {
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python {project_root}/src/intention_audit/hooks/stop_hook.py"
                        }
                    ]
                }
            ]
        }
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    # Copy agent definitions
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    source_agents_dir = project_root / "src" / "intention_audit" / "agents"
    if source_agents_dir.exists():
        for md_file in source_agents_dir.glob("*.md"):
            shutil.copy(md_file, agents_dir / md_file.name)

    return mcp_config_path


def _extract_session_id(stream_output: str) -> str | None:
    """Extract session ID from stream-json output."""
    for line in stream_output.strip().split("\n"):
        try:
            event = json.loads(line)
            # session_id appears in init, assistant, and result events
            session_id = event.get("session_id")
            if session_id:
                return session_id
        except json.JSONDecodeError:
            continue
    return None


def _extract_mcp_calls(transcript_path: Path) -> list[dict[str, Any]]:
    """
    Extract all MCP tool calls from a transcript file.

    Args:
        transcript_path: Path to the JSONL transcript file.

    Returns:
        List of MCP call dictionaries with tool name, input, and result.
    """
    mcp_calls: list[dict[str, Any]] = []
    pending_calls: dict[str, dict[str, Any]] = {}  # tool_use_id -> call data

    if not transcript_path.exists():
        return mcp_calls

    with open(transcript_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                entry_type = entry.get("type", "")
                timestamp = entry.get("timestamp", "")

                # Look for MCP tool_use in assistant entries
                if entry_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                if tool_name.startswith("mcp__"):
                                    tool_use_id = item.get("id", "")
                                    call_data = {
                                        "tool_name": tool_name,
                                        "input": item.get("input", {}),
                                        "timestamp": timestamp,
                                        "result": None,
                                        "is_error": False,
                                    }
                                    if tool_use_id:
                                        pending_calls[tool_use_id] = call_data
                                    mcp_calls.append(call_data)

                # Look for tool results in user entries
                elif entry_type == "user":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if item.get("type") == "tool_result":
                                tool_use_id = item.get("tool_use_id", "")
                                if tool_use_id in pending_calls:
                                    pending_calls[tool_use_id]["result"] = item.get(
                                        "content", ""
                                    )
                                    pending_calls[tool_use_id]["is_error"] = item.get(
                                        "is_error", False
                                    )

            except json.JSONDecodeError:
                continue

    return mcp_calls


def _extract_hook_output(stream_output: str) -> str:
    """
    Extract hook stdout/stderr from stream-json output.

    Args:
        stream_output: Raw stream-json output from claude session.

    Returns:
        Combined hook output text.
    """
    hook_output_lines: list[str] = []

    for line in stream_output.strip().split("\n"):
        try:
            event = json.loads(line)
            event_type = event.get("type", "")

            # Hook progress events contain output
            if event_type == "progress":
                data = event.get("data", {})
                progress_type = data.get("type", "")
                if progress_type == "hook_progress":
                    hook_name = data.get("hookName", "")
                    output = data.get("output", "") or data.get("fullOutput", "")
                    stderr = data.get("stderr", "")
                    if output or stderr:
                        hook_output_lines.append(f"=== [{hook_name}] ===")
                        if output:
                            hook_output_lines.append(f"stdout:\n{output}")
                        if stderr:
                            hook_output_lines.append(f"stderr:\n{stderr}")
                        hook_output_lines.append("")

            # System events may contain hook summaries
            elif event_type == "system":
                subtype = event.get("subtype", "")
                if subtype == "stop_hook_summary":
                    prevented = event.get("preventedContinuation", False)
                    hook_infos = event.get("hookInfos", [])
                    hook_output_lines.append("=== [Stop Hook Summary] ===")
                    hook_output_lines.append(f"Prevented continuation: {prevented}")
                    for info in hook_infos:
                        command = info.get("command", "")
                        exit_code = info.get("exitCode", 0)
                        stdout = info.get("stdout", "")
                        stderr = info.get("stderr", "")
                        hook_output_lines.append(f"Command: {command}")
                        hook_output_lines.append(f"Exit code: {exit_code}")
                        if stdout:
                            hook_output_lines.append(f"stdout:\n{stdout}")
                        if stderr:
                            hook_output_lines.append(f"stderr:\n{stderr}")
                    hook_output_lines.append("")

        except json.JSONDecodeError:
            continue

    return "\n".join(hook_output_lines)


def _capture_git_state(repo_path: Path) -> tuple[str, str]:
    """
    Capture git log and git status output.

    Args:
        repo_path: Path to the repository.

    Returns:
        Tuple of (git_log_output, git_status_output).
    """
    # Get git log with commit messages and trailers
    log_result = subprocess.run(
        ["git", "log", "--oneline", "-20", "--format=fuller"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    git_log = log_result.stdout if log_result.returncode == 0 else log_result.stderr

    # Get git status
    status_result = subprocess.run(
        ["git", "status", "--porcelain=v2", "--branch"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    git_status = (
        status_result.stdout if status_result.returncode == 0 else status_result.stderr
    )

    return git_log, git_status


def _copy_transcript_files(
    output_dir: Path,
    repo_path: Path,
    session_id: str,
) -> None:
    """
    Copy main and subagent transcript files to output directory.

    Args:
        output_dir: Directory to save files to.
        repo_path: Path to the test repository.
        session_id: Session ID for finding transcripts.
    """
    from tests.e2e.transcript_compiler import (
        get_session_transcript_path,
        get_subagent_transcripts,
    )

    # Copy main transcript
    main_transcript = get_session_transcript_path(session_id, repo_path)
    if main_transcript and main_transcript.exists():
        shutil.copy2(main_transcript, output_dir / "main-transcript.jsonl")

    # Copy subagent transcripts
    subagent_paths = get_subagent_transcripts(session_id, repo_path)
    for agent_id, agent_path in subagent_paths.items():
        if agent_path.exists():
            shutil.copy2(agent_path, output_dir / f"subagent-{agent_id}.jsonl")


def _extract_final_result(stream_output: str) -> str:
    """Extract the final assistant text from stream-json output."""
    final_text = ""
    for line in stream_output.strip().split("\n"):
        try:
            event = json.loads(line)
            if event.get("type") == "assistant":
                message = event.get("message", {})
                content = message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            final_text = item.get("text", "")
        except json.JSONDecodeError:
            continue
    return final_text


def run_claude_session(
    repo_path: Path,
    prompt: str,
    project_root: Path,
    timeout_seconds: int = 180,
    model: str = "haiku",
    test_name: str | None = None,
    output_dir: Path | None = None,
) -> tuple[int, str, str, Path | None]:
    """
    Run a claude -p session with intention audit configured.

    This function sets up the MCP server, hooks, and agent definitions,
    then runs claude -p with the given prompt.

    After session completion, captures component-level outputs:
    - main-transcript.jsonl: Raw main agent data
    - subagent-<id>.jsonl: Sub-agent transcripts
    - hook-output.txt: Stop hook stdout/stderr
    - mcp-calls.json: All MCP tool calls with payloads
    - artifacts/*.yaml: Generated intentions/plans from .intent_audit/
    - git-log.txt: Git history after test
    - git-status.txt: Final repo state

    Args:
        repo_path: Path to the test repository.
        prompt: The prompt to send to Claude.
        project_root: Path to the project root (for finding MCP server and hooks).
        timeout_seconds: Maximum time to wait for the session to complete.
        model: Model to use (default: haiku for cost efficiency).
        test_name: Name of the test (for transcript output).
        output_dir: Base directory for outputs (will create timestamped subdir).

    Returns:
        Tuple of (exit_code, stdout, stderr, component_output_dir).
    """
    # Set up MCP config and hooks
    mcp_config_path = setup_claude_config(repo_path, project_root)

    # Ensure internal directories are in .gitignore
    gitignore_path = repo_path / ".gitignore"
    gitignore_content = ""
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()

    additions = []
    for pattern in [".intent_audit/", ".claude/", ".mcp.json"]:
        if pattern not in gitignore_content:
            additions.append(pattern)

    if additions:
        with open(gitignore_path, "a") as f:
            if not gitignore_content.endswith("\n") and gitignore_content:
                f.write("\n")
            for pattern in additions:
                f.write(f"{pattern}\n")
        # Stage the .gitignore change so it doesn't interfere
        subprocess.run(
            ["git", "add", ".gitignore"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: add internal paths to .gitignore"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )

    # Run claude -p with stream-json for structured output
    result = subprocess.run(
        [
            "claude",
            "-p",
            "--model",
            model,
            "--mcp-config",
            str(mcp_config_path),
            "--permission-mode",
            "bypassPermissions",
            "--output-format",
            "stream-json",
            "--verbose",
            prompt,
        ],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )

    # Capture component-level outputs
    component_output_dir = None
    if output_dir and test_name:
        session_id = _extract_session_id(result.stdout)

        # Create timestamped output directory using output_capture module
        component_output_dir = create_output_dir(test_name, output_dir)

        if session_id:
            # 1. Copy main and subagent transcript files
            _copy_transcript_files(component_output_dir, repo_path, session_id)

            # 2. Extract MCP calls from main transcript
            from tests.e2e.transcript_compiler import get_session_transcript_path

            main_transcript = get_session_transcript_path(session_id, repo_path)
            if main_transcript and main_transcript.exists():
                mcp_calls = _extract_mcp_calls(main_transcript)
                save_component(
                    component_output_dir,
                    "mcp-calls.json",
                    json.dumps(mcp_calls, indent=2),
                )

            # 3. Compile readable markdown transcript
            from tests.e2e.transcript_compiler import TranscriptCompiler

            compiler = TranscriptCompiler(test_name, component_output_dir)
            compiler.compile_session(repo_path, session_id)
            compiler.save()

        # 4. Capture hook output from stream
        hook_output = _extract_hook_output(result.stdout)
        if hook_output:
            save_component(component_output_dir, "hook-output.txt", hook_output)

        # 5. Copy artifacts from .intent_audit/ directory
        intent_audit_dir = repo_path / ".intent_audit"
        copy_artifacts(component_output_dir, intent_audit_dir)

        # 6. Capture git state (log and status)
        git_log, git_status = _capture_git_state(repo_path)
        save_component(component_output_dir, "git-log.txt", git_log)
        save_component(component_output_dir, "git-status.txt", git_status)

    # Extract final result text for backwards compatibility
    final_text = _extract_final_result(result.stdout)

    return result.returncode, final_text, result.stderr, component_output_dir


@pytest.fixture
def claude_session_runner(project_root: Path, request) -> callable:
    """
    Factory fixture that returns a function to run claude -p sessions.

    Automatically captures component-level outputs to tests/e2e/outputs/<test>/<timestamp>/:
    - main-transcript.jsonl: Raw main agent data
    - subagent-<id>.jsonl: Sub-agent transcripts
    - hook-output.txt: Stop hook stdout/stderr
    - mcp-calls.json: All MCP tool calls with payloads
    - artifacts/*.yaml: Generated intentions/plans
    - git-log.txt: Git history after test
    - git-status.txt: Final repo state

    Usage:
        def test_something(basic_repo, claude_session_runner):
            exit_code, stdout, stderr = claude_session_runner(
                basic_repo,
                "Create a file and stop",
            )
    """
    output_dir = project_root / "tests" / "e2e" / "outputs"

    def _run(
        repo_path: Path,
        prompt: str,
        timeout_seconds: int = 180,
        model: str = "haiku",
    ) -> tuple[int, str, str]:
        test_name = request.node.name

        exit_code, stdout, stderr, component_output_dir = run_claude_session(
            repo_path=repo_path,
            prompt=prompt,
            project_root=project_root,
            timeout_seconds=timeout_seconds,
            model=model,
            test_name=test_name,
            output_dir=output_dir,
        )

        if component_output_dir:
            print(f"\nComponent outputs: {component_output_dir}")

        return exit_code, stdout, stderr

    return _run
