"""Tests for drift detection model and tool."""

import json
import tempfile
from pathlib import Path

from intention_audit.models.drift_alert import (
    DriftAlert,
    DriftHistory,
    DriftSeverity,
    DriftType,
)
from mcp_servers.intention_audit.tools.compute_drift_score import compute_drift_score


class TestDriftAlert:
    """Tests for DriftAlert dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating DriftAlert from minimal dict."""
        data = {
            "id": "DRIFT-2026-01-31-0001",
            "type": "scope_creep",
            "severity": "medium",
            "drift_score": 0.55,
            "threshold": 0.5,
            "root_intention_id": "INT-001",
            "current_focus": "Adding extra features",
            "message": "Work expanding beyond scope",
        }
        alert = DriftAlert.from_dict(data)

        assert alert.id == "DRIFT-2026-01-31-0001"
        assert alert.type == DriftType.SCOPE_CREEP
        assert alert.severity == DriftSeverity.MEDIUM
        assert alert.drift_score == 0.55

    def test_from_dict_full(self) -> None:
        """Test creating DriftAlert with all fields."""
        data = {
            "id": "DRIFT-2026-01-31-0002",
            "type": "goal_divergence",
            "severity": "high",
            "drift_score": 0.75,
            "threshold": 0.7,
            "root_intention_id": "INT-001",
            "current_focus": "Refactoring unrelated code",
            "message": "Major divergence from goal",
            "affected_files": ["src/other.py"],
            "affected_intentions": ["INT-003"],
            "previous_score": 0.50,
            "trajectory": "worsening",
            "suggested_action": "Return to main goal",
            "recovery_options": ["Stash changes", "Create new task"],
            "detected_at": "2026-01-31T11:00:00Z",
        }
        alert = DriftAlert.from_dict(data)

        assert alert.type == DriftType.GOAL_DIVERGENCE
        assert alert.severity == DriftSeverity.HIGH
        assert alert.trajectory == "worsening"
        assert len(alert.recovery_options) == 2

    def test_to_dict(self) -> None:
        """Test serializing DriftAlert to dict."""
        alert = DriftAlert(
            id="DRIFT-001",
            type=DriftType.PATTERN_DRIFT,
            severity=DriftSeverity.LOW,
            drift_score=0.25,
            threshold=0.3,
            root_intention_id="INT-001",
            current_focus="Minor tangent",
            message="Slight pattern drift",
        )
        result = alert.to_dict()

        assert result["id"] == "DRIFT-001"
        assert result["type"] == "pattern_drift"
        assert result["severity"] == "low"
        assert result["drift_score"] == 0.25


class TestDriftHistory:
    """Tests for DriftHistory dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating DriftHistory from minimal dict."""
        data = {
            "session_id": "test-session",
            "root_intention_id": "INT-001",
        }
        history = DriftHistory.from_dict(data)

        assert history.session_id == "test-session"
        assert history.root_intention_id == "INT-001"
        assert history.scores == []
        assert history.alerts == []

    def test_from_dict_with_scores_and_alerts(self) -> None:
        """Test creating DriftHistory with scores and alerts."""
        data = {
            "session_id": "test-session",
            "root_intention_id": "INT-001",
            "scores": [
                {"timestamp": "2026-01-31T10:00:00Z", "score": 0.1, "files_checked": 3},
                {"timestamp": "2026-01-31T10:30:00Z", "score": 0.4, "files_checked": 5},
            ],
            "alerts": [
                {
                    "id": "DRIFT-001",
                    "type": "scope_creep",
                    "severity": "medium",
                    "drift_score": 0.55,
                    "threshold": 0.5,
                    "root_intention_id": "INT-001",
                    "current_focus": "Extra work",
                    "message": "Scope expanded",
                }
            ],
            "current_score": 0.4,
            "max_score": 0.4,
            "avg_score": 0.25,
            "trend": "worsening",
        }
        history = DriftHistory.from_dict(data)

        assert len(history.scores) == 2
        assert len(history.alerts) == 1
        assert history.current_score == 0.4
        assert history.trend == "worsening"

    def test_to_dict(self) -> None:
        """Test serializing DriftHistory to dict."""
        history = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
            current_score=0.3,
        )
        result = history.to_dict()

        assert result["session_id"] == "test-session"
        assert result["root_intention_id"] == "INT-001"
        assert result["current_score"] == 0.3

    def test_add_score(self) -> None:
        """Test adding scores and updating metrics."""
        history = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
        )

        history.add_score(0.1, "2026-01-31T10:00:00Z", 3)
        assert history.current_score == 0.1
        assert history.max_score == 0.1

        history.add_score(0.4, "2026-01-31T10:30:00Z", 5)
        assert history.current_score == 0.4
        assert history.max_score == 0.4
        assert history.avg_score == 0.25

    def test_trend_calculation(self) -> None:
        """Test trend calculation based on score history."""
        history = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
        )

        # Add worsening trend
        history.add_score(0.1, "2026-01-31T10:00:00Z")
        history.add_score(0.3, "2026-01-31T10:30:00Z")
        history.add_score(0.5, "2026-01-31T11:00:00Z")

        assert history.trend == "worsening"

    def test_has_active_alerts(self) -> None:
        """Test has_active_alerts method."""
        history_no_alerts = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
            alerts=[],
        )
        alert = DriftAlert(
            id="DRIFT-001",
            type=DriftType.SCOPE_CREEP,
            severity=DriftSeverity.MEDIUM,
            drift_score=0.55,
            threshold=0.5,
            root_intention_id="INT-001",
            current_focus="Extra",
            message="Test",
        )
        history_with_alerts = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
            alerts=[alert],
        )

        assert history_no_alerts.has_active_alerts() is False
        assert history_with_alerts.has_active_alerts() is True

    def test_is_drifting(self) -> None:
        """Test is_drifting method."""
        low_drift = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
            current_score=0.3,
            warning_threshold=0.5,
        )
        high_drift = DriftHistory(
            session_id="test-session",
            root_intention_id="INT-001",
            current_score=0.6,
            warning_threshold=0.5,
        )

        assert low_drift.is_drifting() is False
        assert high_drift.is_drifting() is True

    def test_load_from_file(self) -> None:
        """Test loading DriftHistory from JSON file."""
        data = {
            "session_id": "test-session",
            "root_intention_id": "INT-001",
            "current_score": 0.3,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)

        try:
            history = DriftHistory.load(path)
            assert history.session_id == "test-session"
        finally:
            path.unlink()


class TestComputeDriftScore:
    """Tests for compute_drift_score MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal drift data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data = {
                "session_id": "test-session",
                "root_intention_id": "INT-001",
            }

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is True
            assert "path" in result
            assert Path(result["path"]).exists()

    def test_valid_with_scores_and_alerts(self) -> None:
        """Test saving drift data with scores and alerts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data = {
                "session_id": "test-session",
                "root_intention_id": "INT-001",
                "scores": [
                    {"timestamp": "2026-01-31T10:00:00Z", "score": 0.5},
                ],
                "alerts": [
                    {
                        "id": "DRIFT-001",
                        "type": "scope_creep",
                        "severity": "high",
                        "drift_score": 0.75,
                        "threshold": 0.7,
                        "root_intention_id": "INT-001",
                        "current_focus": "Extra work",
                        "message": "Drift detected",
                    }
                ],
                "current_score": 0.75,
                "trend": "worsening",
            }

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is True
            assert result["current_score"] == 0.75
            assert result["has_alerts"] is True
            assert result["alert_count"] == 1
            assert result["trend"] == "worsening"

    def test_missing_required_field(self) -> None:
        """Test that missing required field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data: dict = {"session_id": "test-session"}  # Missing root_intention_id

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is False
            assert "error" in result
            assert "root_intention_id" in result["error"]

    def test_invalid_score_range(self) -> None:
        """Test that out-of-range score causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data = {
                "session_id": "test-session",
                "root_intention_id": "INT-001",
                "current_score": 1.5,  # Invalid: > 1.0
            }

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is False
            assert "error" in result

    def test_invalid_alert_type(self) -> None:
        """Test that invalid alert type causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data = {
                "session_id": "test-session",
                "root_intention_id": "INT-001",
                "alerts": [
                    {
                        "id": "DRIFT-001",
                        "type": "invalid_type",
                        "severity": "high",
                        "message": "Test",
                    }
                ],
            }

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is False
            assert "type" in result["error"]

    def test_critical_count(self) -> None:
        """Test counting critical alerts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            drift_data = {
                "session_id": "test-session",
                "root_intention_id": "INT-001",
                "alerts": [
                    {
                        "id": "DRIFT-001",
                        "type": "scope_creep",
                        "severity": "critical",
                        "message": "Critical drift",
                    },
                    {
                        "id": "DRIFT-002",
                        "type": "goal_divergence",
                        "severity": "high",
                        "message": "High drift",
                    },
                ],
            }

            result = compute_drift_score(
                session_id="test-session",
                cwd=tmpdir,
                drift_data=drift_data,
            )

            assert result["success"] is True
            assert result["critical_count"] == 1
            assert result["alert_count"] == 2
