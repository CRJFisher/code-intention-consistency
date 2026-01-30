# Intention Audit Trail (MVP stop hook)

This repo currently contains a **Claude Code `Stop` hook** MVP that enforces an
**intention → edits → commits** discipline.

At a high level:
- If there are uncommitted changes, the stop hook **blocks** until there is a
  complete mapping from changed files to intention IDs.
- Once coverage is complete, the stop hook **creates the commits automatically**
  and encodes intention metadata as Git commit trailers.

## Key files

- **Project hook config**: `.claude/settings.json`
- **Stop hook script**: `.claude/hooks/intent_audit_stop_hook.py`

## Data contract (MVP)

The stop hook looks for these files under `.intent_audit/<session_id>/<diff_hash>/`:

- `intentions.yaml`
  - Intention tree for this session/diff
  - MVP only requires that each `intent_id` referenced by the commit plan exists
    somewhere in this file (text match).
- `commit_plan.yaml`
  - **Required** for committing
  - **MVP restriction**: must be valid **JSON** (YAML JSON-subset is accepted)
  - Each changed file must appear in **exactly one** `commits[].files` list
    (file-scoped MVP; no hunk splitting yet)
- Optional `.intent_audit/config.json`
  - Can set the MCP tool name the hook tells the agent to call:

```json
{ "mcp_tool_name": "mcp__intention_audit__plan_commits" }
```

You can also override with an env var:
- `INTENTION_AUDIT_MCP_TOOL`

### `commit_plan.yaml` schema (minimal)

```json
{
  "version": 1,
  "ready": true,
  "commits": [
    {
      "intent_id": "INT-YYYY-MM-DD-NNNN",
      "intent_path": "Goal/Feature/Leaf",
      "subject": "feat: short summary",
      "body": "optional longer explanation",
      "files": ["relative/path/to/file1", "relative/path/to/file2"]
    }
  ]
}
```

Sample templates:
- `intentions.yaml.example`
- `examples/commit_plan.yaml`

## Commit message format

The stop hook creates commits using this structure:

```
<subject>

<body (optional)>

Intent-Id: <intent_id>
Intent-Path: <intent_path (optional)>
Intent-Confidence: <optional>
```

## Setup notes

Claude Code hooks are configured via:
- Project settings: `.claude/settings.json` (this repo uses this)

After editing hook settings, you typically need to review/apply changes in the
Claude Code `/hooks` UI (Claude snapshots hooks at session start).

**Important**: Add `.intent_audit/` to your `.gitignore`. The artifact directory
must not appear as untracked files, otherwise the diff hash changes on every
stop invocation, creating an infinite blocking loop.

## Known MVP limitations

- **File-scoped commits only**: a single file cannot be split across multiple
  intention commits in this MVP.
- **Plan file is JSON-only**: avoids needing a YAML parser dependency in the hook.
- Requires a **clean Git index** (no staged changes) so the hook can stage per
  intention safely.

## Design docs

- `Intention Audit Trail Design Document.md`
- `Intention Audit Trail Design.md`

