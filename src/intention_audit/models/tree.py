"""
Intention tree traversal and lookup utilities.
"""

from __future__ import annotations

from intention_audit.models.intention import Intention, IntentionKind


def find_intention(root: Intention, intent_id: str) -> Intention | None:
    """
    Find an intention by ID in the tree.

    Args:
        root: Root intention node.
        intent_id: ID to search for.

    Returns:
        The Intention if found, None otherwise.
    """
    if root.id == intent_id:
        return root

    for child in root.children:
        result = find_intention(child, intent_id)
        if result is not None:
            return result

    return None


def find_functionality_ancestor(root: Intention, intent_id: str) -> Intention | None:
    """
    Find the closest functionality ancestor for an intention.

    Traverses up from the intention to find the nearest parent with kind=functionality.
    If the intention itself is a functionality, returns it.

    Args:
        root: Root intention node.
        intent_id: ID of the intention to find ancestor for.

    Returns:
        The closest functionality ancestor, or None if not found.
    """
    path = _get_path_to_intention(root, intent_id)
    if not path:
        return None

    # Walk the path from the target back to root
    # looking for the first functionality node
    for intention in reversed(path):
        if intention.kind == IntentionKind.FUNCTIONALITY:
            return intention

    return None


def get_intention_path(root: Intention, intent_id: str) -> str | None:
    """
    Get the human-readable path to an intention.

    Returns a string like "Goal/Feature/Implementation".

    Args:
        root: Root intention node.
        intent_id: ID of the intention.

    Returns:
        Path string, or None if intention not found.
    """
    path = _get_path_to_intention(root, intent_id)
    if not path:
        return None

    return "/".join(i.title for i in path)


def validate_intent_id_exists(root: Intention, intent_id: str) -> bool:
    """
    Check if an intent_id exists in the tree.

    Args:
        root: Root intention node.
        intent_id: ID to check.

    Returns:
        True if the ID exists in the tree, False otherwise.
    """
    return find_intention(root, intent_id) is not None


def get_all_intent_ids(root: Intention) -> list[str]:
    """
    Get all intention IDs in the tree.

    Args:
        root: Root intention node.

    Returns:
        List of all intention IDs.
    """
    ids = [root.id]
    for child in root.children:
        ids.extend(get_all_intent_ids(child))
    return ids


def get_intentions_by_kind(root: Intention, kind: IntentionKind) -> list[Intention]:
    """
    Get all intentions of a specific kind.

    Args:
        root: Root intention node.
        kind: The kind to filter by.

    Returns:
        List of intentions with the specified kind.
    """
    result = []
    if root.kind == kind:
        result.append(root)
    for child in root.children:
        result.extend(get_intentions_by_kind(child, kind))
    return result


def _get_path_to_intention(root: Intention, intent_id: str) -> list[Intention]:
    """
    Get the path from root to an intention (inclusive).

    Returns empty list if intention not found.
    """
    if root.id == intent_id:
        return [root]

    for child in root.children:
        child_path = _get_path_to_intention(child, intent_id)
        if child_path:
            return [root, *child_path]

    return []
