---
id: doc-2
title: 001 Intention Audit Trail — Implementation Plan
type: plan
created_date: '2026-06-02 12:09'
---


# Implementation Plan: Intention Audit Trail MVP (Stop Hook + MCP Planner)

**Branch**: `[main]` | **Date**: 2026-01-27 | **Spec**: `specs/main/spec.md`  
**Input**: Feature specification from `specs/main/spec.md`

## Summary

Build an intention audit trail / consistency engine enforced by a Claude Code **Stop hook**.

### Core Architecture: Hook → Sub-Agent → MCP Tool

The system has three distinct components with clear responsibilities:

1. **Hook (deterministic checker)**: Checks for session-keyed artifact files. If missing, blocks and logs which sub-agent to run.
2. **Sub-Agent (LLM analyzer)**: Pre-configured Claude agent that analyzes the trajectory/diff and calls MCP tools with analyzed data.
3. **MCP Tool (persistence endpoint)**: Validates and persists the structured data the sub-agent passes to it.

**CRITICAL**: The MCP tool does NOT analyze anything. The sub-agent (an LLM) does all analysis. The MCP tool just receives structured data and writes it to files.

### Session-Keyed Artifacts

All artifact files are keyed by the Claude Code session ID to ensure:
- Each session's artifacts are tracked separately
- Stale artifacts from previous sessions don't cause false positives
- The hook knows exactly which artifacts belong to the current session

Artifact location: `.intent_audit/<session_id>/` contains:
- `intentions.yaml` (or symlink to project-root intentions.yaml)
- `commit_plan.yaml`
- `evidence_results.json`
- `structure_validation.json`
- `session_record.json`

### Blocking Loop

The hook keeps blocking until all required artifacts are present and valid:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOP-LEVEL AGENT SESSION                      │
│                                                                 │
│  1. User makes changes with Claude Code                         │
│  2. User attempts to stop (or post-tool-use hook triggers)      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    HOOK EXECUTES                         │   │
│  │                                                          │   │
│  │  • Reads session_id from hook input                      │   │
│  │  • Checks for .intent_audit/<session_id>/artifacts       │   │
│  │  • If artifact missing → BLOCK with message:             │   │
│  │    "Run sub-agent X with inputs: session_id, cwd, ..."   │   │
│  │  • If all artifacts valid → ALLOW (execute commit plan)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼ (if blocked)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  SUB-AGENT SPAWNED                       │   │
│  │                                                          │   │
│  │  • Sub-agent is an LLM with pre-configured tools         │   │
│  │  • Sub-agent ANALYZES: reads transcript, diffs, etc.     │   │
│  │  • Sub-agent CALLS MCP tool with structured data:        │   │
│  │    mcp__intention_audit__save_intentions({               │   │
│  │      session_id: "...",                                  │   │
│  │      intentions: { id: "...", title: "...", ... }        │   │
│  │    })                                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   MCP TOOL EXECUTES                      │   │
│  │                                                          │   │
│  │  • Receives structured data from sub-agent               │   │
│  │  • Validates schema                                      │   │
│  │  • Writes to .intent_audit/<session_id>/<artifact>.yaml  │   │
│  │  • Returns success/error                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  3. Agent attempts to stop again → hook re-checks artifacts     │
│  4. Repeat until all artifacts present and valid                │
│  5. Hook executes commit plan, allows stop                      │
└─────────────────────────────────────────────────────────────────┘
```

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

### Product vs Tooling Distinction

This project has two distinct categories of artifacts:

| Category | Location | Purpose | Deployment |
| -------- | -------- | ------- | ---------- |
| **PRODUCT** | `src/intention_audit/` | The tool being built | Copied to target repos |
| **PRODUCT** | `mcp_servers/intention_audit/` | MCP tools called by sub-agents | Server for target repos |
| **TOOLING** | `.claude/hooks/` | Hooks for developing THIS repo | N/A - local only |
| **TOOLING** | `.claude/agents/` | Agents for developing THIS repo | N/A - local only |

### Documentation (this feature)

```text
specs/001-intent-audit-trail/
├── spec.md              # Feature spec (this feature)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (PRODUCT - being developed)

```text
src/
└── intention_audit/
    ├── hooks/                         # Stop hook (PRODUCT - copied to target repos)
    │   └── stop_hook.py               # intention audit stop hook
    ├── agents/                        # Sub-agent definitions (PRODUCT - copied to target repos)
    │   ├── README.md                  # Documents the sub-agent pattern
    │   ├── intention-mapper.yaml      # calls map_intentions MCP tool
    │   ├── commit-planner.yaml        # calls plan_commits MCP tool
    │   ├── evidence-checker.yaml      # calls check_evidence MCP tool
    │   ├── structure-validator.yaml   # calls validate_structure MCP tool
    │   └── session-recorder.yaml      # calls record_session MCP tool
    ├── models/                        # intention tree + plan parsing models
    ├── diff/                          # hunk parsing + patch building utilities
    ├── evidence/                      # evidence test runner
    ├── structure/                     # code_home boundary checking
    ├── session/                       # session recording
    ├── docs/                          # docs linkage validation
    └── reporting/                     # intention failure context rendering

mcp_servers/
└── intention_audit/                   # MCP server (PRODUCT - runs as service for target repos)
    ├── server.py                      # MCP server entry point
    └── tools/
        ├── map_intentions.py          # trajectory → intentions.yaml
        ├── plan_commits.py            # diff + intentions → commit_plan.yaml
        ├── check_evidence.py          # run pytest, output evidence_results.json
        ├── validate_structure.py      # check code_home boundaries
        └── record_session.py          # create session record JSON
```

### Development Tooling (TOOLING - for developing THIS repo)

```text
.claude/
├── hooks/                             # PROJECT-LOCAL HOOKS (for developing THIS repo)
│   ├── post_edit.py                   # runs ruff + pyright on edited files
│   ├── stop_run_tests.py              # runs all unit tests on stop
│   └── stop_lint_all.py               # runs ruff --fix + pyright on all files on stop
└── agents/                            # PROJECT-LOCAL AGENTS (for developing THIS repo, if any)
    └── (none currently)
```

### Test Infrastructure

```text
tests/
├── fixtures/
│   └── sample_repos/                  # Sample repo templates (NO .git, NO .claude - created at test time)
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
├── integration/                       # integration tests for individual MCP tools
└── e2e/                               # E2E tests using sample repos + real MCP tools
    ├── conftest.py                    # pytest fixtures: create .git, install product, cleanup
    ├── test_stop_hook_basic.py        # basic stop hook validation tests
    ├── test_demo_scenario.py          # MVP demo: failing evidence surfaces intention context
    └── test_structure_alignment.py    # structural alignment enforcement tests
```

### E2E Output Capture Infrastructure

All E2E test runs produce structured outputs for debugging and analysis:

**Directory structure**: `tests/e2e/outputs/<test-name>/<iso-datetime>/`

**Component files**:
| File | Content | Purpose |
|------|---------|---------|
| `main-transcript.jsonl` | Raw JSONL from main session | Preserve original data |
| `subagent-<id>.jsonl` | Raw sub-agent transcripts | Track agent execution |
| `hook-output.txt` | Stop hook stdout/stderr | Debug blocking messages |
| `mcp-calls.json` | All MCP invocations | Verify tool payloads |
| `artifacts/*.yaml` | Copies of generated files | Inspect actual outputs |
| `git-log.txt` | Final commit log | Verify trailers |
| `combined.md` | Merged transcript | Human-readable analysis |

**Key principle**: No truncation in any component file. Full payloads preserved.

### Runtime State (created by PRODUCT in target repos, NOT in this repo)

```text
# In TARGET repos (not this development repo):
.intent_audit/
├── <session_id>/                      # Session-keyed directory (prevents stale artifact confusion)
│   ├── intentions.yaml                # MCP tool output: intention tree for this session
│   ├── commit_plan.yaml               # MCP tool output: commit plan for this session
│   ├── evidence_results.json          # MCP tool output: test results for this session
│   ├── structure_validation.json      # MCP tool output: boundary check results
│   └── session_record.json            # MCP tool output: audit record (committed at end)
└── sessions/                          # Historical session records (committed to repo)
    └── <session_id>.json              # Moved here after successful stop
```

**Session ID**: Obtained from Claude Code hook input JSON. Each session gets its own artifact directory.

**Why session-keyed?**
- Prevents stale artifacts from previous sessions causing false positives
- Allows parallel sessions (rare but possible)
- Clear cleanup: delete entire session directory after successful commit

**Structure Decision**: single-repo layout with a deterministic nested fixture repo for E2E validation. Functionality intentions define module boundaries via `code_home`.

## Stop Hook → Sub-Agent → MCP Tool Flow

### Component Responsibilities (CRITICAL)

| Component | Responsibility | Does NOT |
|-----------|----------------|----------|
| **Hook** | Check for session-keyed artifacts; block with sub-agent instructions; **execute commit plan when all artifacts present (stop hook only)** | Analyze anything; call MCP tools |
| **Sub-Agent** | Analyze trajectory/diff; determine intentions; call MCP tools with structured data | Write files directly; validate schemas |
| **MCP Tool** | Validate schema; write artifact files; return success/error | Analyze anything; make decisions |

### Detailed Flow

**Step 1: Hook Triggered**
- Hook receives input JSON with `session_id`, `cwd`, etc.
- Hook checks for `.intent_audit/<session_id>/` artifacts
- Artifacts are **keyed by session_id** to prevent stale data confusion

**Step 2: Hook Blocks (if artifacts missing)**
- Returns exit code 2 (block)
- Stderr message: `"Run the 'intention-mapper' sub-agent with inputs: session_id=<id>, cwd=<path>"`
- The message tells the top-level agent WHICH sub-agent to spawn and WHAT inputs to provide

**Step 3: Top-Level Agent Spawns Sub-Agent**
- The main Claude Code agent sees the block message
- Spawns the specified sub-agent (e.g., `intention-mapper`)
- Sub-agent is an LLM with pre-configured tool access

**Step 4: Sub-Agent Analyzes and Calls MCP Tool**
- Sub-agent reads the conversation history/trajectory
- Sub-agent identifies user intentions (THIS IS WHERE LLM ANALYSIS HAPPENS)
- Sub-agent calls MCP tool with analyzed, structured data:
  ```
  mcp__intention_audit__save_intentions({
    session_id: "abc123",
    cwd: "/path/to/repo",
    intentions: {
      id: "INT-2026-01-30-0001",
      title: "Add authentication",
      kind: "functionality",
      children: [...]
    }
  })
  ```

**Step 5: MCP Tool Persists Data**
- MCP tool receives structured data from sub-agent
- Validates against JSON schema
- Writes to `.intent_audit/<session_id>/intentions.yaml`
- Returns `{success: true, path: "..."}` or `{success: false, error: "..."}`

**Step 6: Hook Re-checks**
- On next stop attempt, hook sees the artifact now exists
- Proceeds to next check (or allows stop if all checks pass)

### Sub-Agent Definitions (PRODUCT)

Sub-agents are **PRODUCT code** defined in `src/intention_audit/agents/` (not `.claude/agents/`).

During deployment to target repos, these YAML files are copied to the target repo's `.claude/agents/` directory.

Each sub-agent definition specifies:
- **Tool access**: Which MCP tool(s) the sub-agent can call
- **Input parameters**: Expected inputs (session_id, cwd, etc.)
- **Analysis instructions**: What to analyze and how
- **Output specification**: What data to pass to the MCP tool

**Sub-agents and their MCP tools:**

| Sub-Agent | MCP Tool | Sub-Agent Analyzes | Tool Persists |
|-----------|----------|-------------------|---------------|
| `intention-mapper` | `save_intentions` | Transcript → intention tree | `intentions.yaml` |
| `commit-planner` | `save_commit_plan` | Diff + intentions → commit mapping | `commit_plan.yaml` |
| `evidence-checker` | `save_evidence_results` | Test execution → results | `evidence_results.json` |
| `structure-validator` | `save_structure_validation` | Paths vs code_home → violations | `structure_validation.json` |
| `session-recorder` | `save_session_record` | Session summary → audit record | `session_record.json` |

### Sub-Agent Context Protocol

**Rationale**: Main agent has conversation context. Sub-agents need structured summaries, not raw transcripts.

**Main Agent's Responsibility When Spawning intention-mapper:**

The main agent MUST compile and pass:

1. **User-Stated Intentions** (from conversation):
   ```
   - "Create a greeting function that returns Hello World"
   - "Put it in src/feature_x/greet.py"
   - "Keep it simple"
   ```

2. **Implementation Augmentations** (discovered during work):
   ```
   - Created directory src/feature_x/ (didn't exist)
   - Used standard Python string return (no formatting)
   - Added newline at end of file (PEP8)
   ```

3. **Changed Files Summary**:
   ```
   - src/feature_x/greet.py (new file) - contains greet() function
   ```

**intention-mapper Sub-Agent's Responsibility:**

1. Read `git diff HEAD` to see exact changes
2. For each changed file, identify which intention(s) it serves
3. Structure as tree: goal → functionality → implementation
4. Link files to leaf intentions via `code_home` or explicit mapping
5. Call `mcp__intention-audit__save_intentions` with structured tree

**commit-planner Sub-Agent's Responsibility:**

1. Read the saved `intentions.yaml`
2. Read `git diff HEAD` to see all changes
3. Group files by the intention they serve
4. Create commit entries with proper trailers
5. Call `mcp__intention-audit__save_commit_plan`

### Stop Hook Blocking Message Format

When blocking for missing intentions:
```
Intention Audit Stop Hook blocked: missing intentions artifact.

Session ID: <session_id>
Diff hash: <diff_hash>
Expected artifact: .intent_audit/<session_id>/<diff_hash>/intentions.yaml

Changed files:
- src/feature_x/greet.py (new file)
- src/feature_x/__init__.py (new file)

ACTION REQUIRED:
1. Compile a summary of:
   - User-stated intentions from this conversation
   - Implementation decisions/discoveries you made
2. Spawn intention-mapper sub-agent with this context
3. The sub-agent will analyze diffs and link changes to intentions
```

### Stop Hook Check Sequence

On each stop attempt, the hook performs checks in order:

1. **Uncommitted changes check**: If `git diff HEAD` is empty → allow stop
2. **Intention mapping check**: If `.intent_audit/<session_id>/intentions.yaml` missing or invalid → block, instruct `intention-mapper` sub-agent
3. **Commit planning check**: If `.intent_audit/<session_id>/commit_plan.yaml` missing or invalid → block, instruct `commit-planner` sub-agent
4. **Coverage check**: If commit plan doesn't cover 100% of diff → block, instruct `commit-planner` sub-agent with coverage error
5. **Evidence check** (if enabled): If `.intent_audit/<session_id>/evidence_results.json` missing → block, instruct `evidence-checker` sub-agent
6. **Evidence failure check**: If evidence_results.json shows failures → block with intention context report (agent must fix or supersede)
7. **Structure alignment check**: If `.intent_audit/<session_id>/structure_validation.json` missing or shows violations → block, instruct `structure-validator` sub-agent
8. **All checks pass**: Execute commit plan (apply patches, create commits with trailers), clean up `.intent_audit/<session_id>/`, allow stop

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
2. Test installs PRODUCT artifacts into sample repo:
   - `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
   - `src/intention_audit/agents/*.yaml` → sample repo `.claude/agents/`
   - Creates `.intent_audit/` directory structure in sample repo
   - Configures MCP server access for real tool execution
3. Test runs stop hook against sample repo
4. Test cleanup deletes `.git`, `.claude/`, and `.intent_audit/` from sample repo

This separation ensures:
- Clean development workflow (project-local hooks)
- Testable product (project-focus artifacts tested in isolation)
- No confusion about which artifacts are product vs tooling

### Deterministic E2E execution model

E2E tests treat the **PRODUCT stop hook as a CLI** running in isolated sample repos:

**Test Setup** (pytest fixtures in `tests/e2e/conftest.py`):
- Create `.git` repository in sample repo directory using `subprocess.run(["git", "init"])`
- Install PRODUCT artifacts into sample repo:
  - `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
  - `src/intention_audit/agents/*.yaml` → sample repo `.claude/agents/`
  - Create `.intent_audit/` directory structure
- Configure MCP server access for real tool execution
- Create initial commit with sample code
- Apply test-specific changes (edits, regressions, etc.)

**Test Execution**:
- Invoke stop hook with **synthetic Stop-hook JSON input** on stdin
- Run inside the sample repo working directory
- Call real MCP tools to simulate sub-agent execution between stop-hook invocations
- Assert on:
  - exit code (0 allow stop, 2 block)
  - stderr "block reason" content
  - Git state (commits created, trailers present, clean working tree)

**Test Cleanup**:
- Delete `.git/` directory from sample repo
- Delete `.claude/` directory from sample repo
- Delete `.intent_audit/` directory from sample repo
- Reset sample repo to original state

**Critical**: Sample repos are **template directories** only. Their runtime state is:
- Created at test time
- Never committed to this repository
- Deleted after each test run
- Excluded via `.gitignore` if accidentally created

### MCP tools in E2E tests

E2E tests use the **real MCP tools** from `mcp_servers/intention_audit/tools/` for complete integration testing.

**IMPORTANT**: In E2E tests, we simulate the sub-agent's job by calling MCP tools directly with pre-determined test data. This is valid because:
- The MCP tool's job is just to validate schema and persist data
- The sub-agent (LLM) analysis is the non-deterministic part we can't test end-to-end deterministically
- We test that the hook→tool→artifact→hook flow works correctly

**MCP Tools (persistence endpoints):**

| Tool | Input | Output |
|------|-------|--------|
| `save_intentions` | `{session_id, cwd, intentions: {...}}` | `intentions.yaml` |
| `save_commit_plan` | `{session_id, cwd, plan: {...}}` | `commit_plan.yaml` |
| `save_evidence_results` | `{session_id, cwd, results: {...}}` | `evidence_results.json` |
| `save_structure_validation` | `{session_id, cwd, validation: {...}}` | `structure_validation.json` |
| `save_session_record` | `{session_id, cwd, record: {...}}` | `session_record.json` |

**E2E Test Flow:**
1. Set up sample repo with changes
2. Run stop hook → blocks, says "run intention-mapper with session_id=X"
3. Test harness calls `save_intentions` MCP tool with test intention data
4. Run stop hook again → blocks, says "run commit-planner"
5. Test harness calls `save_commit_plan` MCP tool with test plan data
6. Run stop hook again → passes, creates commits
7. Verify commits have correct trailers

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
