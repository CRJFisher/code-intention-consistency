# Quickstart: Intention Audit Trail MVP

This quickstart describes the **demo flow** for the MVP: stop-time consistency checks that are intention-aware.

## Prerequisites
- Claude Code hooks enabled for the repo
- An MCP server tool implementing `mcp__intention_audit__plan_intention_commits`

## Demo scenario: failing evidence surfaces intention context

### 1) Establish a baseline intention with evidence + docs
- Add a small “feature_x” module, a unit test, and a doc entry.
- Create intentions:
  - Functionality intention with `code_home` for the module boundary
  - Implementation intention for the initial behavior
  - Tests/docs nodes (or linked artifacts) as evidence/support

### 2) Attempt to stop with unplanned changes
- Make a code edit.
- Attempt to stop.
- **Expected**: stop hook blocks and instructs calling the MCP planner tool in a sub-agent.

### 3) Call planner and produce artifacts
Planner outputs:
- `intentions.yaml`
- `.intent_audit/sessions/<session_id>.json`
- `.intent_audit/commit_plan.yaml` (patch-level; complete coverage)

### 4) Stop gate commits the baseline
- Attempt to stop again.
- **Expected**: stop hook validates and creates intention-scoped commits with trailers.

### 5) Introduce a regression (break the evidence)
- Make a change that breaks the evidence test.
- Attempt to stop.
- **Expected**: stop hook runs impacted evidence tests (demo mode), blocks, and prints:
  - failing tests
  - the intention(s) evidenced
  - linked docs
  - code scope (paths; symbols if recorded)

### 6) Repair or supersede
- Repair code to restore support, OR explicitly supersede the intention and update docs/evidence.
- Attempt to stop.
- **Expected**: stop hook passes and commits the updated state.

## Success criteria (demo)
- The stop gate prevents stopping until intention coverage is complete.
- A failing intention-linked test produces an intention-aware report (not just “tests failed”).
- The agent can decide “repair vs supersede” based on surfaced linked artifacts.

