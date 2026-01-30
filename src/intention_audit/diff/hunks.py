"""
Hunk parsing utilities for unified diffs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass
class Hunk:
    """Represents a single hunk from a unified diff."""

    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    content: str  # The raw hunk content including @@ header

    def __str__(self) -> str:
        return f"Hunk({self.file_path}:{self.new_start}-{self.new_start + self.new_count})"


# Regex for parsing diff file headers
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)

# Regex for parsing hunk headers: @@ -old_start,old_count +new_start,new_count @@
_HUNK_HEADER_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$",
    re.MULTILINE,
)


def parse_unified_diff(diff_text: str) -> list[Hunk]:
    """
    Parse a unified diff into a list of Hunk objects.

    Args:
        diff_text: The full unified diff text.

    Returns:
        List of Hunk objects, one per hunk in the diff.
    """
    if not diff_text.strip():
        return []

    hunks: list[Hunk] = []
    current_file: str | None = None

    lines = diff_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for diff header
        header_match = _DIFF_HEADER_RE.match(line)
        if header_match:
            # Use the 'b/' path (destination) as the file path
            current_file = header_match.group(2)
            i += 1
            continue

        # Check for hunk header
        hunk_match = _HUNK_HEADER_RE.match(line)
        if hunk_match and current_file:
            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

            # Collect hunk content until next hunk or next file
            hunk_lines = [line]
            i += 1

            while i < len(lines):
                next_line = lines[i]
                # Stop at next hunk header or diff header
                if next_line.startswith("@@") or next_line.startswith("diff --git"):
                    break
                # Include context and change lines
                if next_line.startswith((" ", "+", "-", "\\")):
                    hunk_lines.append(next_line)
                    i += 1
                elif next_line == "":
                    # Empty line might be part of the hunk or separator
                    hunk_lines.append(next_line)
                    i += 1
                else:
                    break

            hunks.append(
                Hunk(
                    file_path=current_file,
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    content="\n".join(hunk_lines),
                )
            )
            continue

        i += 1

    return hunks


def compute_diff_hash(hunks: list[Hunk]) -> str:
    """
    Compute a deterministic hash for a list of hunks.

    The hash is computed from the normalized content of all hunks,
    sorted by file path and position for determinism.

    Args:
        hunks: List of Hunk objects.

    Returns:
        SHA-256 hash as a hex string.
    """
    if not hunks:
        return hashlib.sha256(b"").hexdigest()

    # Sort hunks by file path, then by line number
    sorted_hunks = sorted(hunks, key=lambda h: (h.file_path, h.new_start))

    # Build normalized content
    parts = []
    for hunk in sorted_hunks:
        # Include file path and position for uniqueness
        parts.append(f"FILE:{hunk.file_path}")
        parts.append(f"POS:{hunk.old_start},{hunk.old_count},{hunk.new_start},{hunk.new_count}")
        parts.append(hunk.content)

    combined = "\n".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
