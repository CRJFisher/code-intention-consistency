"""
Documentation linkage validator for intention audit.

This module validates that behavior-affecting intentions have proper
documentation links (supporting_docs) or explicit rationale for their absence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from intention_audit.models.commit_plan import CommitPlan
    from intention_audit.models.intention import Intention


# Kinds that typically require documentation
BEHAVIOR_AFFECTING_KINDS = {"functionality", "implementation"}


@dataclass
class DocsViolation:
    """A violation where documentation links are missing."""

    intent_id: str
    """Intent ID that is missing documentation."""

    intent_title: str
    """Title of the intention."""

    intent_kind: str
    """Kind of the intention."""

    reason: str = "missing_docs"
    """Reason for the violation (missing_docs, missing_rationale, etc.)."""

    suggested_fix: str = ""
    """Suggested resolution for the violation."""

    details: dict[str, Any] = field(default_factory=dict)
    """Additional details about the violation."""


def _collect_intentions_from_plan(
    root: Intention,
    plan: CommitPlan,
) -> list[Intention]:
    """Collect all intentions referenced by the commit plan."""
    intent_ids = {entry.intent_id for entry in plan.commits}
    if hasattr(plan, "commits"):
        for entry in plan.commits:
            if hasattr(entry, "functionality_intent_id") and entry.functionality_intent_id:
                intent_ids.add(entry.functionality_intent_id)

    def _find_all(node: Intention, ids: set[str]) -> list[Intention]:
        found = []
        if node.id in ids:
            found.append(node)
        for child in node.children:
            found.extend(_find_all(child, ids))
        return found

    return _find_all(root, intent_ids)


def _intention_has_docs(intention: Intention) -> bool:
    """Check if an intention has documentation links."""
    supporting_docs = getattr(intention, "supporting_docs", None)
    return bool(supporting_docs and len(supporting_docs) > 0)


def _intention_has_rationale(intention: Intention) -> bool:
    """Check if an intention has a rationale (can substitute for docs)."""
    rationale = getattr(intention, "rationale", None)
    return bool(rationale and len(str(rationale).strip()) > 0)


def validate_docs_links(
    root: Intention,
    plan: CommitPlan,
    require_all: bool = False,
) -> list[DocsViolation]:
    """
    Validate that behavior-affecting intentions have documentation links.

    Args:
        root: Root intention of the intention tree.
        plan: Commit plan to validate.
        require_all: If True, require docs for all intentions (not just behavior-affecting).

    Returns:
        List of documentation violations found. Empty list if all are valid.
    """
    violations: list[DocsViolation] = []

    # Get all intentions referenced in the plan
    intentions = _collect_intentions_from_plan(root, plan)

    for intention in intentions:
        # Get the kind value (handle both enum and string)
        kind_value = (
            intention.kind.value if hasattr(intention.kind, "value") else intention.kind
        )

        # Skip non-behavior-affecting kinds unless require_all is True
        if not require_all and kind_value not in BEHAVIOR_AFFECTING_KINDS:
            continue

        # Check for documentation or rationale
        has_docs = _intention_has_docs(intention)
        has_rationale = _intention_has_rationale(intention)

        if not has_docs and not has_rationale:
            violations.append(
                DocsViolation(
                    intent_id=intention.id,
                    intent_title=intention.title,
                    intent_kind=kind_value,
                    reason="missing_docs",
                    suggested_fix=(
                        f"Add 'supporting_docs' to intention {intention.id} "
                        f"or provide a 'rationale'"
                    ),
                    details={
                        "checked_fields": ["supporting_docs", "rationale"],
                        "behavior_affecting": kind_value in BEHAVIOR_AFFECTING_KINDS,
                    },
                )
            )

    return violations


def format_docs_violations(violations: list[DocsViolation], warn_only: bool = True) -> str:
    """
    Format documentation violations as a human-readable message.

    Args:
        violations: List of violations to format.
        warn_only: If True, format as warnings; if False, format as errors.

    Returns:
        Formatted message string.
    """
    if not violations:
        return ""

    severity = "Warning" if warn_only else "Error"
    lines = [
        f"Documentation Validation {severity}s ({len(violations)} issue(s)):",
        "",
    ]

    for v in violations:
        lines.append(f"  - {v.intent_id} ({v.intent_kind}): {v.intent_title}")
        lines.append(f"    Reason: {v.reason}")
        lines.append(f"    Fix: {v.suggested_fix}")
        lines.append("")

    if warn_only:
        lines.append("Note: Documentation validation is currently warn-only.")

    return "\n".join(lines)
