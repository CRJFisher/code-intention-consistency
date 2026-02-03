"""
HunkAnalysis model for semantic tangled-commit detection.

Based on ColaUntangle research insight: Use both explicit (AST-based)
and implicit (semantic) dependency analysis to detect when changes
serve multiple intentions and should be split.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TangleType(Enum):
    """Type of tangling detected."""

    SEMANTIC = "semantic"  # Different semantic purposes in same file/hunk
    FUNCTIONAL = "functional"  # Different functionality areas mixed
    STRUCTURAL = "structural"  # Code structure suggests separation
    DEPENDENCY = "dependency"  # Dependency analysis suggests split


class TangleSeverity(Enum):
    """Severity of tangling detected."""

    LOW = "low"  # Minor mixing, acceptable in MVP
    MEDIUM = "medium"  # Notable mixing, consider splitting
    HIGH = "high"  # Significant mixing, strongly recommend splitting


@dataclass
class HunkMapping:
    """Mapping of a diff hunk to an intention."""

    file_path: str
    hunk_index: int  # 0-based index of hunk in file
    start_line: int
    end_line: int

    # Intent mapping
    intent_id: str
    intent_confidence: float  # 0.0-1.0

    # Semantic analysis
    semantic_purpose: str  # Brief description of what this hunk does
    dependencies: list[str] = field(default_factory=list)  # Other hunks this depends on

    @classmethod
    def from_dict(cls, data: dict) -> HunkMapping:
        """Create a HunkMapping from a dictionary."""
        return cls(
            file_path=data["file_path"],
            hunk_index=data["hunk_index"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            intent_id=data["intent_id"],
            intent_confidence=data.get("intent_confidence", 0.0),
            semantic_purpose=data.get("semantic_purpose", ""),
            dependencies=data.get("dependencies", []),
        )

    def to_dict(self) -> dict:
        """Convert HunkMapping to a dictionary for serialization."""
        result: dict = {
            "file_path": self.file_path,
            "hunk_index": self.hunk_index,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "intent_id": self.intent_id,
            "intent_confidence": self.intent_confidence,
        }

        if self.semantic_purpose:
            result["semantic_purpose"] = self.semantic_purpose
        if self.dependencies:
            result["dependencies"] = self.dependencies

        return result


@dataclass
class TangleDetection:
    """A detected case of tangled changes."""

    file_path: str
    type: TangleType
    severity: TangleSeverity

    # Affected hunks
    hunk_indices: list[int]  # Indices of tangled hunks
    intent_ids: list[str]  # Different intents mixed in this tangle

    # Analysis
    message: str
    suggested_split: list[dict] = field(default_factory=list)  # How to split

    # Explicit vs Implicit analysis (from ColaUntangle)
    explicit_evidence: str | None = None  # AST/structural evidence
    implicit_evidence: str | None = None  # Semantic/LLM evidence

    @classmethod
    def from_dict(cls, data: dict) -> TangleDetection:
        """Create a TangleDetection from a dictionary."""
        return cls(
            file_path=data["file_path"],
            type=TangleType(data["type"]),
            severity=TangleSeverity(data["severity"]),
            hunk_indices=data["hunk_indices"],
            intent_ids=data["intent_ids"],
            message=data["message"],
            suggested_split=data.get("suggested_split", []),
            explicit_evidence=data.get("explicit_evidence"),
            implicit_evidence=data.get("implicit_evidence"),
        )

    def to_dict(self) -> dict:
        """Convert TangleDetection to a dictionary for serialization."""
        result: dict = {
            "file_path": self.file_path,
            "type": self.type.value,
            "severity": self.severity.value,
            "hunk_indices": self.hunk_indices,
            "intent_ids": self.intent_ids,
            "message": self.message,
        }

        if self.suggested_split:
            result["suggested_split"] = self.suggested_split
        if self.explicit_evidence:
            result["explicit_evidence"] = self.explicit_evidence
        if self.implicit_evidence:
            result["implicit_evidence"] = self.implicit_evidence

        return result


@dataclass
class HunkAnalysis:
    """
    Complete analysis of hunks for tangled commit detection.

    Based on ColaUntangle dual-worker approach:
    - Explicit Worker: AST-based dependency detection
    - Implicit Worker: Semantic similarity analysis
    """

    # Summary
    passed: bool  # True if no high-severity tangles
    total_hunks: int = 0
    files_analyzed: int = 0

    # Mappings
    hunk_mappings: list[HunkMapping] = field(default_factory=list)

    # Detected tangles
    tangles: list[TangleDetection] = field(default_factory=list)

    # Statistics
    clean_files: int = 0  # Files with no tangling
    tangled_files: int = 0  # Files with some tangling
    low_tangles: int = 0
    medium_tangles: int = 0
    high_tangles: int = 0

    # Optional override
    override_rationale: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> HunkAnalysis:
        """Create a HunkAnalysis from a dictionary."""
        mappings_data = data.get("hunk_mappings", [])
        hunk_mappings = [HunkMapping.from_dict(m) for m in mappings_data]

        tangles_data = data.get("tangles", [])
        tangles = [TangleDetection.from_dict(t) for t in tangles_data]

        return cls(
            passed=data["passed"],
            total_hunks=data.get("total_hunks", 0),
            files_analyzed=data.get("files_analyzed", 0),
            hunk_mappings=hunk_mappings,
            tangles=tangles,
            clean_files=data.get("clean_files", 0),
            tangled_files=data.get("tangled_files", 0),
            low_tangles=data.get("low_tangles", 0),
            medium_tangles=data.get("medium_tangles", 0),
            high_tangles=data.get("high_tangles", 0),
            override_rationale=data.get("override_rationale"),
        )

    def to_dict(self) -> dict:
        """Convert HunkAnalysis to a dictionary for serialization."""
        result: dict = {
            "passed": self.passed,
            "total_hunks": self.total_hunks,
            "files_analyzed": self.files_analyzed,
            "hunk_mappings": [m.to_dict() for m in self.hunk_mappings],
            "tangles": [t.to_dict() for t in self.tangles],
            "clean_files": self.clean_files,
            "tangled_files": self.tangled_files,
            "low_tangles": self.low_tangles,
            "medium_tangles": self.medium_tangles,
            "high_tangles": self.high_tangles,
        }

        if self.override_rationale:
            result["override_rationale"] = self.override_rationale

        return result

    @classmethod
    def load(cls, path) -> HunkAnalysis:
        """Load HunkAnalysis from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def get_high_severity_tangles(self) -> list[TangleDetection]:
        """Get all high-severity tangles."""
        return [t for t in self.tangles if t.severity == TangleSeverity.HIGH]

    def get_tangles_for_file(self, file_path: str) -> list[TangleDetection]:
        """Get all tangles for a specific file."""
        return [t for t in self.tangles if t.file_path == file_path]

    def has_blocking_tangles(self) -> bool:
        """Check if there are tangles that should block commit."""
        return self.high_tangles > 0 and self.override_rationale is None
