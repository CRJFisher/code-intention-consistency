"""
ConfidenceValidation model for confidence-tiered validation.

Based on research insight: LLM confidence calibration matters.
Low-confidence mappings need extra scrutiny.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ConfidenceTier(Enum):
    """Tier of confidence for validation requirements."""

    HIGH = "high"  # >0.8: Standard validation
    MEDIUM = "medium"  # 0.5-0.8: Require additional evidence
    LOW = "low"  # <0.5: Require human confirmation


class ValidationRequirement(Enum):
    """What validation is required based on confidence."""

    STANDARD = "standard"  # Normal validation flow
    ADDITIONAL_EVIDENCE = "additional_evidence"  # Need more tests
    HUMAN_CONFIRMATION = "human_confirmation"  # Must confirm manually


@dataclass
class ConfidenceThresholds:
    """Configurable confidence thresholds."""

    high_threshold: float = 0.8  # Above this is high confidence
    medium_threshold: float = 0.5  # Above this is medium, below is low

    @classmethod
    def from_dict(cls, data: dict) -> ConfidenceThresholds:
        """Create ConfidenceThresholds from a dictionary."""
        return cls(
            high_threshold=data.get("high_threshold", 0.8),
            medium_threshold=data.get("medium_threshold", 0.5),
        )

    def to_dict(self) -> dict:
        """Convert ConfidenceThresholds to a dictionary."""
        return {
            "high_threshold": self.high_threshold,
            "medium_threshold": self.medium_threshold,
        }

    def get_tier(self, confidence: float) -> ConfidenceTier:
        """Determine the confidence tier for a given score."""
        if confidence >= self.high_threshold:
            return ConfidenceTier.HIGH
        elif confidence >= self.medium_threshold:
            return ConfidenceTier.MEDIUM
        else:
            return ConfidenceTier.LOW

    def get_requirement(self, confidence: float) -> ValidationRequirement:
        """Determine validation requirement for a given confidence."""
        tier = self.get_tier(confidence)
        if tier == ConfidenceTier.HIGH:
            return ValidationRequirement.STANDARD
        elif tier == ConfidenceTier.MEDIUM:
            return ValidationRequirement.ADDITIONAL_EVIDENCE
        else:
            return ValidationRequirement.HUMAN_CONFIRMATION


@dataclass
class IntentionConfidenceCheck:
    """Result of checking confidence for a single intention."""

    intent_id: str
    confidence: float
    tier: ConfidenceTier
    requirement: ValidationRequirement

    # Evidence status
    has_evidence_tests: bool = False
    evidence_tests_passed: bool | None = None  # None if not run

    # Human confirmation
    human_confirmed: bool = False
    confirmation_rationale: str | None = None

    # Computed result
    passed: bool = False
    message: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> IntentionConfidenceCheck:
        """Create an IntentionConfidenceCheck from a dictionary."""
        return cls(
            intent_id=data["intent_id"],
            confidence=data["confidence"],
            tier=ConfidenceTier(data["tier"]),
            requirement=ValidationRequirement(data["requirement"]),
            has_evidence_tests=data.get("has_evidence_tests", False),
            evidence_tests_passed=data.get("evidence_tests_passed"),
            human_confirmed=data.get("human_confirmed", False),
            confirmation_rationale=data.get("confirmation_rationale"),
            passed=data.get("passed", False),
            message=data.get("message", ""),
        )

    def to_dict(self) -> dict:
        """Convert IntentionConfidenceCheck to a dictionary."""
        result: dict = {
            "intent_id": self.intent_id,
            "confidence": self.confidence,
            "tier": self.tier.value,
            "requirement": self.requirement.value,
            "has_evidence_tests": self.has_evidence_tests,
            "passed": self.passed,
            "message": self.message,
        }

        if self.evidence_tests_passed is not None:
            result["evidence_tests_passed"] = self.evidence_tests_passed
        if self.human_confirmed:
            result["human_confirmed"] = self.human_confirmed
        if self.confirmation_rationale:
            result["confirmation_rationale"] = self.confirmation_rationale

        return result


@dataclass
class ConfidenceValidationResult:
    """Complete result of confidence-based validation."""

    # Summary
    passed: bool
    total_checked: int = 0
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0

    # Detailed checks
    checks: list[IntentionConfidenceCheck] = field(default_factory=list)

    # Thresholds used
    thresholds: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)

    # Failures
    needs_additional_evidence: list[str] = field(default_factory=list)  # intent_ids
    needs_human_confirmation: list[str] = field(default_factory=list)  # intent_ids

    # Override
    override_rationale: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ConfidenceValidationResult:
        """Create a ConfidenceValidationResult from a dictionary."""
        checks_data = data.get("checks", [])
        checks = [IntentionConfidenceCheck.from_dict(c) for c in checks_data]

        thresholds_data = data.get("thresholds", {})
        thresholds = ConfidenceThresholds.from_dict(thresholds_data)

        return cls(
            passed=data["passed"],
            total_checked=data.get("total_checked", 0),
            high_confidence_count=data.get("high_confidence_count", 0),
            medium_confidence_count=data.get("medium_confidence_count", 0),
            low_confidence_count=data.get("low_confidence_count", 0),
            checks=checks,
            thresholds=thresholds,
            needs_additional_evidence=data.get("needs_additional_evidence", []),
            needs_human_confirmation=data.get("needs_human_confirmation", []),
            override_rationale=data.get("override_rationale"),
        )

    def to_dict(self) -> dict:
        """Convert ConfidenceValidationResult to a dictionary."""
        result: dict = {
            "passed": self.passed,
            "total_checked": self.total_checked,
            "high_confidence_count": self.high_confidence_count,
            "medium_confidence_count": self.medium_confidence_count,
            "low_confidence_count": self.low_confidence_count,
            "checks": [c.to_dict() for c in self.checks],
            "thresholds": self.thresholds.to_dict(),
        }

        if self.needs_additional_evidence:
            result["needs_additional_evidence"] = self.needs_additional_evidence
        if self.needs_human_confirmation:
            result["needs_human_confirmation"] = self.needs_human_confirmation
        if self.override_rationale:
            result["override_rationale"] = self.override_rationale

        return result

    @classmethod
    def load(cls, path) -> ConfidenceValidationResult:
        """Load ConfidenceValidationResult from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def get_failing_checks(self) -> list[IntentionConfidenceCheck]:
        """Get all checks that failed."""
        return [c for c in self.checks if not c.passed]

    def get_checks_by_tier(self, tier: ConfidenceTier) -> list[IntentionConfidenceCheck]:
        """Get all checks for a specific tier."""
        return [c for c in self.checks if c.tier == tier]

    def has_blocking_issues(self) -> bool:
        """Check if there are blocking confidence issues."""
        if self.override_rationale:
            return False
        return bool(self.needs_human_confirmation) or bool(self.needs_additional_evidence)

    def get_average_confidence(self) -> float:
        """Calculate average confidence across all checks."""
        if not self.checks:
            return 0.0
        return sum(c.confidence for c in self.checks) / len(self.checks)
