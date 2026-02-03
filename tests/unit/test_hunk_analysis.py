"""Tests for hunk analysis model and tool."""

import json
import tempfile
from pathlib import Path

from intention_audit.models.hunk_analysis import (
    HunkAnalysis,
    HunkMapping,
    TangleDetection,
    TangleSeverity,
    TangleType,
)
from mcp_servers.intention_audit.tools.analyze_hunk_intents import analyze_hunk_intents


class TestHunkMapping:
    """Tests for HunkMapping dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating HunkMapping from minimal dict."""
        data = {
            "file_path": "src/auth/login.py",
            "hunk_index": 0,
            "start_line": 10,
            "end_line": 20,
            "intent_id": "INT-001",
        }
        mapping = HunkMapping.from_dict(data)

        assert mapping.file_path == "src/auth/login.py"
        assert mapping.hunk_index == 0
        assert mapping.start_line == 10
        assert mapping.end_line == 20
        assert mapping.intent_id == "INT-001"

    def test_from_dict_full(self) -> None:
        """Test creating HunkMapping with all fields."""
        data = {
            "file_path": "src/auth/login.py",
            "hunk_index": 0,
            "start_line": 10,
            "end_line": 20,
            "intent_id": "INT-001",
            "intent_confidence": 0.95,
            "semantic_purpose": "Add email validation",
            "dependencies": ["hunk_1", "hunk_2"],
        }
        mapping = HunkMapping.from_dict(data)

        assert mapping.intent_confidence == 0.95
        assert mapping.semantic_purpose == "Add email validation"
        assert len(mapping.dependencies) == 2

    def test_to_dict(self) -> None:
        """Test serializing HunkMapping to dict."""
        mapping = HunkMapping(
            file_path="src/test.py",
            hunk_index=1,
            start_line=5,
            end_line=15,
            intent_id="INT-002",
            intent_confidence=0.85,
            semantic_purpose="Test serialization",
        )
        result = mapping.to_dict()

        assert result["file_path"] == "src/test.py"
        assert result["hunk_index"] == 1
        assert result["intent_confidence"] == 0.85


class TestTangleDetection:
    """Tests for TangleDetection dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating TangleDetection from minimal dict."""
        data = {
            "file_path": "src/auth/login.py",
            "type": "semantic",
            "severity": "medium",
            "hunk_indices": [0, 1],
            "intent_ids": ["INT-001", "INT-002"],
            "message": "Mixed changes detected",
        }
        tangle = TangleDetection.from_dict(data)

        assert tangle.file_path == "src/auth/login.py"
        assert tangle.type == TangleType.SEMANTIC
        assert tangle.severity == TangleSeverity.MEDIUM
        assert len(tangle.hunk_indices) == 2

    def test_from_dict_full(self) -> None:
        """Test creating TangleDetection with all fields."""
        data = {
            "file_path": "src/auth/login.py",
            "type": "functional",
            "severity": "high",
            "hunk_indices": [0, 1, 2],
            "intent_ids": ["INT-001", "INT-002"],
            "message": "Multiple functions mixed",
            "suggested_split": [
                {"hunks": [0], "intent_id": "INT-001"},
                {"hunks": [1, 2], "intent_id": "INT-002"},
            ],
            "explicit_evidence": "Different functions modified",
            "implicit_evidence": "Semantic purposes differ",
        }
        tangle = TangleDetection.from_dict(data)

        assert tangle.type == TangleType.FUNCTIONAL
        assert tangle.severity == TangleSeverity.HIGH
        assert len(tangle.suggested_split) == 2
        assert tangle.explicit_evidence is not None

    def test_to_dict(self) -> None:
        """Test serializing TangleDetection to dict."""
        tangle = TangleDetection(
            file_path="src/test.py",
            type=TangleType.STRUCTURAL,
            severity=TangleSeverity.LOW,
            hunk_indices=[0],
            intent_ids=["INT-001"],
            message="Minor structural issue",
        )
        result = tangle.to_dict()

        assert result["type"] == "structural"
        assert result["severity"] == "low"


class TestHunkAnalysis:
    """Tests for HunkAnalysis dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating HunkAnalysis from minimal dict."""
        data = {"passed": True}
        analysis = HunkAnalysis.from_dict(data)

        assert analysis.passed is True
        assert analysis.hunk_mappings == []
        assert analysis.tangles == []

    def test_from_dict_full(self) -> None:
        """Test creating HunkAnalysis with mappings and tangles."""
        data = {
            "passed": True,
            "total_hunks": 3,
            "files_analyzed": 2,
            "hunk_mappings": [
                {
                    "file_path": "src/a.py",
                    "hunk_index": 0,
                    "start_line": 1,
                    "end_line": 10,
                    "intent_id": "INT-001",
                }
            ],
            "tangles": [
                {
                    "file_path": "src/b.py",
                    "type": "semantic",
                    "severity": "medium",
                    "hunk_indices": [0, 1],
                    "intent_ids": ["INT-001", "INT-002"],
                    "message": "Mixed",
                }
            ],
            "clean_files": 1,
            "tangled_files": 1,
            "medium_tangles": 1,
        }
        analysis = HunkAnalysis.from_dict(data)

        assert len(analysis.hunk_mappings) == 1
        assert len(analysis.tangles) == 1
        assert analysis.clean_files == 1
        assert analysis.tangled_files == 1

    def test_to_dict(self) -> None:
        """Test serializing HunkAnalysis to dict."""
        analysis = HunkAnalysis(
            passed=True,
            total_hunks=5,
            files_analyzed=2,
        )
        result = analysis.to_dict()

        assert result["passed"] is True
        assert result["total_hunks"] == 5

    def test_get_high_severity_tangles(self) -> None:
        """Test getting high severity tangles."""
        high = TangleDetection(
            file_path="a.py",
            type=TangleType.SEMANTIC,
            severity=TangleSeverity.HIGH,
            hunk_indices=[0],
            intent_ids=["INT-001"],
            message="High",
        )
        medium = TangleDetection(
            file_path="b.py",
            type=TangleType.SEMANTIC,
            severity=TangleSeverity.MEDIUM,
            hunk_indices=[0],
            intent_ids=["INT-002"],
            message="Medium",
        )

        analysis = HunkAnalysis(passed=False, tangles=[high, medium])

        high_tangles = analysis.get_high_severity_tangles()
        assert len(high_tangles) == 1
        assert high_tangles[0].file_path == "a.py"

    def test_get_tangles_for_file(self) -> None:
        """Test getting tangles for specific file."""
        t1 = TangleDetection(
            file_path="src/a.py",
            type=TangleType.SEMANTIC,
            severity=TangleSeverity.LOW,
            hunk_indices=[0],
            intent_ids=["INT-001"],
            message="T1",
        )
        t2 = TangleDetection(
            file_path="src/b.py",
            type=TangleType.SEMANTIC,
            severity=TangleSeverity.LOW,
            hunk_indices=[0],
            intent_ids=["INT-002"],
            message="T2",
        )

        analysis = HunkAnalysis(passed=True, tangles=[t1, t2])

        a_tangles = analysis.get_tangles_for_file("src/a.py")
        assert len(a_tangles) == 1
        assert a_tangles[0].message == "T1"

    def test_has_blocking_tangles(self) -> None:
        """Test has_blocking_tangles method."""
        no_high = HunkAnalysis(passed=True, high_tangles=0)
        with_high = HunkAnalysis(passed=False, high_tangles=1)
        with_override = HunkAnalysis(passed=False, high_tangles=1, override_rationale="Approved")

        assert no_high.has_blocking_tangles() is False
        assert with_high.has_blocking_tangles() is True
        assert with_override.has_blocking_tangles() is False

    def test_load_from_file(self) -> None:
        """Test loading HunkAnalysis from JSON file."""
        data = {"passed": True, "total_hunks": 3}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)

        try:
            analysis = HunkAnalysis.load(path)
            assert analysis.passed is True
            assert analysis.total_hunks == 3
        finally:
            path.unlink()


class TestAnalyzeHunkIntents:
    """Tests for analyze_hunk_intents MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal hunk analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = {"passed": True}

            result = analyze_hunk_intents(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                analysis=analysis,
            )

            assert result["success"] is True
            assert result["passed"] is True
            assert Path(result["path"]).exists()

    def test_valid_with_mappings_and_tangles(self) -> None:
        """Test saving analysis with mappings and tangles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = {
                "passed": True,
                "total_hunks": 3,
                "files_analyzed": 2,
                "hunk_mappings": [
                    {
                        "file_path": "src/a.py",
                        "hunk_index": 0,
                        "start_line": 1,
                        "end_line": 10,
                        "intent_id": "INT-001",
                    }
                ],
                "tangles": [
                    {
                        "file_path": "src/b.py",
                        "type": "semantic",
                        "severity": "medium",
                        "hunk_indices": [0, 1],
                        "intent_ids": ["INT-001", "INT-002"],
                        "message": "Mixed changes",
                    }
                ],
            }

            result = analyze_hunk_intents(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                analysis=analysis,
            )

            assert result["success"] is True
            assert result["tangle_count"] == 1
            assert result["files_analyzed"] == 2

    def test_missing_passed(self) -> None:
        """Test that missing passed field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis: dict = {"total_hunks": 5}

            result = analyze_hunk_intents(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                analysis=analysis,
            )

            assert result["success"] is False
            assert "passed" in result["error"]

    def test_invalid_tangle_type(self) -> None:
        """Test that invalid tangle type causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = {
                "passed": True,
                "tangles": [
                    {
                        "file_path": "a.py",
                        "type": "invalid_type",
                        "severity": "high",
                        "hunk_indices": [0],
                        "intent_ids": ["INT-001"],
                        "message": "Test",
                    }
                ],
            }

            result = analyze_hunk_intents(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                analysis=analysis,
            )

            assert result["success"] is False
            assert "type" in result["error"]

    def test_high_tangle_count(self) -> None:
        """Test counting high severity tangles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = {
                "passed": False,
                "tangles": [
                    {
                        "file_path": "a.py",
                        "type": "semantic",
                        "severity": "high",
                        "hunk_indices": [0],
                        "intent_ids": ["INT-001"],
                        "message": "High",
                    },
                    {
                        "file_path": "b.py",
                        "type": "semantic",
                        "severity": "medium",
                        "hunk_indices": [0],
                        "intent_ids": ["INT-002"],
                        "message": "Medium",
                    },
                ],
            }

            result = analyze_hunk_intents(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                analysis=analysis,
            )

            assert result["success"] is True
            assert result["tangle_count"] == 2
            assert result["high_tangle_count"] == 1
