"""
Intention model representing a goal/functionality/implementation node.

Based on specs/001-intent-audit-trail/data-model.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class IntentionKind(Enum):
    """Type of intention in the hierarchy."""

    GOAL = "goal"
    FUNCTIONALITY = "functionality"
    IMPLEMENTATION = "implementation"
    TESTS = "tests"
    DOCS = "docs"
    OBSERVABILITY = "observability"


class IntentionStatus(Enum):
    """Current state of an intention."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


@dataclass
class Intention:
    """
    Represents a goal/functionality/implementation/tests/docs node in the intention tree.

    Fields match the data-model.md specification.
    """

    id: str  # Format: INT-YYYY-MM-DD-NNNN
    title: str
    kind: IntentionKind
    status: IntentionStatus = IntentionStatus.PLANNED

    # Hierarchical structure
    children: list[Intention] = field(default_factory=list)

    # Optional metadata
    created_at: str | None = None  # ISO timestamp
    rationale: str | None = None
    constraints: str | list[str] | None = None
    superseded_by: str | None = None  # ID of superseding intention

    # Linkage fields
    evidence_tests: list[str] = field(default_factory=list)  # Test selectors
    supporting_docs: list[str] = field(default_factory=list)  # Doc paths with anchors

    # Structure alignment fields (for functionality nodes)
    code_home: list[str] = field(default_factory=list)  # Repo-relative path prefixes
    named_scopes: list[str] = field(default_factory=list)  # Naming conventions (future)

    @classmethod
    def from_dict(cls, data: dict) -> Intention:
        """Create an Intention from a dictionary (e.g., parsed YAML)."""
        # Handle kind enum
        kind_value = data.get("kind", "implementation")
        kind = IntentionKind(kind_value.lower()) if isinstance(kind_value, str) else kind_value

        # Handle status enum
        status_value = data.get("status", "planned")
        status = IntentionStatus(status_value.lower()) if isinstance(status_value, str) else status_value

        # Handle children recursively
        children_data = data.get("children", [])
        children = [cls.from_dict(child) for child in children_data]

        # Handle constraints (can be string or list)
        constraints = data.get("constraints")

        return cls(
            id=data["id"],
            title=data["title"],
            kind=kind,
            status=status,
            children=children,
            created_at=data.get("created_at"),
            rationale=data.get("rationale"),
            constraints=constraints,
            superseded_by=data.get("superseded_by"),
            evidence_tests=data.get("evidence_tests", []),
            supporting_docs=data.get("supporting_docs", []),
            code_home=data.get("code_home", []),
            named_scopes=data.get("named_scopes", []),
        )

    def to_dict(self) -> dict:
        """Convert Intention to a dictionary for serialization."""
        result: dict = {
            "id": self.id,
            "title": self.title,
            "kind": self.kind.value,
            "status": self.status.value,
        }

        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        if self.created_at:
            result["created_at"] = self.created_at
        if self.rationale:
            result["rationale"] = self.rationale
        if self.constraints:
            result["constraints"] = self.constraints
        if self.superseded_by:
            result["superseded_by"] = self.superseded_by
        if self.evidence_tests:
            result["evidence_tests"] = self.evidence_tests
        if self.supporting_docs:
            result["supporting_docs"] = self.supporting_docs
        if self.code_home:
            result["code_home"] = self.code_home
        if self.named_scopes:
            result["named_scopes"] = self.named_scopes

        return result
