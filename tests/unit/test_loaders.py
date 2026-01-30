"""Unit tests for YAML/JSON loaders."""

import json
from pathlib import Path

import pytest
import yaml

from intention_audit.models.loaders import load_commit_plan, load_intentions, load_session_record


class TestLoadIntentions:
    """Tests for load_intentions function."""

    def test_load_valid_yaml(self, tmp_path: Path):
        """Test loading valid YAML intentions file."""
        content = {
            "id": "INT-2026-01-30-0001",
            "title": "Root Goal",
            "kind": "goal",
            "status": "planned",
            "children": [
                {
                    "id": "INT-2026-01-30-0002",
                    "title": "Feature",
                    "kind": "functionality",
                    "code_home": ["src/feature/"],
                }
            ],
        }
        path = tmp_path / "intentions.yaml"
        path.write_text(yaml.dump(content))

        result = load_intentions(path)

        assert result.id == "INT-2026-01-30-0001"
        assert result.title == "Root Goal"
        assert len(result.children) == 1
        assert result.children[0].code_home == ["src/feature/"]

    def test_load_valid_json(self, tmp_path: Path):
        """Test loading valid JSON intentions file."""
        content = {
            "id": "INT-2026-01-30-0001",
            "title": "Root Goal",
            "kind": "goal",
        }
        path = tmp_path / "intentions.json"
        path.write_text(json.dumps(content))

        result = load_intentions(path)
        assert result.id == "INT-2026-01-30-0001"

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_intentions(Path("/nonexistent/intentions.yaml"))

    def test_invalid_yaml(self, tmp_path: Path):
        """Test error on invalid YAML."""
        path = tmp_path / "bad.yaml"
        path.write_text("invalid: yaml: content: [\n")

        with pytest.raises(ValueError, match="Failed to parse"):
            load_intentions(path)

    def test_missing_id_field(self, tmp_path: Path):
        """Test error when root intention lacks id."""
        content = {"title": "No ID", "kind": "goal"}
        path = tmp_path / "intentions.yaml"
        path.write_text(yaml.dump(content))

        with pytest.raises(ValueError, match="must have a root intention with 'id'"):
            load_intentions(path)

    def test_non_mapping_content(self, tmp_path: Path):
        """Test error when file contains non-mapping."""
        path = tmp_path / "intentions.yaml"
        path.write_text("- item1\n- item2\n")

        with pytest.raises(ValueError, match="must contain a mapping"):
            load_intentions(path)


class TestLoadCommitPlan:
    """Tests for load_commit_plan function."""

    def test_load_valid_yaml(self, tmp_path: Path):
        """Test loading valid YAML commit plan."""
        content = {
            "version": 1,
            "ready": True,
            "diff_base": "HEAD",
            "commits": [
                {
                    "intent_id": "INT-2026-01-30-0001",
                    "subject": "feat: test",
                    "files": ["src/test.py"],
                }
            ],
        }
        path = tmp_path / "commit_plan.yaml"
        path.write_text(yaml.dump(content))

        result = load_commit_plan(path)

        assert result.version == 1
        assert result.ready is True
        assert result.diff_base == "HEAD"
        assert len(result.commits) == 1

    def test_load_valid_json(self, tmp_path: Path):
        """Test loading valid JSON commit plan."""
        content = {
            "version": 1,
            "ready": True,
            "commits": [],
        }
        path = tmp_path / "commit_plan.json"
        path.write_text(json.dumps(content))

        result = load_commit_plan(path)
        assert result.version == 1

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_commit_plan(Path("/nonexistent/commit_plan.yaml"))

    def test_invalid_yaml(self, tmp_path: Path):
        """Test error on invalid YAML."""
        path = tmp_path / "bad.yaml"
        path.write_text("invalid: yaml: [\n")

        with pytest.raises(ValueError, match="Failed to parse"):
            load_commit_plan(path)

    def test_non_mapping_content(self, tmp_path: Path):
        """Test error when file contains non-mapping."""
        path = tmp_path / "plan.yaml"
        path.write_text("- item\n")

        with pytest.raises(ValueError, match="must contain a mapping"):
            load_commit_plan(path)


class TestLoadSessionRecord:
    """Tests for load_session_record function."""

    def test_load_valid_json(self, tmp_path: Path):
        """Test loading valid session record."""
        content = {
            "session_id": "session-123",
            "timestamp": "2026-01-30T10:00:00Z",
            "transcript_ref": "hash-abc",
            "diff_base": "HEAD",
            "diff_hash": "diff-hash",
            "planner_tool": "mcp__intention_audit__plan_commits@1.0",
            "intentions_touched": ["INT-2026-01-30-0001"],
            "mapping_summary": {
                "total_intentions": 3,
                "new_intentions": 1,
                "commits_planned": 2,
            },
        }
        path = tmp_path / "session.json"
        path.write_text(json.dumps(content))

        result = load_session_record(path)

        assert result.session_id == "session-123"
        assert result.timestamp == "2026-01-30T10:00:00Z"
        assert result.mapping_summary.total_intentions == 3

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_session_record(Path("/nonexistent/session.json"))

    def test_invalid_json(self, tmp_path: Path):
        """Test error on invalid JSON."""
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")

        with pytest.raises(ValueError, match="Failed to parse"):
            load_session_record(path)

    def test_missing_session_id(self, tmp_path: Path):
        """Test error when session_id is missing."""
        content = {"timestamp": "2026-01-30T10:00:00Z"}
        path = tmp_path / "session.json"
        path.write_text(json.dumps(content))

        with pytest.raises(ValueError, match="missing required field: session_id"):
            load_session_record(path)

    def test_missing_timestamp(self, tmp_path: Path):
        """Test error when timestamp is missing."""
        content = {"session_id": "session-123"}
        path = tmp_path / "session.json"
        path.write_text(json.dumps(content))

        with pytest.raises(ValueError, match="missing required field: timestamp"):
            load_session_record(path)

    def test_non_object_content(self, tmp_path: Path):
        """Test error when file contains non-object."""
        path = tmp_path / "session.json"
        path.write_text('["array", "content"]')

        with pytest.raises(ValueError, match="must contain an object"):
            load_session_record(path)
