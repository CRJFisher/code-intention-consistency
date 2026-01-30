"""
CommitPlan and CommitEntry models for intention-scoped commits.

Based on specs/001-intent-audit-trail/data-model.md
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CommitEntry:
    """
    Represents a single intention-scoped commit the stop hook will create.
    """

    intent_id: str  # Leaf intention to realize
    subject: str  # Commit subject line
    patch: str  # Unified diff that applies cleanly

    # Optional fields
    intent_path: str | None = None  # Derived human path e.g., "Goal/Feature/Leaf"
    functionality_intent_id: str | None = None  # Closest kind:functionality ancestor
    functionality_intent_path: str | None = None
    body: str | None = None  # Commit body (optional)
    intent_confidence: float | None = None  # 0.0-1.0
    evidence_tests: list[str] = field(default_factory=list)
    supporting_docs: list[str] = field(default_factory=list)

    # Legacy field for file-level mapping (MVP uses this)
    files: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> CommitEntry:
        """Create a CommitEntry from a dictionary."""
        return cls(
            intent_id=data["intent_id"],
            subject=data.get("subject", data.get("title", "")),
            patch=data.get("patch", ""),
            intent_path=data.get("intent_path"),
            functionality_intent_id=data.get("functionality_intent_id"),
            functionality_intent_path=data.get("functionality_intent_path"),
            body=data.get("body"),
            intent_confidence=data.get("intent_confidence"),
            evidence_tests=data.get("evidence_tests", []),
            supporting_docs=data.get("supporting_docs", []),
            files=data.get("files", []),
        )

    def to_dict(self) -> dict:
        """Convert CommitEntry to a dictionary for serialization."""
        result: dict = {
            "intent_id": self.intent_id,
            "subject": self.subject,
        }

        if self.patch:
            result["patch"] = self.patch
        if self.intent_path:
            result["intent_path"] = self.intent_path
        if self.functionality_intent_id:
            result["functionality_intent_id"] = self.functionality_intent_id
        if self.functionality_intent_path:
            result["functionality_intent_path"] = self.functionality_intent_path
        if self.body:
            result["body"] = self.body
        if self.intent_confidence is not None:
            result["intent_confidence"] = self.intent_confidence
        if self.evidence_tests:
            result["evidence_tests"] = self.evidence_tests
        if self.supporting_docs:
            result["supporting_docs"] = self.supporting_docs
        if self.files:
            result["files"] = self.files

        return result


@dataclass
class CommitPlan:
    """
    Planner output used by the stop hook to validate and produce commits.
    """

    version: int  # Schema version, currently 1
    ready: bool  # Whether plan is ready for execution
    commits: list[CommitEntry]

    # Optional fields
    diff_base: str | None = None  # e.g., "HEAD"
    diff_hash: str | None = None  # Normalized hash for the diff

    @classmethod
    def from_dict(cls, data: dict) -> CommitPlan:
        """Create a CommitPlan from a dictionary."""
        commits_data = data.get("commits", [])
        commits = [CommitEntry.from_dict(c) for c in commits_data]

        return cls(
            version=data.get("version", 1),
            ready=data.get("ready", False),
            commits=commits,
            diff_base=data.get("diff_base"),
            diff_hash=data.get("diff_hash"),
        )

    def to_dict(self) -> dict:
        """Convert CommitPlan to a dictionary for serialization."""
        result: dict = {
            "version": self.version,
            "ready": self.ready,
            "commits": [c.to_dict() for c in self.commits],
        }

        if self.diff_base:
            result["diff_base"] = self.diff_base
        if self.diff_hash:
            result["diff_hash"] = self.diff_hash

        return result
