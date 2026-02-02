#!/usr/bin/env python3
"""PostToolUse hook for immediate linting and type checking feedback.

Runs after Edit or Write tool on Python files:
- ruff format (check only)
- ruff check (lint check, no fix)
- pyright (type check)
- mypy (type check)

Exit code 2 blocks further execution on errors.
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run linting and type checking on edited Python files."""
    # Read tool input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    # Extract file path from tool input
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path")

    if not file_path:
        return 0

    # Only process Python files
    if not file_path.endswith(".py"):
        return 0

    # Verify file exists
    if not Path(file_path).exists():
        return 0

    has_errors = False

    # Run ruff format check
    result = subprocess.run(
        ["uv", "run", "ruff", "format", "--check", file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ruff format] {file_path}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        has_errors = True

    # Run ruff check (no fix, to avoid removing imports during dev)
    result = subprocess.run(
        ["uv", "run", "ruff", "check", file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ruff check] {file_path}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        has_errors = True

    # Run pyright
    result = subprocess.run(
        ["uv", "run", "pyright", file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[pyright] {file_path}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        has_errors = True

    # Run mypy
    result = subprocess.run(
        ["uv", "run", "mypy", file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[mypy] {file_path}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        has_errors = True

    # Exit code 2 blocks on errors
    return 2 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
