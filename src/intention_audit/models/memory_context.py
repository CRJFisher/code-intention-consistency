"""
MemoryContext model for hierarchical memory management.

Based on HiAgent research insight: Use subgoal-based memory chunking
where active context gets full detail, recent context gets summaries,
and archived context gets only IDs and outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class MemoryTier(Enum):
    """Tier of memory context."""

    ACTIVE = "active"  # Full detail for current intention
    RECENT = "recent"  # Summaries of sibling intentions
    ARCHIVE = "archive"  # Only IDs and outcomes for completed branches


@dataclass
class IntentionSummary:
    """Summarized view of an intention for tiered context."""

    intent_id: str
    title: str
    type: str  # goal, functionality, implementation

    # Status
    status: str  # pending, in_progress, completed
    outcome: str | None = None  # Brief outcome description

    # Relationships
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> IntentionSummary:
        """Create an IntentionSummary from a dictionary."""
        return cls(
            intent_id=data["intent_id"],
            title=data["title"],
            type=data["type"],
            status=data.get("status", "pending"),
            outcome=data.get("outcome"),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
        )

    def to_dict(self) -> dict:
        """Convert IntentionSummary to a dictionary for serialization."""
        result: dict = {
            "intent_id": self.intent_id,
            "title": self.title,
            "type": self.type,
            "status": self.status,
        }

        if self.outcome:
            result["outcome"] = self.outcome
        if self.parent_id:
            result["parent_id"] = self.parent_id
        if self.child_ids:
            result["child_ids"] = self.child_ids

        return result


@dataclass
class ActiveContext:
    """Full detail context for the currently active intention."""

    intent_id: str
    title: str
    description: str
    type: str

    # Full intention details
    acceptance_criteria: list[str] = field(default_factory=list)
    evidence_tests: list[str] = field(default_factory=list)
    code_home: list[str] = field(default_factory=list)

    # Related artifacts
    related_files: list[str] = field(default_factory=list)
    recent_changes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ActiveContext:
        """Create an ActiveContext from a dictionary."""
        return cls(
            intent_id=data["intent_id"],
            title=data["title"],
            description=data.get("description", ""),
            type=data["type"],
            acceptance_criteria=data.get("acceptance_criteria", []),
            evidence_tests=data.get("evidence_tests", []),
            code_home=data.get("code_home", []),
            related_files=data.get("related_files", []),
            recent_changes=data.get("recent_changes", []),
        )

    def to_dict(self) -> dict:
        """Convert ActiveContext to a dictionary for serialization."""
        result: dict = {
            "intent_id": self.intent_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
        }

        if self.acceptance_criteria:
            result["acceptance_criteria"] = self.acceptance_criteria
        if self.evidence_tests:
            result["evidence_tests"] = self.evidence_tests
        if self.code_home:
            result["code_home"] = self.code_home
        if self.related_files:
            result["related_files"] = self.related_files
        if self.recent_changes:
            result["recent_changes"] = self.recent_changes

        return result


@dataclass
class TieredContext:
    """
    Complete tiered memory context for a sub-agent.

    Based on HiAgent memory hierarchy:
    - Active: Full detail for current intention being worked
    - Recent: Summaries of sibling intentions
    - Archive: Only IDs and outcomes for completed branches
    """

    # Session info
    session_id: str
    active_intention_path: list[str]  # Path from root to active intention

    # Tiered context
    active: ActiveContext | None = None
    recent: list[IntentionSummary] = field(default_factory=list)
    archive: list[IntentionSummary] = field(default_factory=list)

    # Statistics
    total_intentions: int = 0
    active_tier_size: int = 0  # Bytes/tokens in active context
    recent_tier_size: int = 0
    archive_tier_size: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> TieredContext:
        """Create a TieredContext from a dictionary."""
        active_data = data.get("active")
        active = ActiveContext.from_dict(active_data) if active_data else None

        recent_data = data.get("recent", [])
        recent = [IntentionSummary.from_dict(s) for s in recent_data]

        archive_data = data.get("archive", [])
        archive = [IntentionSummary.from_dict(s) for s in archive_data]

        return cls(
            session_id=data["session_id"],
            active_intention_path=data.get("active_intention_path", []),
            active=active,
            recent=recent,
            archive=archive,
            total_intentions=data.get("total_intentions", 0),
            active_tier_size=data.get("active_tier_size", 0),
            recent_tier_size=data.get("recent_tier_size", 0),
            archive_tier_size=data.get("archive_tier_size", 0),
        )

    def to_dict(self) -> dict:
        """Convert TieredContext to a dictionary for serialization."""
        result: dict = {
            "session_id": self.session_id,
            "active_intention_path": self.active_intention_path,
            "total_intentions": self.total_intentions,
            "active_tier_size": self.active_tier_size,
            "recent_tier_size": self.recent_tier_size,
            "archive_tier_size": self.archive_tier_size,
        }

        if self.active:
            result["active"] = self.active.to_dict()
        if self.recent:
            result["recent"] = [s.to_dict() for s in self.recent]
        if self.archive:
            result["archive"] = [s.to_dict() for s in self.archive]

        return result

    @classmethod
    def load(cls, path) -> TieredContext:
        """Load TieredContext from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def get_context_for_tier(self, tier: MemoryTier) -> list[IntentionSummary]:
        """Get intentions for a specific tier."""
        if tier == MemoryTier.RECENT:
            return self.recent
        elif tier == MemoryTier.ARCHIVE:
            return self.archive
        return []

    def get_total_context_size(self) -> int:
        """Get total context size across all tiers."""
        return self.active_tier_size + self.recent_tier_size + self.archive_tier_size

    def is_intention_active(self, intent_id: str) -> bool:
        """Check if an intention is in the active path."""
        return intent_id in self.active_intention_path
