"""
AlignmentReport model for bidirectional intent-code comparison.

Based on NeuroSync research insight: Show user's declared intents vs.
system's inferred intents to enable early correction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class AlignmentStatus(Enum):
    """Status of alignment between declared and inferred intents."""

    ALIGNED = "aligned"  # Declared and inferred match
    PARTIAL = "partial"  # Some overlap but not complete
    MISALIGNED = "misaligned"  # Significant divergence
    MISSING_DECLARED = "missing_declared"  # Inferred but not declared
    MISSING_INFERRED = "missing_inferred"  # Declared but not found in code


@dataclass
class IntentComparison:
    """Comparison between a declared and inferred intent."""

    declared_intent_id: str | None  # From intentions.yaml
    inferred_intent_id: str | None  # From code analysis

    declared_title: str | None
    inferred_title: str | None

    status: AlignmentStatus
    confidence: float  # 0.0-1.0 confidence in the comparison

    # File coverage
    declared_files: list[str] = field(default_factory=list)
    inferred_files: list[str] = field(default_factory=list)
    overlapping_files: list[str] = field(default_factory=list)
    extra_files: list[str] = field(default_factory=list)  # In code but not declared
    missing_files: list[str] = field(default_factory=list)  # Declared but not in code

    # Detailed analysis
    message: str | None = None
    suggested_action: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> IntentComparison:
        """Create an IntentComparison from a dictionary."""
        return cls(
            declared_intent_id=data.get("declared_intent_id"),
            inferred_intent_id=data.get("inferred_intent_id"),
            declared_title=data.get("declared_title"),
            inferred_title=data.get("inferred_title"),
            status=AlignmentStatus(data["status"]),
            confidence=data.get("confidence", 0.0),
            declared_files=data.get("declared_files", []),
            inferred_files=data.get("inferred_files", []),
            overlapping_files=data.get("overlapping_files", []),
            extra_files=data.get("extra_files", []),
            missing_files=data.get("missing_files", []),
            message=data.get("message"),
            suggested_action=data.get("suggested_action"),
        )

    def to_dict(self) -> dict:
        """Convert IntentComparison to a dictionary for serialization."""
        result: dict = {
            "status": self.status.value,
            "confidence": self.confidence,
        }

        if self.declared_intent_id:
            result["declared_intent_id"] = self.declared_intent_id
        if self.inferred_intent_id:
            result["inferred_intent_id"] = self.inferred_intent_id
        if self.declared_title:
            result["declared_title"] = self.declared_title
        if self.inferred_title:
            result["inferred_title"] = self.inferred_title
        if self.declared_files:
            result["declared_files"] = self.declared_files
        if self.inferred_files:
            result["inferred_files"] = self.inferred_files
        if self.overlapping_files:
            result["overlapping_files"] = self.overlapping_files
        if self.extra_files:
            result["extra_files"] = self.extra_files
        if self.missing_files:
            result["missing_files"] = self.missing_files
        if self.message:
            result["message"] = self.message
        if self.suggested_action:
            result["suggested_action"] = self.suggested_action

        return result


@dataclass
class AlignmentReport:
    """
    Report comparing declared intentions vs. inferred intentions from code.

    Based on NeuroSync research: bidirectional comparison enables early correction.
    """

    aligned: bool  # True if overall alignment is acceptable
    comparisons: list[IntentComparison] = field(default_factory=list)

    # Summary statistics
    total_declared: int = 0
    total_inferred: int = 0
    aligned_count: int = 0
    partial_count: int = 0
    misaligned_count: int = 0
    missing_declared_count: int = 0
    missing_inferred_count: int = 0

    # Overall metrics
    alignment_score: float = 0.0  # 0.0-1.0 overall alignment
    coverage_score: float = 0.0  # 0.0-1.0 file coverage
    confidence_avg: float = 0.0  # Average confidence across comparisons

    # Optional override
    override_rationale: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> AlignmentReport:
        """Create an AlignmentReport from a dictionary."""
        comparisons_data = data.get("comparisons", [])
        comparisons = [IntentComparison.from_dict(c) for c in comparisons_data]

        return cls(
            aligned=data["aligned"],
            comparisons=comparisons,
            total_declared=data.get("total_declared", 0),
            total_inferred=data.get("total_inferred", 0),
            aligned_count=data.get("aligned_count", 0),
            partial_count=data.get("partial_count", 0),
            misaligned_count=data.get("misaligned_count", 0),
            missing_declared_count=data.get("missing_declared_count", 0),
            missing_inferred_count=data.get("missing_inferred_count", 0),
            alignment_score=data.get("alignment_score", 0.0),
            coverage_score=data.get("coverage_score", 0.0),
            confidence_avg=data.get("confidence_avg", 0.0),
            override_rationale=data.get("override_rationale"),
        )

    def to_dict(self) -> dict:
        """Convert AlignmentReport to a dictionary for serialization."""
        result: dict = {
            "aligned": self.aligned,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "total_declared": self.total_declared,
            "total_inferred": self.total_inferred,
            "aligned_count": self.aligned_count,
            "partial_count": self.partial_count,
            "misaligned_count": self.misaligned_count,
            "missing_declared_count": self.missing_declared_count,
            "missing_inferred_count": self.missing_inferred_count,
            "alignment_score": self.alignment_score,
            "coverage_score": self.coverage_score,
            "confidence_avg": self.confidence_avg,
        }

        if self.override_rationale:
            result["override_rationale"] = self.override_rationale

        return result

    @classmethod
    def load(cls, path) -> AlignmentReport:
        """Load AlignmentReport from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def get_misalignments(self) -> list[IntentComparison]:
        """Get all misaligned comparisons."""
        return [
            c
            for c in self.comparisons
            if c.status in (AlignmentStatus.MISALIGNED, AlignmentStatus.MISSING_DECLARED)
        ]

    def get_aligned(self) -> list[IntentComparison]:
        """Get all aligned comparisons."""
        return [c for c in self.comparisons if c.status == AlignmentStatus.ALIGNED]

    def needs_review(self) -> bool:
        """Check if the report has issues that need human review."""
        return self.misaligned_count > 0 or self.missing_declared_count > 0
