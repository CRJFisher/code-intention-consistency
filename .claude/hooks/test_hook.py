#!/usr/bin/env python3
"""Stop hook for running all unit tests.

Runs on Stop event:
- pytest (unit tests only, E2E excluded by default)

Always returns 0 (non-blocking, informational).
"""

import subprocess
import sys


def main() -> int:
    """Run all unit tests."""
    print("[stop hook] Running unit tests...", file=sys.stderr)

    result = subprocess.run(
        ["uv", "run", "pytest", "-v"],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("[pytest] Some tests failed", file=sys.stderr)
    else:
        print("[pytest] All tests passed", file=sys.stderr)

    # Always return 0 (non-blocking)
    return 0


if __name__ == "__main__":
    sys.exit(main())
