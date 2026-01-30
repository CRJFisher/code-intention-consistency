"""
Git diff utilities for parsing changed paths and retrieving diffs.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


def get_changed_paths(project_dir: Path) -> list[str]:
    """
    Get list of all changed files in the working directory.

    Uses `git status --porcelain=v1` to get changes.
    Includes staged, unstaged, and untracked files.

    Args:
        project_dir: Path to the git repository root.

    Returns:
        List of changed file paths (relative to project_dir).
    """
    result = _run_git(project_dir, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr}")

    return _parse_porcelain_status(result.stdout)


def get_staged_paths(project_dir: Path) -> list[str]:
    """
    Get list of staged files.

    Uses `git diff --cached --name-only` to get staged changes.

    Args:
        project_dir: Path to the git repository root.

    Returns:
        List of staged file paths (relative to project_dir).
    """
    result = _run_git(project_dir, ["diff", "--cached", "--name-only", "-z"])
    if result.returncode != 0:
        raise RuntimeError(f"git diff --cached failed: {result.stderr}")

    return [p for p in result.stdout.split("\0") if p]


def get_unified_diff(project_dir: Path, base: str = "HEAD") -> str:
    """
    Get the full unified diff from base to working directory.

    Includes both staged and unstaged changes.

    Args:
        project_dir: Path to the git repository root.
        base: Base reference (default: "HEAD").

    Returns:
        Unified diff as a string.
    """
    # Get unstaged changes
    result_unstaged = _run_git(project_dir, ["diff", base])
    if result_unstaged.returncode != 0:
        raise RuntimeError(f"git diff failed: {result_unstaged.stderr}")

    # Get staged changes
    result_staged = _run_git(project_dir, ["diff", "--cached", base])
    if result_staged.returncode != 0:
        raise RuntimeError(f"git diff --cached failed: {result_staged.stderr}")

    # Combine (staged changes first, then unstaged)
    parts = []
    if result_staged.stdout.strip():
        parts.append(result_staged.stdout)
    if result_unstaged.stdout.strip():
        parts.append(result_unstaged.stdout)

    return "\n".join(parts)


def _run_git(project_dir: Path, args: Sequence[str]) -> subprocess.CompletedProcess:
    """Run a git command in the project directory."""
    return subprocess.run(
        ["git", *args],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
    )


def _parse_porcelain_status(output: str) -> list[str]:
    """
    Parse `git status --porcelain=v1 -z` output into a list of paths.

    For renames/copies, includes both old and new paths.
    """
    items = output.split("\0")
    paths: list[str] = []

    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue

        if len(item) < 4:
            i += 1
            continue

        xy = item[0:2]
        path_1 = item[3:]

        is_rename_or_copy = xy[0] in ("R", "C") or xy[1] in ("R", "C")
        if is_rename_or_copy and i + 1 < len(items):
            path_2 = items[i + 1]
            paths.append(path_1)
            if path_2:
                paths.append(path_2)
            i += 2
            continue

        paths.append(path_1)
        i += 1

    # De-dup while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for p in paths:
        if p not in seen:
            deduped.append(p)
            seen.add(p)
    return deduped
