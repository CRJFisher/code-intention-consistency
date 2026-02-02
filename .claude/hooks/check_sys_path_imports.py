#!/usr/bin/env python3
"""
Hook to block commits containing sys.path manipulation patterns.

Detects:
- sys.path.insert(...)
- sys.path.append(...)
- sys.path += [...]

This hook runs on Stop events to prevent sys.path hacks from being committed.
All packages should be properly configured in pyproject.toml and installed via `uv sync`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Patterns that indicate sys.path manipulation
SYS_PATH_PATTERNS = [
    r"sys\.path\.insert\s*\(",
    r"sys\.path\.append\s*\(",
    r"sys\.path\s*\+=",
    r"sys\.path\s*=\s*\[",
]


def get_staged_python_files() -> list[Path]:
    """Get list of staged Python files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if line and line.endswith(".py"):
            path = Path(line)
            if path.exists():
                files.append(path)
    return files


def get_modified_python_files() -> list[Path]:
    """Get list of modified (uncommitted) Python files."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Format: "XY filename" where X is index status, Y is worktree status
        status = line[:2]
        filename = line[3:]
        # Check if modified or added (not deleted) and is a Python file
        is_modified = status[1] in ("M", "A", "?") or status[0] in ("M", "A")
        if is_modified and filename.endswith(".py"):
            path = Path(filename)
            if path.exists():
                files.append(path)
    return files


def check_file_for_sys_path(filepath: Path) -> list[tuple[int, str]]:
    """
    Check a file for sys.path manipulation patterns.

    Returns list of (line_number, line_content) tuples for violations.
    """
    violations = []
    try:
        content = filepath.read_text()
        for i, line in enumerate(content.split("\n"), 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in SYS_PATH_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, line.strip()))
                    break
    except OSError:
        pass
    return violations


def main() -> int:
    """
    Check for sys.path manipulation in modified/staged files.

    Returns:
        0 if no violations found
        2 if violations found (blocks the commit)
    """
    # Read hook input from stdin (Claude Code hook format)
    try:
        hook_input = json.loads(sys.stdin.read())
        cwd = hook_input.get("cwd", ".")
    except (json.JSONDecodeError, KeyError):
        cwd = "."

    # Change to the working directory
    os.chdir(cwd)

    # Get files to check
    files_to_check = set(get_staged_python_files()) | set(get_modified_python_files())

    all_violations: dict[str, list[tuple[int, str]]] = {}
    for file_path in files_to_check:
        violations = check_file_for_sys_path(file_path)
        if violations:
            all_violations[str(file_path)] = violations

    if not all_violations:
        # No violations - allow
        result: dict[str, Any] = {"continue": True}
        print(json.dumps(result))
        return 0

    # Build error message
    error_lines = [
        "sys.path manipulation detected!",
        "",
        "The following files contain sys.path.insert/append patterns:",
        "",
    ]

    for violation_file, file_violations in all_violations.items():
        error_lines.append(f"  {violation_file}:")
        for line_num, line_content in file_violations:
            error_lines.append(f"    Line {line_num}: {line_content}")
        error_lines.append("")

    error_lines.extend(
        [
            "This project uses proper package configuration. Instead of sys.path manipulation:",
            "",
            "1. Ensure packages are configured in pyproject.toml:",
            "   [tool.hatch.build.targets.wheel]",
            '   packages = ["src/intention_audit", "mcp_servers"]',
            "",
            "2. Run `uv sync` to install packages in development mode",
            "",
            "3. Import directly: `from mcp_servers.intention_audit.tools.X import Y`",
            "",
        ]
    )

    error_message = "\n".join(error_lines)

    # Output in Claude Code hook format
    error_result: dict[str, Any] = {
        "continue": False,
        "message": error_message,
    }
    print(json.dumps(error_result))
    sys.stderr.write(error_message)

    return 2


if __name__ == "__main__":
    sys.exit(main())
