#!/usr/bin/env python3
"""
Claude Code Stop hook: intention→edit coverage + auto-commit.

MVP constraints:
- Uses file-level mapping (each changed file belongs to exactly one commit entry).
- Avoids external dependencies by requiring the commit plan file to be JSON
  (YAML JSON-subset is accepted).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HOOK_VERSION = "0.1.0"

INTENTIONS_FILE_REL = "intentions.yaml"
PLAN_FILE_REL = ".intent_audit/commit_plan.yaml"
CONFIG_FILE_REL = ".intent_audit/config.json"

DEFAULT_MCP_TOOL_NAME = "mcp__intention_audit__plan_commits"
MCP_TOOL_ENV_VAR = "INTENTION_AUDIT_MCP_TOOL"

INTERNAL_PATH_PREFIXES = (
    ".intent_audit/",
    ".claude/",
)


@dataclass(frozen=True)
class GitResult:
    stdout: str
    stderr: str
    exit_code: int


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def _read_hook_input() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _project_dir(hook_input: dict[str, Any]) -> Path:
    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return Path(env_project_dir)
    cwd = hook_input.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return Path(cwd)
    return Path.cwd()


def _run_git(project_dir: Path, args: Sequence[str]) -> GitResult:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
    )
    return GitResult(stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)


def _git_ok(project_dir: Path, args: Sequence[str]) -> str:
    result = _run_git(project_dir, args)
    if result.exit_code != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.exit_code}): {result.stderr.strip()}"
        )
    return result.stdout


def _is_git_repo(project_dir: Path) -> bool:
    result = _run_git(project_dir, ["rev-parse", "--is-inside-work-tree"])
    return result.exit_code == 0 and result.stdout.strip() == "true"


def _get_mcp_tool_name(project_dir: Path) -> str:
    env_tool = os.environ.get(MCP_TOOL_ENV_VAR)
    if env_tool:
        return env_tool.strip()

    config_path = project_dir / CONFIG_FILE_REL
    if not config_path.exists():
        return DEFAULT_MCP_TOOL_NAME

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_MCP_TOOL_NAME

    tool_name = config.get("mcp_tool_name")
    if isinstance(tool_name, str) and tool_name.strip():
        return tool_name.strip()
    return DEFAULT_MCP_TOOL_NAME


def _is_internal_path(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in INTERNAL_PATH_PREFIXES)


def _parse_porcelain_v1_z(output: str) -> list[str]:
    """
    Parse `git status --porcelain=v1 -z` output into a list of paths.

    Notes:
    - For renames/copies, porcelain emits: `R  old\0new\0`
      We include both old and new paths so the plan can stage deletions/additions safely.
    """
    items = output.split("\0")
    paths: list[str] = []

    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue

        if len(item) < 4:
            i += 1
            continue

        xy = item[0:2]
        path_1 = item[3:]

        is_rename_or_copy = xy[0] in ("R", "C") or xy[1] in ("R", "C")
        if is_rename_or_copy and i + 1 < len(items):
            path_2 = items[i + 1]
            paths.append(path_1)
            if path_2:
                paths.append(path_2)
            i += 2
            continue

        paths.append(path_1)
        i += 1

    # De-dup while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for p in paths:
        if p not in seen:
            deduped.append(p)
            seen.add(p)
    return deduped


def _get_relevant_changed_paths(project_dir: Path) -> list[str]:
    out = _git_ok(project_dir, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    paths = _parse_porcelain_v1_z(out)
    return [p for p in paths if p and not _is_internal_path(p)]


def _get_staged_paths(project_dir: Path) -> list[str]:
    out = _git_ok(project_dir, ["diff", "--cached", "--name-only", "-z"])
    return [p for p in out.split("\0") if p]


def _block(message: str) -> None:
    _eprint(message.rstrip() + "\n")
    sys.exit(2)


def _format_bullets(lines: Iterable[str], limit: int = 60) -> str:
    items = list(lines)
    shown = items[:limit]
    remaining = len(items) - len(shown)
    rendered = "\n".join(f"- {x}" for x in shown)
    if remaining > 0:
        rendered += f"\n- ... ({remaining} more)"
    return rendered


def _load_plan(plan_path: Path) -> dict[str, Any]:
    """
    MVP: plan file must be JSON (YAML JSON-subset is accepted).
    """
    try:
        return json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {plan_path} (MVP requires JSON/YAML-JSON-subset): {e}"
        ) from e


def _validate_rel_path(path: str) -> None:
    if path.startswith("/"):
        raise ValueError(f"Path must be repo-relative, got absolute: {path}")
    if ".." in Path(path).parts:
        raise ValueError(f"Path must not contain '..': {path}")


def _intent_id_exists(intentions_text: str, intent_id: str) -> bool:
    # Accept either YAML-ish `id: INT-...` or JSON `"id": "INT-..."`
    # Keep it simple for MVP: textual membership is good enough.
    if intent_id in intentions_text:
        return True
    pattern = re.compile(rf"(^|\b)id\s*:\s*{re.escape(intent_id)}(\b|$)", re.M)
    return pattern.search(intentions_text) is not None


def _build_commit_message(entry: dict[str, Any]) -> str:
    intent_id = str(entry.get("intent_id", "")).strip()
    subject = str(entry.get("subject") or entry.get("title") or f"chore: {intent_id}").strip()
    body = str(entry.get("body") or "").rstrip()
    intent_path = str(entry.get("intent_path") or "").strip()
    confidence = entry.get("intent_confidence")

    trailers: list[str] = [f"Intent-Id: {intent_id}"]
    if intent_path:
        trailers.append(f"Intent-Path: {intent_path}")
    if isinstance(confidence, (int, float, str)) and str(confidence).strip():
        trailers.append(f"Intent-Confidence: {str(confidence).strip()}")

    parts: list[str] = [subject, ""]
    if body:
        parts.extend([body, ""])
    parts.extend(trailers)
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    hook_input = _read_hook_input()
    project_dir = _project_dir(hook_input)
    mcp_tool_name = _get_mcp_tool_name(project_dir)

    if not _is_git_repo(project_dir):
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: not a Git repository.",
                    "",
                    "Initialize Git first (example):",
                    "- git init",
                    "- git add .",
                    '- git commit -m "chore: initial commit"',
                    "",
                    "Then rerun the agent; this hook will enforce intention-tagged commits.",
                ]
            )
        )

    staged_paths = _get_staged_paths(project_dir)
    if staged_paths:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: index has staged changes.",
                    "",
                    "MVP requires a clean index so it can stage/commit per intention automatically.",
                    "",
                    "Staged paths:",
                    _format_bullets(staged_paths),
                    "",
                    "Fix: unstage them (example):",
                    "- git reset",
                ]
            )
        )

    relevant_changed_paths = _get_relevant_changed_paths(project_dir)
    if not relevant_changed_paths:
        # Nothing to map/commit.
        sys.exit(0)

    intentions_path = project_dir / INTENTIONS_FILE_REL
    plan_path = project_dir / PLAN_FILE_REL

    missing_files: list[str] = []
    if not intentions_path.exists():
        missing_files.append(INTENTIONS_FILE_REL)
    if not plan_path.exists():
        missing_files.append(PLAN_FILE_REL)

    if missing_files:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: missing intention tracking files.",
                    "",
                    "Changed files that must be mapped to intentions:",
                    _format_bullets(relevant_changed_paths),
                    "",
                    "Missing required file(s):",
                    _format_bullets(missing_files),
                    "",
                    "Next step:",
                    f"- Call MCP tool `{mcp_tool_name}` to (a) detect user intentions and (b) produce a per-commit mapping of changed files.",
                    f"- Write the mapping to `{PLAN_FILE_REL}` (JSON; YAML JSON-subset is OK).",
                    "",
                    "Required schema (minimal):",
                    "{",
                    '  "version": 1,',
                    '  "ready": true,',
                    '  "commits": [',
                    "    {",
                    '      "intent_id": "INT-YYYY-MM-DD-NNNN",',
                    '      "intent_path": "Goal/Feature/Leaf",',
                    '      "subject": "feat: ...",',
                    '      "body": "optional",',
                    f'      "files": ["{relevant_changed_paths[0]}"]',
                    "    }",
                    "  ]",
                    "}",
                ]
            )
        )

    try:
        plan = _load_plan(plan_path)
    except Exception as e:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: cannot parse commit plan file.",
                    "",
                    str(e),
                    "",
                    f"Fix `{PLAN_FILE_REL}` (MVP requires JSON; YAML JSON-subset is accepted).",
                ]
            )
        )

    if plan.get("version") != 1:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: unsupported plan version.",
                    "",
                    "Expected: version = 1",
                    f"Actual: version = {plan.get('version')!r}",
                ]
            )
        )

    commits = plan.get("commits")
    if not isinstance(commits, list) or not commits:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: commit plan has no commits.",
                    "",
                    f"Expected `{PLAN_FILE_REL}` to contain a non-empty `commits` array.",
                ]
            )
        )

    if plan.get("ready") is not True:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: commit plan is not marked ready.",
                    "",
                    f'Set `"ready": true` in `{PLAN_FILE_REL}` once the intention→file mapping is complete and reviewed.',
                ]
            )
        )

    # Read intentions file (text only; schema-agnostic for MVP)
    try:
        intentions_text = intentions_path.read_text(encoding="utf-8")
    except Exception as e:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: cannot read intentions file.",
                    "",
                    str(e),
                ]
            )
        )

    planned_files: list[str] = []
    intent_ids: list[str] = []
    for idx, entry in enumerate(commits):
        if not isinstance(entry, dict):
            _block(f"Commit entry #{idx} must be an object/dict.")

        intent_id = str(entry.get("intent_id", "")).strip()
        if not intent_id:
            _block(f"Commit entry #{idx} is missing required field `intent_id`.")
        intent_ids.append(intent_id)

        files = entry.get("files")
        if not isinstance(files, list) or not files:
            _block(f"Commit entry #{idx} is missing required non-empty field `files`.")

        for f in files:
            if not isinstance(f, str) or not f.strip():
                _block(f"Commit entry #{idx} has an invalid file path in `files`.")
            rel_path = f.strip()
            _validate_rel_path(rel_path)
            if _is_internal_path(rel_path):
                _block(
                    "\n".join(
                        [
                            "Intention Audit Stop Hook blocked: commit plan references internal paths.",
                            "",
                            f"Internal paths must not be committed by this automation: {rel_path}",
                        ]
                    )
                )
            planned_files.append(rel_path)

    # Validate intent ids exist in intentions.yaml
    missing_intents = [
        iid for iid in sorted(set(intent_ids)) if not _intent_id_exists(intentions_text, iid)
    ]
    if missing_intents:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: some intent_id values are not present in intentions.yaml.",
                    "",
                    "Missing intent_id(s):",
                    _format_bullets(missing_intents),
                    "",
                    f"Fix `{INTENTIONS_FILE_REL}` or regenerate the plan via `{mcp_tool_name}`.",
                ]
            )
        )

    # Coverage check: each changed file must be mapped to exactly one commit entry.
    changed_set = set(relevant_changed_paths)
    planned_set = set(planned_files)

    duplicates = sorted({p for p in planned_files if planned_files.count(p) > 1})
    if duplicates:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: a file is assigned to multiple commits (MVP is file-scoped).",
                    "",
                    "Duplicate file assignments:",
                    _format_bullets(duplicates),
                    "",
                    "Fix: ensure each changed file appears in exactly one `commits[].files` list.",
                ]
            )
        )

    unassigned = sorted(changed_set - planned_set)
    extra = sorted(planned_set - changed_set)
    if unassigned or extra:
        lines: list[str] = [
            "Intention Audit Stop Hook blocked: commit plan does not exactly cover changed files.",
            "",
        ]
        if unassigned:
            lines.extend(["Unassigned changed file(s):", _format_bullets(unassigned), ""])
        if extra:
            lines.extend(
                ["Planned file(s) that are not currently changed:", _format_bullets(extra), ""]
            )
        lines.extend(
            [
                f"Fix `{PLAN_FILE_REL}` (or regenerate it via `{mcp_tool_name}`) so commits[].files exactly match the changed files above.",
            ]
        )
        _block("\n".join(lines))

    # Perform commits.
    #
    # MVP limitation: file-scoped commits. If a file contains edits for multiple intentions,
    # the plan must be refined (future hunk-scoped patch support).
    for idx, entry in enumerate(commits):
        files = [str(f).strip() for f in entry.get("files", [])]
        intent_id = str(entry.get("intent_id", "")).strip()

        # Stage only the files for this commit
        _git_ok(project_dir, ["add", "-A", "--", *files])

        staged_after = _get_staged_paths(project_dir)
        staged_relevant = [p for p in staged_after if not _is_internal_path(p)]
        if not staged_relevant:
            _block(
                "\n".join(
                    [
                        "Intention Audit Stop Hook blocked: staging produced no changes.",
                        "",
                        f"Commit entry #{idx} (intent_id={intent_id}) staged nothing.",
                        "This usually means the plan is stale or the files were already committed.",
                    ]
                )
            )

        message = _build_commit_message(entry)
        proc = subprocess.run(
            ["git", "commit", "--file", "-"],
            cwd=str(project_dir),
            text=True,
            input=message,
            capture_output=True,
        )
        if proc.returncode != 0:
            _block(
                "\n".join(
                    [
                        "Intention Audit Stop Hook blocked: git commit failed.",
                        "",
                        f"Commit entry #{idx} (intent_id={intent_id})",
                        "",
                        proc.stderr.strip() or "(no stderr)",
                    ]
                )
            )

    # Sanity check: all relevant changes should now be committed.
    remaining = _get_relevant_changed_paths(project_dir)
    if remaining:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: commits completed, but uncommitted changes remain.",
                    "",
                    "Remaining changed files:",
                    _format_bullets(remaining),
                    "",
                    f"Regenerate `{PLAN_FILE_REL}` via `{mcp_tool_name}` to cover the remaining changes.",
                ]
            )
        )

    # Success: allow Claude to stop.
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _block(
            "\n".join(
                [
                    "Intention Audit Stop Hook blocked: unexpected error.",
                    "",
                    f"{type(e).__name__}: {e}",
                    "",
                    f"Hook version: {HOOK_VERSION}",
                ]
            )
        )
