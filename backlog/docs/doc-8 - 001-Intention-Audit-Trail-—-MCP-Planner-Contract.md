---
id: doc-8
title: 001 Intention Audit Trail — MCP Planner Contract
type: spec
created_date: '2026-06-02 12:09'
---


# MCP Planner Tool Contract (MVP)

## Tool name (proposed)
`mcp__intention_audit__plan_intention_commits`

## Purpose
Analyze the agent’s trajectory (conversation + current diff) and emit the metadata required by the stop gate:
- `intentions.yaml`
- `.intent_audit/sessions/<session_id>.json`
- `.intent_audit/commit_plan.yaml`

## Inputs (minimum)
- `session_id` (string)
- `transcript_path` (string) or `transcript_ref` (string)
- `repo_root` (string)
- `diff_base` (string, e.g. `HEAD`)
- `diff_text` (string, unified diff) OR `diff_hunks` (structured)
- Existing `intentions.yaml` contents if present

## Outputs (required)
- Updated `intentions.yaml` text
- `SessionRecord` JSON object
- `CommitPlan` JSON object (YAML JSON-subset allowed)

## Output responsibilities
- Generate/modify intentions, explicitly differentiating:
  - `kind:functionality` (domain semantics; owns `code_home`)
  - `kind:implementation` (how; maps to commits)
- Link evidence tests and supporting docs to the relevant intentions.
- Produce patch-level commit plan entries that:
  - cover 100% of diff hunks exactly once
  - specify `functionality_intent_id` for structural alignment checks

