"""
Test data factory functions for E2E tests.

These factories create valid intention and commit plan artifacts
that can be passed to the MCP tools or written directly.
"""

from __future__ import annotations

from typing import Any


def minimal_intention(intent_id: str, title: str, kind: str = "functionality") -> dict[str, Any]:
    """
    Create a minimal valid intention structure.

    Args:
        intent_id: Unique identifier (e.g., "INT-001").
        title: Human-readable title.
        kind: Intention kind (goal, functionality, implementation, tests, docs, observability).

    Returns:
        Dictionary conforming to intentions schema.
    """
    return {
        "id": intent_id,
        "title": title,
        "kind": kind,
        "status": "planned",
        "children": [],
    }


def intention_tree(
    root_intent_id: str, root_title: str, children: list[dict] | None = None
) -> dict[str, Any]:
    """
    Create an intention tree with root and optional children.

    Args:
        root_intent_id: Root intention identifier.
        root_title: Root intention title.
        children: List of child intentions (defaults to empty).

    Returns:
        Dictionary with root intention containing children.
    """
    return {
        "id": root_intent_id,
        "title": root_title,
        "kind": "goal",
        "status": "planned",
        "children": children or [],
    }


def minimal_commit_plan(
    intent_id: str,
    files: list[str],
    subject: str,
    ready: bool = True,
) -> dict[str, Any]:
    """
    Create a minimal valid commit plan with a single commit entry.

    Args:
        intent_id: Intent ID this commit maps to.
        files: List of file paths for this commit.
        subject: Commit subject line.
        ready: Whether the plan is ready for execution.

    Returns:
        Dictionary conforming to commit_plan schema.
    """
    return {
        "version": 1,
        "ready": ready,
        "commits": [
            {
                "intent_id": intent_id,
                "subject": subject,
                "files": files,
            }
        ],
    }


def full_commit_entry(
    intent_id: str,
    files: list[str],
    subject: str,
    body: str | None = None,
    intent_path: str | None = None,
    functionality_intent_id: str | None = None,
    intent_confidence: float | None = None,
) -> dict[str, Any]:
    """
    Create a full commit entry with optional trailers.

    Args:
        intent_id: Intent ID this commit maps to.
        files: List of file paths for this commit.
        subject: Commit subject line.
        body: Optional commit body.
        intent_path: Optional intent path for trailer.
        functionality_intent_id: Optional functionality intent ID for trailer.
        intent_confidence: Optional confidence score (0.0-1.0).

    Returns:
        Dictionary for a single commit entry in a plan.
    """
    entry: dict[str, Any] = {
        "intent_id": intent_id,
        "subject": subject,
        "files": files,
    }

    if body:
        entry["body"] = body
    if intent_path:
        entry["intent_path"] = intent_path
    if functionality_intent_id:
        entry["functionality_intent_id"] = functionality_intent_id
    if intent_confidence is not None:
        entry["intent_confidence"] = intent_confidence

    return entry


def multi_commit_plan(commits: list[dict[str, Any]], ready: bool = True) -> dict[str, Any]:
    """
    Create a commit plan with multiple commit entries.

    Args:
        commits: List of commit entries (from full_commit_entry).
        ready: Whether the plan is ready for execution.

    Returns:
        Dictionary conforming to commit_plan schema.
    """
    return {
        "version": 1,
        "ready": ready,
        "commits": commits,
    }
