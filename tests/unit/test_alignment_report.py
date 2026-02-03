"""Tests for alignment report model and validation."""

import json
import tempfile
from pathlib import Path

from intention_audit.models.alignment_report import (
    AlignmentReport,
    AlignmentStatus,
    IntentComparison,
)
from intention_audit.models.validation import validate_alignment_report


class TestIntentComparison:
    """Tests for IntentComparison dataclass."""

    def test_from_dict_aligned(self) -> None:
        """Test creating aligned IntentComparison from dict."""
        data = {
            "declared_intent_id": "INT-2026-01-31-0001",
            "inferred_intent_id": "INT-2026-01-31-0001",
            "declared_title": "Add login feature",
            "inferred_title": "Add login feature",
            "status": "aligned",
            "confidence": 0.95,
            "declared_files": ["src/auth/login.py"],
            "inferred_files": ["src/auth/login.py"],
            "overlapping_files": ["src/auth/login.py"],
        }
        comp = IntentComparison.from_dict(data)

        assert comp.status == AlignmentStatus.ALIGNED
        assert comp.confidence == 0.95
        assert comp.declared_intent_id == "INT-2026-01-31-0001"
        assert comp.overlapping_files == ["src/auth/login.py"]

    def test_from_dict_missing_declared(self) -> None:
        """Test creating IntentComparison for undeclared code."""
        data = {
            "declared_intent_id": None,
            "inferred_intent_id": "inferred-001",
            "declared_title": None,
            "inferred_title": "Config updates",
            "status": "missing_declared",
            "confidence": 0.80,
            "extra_files": [".env.example"],
            "message": "Configuration changes not declared",
        }
        comp = IntentComparison.from_dict(data)

        assert comp.status == AlignmentStatus.MISSING_DECLARED
        assert comp.declared_intent_id is None
        assert comp.extra_files == [".env.example"]

    def test_to_dict(self) -> None:
        """Test serializing IntentComparison to dict."""
        comp = IntentComparison(
            declared_intent_id="INT-001",
            inferred_intent_id="INT-001",
            declared_title="Test feature",
            inferred_title="Test feature",
            status=AlignmentStatus.ALIGNED,
            confidence=0.90,
            declared_files=["src/test.py"],
            inferred_files=["src/test.py"],
            overlapping_files=["src/test.py"],
        )
        result = comp.to_dict()

        assert result["status"] == "aligned"
        assert result["confidence"] == 0.90
        assert result["declared_intent_id"] == "INT-001"


class TestAlignmentReport:
    """Tests for AlignmentReport dataclass."""

    def test_from_dict_aligned(self) -> None:
        """Test creating aligned AlignmentReport from dict."""
        data = {
            "aligned": True,
            "comparisons": [
                {
                    "declared_intent_id": "INT-001",
                    "inferred_intent_id": "INT-001",
                    "status": "aligned",
                    "confidence": 0.95,
                }
            ],
            "total_declared": 1,
            "total_inferred": 1,
            "aligned_count": 1,
            "alignment_score": 1.0,
        }
        report = AlignmentReport.from_dict(data)

        assert report.aligned is True
        assert len(report.comparisons) == 1
        assert report.aligned_count == 1
        assert report.alignment_score == 1.0

    def test_from_dict_with_misalignments(self) -> None:
        """Test creating AlignmentReport with misalignments."""
        data = {
            "aligned": False,
            "comparisons": [
                {"status": "aligned", "confidence": 0.90},
                {"status": "misaligned", "confidence": 0.60},
            ],
            "aligned_count": 1,
            "misaligned_count": 1,
            "alignment_score": 0.50,
        }
        report = AlignmentReport.from_dict(data)

        assert report.aligned is False
        assert report.misaligned_count == 1

    def test_to_dict(self) -> None:
        """Test serializing AlignmentReport to dict."""
        report = AlignmentReport(
            aligned=True,
            comparisons=[],
            total_declared=0,
            total_inferred=0,
            alignment_score=1.0,
        )
        result = report.to_dict()

        assert result["aligned"] is True
        assert result["comparisons"] == []
        assert result["alignment_score"] == 1.0

    def test_get_misalignments(self) -> None:
        """Test get_misalignments method."""
        aligned = IntentComparison(
            declared_intent_id="INT-001",
            inferred_intent_id="INT-001",
            declared_title="A",
            inferred_title="A",
            status=AlignmentStatus.ALIGNED,
            confidence=0.9,
        )
        misaligned = IntentComparison(
            declared_intent_id="INT-002",
            inferred_intent_id="INT-002",
            declared_title="B",
            inferred_title="C",
            status=AlignmentStatus.MISALIGNED,
            confidence=0.5,
        )
        missing = IntentComparison(
            declared_intent_id=None,
            inferred_intent_id="inferred-001",
            declared_title=None,
            inferred_title="D",
            status=AlignmentStatus.MISSING_DECLARED,
            confidence=0.7,
        )

        report = AlignmentReport(
            aligned=False,
            comparisons=[aligned, misaligned, missing],
        )

        misalignments = report.get_misalignments()
        assert len(misalignments) == 2
        assert misaligned in misalignments
        assert missing in misalignments

    def test_get_aligned(self) -> None:
        """Test get_aligned method."""
        aligned = IntentComparison(
            declared_intent_id="INT-001",
            inferred_intent_id="INT-001",
            declared_title="A",
            inferred_title="A",
            status=AlignmentStatus.ALIGNED,
            confidence=0.9,
        )
        partial = IntentComparison(
            declared_intent_id="INT-002",
            inferred_intent_id="INT-002",
            declared_title="B",
            inferred_title="B+",
            status=AlignmentStatus.PARTIAL,
            confidence=0.7,
        )

        report = AlignmentReport(aligned=True, comparisons=[aligned, partial])

        aligned_list = report.get_aligned()
        assert len(aligned_list) == 1
        assert aligned in aligned_list

    def test_needs_review(self) -> None:
        """Test needs_review method."""
        good_report = AlignmentReport(
            aligned=True,
            comparisons=[],
            misaligned_count=0,
            missing_declared_count=0,
        )
        bad_report = AlignmentReport(
            aligned=False,
            comparisons=[],
            misaligned_count=1,
            missing_declared_count=0,
        )

        assert good_report.needs_review() is False
        assert bad_report.needs_review() is True

    def test_load_from_file(self) -> None:
        """Test loading AlignmentReport from JSON file."""
        data = {
            "aligned": True,
            "comparisons": [],
            "alignment_score": 1.0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)

        try:
            report = AlignmentReport.load(path)
            assert report.aligned is True
        finally:
            path.unlink()


class TestValidateAlignmentReport:
    """Tests for validate_alignment_report function."""

    def test_valid_minimal(self) -> None:
        """Test validation of minimal valid data."""
        data = {"aligned": True, "comparisons": []}
        errors = validate_alignment_report(data)
        assert errors == []

    def test_valid_with_comparisons(self) -> None:
        """Test validation of data with valid comparisons."""
        data = {
            "aligned": True,
            "comparisons": [
                {"status": "aligned", "confidence": 0.95},
                {"status": "partial", "confidence": 0.70},
            ],
            "alignment_score": 0.85,
        }
        errors = validate_alignment_report(data)
        assert errors == []

    def test_missing_aligned(self) -> None:
        """Test validation fails when aligned is missing."""
        data: dict = {"comparisons": []}
        errors = validate_alignment_report(data)
        assert any("aligned" in e for e in errors)

    def test_missing_comparisons(self) -> None:
        """Test validation fails when comparisons is missing."""
        data = {"aligned": True}
        errors = validate_alignment_report(data)
        assert any("comparisons" in e for e in errors)

    def test_invalid_aligned_type(self) -> None:
        """Test validation fails when aligned is not boolean."""
        data = {"aligned": "yes", "comparisons": []}
        errors = validate_alignment_report(data)
        assert any("boolean" in e for e in errors)

    def test_invalid_comparisons_type(self) -> None:
        """Test validation fails when comparisons is not an array."""
        data = {"aligned": True, "comparisons": "not an array"}
        errors = validate_alignment_report(data)
        assert any("array" in e for e in errors)

    def test_invalid_status_value(self) -> None:
        """Test validation fails for invalid status."""
        data = {
            "aligned": True,
            "comparisons": [{"status": "invalid_status", "confidence": 0.5}],
        }
        errors = validate_alignment_report(data)
        assert any("status" in e for e in errors)

    def test_invalid_confidence_range(self) -> None:
        """Test validation fails for out-of-range confidence."""
        data = {
            "aligned": True,
            "comparisons": [{"status": "aligned", "confidence": 1.5}],
        }
        errors = validate_alignment_report(data)
        assert any("confidence" in e and "0.0" in e for e in errors)

    def test_invalid_score_range(self) -> None:
        """Test validation fails for out-of-range score."""
        data = {"aligned": True, "comparisons": [], "alignment_score": 1.5}
        errors = validate_alignment_report(data)
        assert any("alignment_score" in e for e in errors)

    def test_invalid_count_type(self) -> None:
        """Test validation fails when counts are not integers."""
        data = {"aligned": True, "comparisons": [], "aligned_count": "five"}
        errors = validate_alignment_report(data)
        assert any("aligned_count" in e and "integer" in e for e in errors)
