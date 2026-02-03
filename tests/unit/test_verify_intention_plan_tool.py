"""Tests for verify_intention_plan MCP tool."""

import json
import tempfile
from pathlib import Path

from mcp_servers.intention_audit.tools.verify_intention_plan import verify_intention_plan


class TestVerifyIntentionPlan:
    """Tests for verify_intention_plan tool."""

    def test_valid_passing_verification(self) -> None:
        """Test saving a passing verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {
                "passed": True,
                "issues": [],
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "intentions_checked": 5,
            }

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is True
            assert result["passed"] is True
            assert result["error_count"] == 0
            assert "path" in result

            # Verify file was created
            path = Path(result["path"])
            assert path.exists()

            # Verify content
            saved = json.loads(path.read_text())
            assert saved["passed"] is True
            assert saved["issues"] == []

    def test_valid_failing_verification(self) -> None:
        """Test saving a failing verification with issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {
                "passed": False,
                "issues": [
                    {
                        "type": "code_home_conflict",
                        "severity": "error",
                        "intent_id": "INT-2026-01-31-0001",
                        "message": "Code home paths overlap",
                    }
                ],
                "error_count": 1,
                "warning_count": 0,
            }

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is True
            assert result["passed"] is False
            assert result["error_count"] == 1

    def test_creates_artifact_directory(self) -> None:
        """Test that artifact directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {"passed": True, "issues": []}

            result = verify_intention_plan(
                session_id="new-session",
                diff_hash="newdiffhash1",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is True
            artifact_dir = Path(tmpdir) / ".intent_audit" / "new-session" / "newdiffhash1"
            assert artifact_dir.exists()

    def test_invalid_missing_passed(self) -> None:
        """Test that missing passed field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification: dict = {"issues": []}

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is False
            assert "error" in result
            assert "passed" in result["error"]

    def test_invalid_missing_issues(self) -> None:
        """Test that missing issues field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {"passed": True}

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is False
            assert "error" in result
            assert "issues" in result["error"]

    def test_invalid_issue_missing_fields(self) -> None:
        """Test that issues with missing required fields cause error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {
                "passed": True,
                "issues": [{"type": "missing_evidence"}],  # Missing severity, intent_id, message
            }

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is False
            assert "error" in result

    def test_verification_with_warnings_only(self) -> None:
        """Test verification that passes with warnings only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verification = {
                "passed": True,
                "issues": [
                    {
                        "type": "missing_evidence",
                        "severity": "warning",
                        "intent_id": "INT-2026-01-31-0001",
                        "message": "No evidence tests found",
                        "suggested_fix": "Add evidence_tests to the intention",
                    }
                ],
                "error_count": 0,
                "warning_count": 1,
            }

            result = verify_intention_plan(
                session_id="test-session",
                diff_hash="abc123def456",
                cwd=tmpdir,
                verification=verification,
            )

            assert result["success"] is True
            assert result["passed"] is True
            assert result["warning_count"] == 1
