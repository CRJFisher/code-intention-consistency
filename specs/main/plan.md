# Implementation Plan: Intention Audit Trail MVP (Stop Hook + MCP Planner)

**Branch**: `[main]` | **Date**: 2026-01-27 | **Spec**: `specs/main/spec.md`  
**Input**: Feature specification from `specs/main/spec.md`

## Summary

Build an intention audit trail / consistency engine enforced by a Claude Code **Stop hook**.

- The stop hook blocks stopping if there are uncommitted changes and missing/invalid metadata.
- When blocked, the hook instructs the agent to run a **specific sub-agent** (e.g., `intention-mapper`, `commit-planner`) with appropriate inputs.
- Each sub-agent is pre-configured to call a dedicated **MCP tool** that:
  - Analyzes trajectory data (conversation + diff)
  - Produces structured output files (`intentions.yaml`, `commit_plan.yaml`, etc.)
- On subsequent stop attempts, the hook checks for file presence to determine completion:
  - `intentions.yaml` present & valid → intention mapping complete
  - `commit_plan.yaml` present & valid → commit planning complete
  - Evidence results present → evidence checking complete
- Once all checks pass, the stop hook executes the commit plan to produce intention-scoped commits with standardized trailers.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Claude Code hooks + sub-agents + MCP server tooling (multiple specialized tools), `uv/uvx` optional for execution
**Storage**: Git commits + YAML/JSON files in-repo (no external DB for MVP)
**Testing**: pytest (evidence tests), plus lightweight unit tests for plan parsing/validation
**Target Platform**: Local developer machines (macOS/Linux)
**Project Type**: single
**Performance Goals**: stop hook validation < 2s for small diffs; < 60s when evidence tests are executed
**Constraints**: deterministic stop gate; modular sub-agent architecture; full diff coverage; auditable artifacts; structure alignment enforcement
**Scale/Scope**: small-to-medium repos; incremental index/graph is deferred post-MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Intention-first development**: PASS (canonical `intentions.yaml`, required commit trailers, stop gate enforcement)
- **Evidence-backed intentions**: PASS (evidence test links required; stop-time execution configurable)
- **Functionality drives structure**: PASS (functionality vs implementation taxonomy + `code_home` boundary checks)
- **Supporting docs linked**: PASS (doc links required or explicit rationale)
- **Deterministic stop hook + planner**: PASS (stop hook enforces; planner generates metadata + plan)

## Phase 0: Outline & Research (resolve clarifications)

All prior “NEEDS CLARIFICATION” items are resolved by choosing defaults compatible with the
design docs and constitution:

- **Canonical SoT**: Git + `intentions.yaml` (no graph DB in MVP; derived index later)
- **Plan execution unit**: patch-level `commit_plan.yaml` with unified diffs per intention commit
- **Evidence policy (demo)**: enable stop-time evidence execution for the demo scenario; allow link-only mode otherwise
- **Structure alignment**: enforce via functionality `code_home` prefixes
- **Session audit record**: commit a normalized session record (no raw transcript by default)

Output: `specs/main/research.md`

## Phase 1: Design & Contracts

1. **Data model**: define the canonical entities and their fields (intentions, commit plans, session records, evidence/docs links).
2. **Contracts**: define JSON schemas for:
   - `intentions.yaml` (JSON-compatible subset)
   - `.intent_audit/commit_plan.yaml`
   - `.intent_audit/sessions/<session_id>.json`
   - MCP planner tool request/response shape
3. **Quickstart**: define how to run the demo scenario end-to-end (stop gate blocks on failing evidence and surfaces intention context).

Output: `specs/main/data-model.md`, `specs/main/contracts/*`, `specs/main/quickstart.md`

## Agent context update

After Phase 1 design outputs are created, run:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

## Phase 2: Tasks planning (not produced by this command)

Use `/speckit.tasks` to generate `specs/main/tasks.md` from the above artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/main/
├── spec.md              # Feature spec (this feature)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks) - not created by /speckit.plan
```

### Source Code + Test Target (repository root)

```text
.claude/
├── hooks/                             # PROJECT-LOCAL HOOKS (for developing THIS repo)
│   ├── post_edit.py                   # runs ruff + pyright on edited files
│   ├── stop_run_tests.py              # runs all unit tests on stop
│   └── stop_lint_all.py               # runs ruff --fix + pyright on all files on stop
└── agents/
    ├── intention-mapper.yaml          # sub-agent: calls map_intentions MCP tool
    ├── commit-planner.yaml            # sub-agent: calls plan_commits MCP tool
    ├── evidence-checker.yaml          # sub-agent: calls check_evidence MCP tool
    ├── structure-validator.yaml       # sub-agent: calls validate_structure MCP tool
    └── session-recorder.yaml          # sub-agent: calls record_session MCP tool

src/
└── intention_audit/
    ├── hooks/                         # PROJECT-FOCUS HOOKS (the product we're building)
    │   └── stop_hook.py               # intention audit stop hook (copied to sample repos for E2E tests)
    ├── models/                        # intention tree + plan parsing models
    ├── diff/                          # hunk parsing + patch building utilities
    └── reporting/                     # intention failure context rendering

mcp_servers/
└── intention_audit/
    ├── server.py                      # MCP server entry point
    └── tools/
        ├── map_intentions.py          # trajectory → intentions.yaml
        ├── plan_commits.py            # diff + intentions → commit_plan.yaml
        ├── check_evidence.py          # run pytest, output evidence_results.json
        ├── validate_structure.py      # check code_home boundaries
        └── record_session.py          # create session record JSON

tests/
├── fixtures/
│   └── sample_repos/                  # sample repo templates (NO .git - created at test time)
│       ├── basic_repo/                # minimal repo for basic stop hook tests
│       │   ├── src/feature_x/         # tiny functionality module
│       │   ├── tests/feature_x/       # pytest evidence tests
│       │   └── docs/                  # supporting docs
│       └── demo_repo/                 # repo for MVP demo scenario
│           ├── src/calculator/        # calculator module with intentional regression
│           ├── tests/calculator/      # evidence test that will fail
│           ├── docs/calculator.md     # supporting docs
│           └── intentions.yaml        # pre-populated intentions with evidence links
├── unit/                              # unit tests for models, diff parsing, reporting
├── integration/                       # integration tests for MCP tools
└── e2e/                               # E2E tests using sample repos
    ├── conftest.py                    # pytest fixtures: create .git, copy hooks, cleanup
    ├── test_stop_hook_basic.py        # basic stop hook validation tests
    ├── test_demo_scenario.py          # MVP demo: failing evidence surfaces intention context
    └── test_structure_alignment.py    # structural alignment enforcement tests

.intent_audit/
├── commit_plan.yaml                   # tool output; checked by stop hook
├── evidence_results.json              # tool output; checked by stop hook
├── structure_validation.json          # tool output; checked by stop hook
└── sessions/
    └── <session_id>.json              # committed audit record
```

**Structure Decision**: single-repo layout with a deterministic nested fixture repo for E2E validation. Functionality intentions define module boundaries via `code_home`.

## Stop Hook → Sub-Agent → MCP Tool Flow

### Architecture Overview

The MVP uses a **modular sub-agent architecture** where each consistency check is handled by a dedicated sub-agent that calls a specialized MCP tool:

1. **Stop hook detects missing checks**: Examines working directory for required files (`.intent_audit/commit_plan.yaml`, `evidence_results.json`, etc.)
2. **Stop hook blocks with instructions**: Returns exit code 2 with message: "Run the `intention-mapper` agent with inputs: session_id=X, cwd=Y, transcript_path=Z"
3. **Agent launches sub-agent**: Main agent spawns the specified sub-agent with provided inputs
4. **Sub-agent calls MCP tool**: Sub-agent is pre-configured to call the appropriate MCP tool (e.g., `mcp__intention_audit__map_intentions`)
5. **MCP tool produces output file**: Tool analyzes trajectory data and writes structured file (e.g., `intentions.yaml`)
6. **File presence indicates completion**: On next stop attempt, hook checks for file and proceeds to next check

### Sub-Agent Definitions

Each sub-agent is defined in `.claude/agents/` with:
- **Tool access**: Granted access to specific MCP tool(s)
- **Input parameters**: Expected inputs (session_id, cwd, transcript_path, diff_base, etc.)
- **Output specification**: File path(s) to create
- **Prompt template**: Instructions for calling the MCP tool with structured parameters

Example sub-agents:
- `intention-mapper`: Calls `map_intentions` tool → produces `intentions.yaml`
- `commit-planner`: Calls `plan_commits` tool → produces `.intent_audit/commit_plan.yaml`
- `evidence-checker`: Calls `check_evidence` tool → produces `.intent_audit/evidence_results.json`
- `structure-validator`: Calls `validate_structure` tool → produces `.intent_audit/structure_validation.json`
- `session-recorder`: Calls `record_session` tool → produces `.intent_audit/sessions/<session_id>.json`

### Stop Hook Check Sequence

On each stop attempt, the hook performs checks in order:

1. **Uncommitted changes check**: If `git diff HEAD` is empty → allow stop
2. **Intention mapping check**: If `intentions.yaml` missing or invalid → block, instruct `intention-mapper` agent
3. **Commit planning check**: If `.intent_audit/commit_plan.yaml` missing or invalid → block, instruct `commit-planner` agent
4. **Coverage check**: If commit plan doesn't cover 100% of diff → block, instruct `commit-planner` agent with coverage error
5. **Evidence check** (if enabled): If `.intent_audit/evidence_results.json` missing → block, instruct `evidence-checker` agent
6. **Evidence failure check**: If evidence_results.json shows failures → block with intention context report
7. **Structure alignment check**: If `.intent_audit/structure_validation.json` missing or shows violations → block, instruct `structure-validator` agent
8. **All checks pass**: Execute commit plan (apply patches, create commits with trailers), clean up `.intent_audit/`, allow stop

## MVP validation strategy (testable target)

### Why a nested fixture repo (vs self-hosting)
For the MVP, we will validate the consistency engine against a **dedicated nested sample repo** rather than trying to “self-host” the audit trail on this project immediately.

- **Determinism**: fixture repo contents, diffs, and expected hook outputs can be versioned as golden test fixtures.
- **E2E testability**: tests can run the stop hook process, inspect created commits, and compare outputs reliably.
- **Avoid bootstrap loops**: self-hosting introduces a chicken/egg problem where the tool evolves while enforcing itself.

Self-hosting remains a strong post-MVP milestone once the gates and reporting are stable.

### Hook Types: Project-Local vs Project-Focus

This repository uses **two distinct types of hooks**:

#### 1. Project-Local Hooks (`.claude/hooks/`)

Hooks for developing **this repository** - standard development workflow automation:

- **`post_edit.py`**: Runs after file edits
  - Executes `ruff check --fix` on edited files
  - Executes `pyright` on edited files
  - Reports linting/type errors immediately

- **`stop_run_tests.py`**: Runs on Stop event
  - Executes `uv run pytest` to run all unit tests
  - Blocks stopping if tests fail

- **`stop_lint_all.py`**: Runs on Stop event
  - Executes `ruff check --fix .` on entire codebase
  - Executes `pyright .` on entire codebase
  - Ensures code quality before stopping

These hooks use the standard Claude Code hook configuration in `.claude/settings.json`.

#### 2. Project-Focus Hooks (`src/intention_audit/hooks/`)

The **intention audit trail stop hook** - the actual product being built:

- **`stop_hook.py`**: The intention audit trail enforcement hook
  - This is what we're developing as the product
  - Dynamically **copied** to sample repos during E2E tests
  - Enforces intention metadata, evidence tests, structural alignment
  - Not used for developing this repo (until post-bootstrap)

**E2E Test Workflow**:
1. Test setup creates `.git` in `tests/fixtures/sample_repos/<repo_name>/`
2. Test copies `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
3. Test runs stop hook against sample repo
4. Test cleanup deletes `.git` and `.claude/` from sample repo

This separation ensures:
- Clean development workflow (project-local hooks)
- Testable product (project-focus hook tested in isolation)
- No confusion about which hook enforces what

### Deterministic E2E execution model

E2E tests treat the **project-focus stop hook as a CLI** running in isolated sample repos:

**Test Setup** (pytest fixtures in `tests/e2e/conftest.py`):
- Create `.git` repository in sample repo directory using `subprocess.run(["git", "init"])`
- Copy `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
- Create initial commit with sample code
- Apply test-specific changes (edits, regressions, etc.)

**Test Execution**:
- Invoke stop hook with **synthetic Stop-hook JSON input** on stdin
- Run inside the sample repo working directory
- Assert on:
  - exit code (0 allow stop, 2 block)
  - stderr "block reason" content
  - Git state (commits created, trailers present, clean working tree)

**Test Cleanup**:
- Delete `.git/` directory from sample repo
- Delete `.claude/` directory from sample repo
- Reset sample repo to original state

**Critical**: Sample repos are **template directories** only. Their `.git` folders are:
- Created at test time
- Never committed to this repository
- Deleted after each test run
- Excluded via `.gitignore` if accidentally created

### MCP tools in E2E tests (mocked for determinism)
The production workflow calls MCP server tools via sub-agents, but tests need deterministic output:

- Provide **mock tool implementations** used in E2E that:
  - `mock_map_intentions`: reads trajectory, writes deterministic `intentions.yaml`
  - `mock_plan_commits`: reads diff + intentions, writes deterministic `commit_plan.yaml`
  - `mock_check_evidence`: runs pytest, writes `evidence_results.json`
  - `mock_validate_structure`: checks boundaries, writes `structure_validation.json`
  - `mock_record_session`: writes `sessions/<session_id>.json`

E2E harness simulates "agent ran sub-agent → sub-agent called MCP tool" by running mock tools between stop-hook invocations.

### Primary E2E demo scenario: failing evidence surfaces intention context

1. **Baseline setup**
   - Make code edit in `fixtures/sample_repo/src/feature_x/calculator.py`
   - Attempt stop → hook blocks: "Run `intention-mapper` agent"
   - Agent runs `intention-mapper` sub-agent → calls `map_intentions` MCP tool → produces `intentions.yaml`
     - Functionality intention: `kind:functionality`, `code_home: ["src/feature_x/"]`
     - Implementation intention: leaf that realizes "Behavior Y"
   - Attempt stop → hook blocks: "Run `commit-planner` agent"
   - Agent runs `commit-planner` sub-agent → calls `plan_commits` MCP tool → produces `commit_plan.yaml`
   - Attempt stop → hook blocks: "Run `evidence-checker` agent" (demo mode enabled)
   - Agent runs `evidence-checker` sub-agent → calls `check_evidence` MCP tool → runs tests → produces `evidence_results.json` (all passing)
   - Attempt stop → hook blocks: "Run `structure-validator` agent"
   - Agent runs `structure-validator` sub-agent → calls `validate_structure` MCP tool → produces `structure_validation.json` (no violations)
   - Attempt stop → hook validates, executes commit plan, creates commits with trailers, cleans up `.intent_audit/`, allows stop

2. **Regression**
   - Make code change that breaks evidence test
   - Attempt stop → hook blocks: "Run `intention-mapper` agent" (intentions.yaml missing after cleanup)
   - Agent runs sub-agent → intentions updated with new edit
   - Attempt stop → hook blocks: "Run `commit-planner` agent"
   - Agent runs sub-agent → commit plan updated
   - Attempt stop → hook blocks: "Run `evidence-checker` agent"
   - Agent runs sub-agent → evidence fails → produces `evidence_results.json` with failures
   - Attempt stop → hook detects failures in `evidence_results.json` → blocks with intention failure context report:
     - failing test selector(s): `tests/feature_x/test_behavior_y.py::test_behavior_y`
     - evidenced intention ID + title + path
     - linked docs: `docs/feature_x.md#behavior-y`
     - code scope: `src/feature_x/calculator.py`

3. **Resolution paths (two tests)**
   - **Repair**: Fix code so evidence passes → re-run `evidence-checker` agent → evidence_results.json now shows passing → stop hook commits
   - **Supersede**: Mark old intention `superseded`, update docs, update/replace evidence → re-run all sub-agents → stop hook commits with new `Intent-Id`s

### Secondary E2E checks
- **Coverage failure**: uncommitted changes without complete mapping → block with missing coverage details.
- **Structural alignment failure**: patch touches outside functionality `code_home` → block until plan includes move/rename/split or explicit override rationale.
- **Docs linkage failure**: externally-relevant behavior change without docs link/rationale → block.

## Complexity Tracking

No constitution violations expected for MVP scope (no external DB; derived index deferred).
