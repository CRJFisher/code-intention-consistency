"""
Unit tests for stop_hook module functions.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from intention_audit.hooks.stop_hook import (
    _compute_diff_hash,
    _get_artifact_dir,
)


class TestComputeDiffHash:
    """Tests for _compute_diff_hash function."""

    def test_returns_16_char_hex_string(self, tmp_path: Path) -> None:
        """Hash should be a 16-character hex string."""
        # Set up a minimal git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Make some changes
        (tmp_path / "file.txt").write_text("hello world")

        result = _compute_diff_hash(tmp_path)

        assert isinstance(result, str)
        assert len(result) == 16
        # Verify it's valid hex
        int(result, 16)

    def test_same_diff_produces_same_hash(self, tmp_path: Path) -> None:
        """Same uncommitted changes should produce the same hash (idempotent)."""
        # Set up git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("original")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Make changes
        (tmp_path / "file.txt").write_text("modified content")

        hash1 = _compute_diff_hash(tmp_path)
        hash2 = _compute_diff_hash(tmp_path)

        assert hash1 == hash2

    def test_different_diff_produces_different_hash(self, tmp_path: Path) -> None:
        """Different uncommitted changes should produce different hashes."""
        # Set up git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("original")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # First set of changes
        (tmp_path / "file.txt").write_text("change A")
        hash1 = _compute_diff_hash(tmp_path)

        # Different changes
        (tmp_path / "file.txt").write_text("change B")
        hash2 = _compute_diff_hash(tmp_path)

        assert hash1 != hash2

    def test_includes_untracked_files(self, tmp_path: Path) -> None:
        """Untracked files should be included in the hash."""
        # Set up git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("original")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Get hash with no changes
        hash_clean = _compute_diff_hash(tmp_path)

        # Add an untracked file
        (tmp_path / "new_file.txt").write_text("untracked content")
        hash_with_untracked = _compute_diff_hash(tmp_path)

        assert hash_clean != hash_with_untracked

    def test_empty_diff_produces_consistent_hash(self, tmp_path: Path) -> None:
        """An empty diff (no changes) should produce a consistent hash."""
        # Set up git repo with clean state
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        (tmp_path / "file.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        hash1 = _compute_diff_hash(tmp_path)
        hash2 = _compute_diff_hash(tmp_path)

        assert hash1 == hash2


class TestGetArtifactDir:
    """Tests for _get_artifact_dir function."""

    def test_returns_correct_path(self, tmp_path: Path) -> None:
        """Should return project_dir / .intent_audit / session_id / diff_hash."""
        session_id = "abc123"
        diff_hash = "1234567890abcdef"

        result = _get_artifact_dir(tmp_path, session_id, diff_hash)

        assert result == tmp_path / ".intent_audit" / session_id / diff_hash

    def test_handles_different_inputs(self, tmp_path: Path) -> None:
        """Should correctly combine various session_id and diff_hash values."""
        test_cases = [
            ("session-1", "aaaa1111bbbb2222"),
            ("long-session-id-12345", "0000000000000000"),
            ("x", "ffffffffffffffff"),
        ]

        for session_id, diff_hash in test_cases:
            result = _get_artifact_dir(tmp_path, session_id, diff_hash)
            assert result == tmp_path / ".intent_audit" / session_id / diff_hash
