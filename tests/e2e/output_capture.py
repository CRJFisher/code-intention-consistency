"""
E2E output capture utilities for structured test output.

Creates structured output directories: tests/e2e/outputs/<test-name>/<iso-datetime>/
Provides utilities for saving component files and copying artifacts.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path


def create_output_dir(test_name: str, base_dir: Path | None = None) -> Path:
    """
    Create a timestamped output directory for a test run.

    Args:
        test_name: Name of the test (e.g., 'test_stop_hook_basic').
        base_dir: Base directory for outputs (defaults to tests/e2e/outputs/).

    Returns:
        Path to the created output directory.
    """
    if base_dir is None:
        base_dir = Path(__file__).parent / "outputs"

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    output_dir = base_dir / test_name / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_component(output_dir: Path, name: str, content: str) -> Path:
    """
    Save a component file to the output directory.

    Args:
        output_dir: Directory to save to.
        name: Component name (used as filename).
        content: Content to write.

    Returns:
        Path to the saved file.
    """
    path = output_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def copy_artifacts(output_dir: Path, artifact_dir: Path) -> list[Path]:
    """
    Copy all artifacts from an artifact directory to the output directory.

    Args:
        output_dir: Destination output directory.
        artifact_dir: Source artifact directory.

    Returns:
        List of paths to copied files.
    """
    if not artifact_dir.exists():
        return []

    artifacts_dest = output_dir / "artifacts"
    artifacts_dest.mkdir(parents=True, exist_ok=True)

    copied = []
    for src_file in artifact_dir.rglob("*"):
        if src_file.is_file():
            rel_path = src_file.relative_to(artifact_dir)
            dest_file = artifacts_dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            copied.append(dest_file)

    return copied
