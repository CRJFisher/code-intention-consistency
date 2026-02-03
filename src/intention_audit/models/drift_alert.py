"""
DriftAlert model for real-time goal drift detection.

Based on research insight: Agents exhibit "pattern-matching drift" where
they continue recent behaviors even when violating high-level goals.
Active drift monitoring with threshold alerts enables early correction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class DriftSeverity(Enum):
    """Severity level of drift detected."""

    LOW = "low"  # Minor deviation, informational
    MEDIUM = "medium"  # Notable deviation, review recommended
    HIGH = "high"  # Significant deviation, action required
    CRITICAL = "critical"  # Major deviation, blocks progress


class DriftType(Enum):
    """Type of drift detected."""

    SCOPE_CREEP = "scope_creep"  # Work expanding beyond declared intentions
    GOAL_DIVERGENCE = "goal_divergence"  # Direction deviating from root goal
    PATTERN_DRIFT = "pattern_drift"  # Continuing patterns that violate goals
    CONTEXT_LOSS = "context_loss"  # Losing sight of original context
    PRIORITY_SHIFT = "priority_shift"  # Implicit priority change detected


@dataclass
class DriftAlert:
    """A single drift alert triggered when threshold is exceeded."""

    id: str  # Alert identifier (e.g., DRIFT-2026-01-31-0001)
    type: DriftType
    severity: DriftSeverity
    drift_score: float  # 0.0-1.0, higher means more drift
    threshold: float  # The threshold that was exceeded

    # Context
    root_intention_id: str  # The root goal being drifted from
    current_focus: str  # Description of current work focus
    message: str  # Human-readable alert message

    # Affected items
    affected_files: list[str] = field(default_factory=list)
    affected_intentions: list[str] = field(default_factory=list)

    # Trajectory info
    previous_score: float | None = None  # Previous drift score for trajectory
    trajectory: str | None = None  # "improving", "stable", "worsening"

    # Recommendations
    suggested_action: str | None = None
    recovery_options: list[str] = field(default_factory=list)

    # Timestamps
    detected_at: str | None = None  # ISO timestamp

    @classmethod
    def from_dict(cls, data: dict) -> DriftAlert:
        """Create a DriftAlert from a dictionary."""
        return cls(
            id=data["id"],
            type=DriftType(data["type"]),
            severity=DriftSeverity(data["severity"]),
            drift_score=data["drift_score"],
            threshold=data["threshold"],
            root_intention_id=data["root_intention_id"],
            current_focus=data["current_focus"],
            message=data["message"],
            affected_files=data.get("affected_files", []),
            affected_intentions=data.get("affected_intentions", []),
            previous_score=data.get("previous_score"),
            trajectory=data.get("trajectory"),
            suggested_action=data.get("suggested_action"),
            recovery_options=data.get("recovery_options", []),
            detected_at=data.get("detected_at"),
        )

    def to_dict(self) -> dict:
        """Convert DriftAlert to a dictionary for serialization."""
        result: dict = {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "drift_score": self.drift_score,
            "threshold": self.threshold,
            "root_intention_id": self.root_intention_id,
            "current_focus": self.current_focus,
            "message": self.message,
        }

        if self.affected_files:
            result["affected_files"] = self.affected_files
        if self.affected_intentions:
            result["affected_intentions"] = self.affected_intentions
        if self.previous_score is not None:
            result["previous_score"] = self.previous_score
        if self.trajectory:
            result["trajectory"] = self.trajectory
        if self.suggested_action:
            result["suggested_action"] = self.suggested_action
        if self.recovery_options:
            result["recovery_options"] = self.recovery_options
        if self.detected_at:
            result["detected_at"] = self.detected_at

        return result


@dataclass
class DriftHistory:
    """
    History of drift scores and alerts for a session.

    Tracks drift trajectory over time to detect patterns.
    """

    session_id: str
    root_intention_id: str

    # Score history
    scores: list[dict] = field(default_factory=list)  # [{timestamp, score, files_checked}]

    # Active alerts
    alerts: list[DriftAlert] = field(default_factory=list)

    # Configuration
    alert_threshold: float = 0.7  # Score above which to alert
    warning_threshold: float = 0.5  # Score for warnings

    # Summary
    current_score: float = 0.0
    max_score: float = 0.0
    avg_score: float = 0.0
    trend: str | None = None  # "improving", "stable", "worsening"

    @classmethod
    def from_dict(cls, data: dict) -> DriftHistory:
        """Create a DriftHistory from a dictionary."""
        alerts_data = data.get("alerts", [])
        alerts = [DriftAlert.from_dict(a) for a in alerts_data]

        return cls(
            session_id=data["session_id"],
            root_intention_id=data["root_intention_id"],
            scores=data.get("scores", []),
            alerts=alerts,
            alert_threshold=data.get("alert_threshold", 0.7),
            warning_threshold=data.get("warning_threshold", 0.5),
            current_score=data.get("current_score", 0.0),
            max_score=data.get("max_score", 0.0),
            avg_score=data.get("avg_score", 0.0),
            trend=data.get("trend"),
        )

    def to_dict(self) -> dict:
        """Convert DriftHistory to a dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "root_intention_id": self.root_intention_id,
            "scores": self.scores,
            "alerts": [a.to_dict() for a in self.alerts],
            "alert_threshold": self.alert_threshold,
            "warning_threshold": self.warning_threshold,
            "current_score": self.current_score,
            "max_score": self.max_score,
            "avg_score": self.avg_score,
            "trend": self.trend,
        }

    @classmethod
    def load(cls, path) -> DriftHistory:
        """Load DriftHistory from a JSON file."""
        import json
        from pathlib import Path

        p = Path(path) if not isinstance(path, Path) else path
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def add_score(self, score: float, timestamp: str, files_checked: int = 0) -> None:
        """Add a new drift score measurement."""
        self.scores.append(
            {
                "timestamp": timestamp,
                "score": score,
                "files_checked": files_checked,
            }
        )
        self.current_score = score
        self.max_score = max(self.max_score, score)
        if self.scores:
            self.avg_score = sum(s["score"] for s in self.scores) / len(self.scores)
        self._update_trend()

    def _update_trend(self) -> None:
        """Update trend based on recent scores."""
        if len(self.scores) < 2:
            self.trend = None
            return

        recent = self.scores[-3:]  # Last 3 scores
        if len(recent) < 2:
            self.trend = "stable"
            return

        deltas = [recent[i + 1]["score"] - recent[i]["score"] for i in range(len(recent) - 1)]
        avg_delta = sum(deltas) / len(deltas)

        if avg_delta > 0.05:
            self.trend = "worsening"
        elif avg_delta < -0.05:
            self.trend = "improving"
        else:
            self.trend = "stable"

    def has_active_alerts(self) -> bool:
        """Check if there are any active alerts."""
        return len(self.alerts) > 0

    def get_critical_alerts(self) -> list[DriftAlert]:
        """Get all critical severity alerts."""
        return [a for a in self.alerts if a.severity == DriftSeverity.CRITICAL]

    def is_drifting(self) -> bool:
        """Check if current score indicates drift."""
        return self.current_score >= self.warning_threshold
