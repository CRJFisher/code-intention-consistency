"""
Utility functions for setting up .intent_audit/ directory in sample repos.

These utilities are used by E2E test fixtures to create the runtime state
directory structure that the intention audit trail uses during operation.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def setup_intent_audit_dir(repo_path: Path) -> None:
    """
    Create the .intent_audit/ directory structure in a sample repo.

    Args:
        repo_path: Path to the sample repository root.

    Creates:
        .intent_audit/
        └── sessions/   (for session records)
    """
    intent_audit_dir = repo_path / ".intent_audit"
    sessions_dir = intent_audit_dir / "sessions"

    intent_audit_dir.mkdir(exist_ok=True)
    sessions_dir.mkdir(exist_ok=True)


def cleanup_intent_audit_dir(repo_path: Path) -> None:
    """
    Remove the .intent_audit/ directory from a sample repo.

    Args:
        repo_path: Path to the sample repository root.
    """
    intent_audit_dir = repo_path / ".intent_audit"
    if intent_audit_dir.exists():
        shutil.rmtree(intent_audit_dir)
