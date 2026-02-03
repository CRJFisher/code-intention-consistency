"""Tests for plan verification model and validation."""

import json
import tempfile
from pathlib import Path

from intention_audit.models.plan_verification import (
    PlanVerification,
    VerificationIssue,
    VerificationIssueType,
    VerificationSeverity,
)
from intention_audit.models.validation import validate_plan_verification


class TestVerificationIssue:
    """Tests for VerificationIssue dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating VerificationIssue from minimal dict."""
        data = {
            "type": "missing_evidence",
            "severity": "warning",
            "intent_id": "INT-2026-01-31-0001",
            "message": "Implementation lacks evidence tests",
        }
        issue = VerificationIssue.from_dict(data)

        assert issue.type == VerificationIssueType.MISSING_EVIDENCE
        assert issue.severity == VerificationSeverity.WARNING
        assert issue.intent_id == "INT-2026-01-31-0001"
        assert issue.message == "Implementation lacks evidence tests"
        assert issue.related_intent_ids == []
        assert issue.conflicting_paths == []
        assert issue.suggested_fix is None
        assert issue.details is None

    def test_from_dict_full(self) -> None:
        """Test creating VerificationIssue with all fields."""
        data = {
            "type": "code_home_conflict",
            "severity": "error",
            "intent_id": "INT-2026-01-31-0001",
            "message": "Code home paths overlap",
            "related_intent_ids": ["INT-2026-01-31-0002"],
            "conflicting_paths": ["src/auth/"],
            "suggested_fix": "Separate the code_home paths",
            "details": {"overlap_percentage": 80},
        }
        issue = VerificationIssue.from_dict(data)

        assert issue.type == VerificationIssueType.CODE_HOME_CONFLICT
        assert issue.severity == VerificationSeverity.ERROR
        assert issue.related_intent_ids == ["INT-2026-01-31-0002"]
        assert issue.conflicting_paths == ["src/auth/"]
        assert issue.suggested_fix == "Separate the code_home paths"
        assert issue.details == {"overlap_percentage": 80}

    def test_to_dict_minimal(self) -> None:
        """Test serializing VerificationIssue to dict."""
        issue = VerificationIssue(
            type=VerificationIssueType.ORPHAN_INTENTION,
            severity=VerificationSeverity.ERROR,
            intent_id="INT-2026-01-31-0003",
            message="Intention has no parent chain to goal",
        )
        result = issue.to_dict()

        assert result == {
            "type": "orphan_intention",
            "severity": "error",
            "intent_id": "INT-2026-01-31-0003",
            "message": "Intention has no parent chain to goal",
        }

    def test_to_dict_full(self) -> None:
        """Test serializing VerificationIssue with all fields."""
        issue = VerificationIssue(
            type=VerificationIssueType.SCOPE_OVERLAP,
            severity=VerificationSeverity.WARNING,
            intent_id="INT-2026-01-31-0004",
            message="Multiple intentions affect same files",
            related_intent_ids=["INT-2026-01-31-0005"],
            conflicting_paths=["src/utils.py"],
            suggested_fix="Consolidate into single intention",
            details={"affected_files": 3},
        )
        result = issue.to_dict()

        assert result["related_intent_ids"] == ["INT-2026-01-31-0005"]
        assert result["conflicting_paths"] == ["src/utils.py"]
        assert result["suggested_fix"] == "Consolidate into single intention"
        assert result["details"] == {"affected_files": 3}


class TestPlanVerification:
    """Tests for PlanVerification dataclass."""

    def test_from_dict_passing(self) -> None:
        """Test creating PlanVerification that passes."""
        data = {
            "passed": True,
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "intentions_checked": 5,
            "code_homes_validated": 2,
            "evidence_tests_found": 3,
        }
        verification = PlanVerification.from_dict(data)

        assert verification.passed is True
        assert verification.issues == []
        assert verification.error_count == 0
        assert verification.intentions_checked == 5

    def test_from_dict_with_issues(self) -> None:
        """Test creating PlanVerification with issues."""
        data = {
            "passed": True,
            "issues": [
                {
                    "type": "missing_evidence",
                    "severity": "warning",
                    "intent_id": "INT-2026-01-31-0001",
                    "message": "No evidence tests",
                }
            ],
            "error_count": 0,
            "warning_count": 1,
            "info_count": 0,
        }
        verification = PlanVerification.from_dict(data)

        assert verification.passed is True
        assert len(verification.issues) == 1
        assert verification.issues[0].type == VerificationIssueType.MISSING_EVIDENCE
        assert verification.warning_count == 1

    def test_from_dict_failing(self) -> None:
        """Test creating PlanVerification that fails."""
        data = {
            "passed": False,
            "issues": [
                {
                    "type": "code_home_conflict",
                    "severity": "error",
                    "intent_id": "INT-2026-01-31-0001",
                    "message": "Conflicting paths",
                }
            ],
            "error_count": 1,
            "warning_count": 0,
            "info_count": 0,
        }
        verification = PlanVerification.from_dict(data)

        assert verification.passed is False
        assert verification.error_count == 1

    def test_to_dict(self) -> None:
        """Test serializing PlanVerification to dict."""
        verification = PlanVerification(
            passed=True,
            issues=[],
            error_count=0,
            warning_count=0,
            info_count=0,
            intentions_checked=3,
            code_homes_validated=1,
            evidence_tests_found=2,
        )
        result = verification.to_dict()

        assert result["passed"] is True
        assert result["issues"] == []
        assert result["intentions_checked"] == 3

    def test_has_errors(self) -> None:
        """Test has_errors method."""
        issue_error = VerificationIssue(
            type=VerificationIssueType.ORPHAN_INTENTION,
            severity=VerificationSeverity.ERROR,
            intent_id="INT-001",
            message="Error",
        )
        issue_warning = VerificationIssue(
            type=VerificationIssueType.MISSING_EVIDENCE,
            severity=VerificationSeverity.WARNING,
            intent_id="INT-002",
            message="Warning",
        )

        verification_with_error = PlanVerification(passed=False, issues=[issue_error])
        verification_with_warning = PlanVerification(passed=True, issues=[issue_warning])

        assert verification_with_error.has_errors() is True
        assert verification_with_warning.has_errors() is False

    def test_get_errors_and_warnings(self) -> None:
        """Test get_errors and get_warnings methods."""
        error = VerificationIssue(
            type=VerificationIssueType.ORPHAN_INTENTION,
            severity=VerificationSeverity.ERROR,
            intent_id="INT-001",
            message="Error",
        )
        warning = VerificationIssue(
            type=VerificationIssueType.MISSING_EVIDENCE,
            severity=VerificationSeverity.WARNING,
            intent_id="INT-002",
            message="Warning",
        )

        verification = PlanVerification(passed=False, issues=[error, warning])

        assert len(verification.get_errors()) == 1
        assert len(verification.get_warnings()) == 1
        assert verification.get_errors()[0].intent_id == "INT-001"
        assert verification.get_warnings()[0].intent_id == "INT-002"

    def test_load_from_file(self) -> None:
        """Test loading PlanVerification from JSON file."""
        data = {
            "passed": True,
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)

        try:
            verification = PlanVerification.load(path)
            assert verification.passed is True
            assert verification.issues == []
        finally:
            path.unlink()


class TestValidatePlanVerification:
    """Tests for validate_plan_verification function."""

    def test_valid_minimal(self) -> None:
        """Test validation of minimal valid data."""
        data = {"passed": True, "issues": []}
        errors = validate_plan_verification(data)
        assert errors == []

    def test_valid_with_issues(self) -> None:
        """Test validation of data with valid issues."""
        data = {
            "passed": False,
            "issues": [
                {
                    "type": "code_home_conflict",
                    "severity": "error",
                    "intent_id": "INT-2026-01-31-0001",
                    "message": "Paths conflict",
                }
            ],
            "error_count": 1,
            "warning_count": 0,
        }
        errors = validate_plan_verification(data)
        assert errors == []

    def test_missing_passed(self) -> None:
        """Test validation fails when passed is missing."""
        data: dict = {"issues": []}
        errors = validate_plan_verification(data)
        assert any("passed" in e for e in errors)

    def test_missing_issues(self) -> None:
        """Test validation fails when issues is missing."""
        data = {"passed": True}
        errors = validate_plan_verification(data)
        assert any("issues" in e for e in errors)

    def test_invalid_passed_type(self) -> None:
        """Test validation fails when passed is not boolean."""
        data = {"passed": "yes", "issues": []}
        errors = validate_plan_verification(data)
        assert any("boolean" in e for e in errors)

    def test_invalid_issues_type(self) -> None:
        """Test validation fails when issues is not an array."""
        data = {"passed": True, "issues": "not an array"}
        errors = validate_plan_verification(data)
        assert any("array" in e for e in errors)

    def test_invalid_issue_type_value(self) -> None:
        """Test validation fails for invalid issue type."""
        data = {
            "passed": True,
            "issues": [
                {
                    "type": "invalid_type",
                    "severity": "error",
                    "intent_id": "INT-001",
                    "message": "Test",
                }
            ],
        }
        errors = validate_plan_verification(data)
        assert any("type" in e for e in errors)

    def test_invalid_severity_value(self) -> None:
        """Test validation fails for invalid severity."""
        data = {
            "passed": True,
            "issues": [
                {
                    "type": "missing_evidence",
                    "severity": "critical",
                    "intent_id": "INT-001",
                    "message": "Test",
                }
            ],
        }
        errors = validate_plan_verification(data)
        assert any("severity" in e for e in errors)

    def test_missing_issue_required_fields(self) -> None:
        """Test validation fails when issue is missing required fields."""
        data = {
            "passed": True,
            "issues": [{"type": "missing_evidence"}],
        }
        errors = validate_plan_verification(data)
        assert any("severity" in e for e in errors)
        assert any("intent_id" in e for e in errors)
        assert any("message" in e for e in errors)

    def test_invalid_count_type(self) -> None:
        """Test validation fails when counts are not integers."""
        data = {"passed": True, "issues": [], "error_count": "zero"}
        errors = validate_plan_verification(data)
        assert any("error_count" in e and "integer" in e for e in errors)

    def test_invalid_override_rationale_type(self) -> None:
        """Test validation fails when override_rationale is not string."""
        data = {"passed": True, "issues": [], "override_rationale": 123}
        errors = validate_plan_verification(data)
        assert any("override_rationale" in e for e in errors)
