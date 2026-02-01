"""
Intention failure context builder.

Maps failed evidence tests back to their evidenced intentions for failure reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from intention_audit.models.evidence_results import EvidenceResults
from intention_audit.models.intention import Intention
from intention_audit.models.tree import (
    find_functionality_ancestor,
    get_intention_path,
)


@dataclass
class IntentionFailureContext:
    """Context for a failed evidence test linked to an intention."""

    intention_id: str
    intention_title: str
    intention_path: str  # Human-readable path: "Goal/Feature/Leaf"
    failed_tests: list[str] = field(default_factory=list)  # Test selectors that failed
    linked_docs: list[str] = field(default_factory=list)  # Supporting doc paths
    code_scope: list[str] = field(default_factory=list)  # Paths from code_home


def _collect_intentions_with_evidence(root: Intention) -> list[Intention]:
    """
    Collect all intentions in the tree that have evidence_tests defined.

    Args:
        root: Root intention node.

    Returns:
        List of intentions that have evidence_tests.
    """
    result: list[Intention] = []
    if root.evidence_tests:
        result.append(root)
    for child in root.children:
        result.extend(_collect_intentions_with_evidence(child))
    return result


def _find_intentions_by_test_selector(
    root: Intention,
    test_selector: str,
) -> list[Intention]:
    """
    Find all intentions that reference a specific test selector.

    Args:
        root: Root intention node.
        test_selector: The test selector to search for.

    Returns:
        List of intentions that reference this test selector.
    """
    result: list[Intention] = []
    intentions_with_evidence = _collect_intentions_with_evidence(root)

    for intention in intentions_with_evidence:
        if test_selector in intention.evidence_tests:
            result.append(intention)

    return result


def build_failure_context(
    root: Intention,
    evidence_results: EvidenceResults,
) -> list[IntentionFailureContext]:
    """
    Build failure contexts from evidence results.

    For each failed test in evidence_results:
    1. Find the intention(s) that reference this test in evidence_tests
    2. Get the intention path using tree utilities
    3. Get linked_docs from supporting_docs
    4. Get code_scope from the functionality ancestor's code_home

    Args:
        root: Root intention node.
        evidence_results: Results from running evidence tests.

    Returns:
        A list of contexts, one per unique intention with failures.
    """
    # Map intention ID -> failure context (to aggregate failures per intention)
    contexts_by_id: dict[str, IntentionFailureContext] = {}

    # Get all failed tests (both assertion failures and errors)
    failed_results = [r for r in evidence_results.results if not r.passed]

    for result in failed_results:
        test_selector = result.selector

        # Find intentions that reference this test
        linked_intentions = _find_intentions_by_test_selector(root, test_selector)

        for intention in linked_intentions:
            if intention.id not in contexts_by_id:
                # Build path
                path = get_intention_path(root, intention.id)
                if path is None:
                    path = intention.title  # Fallback if path lookup fails

                # Get code_scope from functionality ancestor
                code_scope: list[str] = []
                functionality = find_functionality_ancestor(root, intention.id)
                if functionality is not None:
                    code_scope = functionality.code_home.copy()

                contexts_by_id[intention.id] = IntentionFailureContext(
                    intention_id=intention.id,
                    intention_title=intention.title,
                    intention_path=path,
                    failed_tests=[],
                    linked_docs=intention.supporting_docs.copy(),
                    code_scope=code_scope,
                )

            # Add this test selector to the failure context
            if test_selector not in contexts_by_id[intention.id].failed_tests:
                contexts_by_id[intention.id].failed_tests.append(test_selector)

    return list(contexts_by_id.values())
