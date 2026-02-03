"""
PlanVerification model for pre-implementation plan coherence checking.

Based on LPW (Language-Model-Powered Workflow) research insight:
Verify plans *before* coding to catch issues early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class VerificationIssueType(Enum):
    """Type of verification issue detected."""

    CODE_HOME_CONFLICT = "code_home_conflict"  # Intentions conflict with code_home boundaries
    MISSING_EVIDENCE = "missing_evidence"  # Leaf intention lacks evidence tests
    ORPHAN_INTENTION = "orphan_intention"  # Intention without clear parent chain
    CIRCULAR_DEPENDENCY = "circular_dependency"  # Intent references create a cycle
    SCOPE_OVERLAP = "scope_overlap"  # Multiple intentions claim same code_home
    PATTERN_MISMATCH = "pattern_mismatch"  # Intention doesn't match codebase patterns
    CONFIDENCE_LOW = "confidence_low"  # Intent confidence below threshold


class VerificationSeverity(Enum):
    """Severity level of a verification issue."""

    ERROR = "error"  # Must be fixed before proceeding
    WARNING = "warning"  # Should be reviewed but can proceed
    INFO = "info"  # Informational, no action required


@dataclass
class VerificationIssue:
    """A single issue found during plan verification."""

    type: VerificationIssueType
    severity: VerificationSeverity
    intent_id: str  # Intention that has the issue
    message: str  # Human-readable description

    # Optional context
    related_intent_ids: list[str] = field(default_factory=list)
    conflicting_paths: list[str] = field(default_factory=list)
    suggested_fix: str | None = None
    details: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> VerificationIssue:
        """Create a VerificationIssue from a dictionary."""
        return cls(
            type=VerificationIssueType(data["type"]),
            severity=VerificationSeverity(data["severity"]),
            intent_id=data["intent_id"],
            message=data["message"],
            related_intent_ids=data.get("related_intent_ids", []),
            conflicting_paths=data.get("conflicting_paths", []),
            suggested_fix=data.get("suggested_fix"),
            details=data.get("details"),
        )

    def to_dict(self) -> dict:
        """Convert VerificationIssue to a dictionary for serialization."""
        result: dict = {
            "type": self.type.value,
            "severity": self.severity.value,
            "intent_id": self.intent_id,
            "message": self.message,
        }

        if self.related_intent_ids:
            result["related_intent_ids"] = self.related_intent_ids
        if self.conflicting_paths:
            result["conflicting_paths"] = self.conflicting_paths
        if self.suggested_fix:
            result["suggested_fix"] = self.suggested_fix
        if self.details:
            result["details"] = self.details

        return result


@dataclass
class PlanVerification:
    """
    Result of plan verification before implementation.

    Based on LPW research: verify plan coherence before coding.
    """

    passed: bool  # True if no errors (warnings allowed)
    issues: list[VerificationIssue] = field(default_factory=list)

    # Summary statistics
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    # Verification context
    intentions_checked: int = 0
    code_homes_validated: int = 0
    evidence_tests_found: int = 0

    # Optional override
    override_rationale: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> PlanVerification:
        """Create a PlanVerification from a dictionary."""
        issues_data = data.get("issues", [])
        issues = [VerificationIssue.from_dict(issue) for issue in issues_data]

        return cls(
            passed=data["passed"],
            issues=issues,
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            info_count=data.get("info_count", 0),
            intentions_checked=data.get("intentions_checked", 0),
            code_homes_validated=data.get("code_homes_validated", 0),
            evidence_tests_found=data.get("evidence_tests_found", 0),
            override_rationale=data.get("override_rationale"),
        )

    def to_dict(self) -> dict:
        """Convert PlanVerification to a dictionary for serialization."""
        result: dict = {
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "intentions_checked": self.intentions_checked,
            "code_homes_validated": self.code_homes_validated,
            "evidence_tests_found": self.evidence_tests_found,
        }

        if self.override_rationale:
            result["override_rationale"] = self.override_rationale

        return result

    @classmethod
    def load(cls, path) -> PlanVerification:
        """Load PlanVerification from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == VerificationSeverity.ERROR for issue in self.issues)

    def get_errors(self) -> list[VerificationIssue]:
        """Get all error-level issues."""
        return [issue for issue in self.issues if issue.severity == VerificationSeverity.ERROR]

    def get_warnings(self) -> list[VerificationIssue]:
        """Get all warning-level issues."""
        return [issue for issue in self.issues if issue.severity == VerificationSeverity.WARNING]
