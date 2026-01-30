"""
Patch application and coverage validation utilities.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from intention_audit.diff.hunks import Hunk
from intention_audit.models.commit_plan import CommitPlan


def apply_patch(project_dir: Path, patch: str) -> bool:
    """
    Apply a unified diff patch to the project.

    Args:
        project_dir: Path to the git repository root.
        patch: The unified diff patch content.

    Returns:
        True if patch applied successfully, False otherwise.
    """
    if not patch.strip():
        return True  # Empty patch is a no-op

    result = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=str(project_dir),
        input=patch,
        text=True,
        capture_output=True,
    )

    # First check if patch would apply cleanly
    if result.returncode != 0:
        return False

    # Actually apply the patch
    result = subprocess.run(
        ["git", "apply", "-"],
        cwd=str(project_dir),
        input=patch,
        text=True,
        capture_output=True,
    )

    return result.returncode == 0


def validate_patch_coverage(
    hunks: list[Hunk], plan: CommitPlan
) -> tuple[list[Hunk], list[Hunk]]:
    """
    Validate that a commit plan covers all hunks in the diff.

    Args:
        hunks: List of hunks from the current diff.
        plan: The commit plan to validate.

    Returns:
        Tuple of (covered_hunks, uncovered_hunks).
        Covered hunks are those that appear in at least one commit entry's patch.
        Uncovered hunks are those not covered by any commit entry.
    """
    # Build a set of hunk identifiers from the plan's patches
    planned_hunk_ids: set[tuple[str, int, int]] = set()

    for entry in plan.commits:
        if not entry.patch:
            # Fall back to file-level coverage if no patch
            for file_path in entry.files:
                # Mark all hunks in this file as covered
                for hunk in hunks:
                    if hunk.file_path == file_path:
                        planned_hunk_ids.add((hunk.file_path, hunk.new_start, hunk.new_count))
        else:
            # Parse the patch to find covered hunks
            from intention_audit.diff.hunks import parse_unified_diff

            patch_hunks = parse_unified_diff(entry.patch)
            for ph in patch_hunks:
                planned_hunk_ids.add((ph.file_path, ph.new_start, ph.new_count))

    # Classify hunks as covered or uncovered
    covered: list[Hunk] = []
    uncovered: list[Hunk] = []

    for hunk in hunks:
        hunk_id = (hunk.file_path, hunk.new_start, hunk.new_count)
        if hunk_id in planned_hunk_ids:
            covered.append(hunk)
        else:
            uncovered.append(hunk)

    return covered, uncovered
