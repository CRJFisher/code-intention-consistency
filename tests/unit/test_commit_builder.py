"""Unit tests for commit message builder."""

from intention_audit.hooks.commit_builder import (
    build_commit_message,
    extract_intent_id,
    parse_commit_trailers,
)
from intention_audit.models.commit_plan import CommitEntry


class TestBuildCommitMessage:
    """Tests for build_commit_message function."""

    def test_minimal_entry(self):
        """Test building message with minimal entry."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
        )
        message = build_commit_message(entry)

        assert "feat: add feature" in message
        assert "Intent-Id: INT-2026-01-30-0001" in message
        assert message.endswith("\n")

    def test_with_body(self):
        """Test building message with body."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            body="This is a detailed description.\n\nWith multiple paragraphs.",
        )
        message = build_commit_message(entry)

        assert "feat: add feature" in message
        assert "This is a detailed description." in message
        assert "With multiple paragraphs." in message
        assert "Intent-Id: INT-2026-01-30-0001" in message

    def test_with_intent_path(self):
        """Test building message with intent path."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            intent_path="Goal/Feature/Implementation",
        )
        message = build_commit_message(entry)

        assert "Intent-Path: Goal/Feature/Implementation" in message

    def test_with_override_path(self):
        """Test that override path takes precedence."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            intent_path="Original/Path",
        )
        message = build_commit_message(entry, intent_path="Override/Path")

        assert "Intent-Path: Override/Path" in message
        assert "Original/Path" not in message

    def test_with_functionality_id(self):
        """Test building message with functionality intent ID."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            functionality_intent_id="INT-2026-01-30-0002",
        )
        message = build_commit_message(entry)

        assert "Functionality-Intent-Id: INT-2026-01-30-0002" in message

    def test_with_confidence(self):
        """Test building message with confidence."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            intent_confidence=0.95,
        )
        message = build_commit_message(entry)

        assert "Intent-Confidence: 0.95" in message

    def test_with_evidence_tests(self):
        """Test building message with evidence tests."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            evidence_tests=["tests/test_x.py::test_a", "tests/test_x.py::test_b"],
        )
        message = build_commit_message(entry)

        assert "Evidence-Test: tests/test_x.py::test_a" in message
        assert "Evidence-Test: tests/test_x.py::test_b" in message

    def test_with_supporting_docs(self):
        """Test building message with supporting docs."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            supporting_docs=["docs/feature.md#section"],
        )
        message = build_commit_message(entry)

        assert "Supporting-Doc: docs/feature.md#section" in message

    def test_full_message_format(self):
        """Test the full message format matches expected structure."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="feat: add feature",
            patch="",
            body="Description here",
            intent_path="Goal/Feature",
            functionality_intent_id="INT-2026-01-30-0002",
            intent_confidence=0.9,
        )
        message = build_commit_message(entry)

        lines = message.strip().split("\n")
        assert lines[0] == "feat: add feature"
        assert lines[1] == ""  # Blank line after subject
        assert lines[2] == "Description here"
        assert lines[3] == ""  # Blank line after body
        # Trailers follow
        assert any("Intent-Id:" in line for line in lines[4:])

    def test_empty_subject_fallback(self):
        """Test fallback subject when empty."""
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="",
            patch="",
        )
        message = build_commit_message(entry)

        assert "chore: INT-2026-01-30-0001" in message


class TestParseCommitTrailers:
    """Tests for parse_commit_trailers function."""

    def test_single_trailer(self):
        """Test parsing single trailer."""
        message = """feat: add feature

Intent-Id: INT-2026-01-30-0001
"""
        trailers = parse_commit_trailers(message)

        assert "Intent-Id" in trailers
        assert trailers["Intent-Id"] == ["INT-2026-01-30-0001"]

    def test_multiple_trailers(self):
        """Test parsing multiple different trailers."""
        message = """feat: add feature

Intent-Id: INT-2026-01-30-0001
Intent-Path: Goal/Feature
Intent-Confidence: 0.95
"""
        trailers = parse_commit_trailers(message)

        assert trailers["Intent-Id"] == ["INT-2026-01-30-0001"]
        assert trailers["Intent-Path"] == ["Goal/Feature"]
        assert trailers["Intent-Confidence"] == ["0.95"]

    def test_repeated_trailers(self):
        """Test parsing repeated trailers (same key)."""
        message = """feat: add feature

Evidence-Test: tests/test_a.py::test_1
Evidence-Test: tests/test_b.py::test_2
"""
        trailers = parse_commit_trailers(message)

        assert "Evidence-Test" in trailers
        assert len(trailers["Evidence-Test"]) == 2
        assert "tests/test_a.py::test_1" in trailers["Evidence-Test"]
        assert "tests/test_b.py::test_2" in trailers["Evidence-Test"]

    def test_no_trailers(self):
        """Test parsing message with no trailers."""
        message = """feat: add feature

Just a description with no trailers.
"""
        trailers = parse_commit_trailers(message)

        # May have empty dict or some parse artifacts
        # The key assertion is no Intent-Id
        assert "Intent-Id" not in trailers


class TestExtractIntentId:
    """Tests for extract_intent_id function."""

    def test_extracts_intent_id(self):
        """Test extracting Intent-Id from message."""
        message = """feat: add feature

Intent-Id: INT-2026-01-30-0001
"""
        intent_id = extract_intent_id(message)
        assert intent_id == "INT-2026-01-30-0001"

    def test_returns_none_when_missing(self):
        """Test returning None when no Intent-Id."""
        message = """feat: add feature

No trailers here.
"""
        intent_id = extract_intent_id(message)
        assert intent_id is None

    def test_returns_first_when_multiple(self):
        """Test returning first Intent-Id when multiple present."""
        message = """feat: add feature

Intent-Id: INT-2026-01-30-0001
Intent-Id: INT-2026-01-30-0002
"""
        intent_id = extract_intent_id(message)
        assert intent_id == "INT-2026-01-30-0001"
