---
id: doc-4
title: 001 Intention Audit Trail — Research
type: note
created_date: '2026-06-02 12:09'
---


# Research: Intention Audit Trail MVP (Stop Hook + MCP Planner)

**Date**: 2026-01-27  
**Spec**: `specs/main/spec.md`  
**Plan**: `specs/main/plan.md`

## Decisions

### Decision: Git + `intentions.yaml` is canonical source of truth (MVP)
**Chosen**: Store the intention tree and intention metadata in-repo as `intentions.yaml`, and encode `Intent-Id` trailers in commits.  
**Rationale**: Auditability, distribution, offline availability, and `git blame → commit → Intent-Id → intentions.yaml@commit`.  
**Alternatives considered**:
- Graph DB as source-of-truth: better queries, but worse portability and harder historical reconstruction.

### Decision: Stop hook is the deterministic gate; MCP planner is the analyzer
**Chosen**: Use Claude Code `Stop` hook to enforce invariants and block stopping. When blocked, instruct agent to call an MCP planner tool to generate the required metadata + plan.  
**Rationale**: Enforcement must be deterministic; analysis can be LLM-driven.

### Decision: Patch-level commit plan
**Chosen**: `.intent_audit/commit_plan.yaml` contains unified-diff patches per intention-scoped commit entry.  
**Rationale**: Patch-level planning supports splitting a single file across multiple intention commits safely and deterministically.

### Decision: Evidence and docs are first-class links
**Chosen**: Intentions link `evidence_tests` and `supporting_docs` (either embedded in `intentions.yaml` and/or duplicated into commit plan + commit trailers).  
**Rationale**: “still supported” requires objective evidence; coordination also requires linked supporting information.

### Decision: Functionality vs implementation intentions (DDD alignment)
**Chosen**:
- `kind: functionality` intentions define module semantics and carry `code_home` boundaries.
- `kind: implementation` intentions realize functionality, should map cleanly to commits, and should remain within `code_home` unless structure changes are also planned.  
**Rationale**: Folder/file/named-scope naming should encode domain meaning, not mechanism.

## Policies (MVP defaults)

### Evidence policy
- Default mode: **link-only** enforcement (evidence links required).
- Demo mode: **execute impacted evidence tests at stop time** and block on failures.

### Docs policy
- If intention affects externally-relevant behavior, link docs or provide a rationale for no docs.

### Structure alignment policy
- Every intention commit entry MUST specify its `functionality_intent_id` (closest functionality ancestor).
- The stop gate MUST ensure patches only touch paths within that functionality’s `code_home`, unless the plan includes a move/rename/split patch or explicit override rationale.

## Open questions (deferred)
- Whether to store raw transcript text vs hashes/summaries in session records.
- Whether to add a derived SQLite/graph index post-MVP for fast longitudinal queries.

