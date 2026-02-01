"""
Structure validation data model for code_home boundary checking.

This module defines the data structures for capturing structure alignment
validation results as part of the intention audit workflow.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class StructureViolation:
    """A single structure validation violation."""

    type: str
    """Type of violation (e.g., 'code_home_boundary', 'missing_code_home')."""

    intent_id: str
    """Intent ID associated with the violation."""

    functionality_intent_id: str | None
    """Functionality intent that defines the boundary (if applicable)."""

    details: dict[str, Any] = field(default_factory=dict)
    """Additional details about the violation."""

    suggested_fix: str = ""
    """Suggested resolution for the violation."""

    violating_paths: list[str] = field(default_factory=list)
    """Paths that violate the boundary (if applicable)."""

    expected_prefixes: list[str] = field(default_factory=list)
    """Expected code_home prefixes (if applicable)."""


@dataclass
class StructureValidation:
    """Complete structure validation results."""

    violations: list[StructureViolation] = field(default_factory=list)
    """List of validation violations found."""

    passed: bool = True
    """Whether validation passed (no violations)."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    """When validation was performed."""

    override_rationale: str | None = None
    """If violations are overridden, the rationale provided."""

    @property
    def summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        violation_types: dict[str, int] = {}
        for v in self.violations:
            violation_types[v.type] = violation_types.get(v.type, 0) + 1

        return {
            "passed": self.passed,
            "total_violations": len(self.violations),
            "violation_types": violation_types,
            "timestamp": self.timestamp,
            "has_override": self.override_rationale is not None,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "violations": [asdict(v) for v in self.violations],
            "passed": self.passed,
            "timestamp": self.timestamp,
            "override_rationale": self.override_rationale,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructureValidation:
        """Create from dictionary."""
        violations = [
            StructureViolation(
                type=v["type"],
                intent_id=v["intent_id"],
                functionality_intent_id=v.get("functionality_intent_id"),
                details=v.get("details", {}),
                suggested_fix=v.get("suggested_fix", ""),
                violating_paths=v.get("violating_paths", []),
                expected_prefixes=v.get("expected_prefixes", []),
            )
            for v in data.get("violations", [])
        ]
        return cls(
            violations=violations,
            passed=data.get("passed", True),
            timestamp=data.get("timestamp", ""),
            override_rationale=data.get("override_rationale"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> StructureValidation:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, path: Path) -> StructureValidation:
        """Load from a JSON file."""
        return cls.from_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        """Save to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
