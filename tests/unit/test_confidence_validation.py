"""Tests for confidence validation model and tool."""

import tempfile
from pathlib import Path

from intention_audit.models.confidence_validation import (
    ConfidenceThresholds,
    ConfidenceTier,
    ConfidenceValidationResult,
    IntentionConfidenceCheck,
    ValidationRequirement,
)
from mcp_servers.intention_audit.tools.validate_confidence import validate_confidence


class TestConfidenceThresholds:
    """Tests for ConfidenceThresholds dataclass."""

    def test_default_thresholds(self) -> None:
        """Test default threshold values."""
        thresholds = ConfidenceThresholds()

        assert thresholds.high_threshold == 0.8
        assert thresholds.medium_threshold == 0.5

    def test_from_dict(self) -> None:
        """Test creating thresholds from dict."""
        data: dict = {
            "high_threshold": 0.85,
            "medium_threshold": 0.6,
        }
        thresholds = ConfidenceThresholds.from_dict(data)

        assert thresholds.high_threshold == 0.85
        assert thresholds.medium_threshold == 0.6

    def test_get_tier_high(self) -> None:
        """Test getting high confidence tier."""
        thresholds = ConfidenceThresholds()

        assert thresholds.get_tier(0.9) == ConfidenceTier.HIGH
        assert thresholds.get_tier(0.8) == ConfidenceTier.HIGH

    def test_get_tier_medium(self) -> None:
        """Test getting medium confidence tier."""
        thresholds = ConfidenceThresholds()

        assert thresholds.get_tier(0.7) == ConfidenceTier.MEDIUM
        assert thresholds.get_tier(0.5) == ConfidenceTier.MEDIUM

    def test_get_tier_low(self) -> None:
        """Test getting low confidence tier."""
        thresholds = ConfidenceThresholds()

        assert thresholds.get_tier(0.4) == ConfidenceTier.LOW
        assert thresholds.get_tier(0.0) == ConfidenceTier.LOW

    def test_get_requirement(self) -> None:
        """Test getting validation requirements."""
        thresholds = ConfidenceThresholds()

        assert thresholds.get_requirement(0.9) == ValidationRequirement.STANDARD
        assert thresholds.get_requirement(0.7) == ValidationRequirement.ADDITIONAL_EVIDENCE
        assert thresholds.get_requirement(0.3) == ValidationRequirement.HUMAN_CONFIRMATION


class TestIntentionConfidenceCheck:
    """Tests for IntentionConfidenceCheck dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating check from minimal dict."""
        data: dict = {
            "intent_id": "INT-001",
            "confidence": 0.9,
            "tier": "high",
            "requirement": "standard",
        }
        check = IntentionConfidenceCheck.from_dict(data)

        assert check.intent_id == "INT-001"
        assert check.confidence == 0.9
        assert check.tier == ConfidenceTier.HIGH
        assert check.requirement == ValidationRequirement.STANDARD

    def test_from_dict_full(self) -> None:
        """Test creating check with all fields."""
        data: dict = {
            "intent_id": "INT-002",
            "confidence": 0.4,
            "tier": "low",
            "requirement": "human_confirmation",
            "has_evidence_tests": False,
            "human_confirmed": True,
            "confirmation_rationale": "Reviewed and approved",
            "passed": True,
            "message": "Low confidence confirmed by human",
        }
        check = IntentionConfidenceCheck.from_dict(data)

        assert check.human_confirmed is True
        assert check.confirmation_rationale == "Reviewed and approved"
        assert check.passed is True

    def test_to_dict(self) -> None:
        """Test serializing check to dict."""
        check = IntentionConfidenceCheck(
            intent_id="INT-003",
            confidence=0.75,
            tier=ConfidenceTier.MEDIUM,
            requirement=ValidationRequirement.ADDITIONAL_EVIDENCE,
            has_evidence_tests=True,
            evidence_tests_passed=True,
            passed=True,
            message="Medium confidence validated",
        )
        result = check.to_dict()

        assert result["intent_id"] == "INT-003"
        assert result["tier"] == "medium"
        assert result["requirement"] == "additional_evidence"


class TestConfidenceValidationResult:
    """Tests for ConfidenceValidationResult dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating result from minimal dict."""
        data: dict = {"passed": True}
        result = ConfidenceValidationResult.from_dict(data)

        assert result.passed is True
        assert result.checks == []

    def test_from_dict_full(self) -> None:
        """Test creating result with all fields."""
        data: dict = {
            "passed": False,
            "total_checked": 3,
            "high_confidence_count": 1,
            "medium_confidence_count": 1,
            "low_confidence_count": 1,
            "checks": [
                {
                    "intent_id": "INT-001",
                    "confidence": 0.9,
                    "tier": "high",
                    "requirement": "standard",
                    "passed": True,
                }
            ],
            "thresholds": {
                "high_threshold": 0.8,
                "medium_threshold": 0.5,
            },
            "needs_human_confirmation": ["INT-003"],
        }
        result = ConfidenceValidationResult.from_dict(data)

        assert result.total_checked == 3
        assert len(result.checks) == 1
        assert len(result.needs_human_confirmation) == 1

    def test_to_dict(self) -> None:
        """Test serializing result to dict."""
        result = ConfidenceValidationResult(
            passed=True,
            total_checked=2,
            high_confidence_count=2,
        )
        data = result.to_dict()

        assert data["passed"] is True
        assert data["total_checked"] == 2

    def test_get_failing_checks(self) -> None:
        """Test getting failing checks."""
        passing = IntentionConfidenceCheck(
            intent_id="INT-001",
            confidence=0.9,
            tier=ConfidenceTier.HIGH,
            requirement=ValidationRequirement.STANDARD,
            passed=True,
            message="OK",
        )
        failing = IntentionConfidenceCheck(
            intent_id="INT-002",
            confidence=0.3,
            tier=ConfidenceTier.LOW,
            requirement=ValidationRequirement.HUMAN_CONFIRMATION,
            passed=False,
            message="Needs confirmation",
        )

        result = ConfidenceValidationResult(
            passed=False,
            checks=[passing, failing],
        )

        failing_checks = result.get_failing_checks()
        assert len(failing_checks) == 1
        assert failing_checks[0].intent_id == "INT-002"

    def test_get_checks_by_tier(self) -> None:
        """Test getting checks by tier."""
        high = IntentionConfidenceCheck(
            intent_id="INT-001",
            confidence=0.9,
            tier=ConfidenceTier.HIGH,
            requirement=ValidationRequirement.STANDARD,
            passed=True,
            message="OK",
        )
        low = IntentionConfidenceCheck(
            intent_id="INT-002",
            confidence=0.3,
            tier=ConfidenceTier.LOW,
            requirement=ValidationRequirement.HUMAN_CONFIRMATION,
            passed=False,
            message="Needs confirmation",
        )

        result = ConfidenceValidationResult(
            passed=False,
            checks=[high, low],
        )

        high_checks = result.get_checks_by_tier(ConfidenceTier.HIGH)
        low_checks = result.get_checks_by_tier(ConfidenceTier.LOW)

        assert len(high_checks) == 1
        assert len(low_checks) == 1

    def test_has_blocking_issues(self) -> None:
        """Test has_blocking_issues method."""
        no_issues = ConfidenceValidationResult(passed=True)
        with_confirmation = ConfidenceValidationResult(
            passed=False,
            needs_human_confirmation=["INT-001"],
        )
        with_override = ConfidenceValidationResult(
            passed=False,
            needs_human_confirmation=["INT-001"],
            override_rationale="Approved by tech lead",
        )

        assert no_issues.has_blocking_issues() is False
        assert with_confirmation.has_blocking_issues() is True
        assert with_override.has_blocking_issues() is False

    def test_get_average_confidence(self) -> None:
        """Test calculating average confidence."""
        check1 = IntentionConfidenceCheck(
            intent_id="INT-001",
            confidence=0.8,
            tier=ConfidenceTier.HIGH,
            requirement=ValidationRequirement.STANDARD,
            passed=True,
            message="OK",
        )
        check2 = IntentionConfidenceCheck(
            intent_id="INT-002",
            confidence=0.6,
            tier=ConfidenceTier.MEDIUM,
            requirement=ValidationRequirement.ADDITIONAL_EVIDENCE,
            passed=True,
            message="OK",
        )

        result = ConfidenceValidationResult(
            passed=True,
            checks=[check1, check2],
        )

        assert result.get_average_confidence() == 0.7

    def test_get_average_confidence_empty(self) -> None:
        """Test average confidence with no checks."""
        result = ConfidenceValidationResult(passed=True)

        assert result.get_average_confidence() == 0.0


class TestValidateConfidence:
    """Tests for validate_confidence MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal validation data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validation: dict = {"passed": True}

            result = validate_confidence(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                validation=validation,
            )

            assert result["success"] is True
            assert result["passed"] is True
            assert Path(result["path"]).exists()

    def test_valid_with_checks(self) -> None:
        """Test saving validation with checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validation: dict = {
                "passed": False,
                "total_checked": 2,
                "checks": [
                    {
                        "intent_id": "INT-001",
                        "confidence": 0.9,
                        "tier": "high",
                        "requirement": "standard",
                    },
                    {
                        "intent_id": "INT-002",
                        "confidence": 0.3,
                        "tier": "low",
                        "requirement": "human_confirmation",
                    },
                ],
                "needs_human_confirmation": ["INT-002"],
            }

            result = validate_confidence(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                validation=validation,
            )

            assert result["success"] is True
            assert result["passed"] is False
            assert result["needs_confirmation"] == ["INT-002"]

    def test_missing_passed(self) -> None:
        """Test that missing passed field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validation: dict = {"total_checked": 5}

            result = validate_confidence(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                validation=validation,
            )

            assert result["success"] is False
            assert "passed" in result["error"]

    def test_invalid_confidence_range(self) -> None:
        """Test that invalid confidence range causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validation: dict = {
                "passed": True,
                "checks": [
                    {
                        "intent_id": "INT-001",
                        "confidence": 1.5,  # Invalid: > 1.0
                        "tier": "high",
                        "requirement": "standard",
                    }
                ],
            }

            result = validate_confidence(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                validation=validation,
            )

            assert result["success"] is False
            assert "confidence" in result["error"]

    def test_invalid_tier(self) -> None:
        """Test that invalid tier causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validation: dict = {
                "passed": True,
                "checks": [
                    {
                        "intent_id": "INT-001",
                        "confidence": 0.9,
                        "tier": "invalid_tier",
                        "requirement": "standard",
                    }
                ],
            }

            result = validate_confidence(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                validation=validation,
            )

            assert result["success"] is False
            assert "tier" in result["error"]
