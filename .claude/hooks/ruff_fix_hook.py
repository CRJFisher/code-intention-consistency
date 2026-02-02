#!/usr/bin/env python3
"""Stop hook for auto-fixing lint issues and running type checks on all files.

Runs on Stop event:
- ruff check --fix on src/ and tests/
- ruff format on src/ and tests/
- pyright on src/
- mypy on src/

Always returns 0 (non-blocking, informational).
"""

import subprocess
import sys


def run_command(name: str, cmd: list[str]) -> bool:
    """Run a command and print output. Returns True if successful."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{name}] Issues found:", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False
    else:
        print(f"[{name}] OK", file=sys.stderr)
        return True


def main() -> int:
    """Run linting and type checking on all project files."""
    print("[stop hook] Running linting and type checks on all files...", file=sys.stderr)

    # Run ruff fix on src/ and tests/
    run_command("ruff fix src/", ["uv", "run", "ruff", "check", "--fix", "src/"])
    run_command("ruff fix tests/", ["uv", "run", "ruff", "check", "--fix", "tests/"])

    # Run ruff format on src/ and tests/
    run_command("ruff format src/", ["uv", "run", "ruff", "format", "src/"])
    run_command("ruff format tests/", ["uv", "run", "ruff", "format", "tests/"])

    # Run pyright on src/
    run_command("pyright src/", ["uv", "run", "pyright", "src/"])

    # Run mypy on src/
    run_command("mypy src/", ["uv", "run", "mypy", "src/"])

    # Always return 0 (non-blocking)
    return 0


if __name__ == "__main__":
    sys.exit(main())
