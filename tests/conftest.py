"""
Shared pytest fixtures for all test types.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_repos_path(project_root: Path) -> Path:
    """Return the path to sample_repos fixture directory."""
    return project_root / "tests" / "fixtures" / "sample_repos"


@pytest.fixture
def product_src_path(project_root: Path) -> Path:
    """Return the path to product source code."""
    return project_root / "src" / "intention_audit"
