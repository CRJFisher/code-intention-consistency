---
id: TASK-2
title: "Harden commit-ownership: verify trailers instead of best-effort blocking"
status: To Do
assignee: []
created_date: "2026-06-03 16:20"
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Part of the proposed offline side-agent architecture (see architecture.html / build-plan-offline-sidecar.md). The M5b PreToolUse commit guard denies direct 'git commit' invocations, but it is best-effort, not a sandbox: an agent that writes then executes a shell script can still create a trailer-less commit, leaving permanent holes in the Intent-Id audit trail. This ticket parks the deeper fix.

The robust approach: instead of trying to block every commit path, VERIFY at a boundary (PostToolUse on Bash, and/or SessionEnd) that no new commit landed without Intent-Id trailers. On detecting a trailer-less commit, flag it (and optionally have the offline writer reconcile/amend it with the correct intention mapping).

Contingent on the offline-architecture redesign being adopted; revisit when that parent work is planned.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Detect any commit created during a session that lacks Intent-Id trailers (covering script-indirect commits the PreToolUse guard misses)
- [ ] #2 On detection, surface a clear flag to the user and/or queue reconciliation by the offline writer
- [ ] #3 Decision recorded: verify-at-boundary vs block-every-path (with rationale and chosen scope)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

Deferred from build-plan-offline-sidecar.md M5b. Best-effort blocking is the agreed MVP scope; this is the hardening follow-up. No work until the offline-architecture parent task exists.

<!-- SECTION:NOTES:END -->
