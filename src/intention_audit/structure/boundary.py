"""
Code home boundary checker for structure alignment validation.

This module validates that file changes in a commit plan stay within
the code_home boundaries defined by functionality intentions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intention_audit.models.commit_plan import CommitPlan
    from intention_audit.models.intention import Intention


@dataclass
class BoundaryViolation:
    """A violation where files are outside the expected code_home boundary."""

    commit_entry_index: int
    """Index of the commit entry in the plan."""

    intent_id: str
    """Intent ID of the commit entry."""

    functionality_intent_id: str | None
    """Functionality intent that defines the boundary (if found)."""

    violating_paths: list[str]
    """Paths that are outside the code_home boundary."""

    expected_prefixes: list[str]
    """Expected code_home path prefixes."""

    suggested_fix: str = ""
    """Suggested resolution for the violation."""


def _find_intention_by_id(root: Intention, intent_id: str) -> Intention | None:
    """
    Find an intention by ID in the tree.

    Args:
        root: Root intention node to search from.
        intent_id: The ID to search for.

    Returns:
        The matching Intention or None if not found.
    """
    if root.id == intent_id:
        return root
    for child in root.children:
        found = _find_intention_by_id(child, intent_id)
        if found:
            return found
    return None


def _find_functionality_ancestor(root: Intention, intent_id: str) -> Intention | None:
    """
    Find the nearest functionality ancestor for an intention.

    Traverses the tree to find the target intention, then walks back up
    the path to find the first ancestor with kind="functionality".

    Args:
        root: Root intention node to search from.
        intent_id: The ID of the intention to find the ancestor for.

    Returns:
        The nearest functionality ancestor or None if not found.
    """
    from intention_audit.models.intention import IntentionKind

    def _search(node: Intention, path: list[Intention]) -> Intention | None:
        if node.id == intent_id:
            # Walk back up the path to find the first functionality node
            for ancestor in reversed(path):
                if ancestor.kind == IntentionKind.FUNCTIONALITY:
                    return ancestor
            return None

        for child in node.children:
            result = _search(child, [*path, node])
            if result is not None:
                return result
        return None

    return _search(root, [])


def _path_within_prefixes(path: str, prefixes: list[str]) -> bool:
    """
    Check if a path is within any of the given prefixes.

    Args:
        path: The file path to check.
        prefixes: List of allowed path prefixes.

    Returns:
        True if the path starts with any of the prefixes.
    """
    path_posix = PurePosixPath(path)
    for prefix in prefixes:
        prefix_posix = PurePosixPath(prefix.rstrip("/"))
        # Check if path starts with prefix
        try:
            path_posix.relative_to(prefix_posix)
            return True
        except ValueError:
            continue
    return False


def check_code_home_boundaries(
    root: Intention,
    plan: CommitPlan,
) -> list[BoundaryViolation]:
    """
    Check if all commit entries stay within their functionality's code_home boundaries.

    For each commit entry in the plan, this function:
    1. Finds the associated functionality intention (via functionality_intent_id or ancestor search)
    2. Gets the code_home prefixes from that functionality
    3. Validates that all files in the entry are within those prefixes

    Args:
        root: Root intention of the intention tree.
        plan: Commit plan to validate.

    Returns:
        List of boundary violations found. Empty list if all entries are valid.
    """
    from intention_audit.models.intention import IntentionKind

    violations: list[BoundaryViolation] = []

    for idx, entry in enumerate(plan.commits):
        # Find the functionality ancestor for this intent
        functionality = None
        if entry.functionality_intent_id:
            functionality = _find_intention_by_id(root, entry.functionality_intent_id)

        if functionality is None:
            functionality = _find_functionality_ancestor(root, entry.intent_id)

        if functionality is None:
            # No functionality ancestor found - skip boundary check
            continue

        # Verify we have a functionality node
        if functionality.kind != IntentionKind.FUNCTIONALITY:
            continue

        # Get code_home from functionality
        code_home = functionality.code_home or []
        if not code_home:
            # No code_home defined - skip boundary check
            continue

        # Check each file in the entry
        violating = []
        for file_path in entry.files:
            if not _path_within_prefixes(file_path, code_home):
                violating.append(file_path)

        if violating:
            violations.append(
                BoundaryViolation(
                    commit_entry_index=idx,
                    intent_id=entry.intent_id,
                    functionality_intent_id=functionality.id,
                    violating_paths=violating,
                    expected_prefixes=code_home,
                    suggested_fix=f"Move files to {code_home[0]} or update code_home boundary",
                )
            )

    return violations
