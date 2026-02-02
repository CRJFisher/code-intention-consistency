#!/usr/bin/env python3
"""Stop hook for auto-fixing lint issues before committing.

Parses the transcript to find all edited Python files and runs
ruff check --fix on each.

Always returns 0 (non-blocking, informational).
"""

import json
import subprocess
import sys
from pathlib import Path


def extract_python_files(transcript: list[dict]) -> set[str]:
    """Extract Python file paths from Edit/Write tool uses in transcript."""
    python_files: set[str] = set()

    for message in transcript:
        # Look for assistant messages with tool use
        if message.get("role") != "assistant":
            continue

        content = message.get("content", [])
        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict):
                continue

            if block.get("type") != "tool_use":
                continue

            tool_name = block.get("name", "")
            if tool_name not in ("Edit", "Write"):
                continue

            tool_input = block.get("input", {})
            file_path = tool_input.get("file_path", "")

            if file_path.endswith(".py") and Path(file_path).exists():
                python_files.add(file_path)

    return python_files


def main() -> int:
    """Auto-fix lint issues in all edited Python files."""
    # Read transcript from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    transcript = hook_input.get("transcript", [])
    if not transcript:
        return 0

    python_files = extract_python_files(transcript)
    if not python_files:
        return 0

    print(f"[ruff fix] Auto-fixing {len(python_files)} Python file(s)...", file=sys.stderr)

    for file_path in sorted(python_files):
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "--fix", file_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[ruff fix] {file_path}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
        else:
            print(f"[ruff fix] {file_path} - OK", file=sys.stderr)

    # Always return 0 (non-blocking)
    return 0


if __name__ == "__main__":
    sys.exit(main())
