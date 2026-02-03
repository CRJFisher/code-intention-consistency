"""Tests for memory context model and tools."""

import json
import tempfile
from pathlib import Path

from intention_audit.models.memory_context import (
    ActiveContext,
    IntentionSummary,
    MemoryTier,
    TieredContext,
)
from mcp_servers.intention_audit.tools.get_tiered_context import (
    get_tiered_context,
    save_tiered_context,
)


class TestIntentionSummary:
    """Tests for IntentionSummary dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating IntentionSummary from minimal dict."""
        data: dict = {
            "intent_id": "INT-001",
            "title": "User Authentication",
            "type": "goal",
        }
        summary = IntentionSummary.from_dict(data)

        assert summary.intent_id == "INT-001"
        assert summary.title == "User Authentication"
        assert summary.type == "goal"
        assert summary.status == "pending"

    def test_from_dict_full(self) -> None:
        """Test creating IntentionSummary with all fields."""
        data: dict = {
            "intent_id": "INT-002",
            "title": "Login Flow",
            "type": "functionality",
            "status": "completed",
            "outcome": "Implemented login with email/password",
            "parent_id": "INT-001",
            "child_ids": ["INT-003", "INT-004"],
        }
        summary = IntentionSummary.from_dict(data)

        assert summary.status == "completed"
        assert summary.outcome == "Implemented login with email/password"
        assert summary.parent_id == "INT-001"
        assert len(summary.child_ids) == 2

    def test_to_dict(self) -> None:
        """Test serializing IntentionSummary to dict."""
        summary = IntentionSummary(
            intent_id="INT-003",
            title="Email Validation",
            type="implementation",
            status="in_progress",
        )
        result = summary.to_dict()

        assert result["intent_id"] == "INT-003"
        assert result["title"] == "Email Validation"
        assert result["status"] == "in_progress"


class TestActiveContext:
    """Tests for ActiveContext dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating ActiveContext from minimal dict."""
        data: dict = {
            "intent_id": "INT-003",
            "title": "Email Validation",
            "type": "implementation",
        }
        context = ActiveContext.from_dict(data)

        assert context.intent_id == "INT-003"
        assert context.title == "Email Validation"
        assert context.description == ""

    def test_from_dict_full(self) -> None:
        """Test creating ActiveContext with all fields."""
        data: dict = {
            "intent_id": "INT-003",
            "title": "Email Validation",
            "description": "Validate email format for login",
            "type": "implementation",
            "acceptance_criteria": ["Must contain @", "Domain must be valid"],
            "evidence_tests": ["tests/test_email.py"],
            "code_home": ["src/auth/validation.py"],
            "related_files": ["src/auth/login.py"],
            "recent_changes": ["Added regex pattern"],
        }
        context = ActiveContext.from_dict(data)

        assert context.description == "Validate email format for login"
        assert len(context.acceptance_criteria) == 2
        assert len(context.evidence_tests) == 1
        assert len(context.code_home) == 1

    def test_to_dict(self) -> None:
        """Test serializing ActiveContext to dict."""
        context = ActiveContext(
            intent_id="INT-003",
            title="Email Validation",
            description="Validate email",
            type="implementation",
            acceptance_criteria=["Must contain @"],
        )
        result = context.to_dict()

        assert result["intent_id"] == "INT-003"
        assert result["description"] == "Validate email"
        assert len(result["acceptance_criteria"]) == 1


class TestTieredContext:
    """Tests for TieredContext dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating TieredContext from minimal dict."""
        data: dict = {
            "session_id": "test-session",
        }
        context = TieredContext.from_dict(data)

        assert context.session_id == "test-session"
        assert context.active_intention_path == []
        assert context.active is None
        assert context.recent == []

    def test_from_dict_full(self) -> None:
        """Test creating TieredContext with all tiers."""
        data: dict = {
            "session_id": "test-session",
            "active_intention_path": ["INT-001", "INT-002", "INT-003"],
            "active": {
                "intent_id": "INT-003",
                "title": "Email Validation",
                "description": "Validate email",
                "type": "implementation",
            },
            "recent": [
                {
                    "intent_id": "INT-002",
                    "title": "Login Flow",
                    "type": "functionality",
                    "status": "in_progress",
                }
            ],
            "archive": [
                {
                    "intent_id": "INT-001",
                    "title": "Authentication",
                    "type": "goal",
                    "status": "in_progress",
                }
            ],
            "total_intentions": 3,
            "active_tier_size": 500,
            "recent_tier_size": 200,
            "archive_tier_size": 100,
        }
        context = TieredContext.from_dict(data)

        assert len(context.active_intention_path) == 3
        assert context.active is not None
        assert context.active.intent_id == "INT-003"
        assert len(context.recent) == 1
        assert len(context.archive) == 1
        assert context.total_intentions == 3

    def test_to_dict(self) -> None:
        """Test serializing TieredContext to dict."""
        context = TieredContext(
            session_id="test-session",
            active_intention_path=["INT-001"],
            total_intentions=1,
            active_tier_size=100,
        )
        result = context.to_dict()

        assert result["session_id"] == "test-session"
        assert result["active_intention_path"] == ["INT-001"]
        assert result["total_intentions"] == 1

    def test_get_context_for_tier(self) -> None:
        """Test getting context by tier."""
        recent_summary = IntentionSummary(
            intent_id="INT-002",
            title="Login",
            type="functionality",
            status="in_progress",
        )
        archive_summary = IntentionSummary(
            intent_id="INT-001",
            title="Auth",
            type="goal",
            status="completed",
        )
        context = TieredContext(
            session_id="test",
            active_intention_path=[],
            recent=[recent_summary],
            archive=[archive_summary],
        )

        assert len(context.get_context_for_tier(MemoryTier.RECENT)) == 1
        assert len(context.get_context_for_tier(MemoryTier.ARCHIVE)) == 1
        assert context.get_context_for_tier(MemoryTier.ACTIVE) == []

    def test_get_total_context_size(self) -> None:
        """Test calculating total context size."""
        context = TieredContext(
            session_id="test",
            active_intention_path=[],
            active_tier_size=500,
            recent_tier_size=200,
            archive_tier_size=100,
        )

        assert context.get_total_context_size() == 800

    def test_is_intention_active(self) -> None:
        """Test checking if intention is in active path."""
        context = TieredContext(
            session_id="test",
            active_intention_path=["INT-001", "INT-002", "INT-003"],
        )

        assert context.is_intention_active("INT-002") is True
        assert context.is_intention_active("INT-004") is False

    def test_load_from_file(self) -> None:
        """Test loading TieredContext from JSON file."""
        data: dict = {
            "session_id": "test-session",
            "active_intention_path": ["INT-001"],
            "total_intentions": 1,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)

        try:
            context = TieredContext.load(path)
            assert context.session_id == "test-session"
            assert context.total_intentions == 1
        finally:
            path.unlink()


class TestGetTieredContext:
    """Tests for get_tiered_context MCP tool."""

    def test_session_not_found(self) -> None:
        """Test error when session directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_tiered_context(
                session_id="nonexistent",
                cwd=tmpdir,
            )

            assert result["success"] is False
            assert "not found" in result["error"]

    def test_no_context_file(self) -> None:
        """Test error when no context file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create session directory but no context file
            session_dir = Path(tmpdir) / ".intent_audit" / "test-session"
            session_dir.mkdir(parents=True)

            result = get_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
            )

            assert result["success"] is False
            assert "No tiered context found" in result["error"]

    def test_valid_context_retrieval(self) -> None:
        """Test successful context retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create context file
            session_dir = Path(tmpdir) / ".intent_audit" / "test-session"
            session_dir.mkdir(parents=True)
            context_path = session_dir / "tiered_context.json"

            context_data: dict = {
                "session_id": "test-session",
                "active_intention_path": ["INT-001"],
                "total_intentions": 1,
                "active_tier_size": 100,
                "recent_tier_size": 50,
                "archive_tier_size": 25,
            }
            context_path.write_text(json.dumps(context_data))

            result = get_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
            )

            assert result["success"] is True
            assert result["active_intention"] == "INT-001"
            assert result["context_size"] == 175


class TestSaveTieredContext:
    """Tests for save_tiered_context MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal tiered context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context: dict = {
                "session_id": "test-session",
            }

            result = save_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
                context=context,
            )

            assert result["success"] is True
            assert Path(result["path"]).exists()

    def test_valid_with_all_tiers(self) -> None:
        """Test saving context with all tiers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context: dict = {
                "session_id": "test-session",
                "active_intention_path": ["INT-001", "INT-002"],
                "active": {
                    "intent_id": "INT-002",
                    "title": "Login Flow",
                    "type": "functionality",
                },
                "recent": [
                    {
                        "intent_id": "INT-001",
                        "title": "Auth",
                        "type": "goal",
                    }
                ],
                "total_intentions": 2,
            }

            result = save_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
                context=context,
            )

            assert result["success"] is True
            assert result["active_intention"] == "INT-002"

    def test_missing_session_id(self) -> None:
        """Test that missing session_id causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context: dict = {
                "active_intention_path": ["INT-001"],
            }

            result = save_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
                context=context,
            )

            assert result["success"] is False
            assert "session_id" in result["error"]

    def test_with_diff_hash(self) -> None:
        """Test saving context with diff hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context: dict = {
                "session_id": "test-session",
            }

            result = save_tiered_context(
                session_id="test-session",
                cwd=tmpdir,
                context=context,
                diff_hash="abc123def456",
            )

            assert result["success"] is True
            assert "abc123def456" in result["path"]
