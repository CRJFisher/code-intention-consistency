"""
Bootstrap model for retrospective rationale mining.

Based on UserTrace research insight: Extract user-level requirements from
existing code by ascending Code→IR→UR hierarchy using multi-agent workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class BootstrapStage(Enum):
    """Stage of the bootstrap mining process."""

    CLUSTERING = "clustering"  # Analyzing git history, grouping commits
    EXTRACTING = "extracting"  # Extracting implementation requirements
    SYNTHESIZING = "synthesizing"  # Synthesizing user requirements
    VERIFYING = "verifying"  # Validating and linking intentions
    COMPLETE = "complete"  # Bootstrap finished


class MiningConfidence(Enum):
    """Confidence level for mined intentions."""

    HIGH = "high"  # Strong evidence: clear commit messages, tests exist
    MEDIUM = "medium"  # Moderate evidence: some commit context
    LOW = "low"  # Weak evidence: inferred from code structure only


@dataclass
class CommitCluster:
    """A semantic grouping of related commits."""

    cluster_id: str
    commits: list[str]  # List of commit SHAs
    semantic_label: str  # Brief description of what this cluster represents
    conventional_prefix: str | None = None  # feat:, fix:, refactor:, etc.
    confidence: float = 0.6  # 0.0-1.0
    files_touched: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> CommitCluster:
        """Create a CommitCluster from a dictionary."""
        return cls(
            cluster_id=data["cluster_id"],
            commits=data["commits"],
            semantic_label=data["semantic_label"],
            conventional_prefix=data.get("conventional_prefix"),
            confidence=data.get("confidence", 0.6),
            files_touched=data.get("files_touched", []),
        )

    def to_dict(self) -> dict:
        """Convert CommitCluster to a dictionary for serialization."""
        result: dict = {
            "cluster_id": self.cluster_id,
            "commits": self.commits,
            "semantic_label": self.semantic_label,
            "confidence": self.confidence,
        }

        if self.conventional_prefix:
            result["conventional_prefix"] = self.conventional_prefix
        if self.files_touched:
            result["files_touched"] = self.files_touched

        return result


@dataclass
class ImplementationRequirement:
    """Code-level rationale extracted from a commit cluster."""

    ir_id: str
    cluster_id: str  # Reference to source CommitCluster
    description: str  # What was implemented

    # Code-level details
    functions_modified: list[str] = field(default_factory=list)
    classes_modified: list[str] = field(default_factory=list)
    tests_added: list[str] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)  # e.g., "error handling"

    confidence: float = 0.6

    @classmethod
    def from_dict(cls, data: dict) -> ImplementationRequirement:
        """Create an ImplementationRequirement from a dictionary."""
        return cls(
            ir_id=data["ir_id"],
            cluster_id=data["cluster_id"],
            description=data["description"],
            functions_modified=data.get("functions_modified", []),
            classes_modified=data.get("classes_modified", []),
            tests_added=data.get("tests_added", []),
            patterns_detected=data.get("patterns_detected", []),
            confidence=data.get("confidence", 0.6),
        )

    def to_dict(self) -> dict:
        """Convert ImplementationRequirement to a dictionary for serialization."""
        result: dict = {
            "ir_id": self.ir_id,
            "cluster_id": self.cluster_id,
            "description": self.description,
            "confidence": self.confidence,
        }

        if self.functions_modified:
            result["functions_modified"] = self.functions_modified
        if self.classes_modified:
            result["classes_modified"] = self.classes_modified
        if self.tests_added:
            result["tests_added"] = self.tests_added
        if self.patterns_detected:
            result["patterns_detected"] = self.patterns_detected

        return result


@dataclass
class SynthesizedIntention:
    """A user requirement synthesized from implementation requirements."""

    intent_id: str
    title: str
    description: str
    type: str  # goal, functionality, implementation

    # Source tracing
    source_ir_ids: list[str] = field(default_factory=list)
    source_clusters: list[str] = field(default_factory=list)

    # Linkage
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    code_home: list[str] = field(default_factory=list)
    evidence_tests: list[str] = field(default_factory=list)

    # Mining metadata
    source: str = "mined"  # Always "mined" for bootstrap
    confidence: float = 0.6

    @classmethod
    def from_dict(cls, data: dict) -> SynthesizedIntention:
        """Create a SynthesizedIntention from a dictionary."""
        return cls(
            intent_id=data["intent_id"],
            title=data["title"],
            description=data.get("description", ""),
            type=data["type"],
            source_ir_ids=data.get("source_ir_ids", []),
            source_clusters=data.get("source_clusters", []),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
            code_home=data.get("code_home", []),
            evidence_tests=data.get("evidence_tests", []),
            source=data.get("source", "mined"),
            confidence=data.get("confidence", 0.6),
        )

    def to_dict(self) -> dict:
        """Convert SynthesizedIntention to a dictionary for serialization."""
        result: dict = {
            "intent_id": self.intent_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "source": self.source,
            "confidence": self.confidence,
        }

        if self.source_ir_ids:
            result["source_ir_ids"] = self.source_ir_ids
        if self.source_clusters:
            result["source_clusters"] = self.source_clusters
        if self.parent_id:
            result["parent_id"] = self.parent_id
        if self.child_ids:
            result["child_ids"] = self.child_ids
        if self.code_home:
            result["code_home"] = self.code_home
        if self.evidence_tests:
            result["evidence_tests"] = self.evidence_tests

        return result


@dataclass
class BootstrapResult:
    """Complete result of a bootstrap mining operation."""

    # Status
    stage: BootstrapStage
    success: bool

    # Artifacts
    clusters: list[CommitCluster] = field(default_factory=list)
    implementation_requirements: list[ImplementationRequirement] = field(default_factory=list)
    synthesized_intentions: list[SynthesizedIntention] = field(default_factory=list)

    # Statistics
    commits_analyzed: int = 0
    clusters_created: int = 0
    irs_extracted: int = 0
    intentions_synthesized: int = 0

    # Metadata
    since_date: str | None = None
    branch: str | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> BootstrapResult:
        """Create a BootstrapResult from a dictionary."""
        clusters_data = data.get("clusters", [])
        clusters = [CommitCluster.from_dict(c) for c in clusters_data]

        irs_data = data.get("implementation_requirements", [])
        irs = [ImplementationRequirement.from_dict(ir) for ir in irs_data]

        intentions_data = data.get("synthesized_intentions", [])
        intentions = [SynthesizedIntention.from_dict(i) for i in intentions_data]

        return cls(
            stage=BootstrapStage(data["stage"]),
            success=data["success"],
            clusters=clusters,
            implementation_requirements=irs,
            synthesized_intentions=intentions,
            commits_analyzed=data.get("commits_analyzed", 0),
            clusters_created=data.get("clusters_created", 0),
            irs_extracted=data.get("irs_extracted", 0),
            intentions_synthesized=data.get("intentions_synthesized", 0),
            since_date=data.get("since_date"),
            branch=data.get("branch"),
            error=data.get("error"),
        )

    def to_dict(self) -> dict:
        """Convert BootstrapResult to a dictionary for serialization."""
        result: dict = {
            "stage": self.stage.value,
            "success": self.success,
            "clusters": [c.to_dict() for c in self.clusters],
            "implementation_requirements": [
                ir.to_dict() for ir in self.implementation_requirements
            ],
            "synthesized_intentions": [i.to_dict() for i in self.synthesized_intentions],
            "commits_analyzed": self.commits_analyzed,
            "clusters_created": self.clusters_created,
            "irs_extracted": self.irs_extracted,
            "intentions_synthesized": self.intentions_synthesized,
        }

        if self.since_date:
            result["since_date"] = self.since_date
        if self.branch:
            result["branch"] = self.branch
        if self.error:
            result["error"] = self.error

        return result

    @classmethod
    def load(cls, path) -> BootstrapResult:
        """Load BootstrapResult from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def get_low_confidence_intentions(self, threshold: float = 0.5) -> list[SynthesizedIntention]:
        """Get intentions below confidence threshold for human review."""
        return [i for i in self.synthesized_intentions if i.confidence < threshold]

    def is_complete(self) -> bool:
        """Check if bootstrap is complete."""
        return self.stage == BootstrapStage.COMPLETE and self.success
