"""
Evidence results data model for test execution outcomes.

This module defines the data structures for capturing pytest test results
as part of the intention audit evidence checking workflow.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class EvidenceResult:
    """Result from a single evidence test."""

    selector: str
    """Test selector (e.g., 'tests/test_foo.py::test_bar')."""

    passed: bool
    """Whether the test passed."""

    output: str = ""
    """Test output (stdout/stderr/assertion message)."""

    duration: float = 0.0
    """Test duration in seconds."""

    error_message: str | None = None
    """Error message if test errored (not failed)."""


@dataclass
class EvidenceResults:
    """Aggregated results from running all evidence tests."""

    results: list[EvidenceResult] = field(default_factory=list)
    """Individual test results."""

    all_passed: bool = True
    """Whether all tests passed."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    """When the tests were run."""

    raw_output: str = ""
    """Full raw output from pytest."""

    @property
    def passed(self) -> list[EvidenceResult]:
        """Get all passed tests."""
        return [r for r in self.results if r.passed]

    @property
    def failed(self) -> list[EvidenceResult]:
        """Get all failed tests (assertion failures)."""
        return [r for r in self.results if not r.passed and r.error_message is None]

    @property
    def errors(self) -> list[EvidenceResult]:
        """Get all errored tests (exceptions, not assertions)."""
        return [r for r in self.results if not r.passed and r.error_message is not None]

    @property
    def summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total": len(self.results),
            "passed": len(self.passed),
            "failed": len(self.failed),
            "errors": len(self.errors),
            "all_passed": self.all_passed,
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "results": [asdict(r) for r in self.results],
            "all_passed": self.all_passed,
            "timestamp": self.timestamp,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceResults:
        """Create from dictionary."""
        results = [
            EvidenceResult(
                selector=r["selector"],
                passed=r["passed"],
                output=r.get("output", ""),
                duration=r.get("duration", 0.0),
                error_message=r.get("error_message"),
            )
            for r in data.get("results", [])
        ]
        return cls(
            results=results,
            all_passed=data.get("all_passed", True),
            timestamp=data.get("timestamp", ""),
            raw_output=data.get("raw_output", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> EvidenceResults:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, path: Path) -> EvidenceResults:
        """Load from a JSON file."""
        return cls.from_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        """Save to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
