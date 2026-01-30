"""Unit tests for CommitPlan and CommitEntry models."""


from intention_audit.models.commit_plan import CommitEntry, CommitPlan


class TestCommitEntry:
    """Tests for CommitEntry dataclass."""

    def test_minimal_instantiation(self):
        """Test creating entry with only required fields."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
        )
        assert entry.intent_id == "INT-2026-01-30-0001"
        assert entry.subject == "feat: add feature"
        assert entry.patch == ""
        assert entry.files == []

    def test_full_instantiation(self):
        """Test creating entry with all fields."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="--- a/file.py\n+++ b/file.py\n...",
            intent_path="Goal/Feature/Implementation",
            functionality_intent_id="INT-2026-01-30-0002",
            functionality_intent_path="Goal/Feature",
            body="Detailed description",
            intent_confidence=0.95,
            evidence_tests=["tests/test_x.py::test_y"],
            supporting_docs=["docs/feature.md"],
            files=["src/file.py"],
        )
        assert entry.intent_confidence == 0.95
        assert entry.evidence_tests == ["tests/test_x.py::test_y"]

    def test_from_dict_minimal(self):
        """Test creating entry from minimal dict."""
        data = {
            "intent_id": "INT-2026-01-30-0001",
            "subject": "feat: test",
        }
        entry = CommitEntry.from_dict(data)
        assert entry.intent_id == "INT-2026-01-30-0001"
        assert entry.subject == "feat: test"
        assert entry.patch == ""

    def test_from_dict_uses_title_fallback(self):
        """Test that 'title' is used as fallback for 'subject'."""
        data = {
            "intent_id": "INT-2026-01-30-0001",
            "title": "feat: from title",
        }
        entry = CommitEntry.from_dict(data)
        assert entry.subject == "feat: from title"

    def test_from_dict_with_files(self):
        """Test creating entry with legacy files field."""
        data = {
            "intent_id": "INT-2026-01-30-0001",
            "subject": "feat: test",
            "files": ["src/a.py", "src/b.py"],
        }
        entry = CommitEntry.from_dict(data)
        assert entry.files == ["src/a.py", "src/b.py"]

    def test_to_dict_minimal(self):
        """Test converting minimal entry to dict."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: test",
            patch="",
        )
        data = entry.to_dict()
        assert data["intent_id"] == "INT-2026-01-30-0001"
        assert data["subject"] == "feat: test"
        assert "patch" not in data  # Empty string not included
        assert "files" not in data  # Empty list not included

    def test_to_dict_roundtrip(self):
        """Test dict conversion preserves data."""
        original = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: test",
            patch="--- a/file.py\n+++ b/file.py\n",
            intent_path="Goal/Feature",
            intent_confidence=0.9,
            files=["file.py"],
        )
        data = original.to_dict()
        restored = CommitEntry.from_dict(data)

        assert restored.intent_id == original.intent_id
        assert restored.subject == original.subject
        assert restored.patch == original.patch
        assert restored.intent_path == original.intent_path
        assert restored.intent_confidence == original.intent_confidence
        assert restored.files == original.files


class TestCommitPlan:
    """Tests for CommitPlan dataclass."""

    def test_minimal_instantiation(self):
        """Test creating plan with required fields."""
        plan = CommitPlan(version=1, ready=True, commits=[])
        assert plan.version == 1
        assert plan.ready is True
        assert plan.commits == []

    def test_with_commits(self):
        """Test creating plan with multiple commits."""
        commits = [
            CommitEntry(
                intent_id="INT-2026-01-30-0001",
                subject="feat: first",
                patch="",
            ),
            CommitEntry(
                intent_id="INT-2026-01-30-0002",
                subject="feat: second",
                patch="",
            ),
        ]
        plan = CommitPlan(version=1, ready=True, commits=commits)
        assert len(plan.commits) == 2
        assert plan.commits[0].intent_id == "INT-2026-01-30-0001"
        assert plan.commits[1].intent_id == "INT-2026-01-30-0002"

    def test_version_validation_semantics(self):
        """Test that version is a number."""
        plan = CommitPlan(version=1, ready=True, commits=[])
        assert plan.version == 1

    def test_ready_flag_false(self):
        """Test ready flag can be false (draft plan)."""
        plan = CommitPlan(version=1, ready=False, commits=[])
        assert plan.ready is False

    def test_from_dict_minimal(self):
        """Test creating plan from minimal dict."""
        data = {"version": 1, "ready": True, "commits": []}
        plan = CommitPlan.from_dict(data)
        assert plan.version == 1
        assert plan.ready is True
        assert plan.commits == []

    def test_from_dict_with_commits(self):
        """Test creating plan from dict with commits."""
        data = {
            "version": 1,
            "ready": True,
            "diff_base": "HEAD",
            "diff_hash": "abc123",
            "commits": [
                {"intent_id": "INT-2026-01-30-0001", "subject": "feat: test", "files": ["a.py"]}
            ],
        }
        plan = CommitPlan.from_dict(data)
        assert plan.diff_base == "HEAD"
        assert plan.diff_hash == "abc123"
        assert len(plan.commits) == 1
        assert plan.commits[0].files == ["a.py"]

    def test_to_dict_minimal(self):
        """Test converting minimal plan to dict."""
        plan = CommitPlan(version=1, ready=True, commits=[])
        data = plan.to_dict()
        assert data["version"] == 1
        assert data["ready"] is True
        assert data["commits"] == []
        assert "diff_base" not in data

    def test_to_dict_roundtrip(self):
        """Test dict conversion preserves data."""
        original = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0001",
                    subject="feat: test",
                    patch="patch content",
                    files=["file.py"],
                )
            ],
            diff_base="HEAD",
            diff_hash="abc123",
        )
        data = original.to_dict()
        restored = CommitPlan.from_dict(data)

        assert restored.version == original.version
        assert restored.ready == original.ready
        assert restored.diff_base == original.diff_base
        assert restored.diff_hash == original.diff_hash
        assert len(restored.commits) == 1
        assert restored.commits[0].intent_id == original.commits[0].intent_id

    def test_defaults_for_missing_fields(self):
        """Test that missing optional fields get defaults."""
        data = {}  # Empty dict
        plan = CommitPlan.from_dict(data)
        assert plan.version == 1  # Default version
        assert plan.ready is False  # Default ready
        assert plan.commits == []  # Default commits
        assert plan.diff_base is None
        assert plan.diff_hash is None
