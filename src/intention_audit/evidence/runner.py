"""
Evidence test runner for running pytest tests and capturing results.

This module executes pytest against specified test selectors and captures
structured results for intention audit validation.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TestOutput:
    """Output from a single test."""

    selector: str
    passed: bool
    output: str
    duration: float


@dataclass
class EvidenceResults:
    """Results from running evidence tests."""

    passed: list[TestOutput] = field(default_factory=list)
    failed: list[TestOutput] = field(default_factory=list)
    errors: list[TestOutput] = field(default_factory=list)
    all_passed: bool = True
    raw_output: str = ""

    @property
    def summary(self) -> dict[str, Any]:
        """Generate summary of test results."""
        return {
            "total": len(self.passed) + len(self.failed) + len(self.errors),
            "passed": len(self.passed),
            "failed": len(self.failed),
            "errors": len(self.errors),
            "all_passed": self.all_passed,
        }


def run_evidence_tests(project_dir: Path, test_selectors: list[str]) -> EvidenceResults:
    """
    Run evidence tests via pytest and capture results.

    Args:
        project_dir: Path to the project directory.
        test_selectors: List of pytest test selectors (e.g., "tests/test_foo.py::test_bar").

    Returns:
        EvidenceResults with pass/fail/error categorization.
    """
    results = EvidenceResults()

    if not test_selectors:
        return results

    # Build pytest command with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # verbose for test names
        "--tb=short",  # short traceback
        "--no-header",  # skip header
        *test_selectors,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        results.raw_output = f"{proc.stdout}\n{proc.stderr}"
        results.all_passed = proc.returncode == 0

        # Parse pytest verbose output for test results
        _parse_pytest_output(proc.stdout, results, test_selectors)

    except subprocess.TimeoutExpired:
        for selector in test_selectors:
            results.errors.append(
                TestOutput(
                    selector=selector,
                    passed=False,
                    output="Test execution timed out",
                    duration=0.0,
                )
            )
        results.all_passed = False

    except Exception as e:
        for selector in test_selectors:
            results.errors.append(
                TestOutput(
                    selector=selector,
                    passed=False,
                    output=f"Error running tests: {e}",
                    duration=0.0,
                )
            )
        results.all_passed = False

    return results


def _parse_pytest_output(
    output: str, results: EvidenceResults, selectors: list[str]
) -> None:
    """Parse pytest verbose output to extract test results."""
    lines = output.split("\n")

    # Track which selectors we've seen results for
    seen: set[str] = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for pytest result lines like:
        # tests/test_foo.py::test_bar PASSED
        # tests/test_foo.py::test_baz FAILED
        for selector in selectors:
            # Check if this line contains results for this selector
            if selector in line or any(
                part in line for part in selector.split("::")
            ):
                if " PASSED" in line:
                    results.passed.append(
                        TestOutput(
                            selector=selector,
                            passed=True,
                            output=line,
                            duration=0.0,
                        )
                    )
                    seen.add(selector)
                elif " FAILED" in line:
                    results.failed.append(
                        TestOutput(
                            selector=selector,
                            passed=False,
                            output=line,
                            duration=0.0,
                        )
                    )
                    seen.add(selector)
                elif " ERROR" in line:
                    results.errors.append(
                        TestOutput(
                            selector=selector,
                            passed=False,
                            output=line,
                            duration=0.0,
                        )
                    )
                    seen.add(selector)

    # Any selectors not seen are treated as errors (test not found, etc.)
    for selector in selectors:
        if selector not in seen:
            results.errors.append(
                TestOutput(
                    selector=selector,
                    passed=False,
                    output=f"Test not found or did not run: {selector}",
                    duration=0.0,
                )
            )
            results.all_passed = False
