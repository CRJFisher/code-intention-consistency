"""
YAML/JSON loaders for intention audit models.

Supports both YAML and JSON (YAML JSON-subset is accepted).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from intention_audit.models.commit_plan import CommitPlan
from intention_audit.models.intention import Intention
from intention_audit.models.session_record import SessionRecord


def load_intentions(path: Path) -> Intention:
    """
    Load and parse an intentions.yaml file.

    Args:
        path: Path to the intentions file (YAML or JSON).

    Returns:
        Root Intention node containing the full tree.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Intentions file not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        # Try YAML first (handles JSON too since JSON is valid YAML)
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse intentions file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Intentions file must contain a mapping, got {type(data).__name__}")

    if "id" not in data:
        raise ValueError("Intentions file must have a root intention with 'id' field")

    return Intention.from_dict(data)


def load_commit_plan(path: Path) -> CommitPlan:
    """
    Load and parse a commit_plan.yaml file.

    Args:
        path: Path to the commit plan file (YAML or JSON).

    Returns:
        CommitPlan instance.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Commit plan file not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        # Try YAML first (handles JSON too)
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse commit plan file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Commit plan file must contain a mapping, got {type(data).__name__}")

    return CommitPlan.from_dict(data)


def load_session_record(path: Path) -> SessionRecord:
    """
    Load and parse a session record JSON file.

    Args:
        path: Path to the session record file.

    Returns:
        SessionRecord instance.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Session record file not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse session record file {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Session record file must contain an object, got {type(data).__name__}")

    required_fields = ["session_id", "timestamp"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Session record missing required field: {field}")

    return SessionRecord.from_dict(data)
