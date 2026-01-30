"""
Commit message builder with intention trailers.
"""

from __future__ import annotations

from intention_audit.models.commit_plan import CommitEntry


def build_commit_message(entry: CommitEntry, intent_path: str | None = None) -> str:
    """
    Build a commit message with proper formatting and trailers.

    Format:
        subject

        body (optional)

        Intent-Id: <id>
        Intent-Path: <path> (optional)
        Functionality-Intent-Id: <id> (optional)
        Intent-Confidence: <confidence> (optional)

    Args:
        entry: The commit entry to build message from.
        intent_path: Optional path to override entry.intent_path.

    Returns:
        Formatted commit message string.
    """
    # Build subject
    subject = entry.subject.strip() if entry.subject else f"chore: {entry.intent_id}"

    # Use provided path or fall back to entry's path
    path = intent_path or entry.intent_path

    # Build trailers
    trailers: list[str] = [f"Intent-Id: {entry.intent_id}"]

    if path:
        trailers.append(f"Intent-Path: {path}")

    if entry.functionality_intent_id:
        trailers.append(f"Functionality-Intent-Id: {entry.functionality_intent_id}")

    if entry.intent_confidence is not None:
        trailers.append(f"Intent-Confidence: {entry.intent_confidence}")

    # Build evidence and docs trailers if present
    for test in entry.evidence_tests:
        trailers.append(f"Evidence-Test: {test}")

    for doc in entry.supporting_docs:
        trailers.append(f"Supporting-Doc: {doc}")

    # Assemble message
    parts: list[str] = [subject, ""]

    if entry.body:
        parts.extend([entry.body.strip(), ""])

    parts.extend(trailers)

    return "\n".join(parts).rstrip() + "\n"


def parse_commit_trailers(message: str) -> dict[str, list[str]]:
    """
    Parse trailers from a commit message.

    Args:
        message: The full commit message.

    Returns:
        Dictionary mapping trailer names to list of values.
        Multiple values for the same trailer are collected into a list.
    """
    trailers: dict[str, list[str]] = {}

    lines = message.strip().split("\n")

    # Find trailer section (after last blank line in the message)
    trailer_start = 0
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].strip():
            trailer_start = i + 1
            break

    # Parse trailers
    for line in lines[trailer_start:]:
        if ": " in line:
            key, _, value = line.partition(": ")
            key = key.strip()
            value = value.strip()
            if key and value:
                if key not in trailers:
                    trailers[key] = []
                trailers[key].append(value)

    return trailers


def extract_intent_id(message: str) -> str | None:
    """
    Extract the Intent-Id from a commit message.

    Args:
        message: The full commit message.

    Returns:
        The Intent-Id value, or None if not found.
    """
    trailers = parse_commit_trailers(message)
    intent_ids = trailers.get("Intent-Id", [])
    return intent_ids[0] if intent_ids else None
