"""
SessionRecord model for committed audit records.

Based on the data model in backlog/docs (doc-3).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MappingSummary:
    """Summary of intention mapping for a session."""

    total_intentions: int = 0
    new_intentions: int = 0
    updated_intentions: int = 0
    commits_planned: int = 0
    files_covered: int = 0
    hunks_covered: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> MappingSummary:
        """Create a MappingSummary from a dictionary."""
        return cls(
            total_intentions=data.get("total_intentions", 0),
            new_intentions=data.get("new_intentions", 0),
            updated_intentions=data.get("updated_intentions", 0),
            commits_planned=data.get("commits_planned", 0),
            files_covered=data.get("files_covered", 0),
            hunks_covered=data.get("hunks_covered", 0),
        )

    def to_dict(self) -> dict:
        """Convert MappingSummary to a dictionary for serialization."""
        return {
            "total_intentions": self.total_intentions,
            "new_intentions": self.new_intentions,
            "updated_intentions": self.updated_intentions,
            "commits_planned": self.commits_planned,
            "files_covered": self.files_covered,
            "hunks_covered": self.hunks_covered,
        }


@dataclass
class SessionRecord:
    """
    Committed audit record for a session.

    Normalized and safe to keep in-repo.
    """

    session_id: str
    timestamp: str  # ISO format
    transcript_ref: str  # Hash/identifier for underlying transcript
    diff_base: str  # e.g., "HEAD" or commit hash
    diff_hash: str  # Normalized hash for the diff

    # Tool information
    planner_tool: str  # MCP tool name + version

    # Mapping information
    intentions_touched: list[str] = field(default_factory=list)  # Intention IDs
    mapping_summary: MappingSummary = field(default_factory=MappingSummary)

    # Optional notes
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> SessionRecord:
        """Create a SessionRecord from a dictionary."""
        mapping_data = data.get("mapping_summary", {})
        if isinstance(mapping_data, dict):
            mapping_summary = MappingSummary.from_dict(mapping_data)
        else:
            mapping_summary = MappingSummary()

        return cls(
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            transcript_ref=data.get("transcript_ref", ""),
            diff_base=data.get("diff_base", "HEAD"),
            diff_hash=data.get("diff_hash", ""),
            planner_tool=data.get("planner_tool", ""),
            intentions_touched=data.get("intentions_touched", []),
            mapping_summary=mapping_summary,
            notes=data.get("notes"),
        )

    def to_dict(self) -> dict:
        """Convert SessionRecord to a dictionary for serialization."""
        result: dict = {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "transcript_ref": self.transcript_ref,
            "diff_base": self.diff_base,
            "diff_hash": self.diff_hash,
            "planner_tool": self.planner_tool,
            "intentions_touched": self.intentions_touched,
            "mapping_summary": self.mapping_summary.to_dict(),
        }

        if self.notes:
            result["notes"] = self.notes

        return result
