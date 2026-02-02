"""Unit tests for diff utilities."""

from intention_audit.diff.hunks import Hunk, compute_diff_hash, parse_unified_diff
from intention_audit.diff.patch import validate_patch_coverage
from intention_audit.models.commit_plan import CommitEntry, CommitPlan


class TestParseUnifiedDiff:
    """Tests for parse_unified_diff function."""

    def test_empty_diff(self):
        """Test parsing empty diff."""
        hunks = parse_unified_diff("")
        assert hunks == []

    def test_whitespace_only_diff(self):
        """Test parsing whitespace-only diff."""
        hunks = parse_unified_diff("   \n\n   ")
        assert hunks == []

    def test_single_hunk(self):
        """Test parsing diff with single hunk."""
        diff = """diff --git a/file.py b/file.py
index abc123..def456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3
"""
        hunks = parse_unified_diff(diff)
        assert len(hunks) == 1
        assert hunks[0].file_path == "file.py"
        assert hunks[0].old_start == 1
        assert hunks[0].old_count == 3
        assert hunks[0].new_start == 1
        assert hunks[0].new_count == 4

    def test_multiple_hunks_same_file(self):
        """Test parsing diff with multiple hunks in same file."""
        diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3
@@ -10,3 +11,4 @@
 line10
+another line
 line11
 line12
"""
        hunks = parse_unified_diff(diff)
        assert len(hunks) == 2
        assert hunks[0].new_start == 1
        assert hunks[1].new_start == 11

    def test_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 line1
+new
 line2
 line3
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -5,3 +5,4 @@
 line5
+added
 line6
 line7
"""
        hunks = parse_unified_diff(diff)
        assert len(hunks) == 2
        assert hunks[0].file_path == "file1.py"
        assert hunks[1].file_path == "file2.py"

    def test_hunk_with_no_context(self):
        """Test parsing hunk header without count (defaults to 1)."""
        diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
"""
        hunks = parse_unified_diff(diff)
        assert len(hunks) == 1
        assert hunks[0].old_count == 1
        assert hunks[0].new_count == 1


class TestComputeDiffHash:
    """Tests for compute_diff_hash function."""

    def test_empty_hunks(self):
        """Test hash of empty hunk list."""
        hash1 = compute_diff_hash([])
        hash2 = compute_diff_hash([])
        assert hash1 == hash2  # Deterministic
        assert len(hash1) == 64  # SHA-256 hex length

    def test_same_hunks_same_hash(self):
        """Test that same hunks produce same hash."""
        hunk1 = Hunk("file.py", 1, 3, 1, 4, "@@ -1,3 +1,4 @@\n content")
        hunk2 = Hunk("file.py", 1, 3, 1, 4, "@@ -1,3 +1,4 @@\n content")
        hash1 = compute_diff_hash([hunk1])
        hash2 = compute_diff_hash([hunk2])
        assert hash1 == hash2

    def test_different_hunks_different_hash(self):
        """Test that different hunks produce different hash."""
        hunk1 = Hunk("file.py", 1, 3, 1, 4, "content1")
        hunk2 = Hunk("file.py", 1, 3, 1, 4, "content2")
        hash1 = compute_diff_hash([hunk1])
        hash2 = compute_diff_hash([hunk2])
        assert hash1 != hash2

    def test_order_independent(self):
        """Test that hash is independent of hunk order (sorted internally)."""
        hunk_a = Hunk("a.py", 1, 1, 1, 1, "content a")
        hunk_b = Hunk("b.py", 1, 1, 1, 1, "content b")
        hash1 = compute_diff_hash([hunk_a, hunk_b])
        hash2 = compute_diff_hash([hunk_b, hunk_a])
        assert hash1 == hash2  # Order should not matter


class TestValidatePatchCoverage:
    """Tests for validate_patch_coverage function."""

    def test_empty_plan_no_hunks(self):
        """Test empty plan with no hunks."""
        plan = CommitPlan(version=1, ready=True, commits=[])
        covered, uncovered = validate_patch_coverage([], plan)
        assert covered == []
        assert uncovered == []

    def test_file_level_coverage(self):
        """Test coverage using file-level mapping."""
        hunk = Hunk("file.py", 1, 3, 1, 4, "content")
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="test",
            patch="",
            files=["file.py"],
        )
        plan = CommitPlan(version=1, ready=True, commits=[entry])

        covered, uncovered = validate_patch_coverage([hunk], plan)
        assert len(covered) == 1
        assert len(uncovered) == 0

    def test_uncovered_hunk(self):
        """Test detection of uncovered hunks."""
        hunk1 = Hunk("file1.py", 1, 1, 1, 1, "content1")
        hunk2 = Hunk("file2.py", 1, 1, 1, 1, "content2")
        entry = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="test",
            patch="",
            files=["file1.py"],  # Only covers file1
        )
        plan = CommitPlan(version=1, ready=True, commits=[entry])

        covered, uncovered = validate_patch_coverage([hunk1, hunk2], plan)
        assert len(covered) == 1
        assert len(uncovered) == 1
        assert uncovered[0].file_path == "file2.py"

    def test_multiple_commits_full_coverage(self):
        """Test multiple commits covering all hunks."""
        hunk1 = Hunk("file1.py", 1, 1, 1, 1, "content1")
        hunk2 = Hunk("file2.py", 1, 1, 1, 1, "content2")
        entry1 = CommitEntry(
            intent_id="INT-2026-01-30-0001",
            subject="test1",
            patch="",
            files=["file1.py"],
        )
        entry2 = CommitEntry(
            intent_id="INT-2026-01-30-0002",
            subject="test2",
            patch="",
            files=["file2.py"],
        )
        plan = CommitPlan(version=1, ready=True, commits=[entry1, entry2])

        covered, uncovered = validate_patch_coverage([hunk1, hunk2], plan)
        assert len(covered) == 2
        assert len(uncovered) == 0
