---
id: TASK-1
title: Intention Audit Trail MVP (Stop hook + MCP planner)
status: Done
assignee: []
created_date: "2026-06-02 12:10"
labels:
  - feature
  - mvp
dependencies: []
documentation:
  - doc-1
  - doc-2
  - doc-3
  - doc-6
  - doc-7
  - doc-8
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Intention audit trail enforced by a Claude Code Stop hook that blocks until the agent (via MCP planner tools) produces intention metadata, evidence/docs links, and an intention-scoped commit plan. Originally specified with Spec Kit under specs/001-intent-audit-trail; that spec/plan/data-model/tasks/notes now live in backlog/docs (doc-1 through doc-8), and the artifact JSON schemas are preserved as reference contracts under backlog/docs/contracts/.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Any non-empty working diff cannot stop unless 100% of hunks map to intention commits (SC-001)
- [ ] #2 Produced commits contain Intent-Id trailers traceable via git blame to intentions.yaml (SC-002)
- [ ] #3 A failing evidence test blocks stopping and surfaces intention-linked code/docs/test context for repair-vs-supersede (SC-003)
- [ ] #4 Structure alignment check blocks cross-domain patches unless structure changes or an explicit override is recorded (SC-004)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

Implemented as the 001-intent-audit-trail feature: Stop hook with 5 validation phases, sub-agents (intention-mapper, commit-planner, evidence-checker, structure-validator, session-recorder), MCP persistence tools, and E2E coverage. Full implementation notes preserved in doc-7.

<!-- SECTION:FINAL_SUMMARY:END -->
