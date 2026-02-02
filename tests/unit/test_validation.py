"""Unit tests for schema validation utilities."""

from intention_audit.models.validation import (
    validate_commit_plan,
    validate_intentions,
    validate_session_record,
)


class TestValidateIntentions:
    """Tests for validate_intentions function."""

    def test_valid_minimal_intention(self):
        """Test validation passes for minimal valid intention."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Root Goal",
            "kind": "goal",
            "status": "planned",
            "children": [],
        }
        errors = validate_intentions({"root": data})
        assert errors == []

    def test_valid_nested_intentions(self):
        """Test validation passes for nested intention tree."""
        data = {
            "root": {
                "id": "INT-2026-01-30-0001",
                "title": "Root",
                "kind": "goal",
                "status": "planned",
                "children": [
                    {
                        "id": "INT-2026-01-30-0002",
                        "title": "Child",
                        "kind": "functionality",
                        "status": "implemented",
                        "children": [],
                    }
                ],
            }
        }
        errors = validate_intentions(data)
        assert errors == []

    def test_missing_required_fields(self):
        """Test validation detects missing required fields."""
        data = {"root": {"title": "No ID"}}
        errors = validate_intentions(data)
        # Should report missing id and kind at minimum
        assert any("id" in e for e in errors)

    def test_invalid_kind_value(self):
        """Test validation detects invalid kind enum value."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Test",
            "kind": "invalid_kind",
            "status": "planned",
            "children": [],
        }
        errors = validate_intentions(data)
        assert any("kind" in e.lower() for e in errors)

    def test_invalid_status_value(self):
        """Test validation detects invalid status enum value."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Test",
            "kind": "goal",
            "status": "bad_status",
            "children": [],
        }
        errors = validate_intentions(data)
        assert any("status" in e.lower() for e in errors)

    def test_direct_intention_without_root_key(self):
        """Test validation handles direct intention data without 'root' wrapper."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Direct",
            "kind": "goal",
            "status": "planned",
            "children": [],
        }
        # Should wrap in {"root": data} internally
        errors = validate_intentions(data)
        assert errors == []


class TestValidateCommitPlan:
    """Tests for validate_commit_plan function."""

    def test_valid_minimal_plan(self):
        """Test validation passes for minimal valid plan."""
        data = {
            "version": 1,
            "ready": True,
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": [
                {
                    "intent_id": "INT-2026-01-30-0001",
                    "functionality_intent_id": "INT-2026-01-30-0002",
                    "subject": "feat: test",
                    "patch": "--- a/file\n+++ b/file\n",
                }
            ],
        }
        errors = validate_commit_plan(data)
        assert errors == []

    def test_invalid_version(self):
        """Test validation detects invalid version."""
        data = {
            "version": 2,  # Only version 1 is valid
            "ready": True,
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": [],
        }
        errors = validate_commit_plan(data)
        assert any("version" in e.lower() for e in errors)

    def test_missing_required_fields(self):
        """Test validation detects missing required fields."""
        data = {"version": 1}  # Missing ready, diff_base, etc.
        errors = validate_commit_plan(data)
        assert len(errors) > 0

    def test_empty_commits_array(self):
        """Test validation detects empty commits array."""
        data = {
            "version": 1,
            "ready": True,
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": [],
        }
        errors = validate_commit_plan(data)
        assert any("commits" in e.lower() for e in errors)

    def test_commit_missing_intent_id(self):
        """Test validation detects commit entry missing intent_id."""
        data = {
            "version": 1,
            "ready": True,
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": [{"subject": "test", "patch": ""}],
        }
        errors = validate_commit_plan(data)
        assert any("intent_id" in e for e in errors)

    def test_type_mismatches(self):
        """Test validation detects type mismatches."""
        data = {
            "version": "1",  # Should be number
            "ready": "true",  # Should be boolean
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": "not an array",  # Should be array
        }
        errors = validate_commit_plan(data)
        assert len(errors) > 0


class TestValidateSessionRecord:
    """Tests for validate_session_record function."""

    def test_valid_session_record(self):
        """Test validation passes for valid session record."""
        data = {
            "session_id": "session-123",
            "timestamp": "2026-01-30T10:00:00Z",
            "transcript_ref": "hash-abc",
            "diff_base": "HEAD",
            "diff_hash": "diff-hash",
            "planner_tool": "mcp__intention_audit__plan@1.0",
            "intentions_touched": ["INT-2026-01-30-0001"],
            "mapping_summary": {"total_intentions": 3},
        }
        errors = validate_session_record(data)
        assert errors == []

    def test_missing_required_fields(self):
        """Test validation detects missing required fields."""
        data = {"session_id": "session-123"}
        errors = validate_session_record(data)
        assert len(errors) > 0

    def test_invalid_intentions_touched_type(self):
        """Test validation detects invalid intentions_touched type."""
        data = {
            "session_id": "session-123",
            "timestamp": "2026-01-30T10:00:00Z",
            "transcript_ref": "hash",
            "diff_base": "HEAD",
            "diff_hash": "hash",
            "planner_tool": "tool",
            "intentions_touched": "not an array",
            "mapping_summary": {},
        }
        errors = validate_session_record(data)
        assert any("intentions_touched" in e for e in errors)

    def test_invalid_mapping_summary_type(self):
        """Test validation detects invalid mapping_summary type."""
        data = {
            "session_id": "session-123",
            "timestamp": "2026-01-30T10:00:00Z",
            "transcript_ref": "hash",
            "diff_base": "HEAD",
            "diff_hash": "hash",
            "planner_tool": "tool",
            "intentions_touched": [],
            "mapping_summary": "not an object",
        }
        errors = validate_session_record(data)
        assert any("mapping_summary" in e for e in errors)
