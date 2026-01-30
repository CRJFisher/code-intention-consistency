# Tasks: Intention Audit Trail MVP

**Date**: 2026-01-30
**Spec**: `specs/001-intent-audit-trail/spec.md`
**Plan**: `specs/001-intent-audit-trail/plan.md`

## Overview

This task list implements the Intention Audit Trail MVP across 6 phases:

| Phase   | Description                             | Task Count           |
| ------- | --------------------------------------- | -------------------- |
| Phase 1 | Setup (Shared Infrastructure)           | 10 tasks (T001-T010) |
| Phase 2 | Foundational (Blocking Prerequisites)   | 10 tasks (T011-T020) |
| Phase 3 | User Story 1 - Auto-commit gate (P1)    | 16 tasks (T021-T036) |
| Phase 4 | User Story 2 - Evidence regression (P1) | 14 tasks (T037-T050) |
| Phase 5 | User Story 3 - Structure alignment (P2) | 11 tasks (T051-T061) |
| Phase 6 | Polish & Cross-Cutting                  | 9 tasks (T062-T070)  |

**Total**: 70 tasks

## Product vs Tooling Distinction

This project has two distinct categories of artifacts:

### Product (Being Developed)

Code and configurations that ARE the product - meant to be installed/copied into target repos:

| Artifact | Location | Purpose |
| -------- | -------- | ------- |
| Stop hook | `src/intention_audit/hooks/stop_hook.py` | Enforcement hook for target repos |
| Sub-agent definitions | `src/intention_audit/agents/*.yaml` | Agent configs for target repos |
| Models | `src/intention_audit/models/` | Data models used by hooks/agents |
| MCP server | `mcp_servers/intention_audit/` | MCP tools called by sub-agents |

### Tooling (Being Used)

Code and configurations used to DEVELOP this repo:

| Artifact | Location | Purpose |
| -------- | -------- | ------- |
| Project-local hooks | `.claude/hooks/` | Linting, testing for THIS repo |
| Project-local agents | `.claude/agents/` | Agents for developing THIS repo (if any) |

### E2E Test Strategy

E2E tests copy PRODUCT artifacts into sample repos:

1. Copy `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
2. Copy `src/intention_audit/agents/*.yaml` → sample repo `.claude/agents/`
3. Run stop hook against sample repo
4. Verify behavior

This ensures we test the actual product as it would be deployed.

---

## Architecture: Hook → Sub-Agent → MCP Tool (CRITICAL)

**This section defines the core flow. All tasks MUST adhere to these responsibilities.**

### Component Responsibilities

| Component | IS Responsible For | IS NOT Responsible For |
|-----------|-------------------|------------------------|
| **Hook** | Checking for session-keyed artifacts; blocking with sub-agent instructions | Analysis; calling MCP tools; making decisions |
| **Sub-Agent** | Analyzing trajectory/diff (LLM work); calling MCP tools with structured data | Writing files directly; schema validation |
| **MCP Tool** | Validating schema; persisting data to files; returning success/error | Analysis; decision-making; reading trajectory |

### The Flow

```
1. User makes changes in Claude Code session (session_id = "abc123")
2. User attempts to stop (or post-tool-use hook triggers)
3. HOOK executes:
   - Reads session_id from hook input JSON
   - Checks for .intent_audit/abc123/intentions.yaml
   - NOT FOUND → blocks with: "Run 'intention-mapper' sub-agent with session_id=abc123, cwd=/path"
4. TOP-LEVEL AGENT sees block message, spawns 'intention-mapper' sub-agent
5. SUB-AGENT (LLM) executes:
   - Reads conversation history
   - ANALYZES: identifies intentions, hierarchy, evidence links
   - Calls MCP tool: mcp__intention_audit__save_intentions({
       session_id: "abc123",
       cwd: "/path",
       intentions: { id: "INT-...", title: "...", kind: "...", children: [...] }
     })
6. MCP TOOL executes:
   - Validates intentions against schema
   - Writes to .intent_audit/abc123/intentions.yaml
   - Returns {success: true}
7. User attempts to stop again
8. HOOK re-executes:
   - Checks for .intent_audit/abc123/intentions.yaml → FOUND
   - Checks for .intent_audit/abc123/commit_plan.yaml → NOT FOUND
   - Blocks with: "Run 'commit-planner' sub-agent..."
9. Repeat until all artifacts present
10. HOOK executes commit plan, allows stop
```

### Session-Keyed Artifacts

ALL artifacts MUST be keyed by session_id:
- `.intent_audit/<session_id>/intentions.yaml`
- `.intent_audit/<session_id>/commit_plan.yaml`
- `.intent_audit/<session_id>/evidence_results.json`
- `.intent_audit/<session_id>/structure_validation.json`

**Why?** Prevents stale artifacts from previous sessions causing false positives.

### MCP Tools Are Persistence Endpoints

MCP tools MUST NOT:
- Analyze conversation/trajectory
- Make decisions about intentions
- Read or parse transcripts

MCP tools MUST:
- Accept structured data from sub-agent
- Validate against JSON schema
- Write to session-keyed file path
- Return success/error

### E2E Tests Simulate Sub-Agent Analysis

In E2E tests, we call MCP tools directly with test data to simulate what a sub-agent would produce. This is valid because:
- We're testing the hook → artifact → hook flow
- The sub-agent (LLM analysis) is non-deterministic
- We test with known/controlled intention data

---

## Parallel Opportunities

- **Setup phase**: T001-T006 parallelizable (directory creation)
- **Foundational phase**: T011-T015 parallelizable (models, fixtures)
- **User stories**: Phases 3-5 can run in parallel after Phase 2 completes
- **Within each story**: unit tests, MCP tools, sub-agent definitions parallelizable

## MVP Scope Suggestion

Phases 1-3 only (T001-T036) delivers core value: intention-scoped auto-commit enforcement.

---

## Phase 1: Setup (Shared Infrastructure)

### T001: Create source directory structure

**Status**: [X] completed
**Dependencies**: none
**Parallelizable**: yes (with T002-T006)

Create the `src/intention_audit/` directory structure for PRODUCT code:

```text
src/intention_audit/
├── __init__.py
├── hooks/
│   └── __init__.py
├── agents/              # Sub-agent YAML definitions (PRODUCT)
│   └── README.md
├── models/
│   └── __init__.py
├── diff/
│   └── __init__.py
└── reporting/
    └── __init__.py
```

**Note**: `agents/` contains sub-agent definitions that are PRODUCT artifacts, copied to target repos during deployment/testing.

**Acceptance**: Directories exist with empty `__init__.py` files and agents/README.md.

---

### T002: Create MCP server directory structure

**Status**: [X] completed
**Dependencies**: none
**Parallelizable**: yes (with T001, T003-T006)

Create the `mcp_servers/intention_audit/` directory structure for PRODUCT MCP tools:

```text
mcp_servers/intention_audit/
├── __init__.py
├── server.py          # placeholder
└── tools/
    └── __init__.py
```

**Acceptance**: Directories exist with placeholder files.

---

### T003: Create test directory structure

**Status**: [X] completed
**Dependencies**: none
**Parallelizable**: yes (with T001-T002, T004-T006)

Create the test directory structure:

```text
tests/
├── __init__.py
├── fixtures/
│   └── sample_repos/
│       ├── basic_repo/    # empty dir for now
│       └── demo_repo/     # empty dir for now
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
└── e2e/
    └── __init__.py
```

**Acceptance**: Directories exist with empty `__init__.py` files.

---

### T004: Document sub-agent pattern in product agents directory

**Status**: [X] completed
**Dependencies**: T001
**Parallelizable**: yes (with T002-T003, T005-T006)

Create `src/intention_audit/agents/README.md` explaining:

- These are PRODUCT sub-agent definitions (not development tooling)
- They get copied to target repos' `.claude/agents/` during deployment
- E2E tests copy them to sample repos for testing
- Each YAML defines: purpose, tool access, inputs, outputs, prompt template

**Acceptance**: README.md exists with clear documentation.

---

### T005: Create .intent_audit fixture setup utility

**Status**: [X] completed
**Dependencies**: none
**Parallelizable**: yes (with T001-T004, T006)

Create `tests/e2e/setup_intent_audit.py` utility that populates `.intent_audit/` in sample repos:

- `setup_intent_audit_dir(repo_path: Path) -> None` - creates directory structure
- `cleanup_intent_audit_dir(repo_path: Path) -> None` - removes directory
- Creates: `.intent_audit/sessions/` (for session records)

**Note**: `.intent_audit/` is runtime state created in TARGET repos, not in this development repo. The utility is used by E2E test fixtures.

Also add `.intent_audit/` to `.gitignore` in the root repo (in case of accidental creation during manual testing).

**Acceptance**: Utility functions work correctly; `.gitignore` excludes `.intent_audit/`.

---

### T006: Update pyproject.toml with dependencies

**Status**: [X] completed
**Dependencies**: none
**Parallelizable**: yes (with T001-T005)

Add/verify dependencies in `pyproject.toml`:

- pytest (testing)
- ruff (linting)
- pyright (type checking)
- pyyaml (YAML parsing for intentions/plans)
- jsonschema (contract validation)

**Acceptance**: `uv sync` succeeds, all dependencies available.

---

### T007: Configure pytest for test discovery

**Status**: [X] completed
**Dependencies**: T003, T006

Create/update `pytest.ini` or `pyproject.toml [tool.pytest]` section:

- Test paths: `tests/`
- Markers: `unit`, `integration`, `e2e`
- Default: exclude e2e tests (run via `pytest -m e2e`)

**Acceptance**: `uv run pytest --collect-only` discovers test structure.

---

### T008: Create conftest.py for shared fixtures

**Status**: [X] completed
**Dependencies**: T003, T007

Create `tests/conftest.py` with shared pytest fixtures:

- `project_root` fixture returning the repo root path
- `sample_repos_path` fixture returning `tests/fixtures/sample_repos/`
- `product_src_path` fixture returning `src/intention_audit/`

**Acceptance**: Fixtures importable in test files.

---

### T009: Create E2E conftest.py with repo fixtures

**Status**: [X] completed
**Dependencies**: T003, T005, T008

Create `tests/e2e/conftest.py` with E2E-specific fixtures:

- `basic_repo` fixture: creates temp copy of basic_repo, initializes git, yields path, cleans up
- `demo_repo` fixture: creates temp copy of demo_repo, initializes git, yields path, cleans up
- `install_product_artifacts` fixture: installs all PRODUCT artifacts to sample repo:
  - `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
  - `src/intention_audit/agents/*.yaml` → sample repo `.claude/agents/`
  - Creates `.intent_audit/` directory structure (using T005 utility)
  - Configures MCP server path in sample repo config
- `run_mcp_tool` helper: calls real MCP tools to simulate sub-agent execution
- `cleanup_sample_repo` fixture: removes `.git/`, `.claude/`, `.intent_audit/` from sample repo

**Note**: This fixture installs the PRODUCT into the sample repo, simulating full deployment. E2E tests call real MCP tools (not mocks) for complete integration testing.

**Acceptance**: E2E fixtures properly create/destroy git repos and install all product artifacts.

---

### T010: Verify development environment

**Status**: [X] completed
**Dependencies**: T006-T009

Run verification commands:

- `uv sync`
- `uv run ruff check .`
- `uv run pytest --collect-only`

Fix any configuration issues.

**Acceptance**: All commands succeed with no errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**CRITICAL**: No user story work can begin until this phase is complete.

### T011: Implement Intention model

**Status**: [X] completed
**Dependencies**: T001
**Parallelizable**: yes (with T012-T015)

Create `src/intention_audit/models/intention.py`:

- `Intention` dataclass matching `data-model.md` spec
- Fields: `id`, `title`, `kind`, `status`, `children`, `created_at`, `rationale`, `constraints`, `superseded_by`, `evidence_tests`, `supporting_docs`, `code_home`, `named_scopes`
- `IntentionKind` enum: `goal`, `functionality`, `implementation`, `tests`, `docs`, `observability`
- `IntentionStatus` enum: `planned`, `in_progress`, `implemented`, `superseded`, `deprecated`

**Acceptance**: Model instantiable with type hints passing pyright.

---

### T012: Implement CommitPlan and CommitEntry models

**Status**: [X] completed
**Dependencies**: T001
**Parallelizable**: yes (with T011, T013-T015)

Create `src/intention_audit/models/commit_plan.py`:

- `CommitEntry` dataclass: `intent_id`, `intent_path`, `functionality_intent_id`, `functionality_intent_path`, `subject`, `body`, `intent_confidence`, `evidence_tests`, `supporting_docs`, `patch`
- `CommitPlan` dataclass: `version`, `ready`, `diff_base`, `diff_hash`, `commits`

**Acceptance**: Models instantiable with type hints passing pyright.

---

### T013: Implement SessionRecord model

**Status**: [X] completed
**Dependencies**: T001
**Parallelizable**: yes (with T011-T012, T014-T015)

Create `src/intention_audit/models/session_record.py`:

- `SessionRecord` dataclass: `session_id`, `timestamp`, `transcript_ref`, `diff_base`, `diff_hash`, `planner_tool`, `intentions_touched`, `mapping_summary`, `notes`
- `MappingSummary` dataclass for the nested object

**Acceptance**: Model instantiable with type hints passing pyright.

---

### T014: Implement YAML/JSON loaders for models

**Status**: [X] completed
**Dependencies**: T011-T013
**Parallelizable**: yes (with T015)

Create `src/intention_audit/models/loaders.py`:

- `load_intentions(path: Path) -> Intention` - loads and parses intentions.yaml
- `load_commit_plan(path: Path) -> CommitPlan` - loads and parses commit_plan.yaml
- `load_session_record(path: Path) -> SessionRecord` - loads session JSON
- Handle both YAML and JSON (YAML JSON-subset)

**Acceptance**: Loaders parse valid files, raise clear errors on invalid files.

---

### T015: Create basic_repo fixture content

**Status**: [X] completed
**Dependencies**: T003
**Parallelizable**: yes (with T011-T014)

Populate `tests/fixtures/sample_repos/basic_repo/`:

```text
basic_repo/
├── src/
│   └── feature_x/
│       ├── __init__.py
│       └── calculator.py    # simple add() function
├── tests/
│   └── feature_x/
│       ├── __init__.py
│       └── test_calculator.py  # test for add()
└── docs/
    └── feature_x.md          # basic doc
```

**Note**: No `.git` directory (created at test time). No `.claude/` directory (product artifacts installed at test time).

**Acceptance**: Fixture files exist with minimal working Python code.

---

### T016: Implement unit tests for Intention model

**Status**: [X] completed
**Dependencies**: T011

Create `tests/unit/test_intention_model.py`:

- Test instantiation with all fields
- Test kind/status enum values
- Test children nesting
- Test optional field defaults

**Acceptance**: `uv run pytest tests/unit/test_intention_model.py` passes.

---

### T017: Implement unit tests for CommitPlan model

**Status**: [X] completed
**Dependencies**: T012

Create `tests/unit/test_commit_plan_model.py`:

- Test CommitEntry instantiation
- Test CommitPlan with multiple commits
- Test version validation
- Test ready flag semantics

**Acceptance**: `uv run pytest tests/unit/test_commit_plan_model.py` passes.

---

### T018: Implement unit tests for loaders

**Status**: [X] completed
**Dependencies**: T014

Create `tests/unit/test_loaders.py`:

- Test loading valid intentions.yaml
- Test loading valid commit_plan.yaml
- Test loading valid session_record.json
- Test error handling for invalid files

**Acceptance**: `uv run pytest tests/unit/test_loaders.py` passes.

---

### T019: Implement schema validation utilities

**Status**: [X] completed
**Dependencies**: T014

Create `src/intention_audit/models/validation.py`:

- `validate_intentions(data: dict) -> list[str]` - returns validation errors
- `validate_commit_plan(data: dict) -> list[str]` - returns validation errors
- `validate_session_record(data: dict) -> list[str]` - returns validation errors
- Use JSON schemas from `specs/001-intent-audit-trail/contracts/`

**Acceptance**: Validators detect schema violations.

---

### T020: Implement unit tests for schema validation

**Status**: [X] completed
**Dependencies**: T019

Create `tests/unit/test_validation.py`:

- Test valid documents pass validation
- Test missing required fields detected
- Test invalid enum values detected
- Test type mismatches detected

**Acceptance**: `uv run pytest tests/unit/test_validation.py` passes.

---

## Phase 3: User Story 1 - Auto-commit Gate (P1)

> **User Story**: As a user, I want the agent to be unable to stop with uncommitted changes unless every edit is mapped to an intention leaf (and commit plan exists), so that every change is traceable by intention over time.
>
> **Independent Test**: Make an edit, try to stop; confirm the stop gate blocks until a complete plan exists, then commits are created with intention trailers.

### T021: Reorganize existing stop hook to new location

**Status**: [X] completed
**Dependencies**: T001

Move and reorganize `src/intent_audit_stop_hook.py` to `src/intention_audit/hooks/stop_hook.py`:

- Update imports for new package structure
- Ensure it remains functional after move
- This is PRODUCT code that gets copied to target repos

**Acceptance**: Stop hook works from new location.

---

### T022: Implement diff utilities module

**Status**: [X] completed
**Dependencies**: T001

Create `src/intention_audit/diff/parser.py`:

- `get_changed_paths(project_dir: Path) -> list[str]` - wrapper around git status
- `get_staged_paths(project_dir: Path) -> list[str]` - wrapper around git diff --cached
- `get_unified_diff(project_dir: Path, base: str = "HEAD") -> str` - get full diff

**Acceptance**: Diff utilities correctly parse git output.

---

### T023: Implement hunk parsing utilities

**Status**: [X] completed
**Dependencies**: T022

Create `src/intention_audit/diff/hunks.py`:

- `Hunk` dataclass: `file_path`, `old_start`, `old_count`, `new_start`, `new_count`, `content`
- `parse_unified_diff(diff_text: str) -> list[Hunk]` - parse unified diff into hunks
- `compute_diff_hash(hunks: list[Hunk]) -> str` - deterministic hash for diff

**Acceptance**: Hunk parser correctly identifies all hunks in a diff.

---

### T024: Implement patch utilities

**Status**: [X] completed
**Dependencies**: T023

Create `src/intention_audit/diff/patch.py`:

- `apply_patch(project_dir: Path, patch: str) -> bool` - apply a unified diff patch
- `validate_patch_coverage(hunks: list[Hunk], plan: CommitPlan) -> tuple[list[Hunk], list[Hunk]]` - returns (covered, uncovered) hunks

**Acceptance**: Patch application works correctly; coverage validation accurate.

---

### T025: Implement unit tests for diff utilities

**Status**: [X] completed
**Dependencies**: T022-T024

Create `tests/unit/test_diff.py`:

- Test changed path detection
- Test hunk parsing with various diff formats
- Test diff hash consistency
- Test patch coverage validation

**Acceptance**: `uv run pytest tests/unit/test_diff.py` passes.

---

### T026: Implement intention tree utilities

**Status**: [X] completed
**Dependencies**: T011, T014

Create `src/intention_audit/models/tree.py`:

- `find_intention(root: Intention, intent_id: str) -> Intention | None`
- `find_functionality_ancestor(root: Intention, intent_id: str) -> Intention | None`
- `get_intention_path(root: Intention, intent_id: str) -> str | None` - e.g., "Goal/Feature/Leaf"
- `validate_intent_id_exists(root: Intention, intent_id: str) -> bool`

**Acceptance**: Tree traversal utilities work correctly.

---

### T027: Implement unit tests for intention tree utilities

**Status**: [X] completed
**Dependencies**: T026

Create `tests/unit/test_intention_tree.py`:

- Test finding intentions by ID
- Test finding functionality ancestors
- Test path generation
- Test with deeply nested trees

**Acceptance**: `uv run pytest tests/unit/test_intention_tree.py` passes.

---

### T028: Implement commit message builder

**Status**: [X] completed
**Dependencies**: T012

Create `src/intention_audit/hooks/commit_builder.py`:

- `build_commit_message(entry: CommitEntry, intent_path: str | None = None) -> str`
- Include trailers: `Intent-Id`, `Intent-Path`, `Functionality-Intent-Id`, `Intent-Confidence`
- Format: subject, blank line, body (optional), blank line, trailers

**Acceptance**: Commit messages match expected format with proper trailers.

---

### T029: Implement unit tests for commit message builder

**Status**: [X] completed
**Dependencies**: T028

Create `tests/unit/test_commit_builder.py`:

- Test basic message with required trailers
- Test message with optional body
- Test message with all optional trailers
- Test proper newline handling

**Acceptance**: `uv run pytest tests/unit/test_commit_builder.py` passes.

---

### T030: Refactor stop hook for session-keyed artifacts

**Status**: [X] completed
**Dependencies**: T021-T024, T026, T028

Update `src/intention_audit/hooks/stop_hook.py` to implement the correct architecture:

**CRITICAL changes:**

1. **Read session_id from hook input JSON**:
   - Hook input includes `session_id` field
   - All artifact paths must be keyed: `.intent_audit/<session_id>/`

2. **Check for session-keyed artifacts**:
   - `.intent_audit/<session_id>/intentions.yaml`
   - `.intent_audit/<session_id>/commit_plan.yaml`
   - (Later: evidence_results.json, structure_validation.json)

3. **Block with sub-agent instructions**:
   - When artifact missing, exit code 2 with message:
   - `"Run 'intention-mapper' sub-agent with session_id=<id>, cwd=<path>"`
   - Message tells top-level agent WHICH sub-agent and WHAT inputs

4. **Hook does NOT call MCP tools**:
   - Hook only checks for artifacts and blocks/allows
   - Sub-agents (spawned by top-level agent) call MCP tools

5. **Import and use new modules**:
   - Diff utilities from `diff/`
   - Models from `models/`
   - Commit builder from `hooks/commit_builder.py`

**Acceptance**:
- Hook reads session_id from input
- Hook checks session-keyed artifact paths
- Hook blocks with correct sub-agent instructions
- Hook does NOT analyze or call MCP tools

---

### T031: Implement save_intentions MCP tool (persistence endpoint)

**Status**: [X] completed
**Dependencies**: T002, T011
**Parallelizable**: yes (with T032-T033)

Create `mcp_servers/intention_audit/tools/save_intentions.py`:

**CRITICAL**: This tool is a PERSISTENCE ENDPOINT, not an analyzer.

The tool MUST:
- Accept structured intention data from sub-agent: `{session_id, cwd, intentions: {...}}`
- Validate intentions against JSON schema
- Write to `.intent_audit/<session_id>/intentions.yaml`
- Return `{success: true, path: "..."}` or `{success: false, error: "..."}`

The tool MUST NOT:
- Analyze conversation/trajectory (sub-agent does this)
- Read transcripts (sub-agent does this)
- Make decisions about intention structure (sub-agent does this)

**Acceptance**: MCP tool validates and persists intention data passed to it.

---

### T032: Implement save_commit_plan MCP tool (persistence endpoint)

**Status**: [X] completed
**Dependencies**: T002, T012
**Parallelizable**: yes (with T031, T033)

Create `mcp_servers/intention_audit/tools/save_commit_plan.py`:

**CRITICAL**: This tool is a PERSISTENCE ENDPOINT, not an analyzer.

The tool MUST:
- Accept structured plan data from sub-agent: `{session_id, cwd, plan: {...}}`
- Validate plan against JSON schema
- Write to `.intent_audit/<session_id>/commit_plan.yaml`
- Return `{success: true, path: "..."}` or `{success: false, error: "..."}`

The tool MUST NOT:
- Map diff hunks to intentions (sub-agent does this)
- Analyze the diff (sub-agent does this)
- Decide which files go in which commit (sub-agent does this)

**Acceptance**: MCP tool validates and persists commit plan data passed to it.

---

### T033: Create intention-mapper sub-agent definition (PRODUCT)

**Status**: [X] completed
**Dependencies**: T004
**Parallelizable**: yes (with T031-T032, T034)

Create `src/intention_audit/agents/intention-mapper.yaml`:

**CRITICAL**: The sub-agent (LLM) does the analysis, then calls the MCP tool with structured data.

The sub-agent MUST:
- Read conversation history/trajectory
- ANALYZE: identify user intentions, hierarchy, evidence links, code_home boundaries
- Build a structured intention tree
- Call `mcp__intention_audit__save_intentions` with the analyzed data

Sub-agent definition includes:
- Tool access: `mcp__intention_audit__save_intentions`
- Inputs from hook: `session_id`, `cwd`
- Analysis prompt: how to identify intentions from conversation
- Output: structured data passed TO the MCP tool

**Note**: This is PRODUCT code - gets copied to target repos' `.claude/agents/` during deployment.

**Acceptance**: YAML definition clearly documents that sub-agent ANALYZES, then calls tool with data.

---

### T034: Create commit-planner sub-agent definition (PRODUCT)

**Status**: [X] completed
**Dependencies**: T004
**Parallelizable**: yes (with T031-T033)

Create `src/intention_audit/agents/commit-planner.yaml`:

**CRITICAL**: The sub-agent (LLM) does the analysis, then calls the MCP tool with structured data.

The sub-agent MUST:
- Read current diff (git diff HEAD)
- Read intentions.yaml
- ANALYZE: map each change to an intention, determine commit boundaries
- Build a structured commit plan
- Call `mcp__intention_audit__save_commit_plan` with the analyzed data

Sub-agent definition includes:
- Tool access: `mcp__intention_audit__save_commit_plan`, basic git/file tools
- Inputs from hook: `session_id`, `cwd`, `diff_base`
- Analysis prompt: how to map changes to intentions
- Output: structured data passed TO the MCP tool

**Note**: This is PRODUCT code - gets copied to target repos' `.claude/agents/` during deployment.

**Acceptance**: YAML definition clearly documents that sub-agent ANALYZES, then calls tool with data.

---

### T035: Implement E2E test for basic stop-gate blocking

**Status**: pending
**Dependencies**: T009, T015, T030-T032

Create `tests/e2e/test_stop_hook_basic.py`:

**E2E Test Approach**: We simulate the sub-agent by calling MCP tools directly with test data.
This is valid because we're testing the hook→artifact→hook flow, not the LLM analysis.

Test flow:
1. Set up sample repo with uncommitted changes
2. Run stop hook → verify it blocks with "run intention-mapper with session_id=X"
3. Call `save_intentions` MCP tool with test intention data (simulating sub-agent)
4. Run stop hook → verify it blocks with "run commit-planner"
5. Call `save_commit_plan` MCP tool with test plan data (simulating sub-agent)
6. Run stop hook → verify it passes and creates commits

Test cases:
- Test 1: Uncommitted change, no artifacts → hook blocks with sub-agent instructions
- Test 2: Valid session-keyed artifacts with full coverage → hook creates commits with trailers
- Test 3: Commit plan missing coverage → hook blocks with coverage error
- Test 4: No changes → hook allows stop immediately

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_stop_hook_basic.py` passes.

---

### T036: Implement E2E test for commit trailer verification

**Status**: pending
**Dependencies**: T035

Create `tests/e2e/test_commit_trailers.py`:

After successful stop-gate pass, verify commits have correct trailers:
- `Intent-Id` trailer present in every commit
- `Intent-Path` trailer present (if provided in plan)
- `Functionality-Intent-Id` trailer present (if provided in plan)
- Commits can be traced via `git log --format="%B"` + trailer extraction

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_commit_trailers.py` passes.

---

## Phase 4: User Story 2 - Evidence Regression (P1)

> **User Story**: As a user, when a linked evidence test fails at stop time, I want the tool to surface the intention-linked code/docs/tests so the agent can either restore support or explicitly supersede/retire the intention.
>
> **Independent Test**: Establish baseline intention + evidence test + doc; introduce a breaking change; confirm the stop gate blocks and reports intention context.

### T037: Implement evidence test runner

**Status**: pending
**Dependencies**: T001, T011

Create `src/intention_audit/evidence/runner.py`:

- `run_evidence_tests(project_dir: Path, test_selectors: list[str]) -> EvidenceResults`
- `EvidenceResults` dataclass: `passed`, `failed`, `errors`, `test_outputs`
- Execute via pytest subprocess with JSON output

**Acceptance**: Evidence runner correctly executes pytest and captures results.

---

### T038: Implement evidence results model

**Status**: pending
**Dependencies**: T001

Create `src/intention_audit/models/evidence_results.py`:

- `EvidenceResult` dataclass: `selector`, `passed`, `output`, `duration`
- `EvidenceResults` dataclass: `results`, `all_passed`, `summary`
- Serialization to/from JSON

**Acceptance**: Model handles all pytest result states.

---

### T039: Implement unit tests for evidence runner

**Status**: pending
**Dependencies**: T037, T038

Create `tests/unit/test_evidence_runner.py`:

- Test with passing tests
- Test with failing tests
- Test with missing test files
- Test with pytest errors

**Acceptance**: `uv run pytest tests/unit/test_evidence_runner.py` passes.

---

### T040: Implement intention failure context builder

**Status**: pending
**Dependencies**: T011, T026, T038

Create `src/intention_audit/reporting/failure_context.py`:

- `IntentionFailureContext` dataclass: `intention`, `failed_tests`, `linked_docs`, `code_scope`
- `build_failure_context(root: Intention, evidence_results: EvidenceResults) -> list[IntentionFailureContext]`
- Maps failed tests back to their evidenced intentions

**Acceptance**: Context correctly links failures to intentions.

---

### T041: Implement failure context renderer

**Status**: pending
**Dependencies**: T040

Create `src/intention_audit/reporting/renderer.py`:

- `render_failure_context(contexts: list[IntentionFailureContext]) -> str`
- Human-readable format showing:
  - Failing test selector(s)
  - Evidenced intention ID + title + path
  - Linked docs
  - Code scope (paths from code_home)

**Acceptance**: Rendered output matches spec format.

---

### T042: Implement unit tests for failure context

**Status**: pending
**Dependencies**: T040, T041

Create `tests/unit/test_failure_context.py`:

- Test context building with single failure
- Test context building with multiple failures
- Test rendering format
- Test with missing docs (graceful handling)

**Acceptance**: `uv run pytest tests/unit/test_failure_context.py` passes.

---

### T043: Create demo_repo fixture content

**Status**: pending
**Dependencies**: T003

Populate `tests/fixtures/sample_repos/demo_repo/`:

```text
demo_repo/
├── src/
│   └── calculator/
│       ├── __init__.py
│       └── operations.py   # add(), subtract() with intentional bug potential
├── tests/
│   └── calculator/
│       ├── __init__.py
│       └── test_operations.py  # evidence tests
├── docs/
│   └── calculator.md       # supporting docs with anchors
└── intentions.yaml         # pre-populated with evidence links
```

**Note**: No `.git` or `.claude/` directories (created/installed at test time).

**Acceptance**: Fixture ready for evidence regression testing.

---

### T044: Implement run_evidence_tests MCP tool

**Status**: pending
**Dependencies**: T002, T037
**Parallelizable**: yes (with T045)

Create `mcp_servers/intention_audit/tools/run_evidence_tests.py`:

**Note**: This tool is slightly different - it EXECUTES tests, but the sub-agent decides WHICH tests.

The tool MUST:
- Accept test selectors from sub-agent: `{session_id, cwd, test_selectors: [...]}`
- Run pytest on the specified selectors
- Capture test results (pass/fail/error, output)
- Write to `.intent_audit/<session_id>/evidence_results.json`
- Return `{success: true, all_passed: bool, results: [...]}` or `{success: false, error: "..."}`

The tool MUST NOT:
- Decide which tests to run (sub-agent does this based on intentions)
- Analyze test failures (sub-agent does this)
- Make decisions about repair vs supersede (top-level agent does this)

**Acceptance**: MCP tool runs specified tests and persists results.

---

### T045: Create evidence-checker sub-agent definition (PRODUCT)

**Status**: pending
**Dependencies**: T004
**Parallelizable**: yes (with T044)

Create `src/intention_audit/agents/evidence-checker.yaml`:

**CRITICAL**: The sub-agent (LLM) determines which tests to run, then calls the MCP tool.

The sub-agent MUST:
- Read intentions.yaml and commit_plan.yaml
- ANALYZE: identify evidence_tests linked to impacted intentions
- Determine which test selectors to run
- Call `mcp__intention_audit__run_evidence_tests` with test selectors

Sub-agent definition includes:
- Tool access: `mcp__intention_audit__run_evidence_tests`
- Inputs from hook: `session_id`, `cwd`
- Analysis prompt: how to identify impacted evidence tests
- Output: structured test selector list passed TO the MCP tool

**Note**: This is PRODUCT code - gets copied to target repos' `.claude/agents/` during deployment.

**Acceptance**: YAML definition clearly documents that sub-agent DETERMINES tests, tool RUNS them.

**Acceptance**: YAML definition valid and documented.

---

### T046: Add evidence checking to stop hook

**Status**: pending
**Dependencies**: T030, T037, T040, T041

Update `src/intention_audit/hooks/stop_hook.py`:

- Add evidence check step after commit plan validation
- If evidence_results.json missing → block with instructions to run evidence-checker
- If evidence tests failed → block with intention failure context report
- Configurable: evidence execution enabled/disabled via config

**Acceptance**: Stop hook blocks on evidence failures with proper context.

---

### T047: Implement E2E test for evidence passing scenario

**Status**: pending
**Dependencies**: T043, T044, T046

Create `tests/e2e/test_evidence_passing.py`:

- Setup: demo_repo with passing evidence tests
- Make change that doesn't break tests
- Run through full stop hook flow
- Verify commits created successfully

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_evidence_passing.py` passes.

---

### T048: Implement E2E test for evidence regression scenario

**Status**: pending
**Dependencies**: T043, T044, T046

Create `tests/e2e/test_evidence_regression.py`:

- Setup: demo_repo with passing evidence tests
- Make change that breaks evidence test
- Attempt stop → blocks with intention failure context
- Verify context includes: failing test, intention ID, linked docs, code scope

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_evidence_regression.py` passes.

---

### T049: Implement E2E test for evidence repair path

**Status**: pending
**Dependencies**: T048

Create `tests/e2e/test_evidence_repair.py`:

- Setup: demo_repo with broken evidence (from T048 scenario)
- Fix the code to restore evidence test
- Re-run evidence checker
- Attempt stop → commits created successfully

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_evidence_repair.py` passes.

---

### T050: Implement E2E test for evidence supersede path

**Status**: pending
**Dependencies**: T048

Create `tests/e2e/test_evidence_supersede.py`:

- Setup: demo_repo with broken evidence
- Mark old intention as superseded
- Update evidence links to new intention
- Attempt stop → commits created with new Intent-Id

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_evidence_supersede.py` passes.

---

## Phase 5: User Story 3 - Structure Alignment (P2)

> **User Story**: As a user, I want functionality intentions (domain semantics) to define module boundaries so that folder/file/named-scope meaning stays aligned with the intention hierarchy.
>
> **Independent Test**: Produce a commit plan whose patch touches files outside the owning functionality `code_home`; verify the stop hook blocks with a structural alignment message.

### T051: Implement code_home boundary checker

**Status**: pending
**Dependencies**: T011, T026

Create `src/intention_audit/structure/boundary.py`:

- `check_code_home_boundaries(root: Intention, plan: CommitPlan) -> list[BoundaryViolation]`
- `BoundaryViolation` dataclass: `commit_entry`, `functionality_intent`, `violating_paths`, `expected_prefix`
- Check each commit entry's patch paths against functionality's code_home

**Acceptance**: Boundary checker correctly identifies violations.

---

### T052: Implement structure validation results model

**Status**: pending
**Dependencies**: T001

Create `src/intention_audit/models/structure_validation.py`:

- `StructureViolation` dataclass: `type`, `intent_id`, `details`, `suggested_fix`
- `StructureValidation` dataclass: `violations`, `passed`, `timestamp`
- Serialization to/from JSON

**Acceptance**: Model handles all violation types.

---

### T053: Implement unit tests for boundary checker

**Status**: pending
**Dependencies**: T051, T052

Create `tests/unit/test_boundary_checker.py`:

- Test patch within code_home → no violation
- Test patch outside code_home → violation detected
- Test with multiple code_home prefixes
- Test with nested functionality intentions

**Acceptance**: `uv run pytest tests/unit/test_boundary_checker.py` passes.

---

### T054: Implement structure violation renderer

**Status**: pending
**Dependencies**: T052

Create `src/intention_audit/reporting/structure_renderer.py`:

- `render_structure_violations(validation: StructureValidation) -> str`
- Format showing:
  - Violating path(s)
  - Expected code_home boundary
  - Functionality intention context
  - Suggested fix options (move/rename/split/override)

**Acceptance**: Rendered output clearly explains violations.

---

### T055: Implement save_structure_validation MCP tool (persistence endpoint)

**Status**: pending
**Dependencies**: T002, T051
**Parallelizable**: yes (with T056)

Create `mcp_servers/intention_audit/tools/save_structure_validation.py`:

**CRITICAL**: This tool is a PERSISTENCE ENDPOINT, not an analyzer.

The tool MUST:
- Accept validation results from sub-agent: `{session_id, cwd, validation: {...}}`
- Validate against JSON schema
- Write to `.intent_audit/<session_id>/structure_validation.json`
- Return `{success: true, path: "..."}` or `{success: false, error: "..."}`

The tool MUST NOT:
- Check code_home boundaries (sub-agent does this)
- Analyze file paths (sub-agent does this)
- Suggest fixes (sub-agent does this)

**Acceptance**: MCP tool validates and persists structure validation results passed to it.

---

### T056: Create structure-validator sub-agent definition (PRODUCT)

**Status**: pending
**Dependencies**: T004
**Parallelizable**: yes (with T055)

Create `src/intention_audit/agents/structure-validator.yaml`:

**CRITICAL**: The sub-agent (LLM) does the analysis, then calls the MCP tool with structured data.

The sub-agent MUST:
- Read intentions.yaml and commit_plan.yaml
- ANALYZE: check each commit entry's paths against functionality's code_home
- Identify violations and suggested fixes
- Build a structured validation result
- Call `mcp__intention_audit__save_structure_validation` with the analyzed data

Sub-agent definition includes:
- Tool access: `mcp__intention_audit__save_structure_validation`, basic file tools
- Inputs from hook: `session_id`, `cwd`
- Analysis prompt: how to check code_home boundaries
- Output: structured validation data passed TO the MCP tool

**Note**: This is PRODUCT code - gets copied to target repos' `.claude/agents/` during deployment.

**Acceptance**: YAML definition clearly documents that sub-agent ANALYZES, then calls tool with data.

**Acceptance**: YAML definition valid and documented.

---

### T057: Add structure validation to stop hook

**Status**: pending
**Dependencies**: T030, T051, T054

Update `src/intention_audit/hooks/stop_hook.py`:

- Add structure validation step after evidence checking
- If structure_validation.json missing → block with instructions to run structure-validator
- If structure violations exist → block with violation report
- Support explicit override rationale in commit plan

**Acceptance**: Stop hook blocks on structure violations.

---

### T058: Create structure_violation fixture repo

**Status**: pending
**Dependencies**: T003

Create `tests/fixtures/sample_repos/structure_repo/`:

- Functionality intention with `code_home: ["src/payments/"]`
- Code in `src/payments/` and `src/other_domain/`
- Pre-populated intentions.yaml

**Note**: No `.git` or `.claude/` directories (created/installed at test time).

**Acceptance**: Fixture ready for structure alignment testing.

---

### T059: Implement E2E test for structure alignment pass

**Status**: pending
**Dependencies**: T055, T057, T058

Create `tests/e2e/test_structure_alignment_pass.py`:

- Patch only touches paths within code_home
- Stop hook allows commit

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_structure_alignment_pass.py` passes.

---

### T060: Implement E2E test for structure alignment block

**Status**: pending
**Dependencies**: T055, T057, T058

Create `tests/e2e/test_structure_alignment_block.py`:

- Patch touches paths outside code_home
- Stop hook blocks with structure violation message
- Verify suggested fixes mentioned

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_structure_alignment_block.py` passes.

---

### T061: Implement E2E test for structure override rationale

**Status**: pending
**Dependencies**: T060

Create `tests/e2e/test_structure_override.py`:

- Patch touches paths outside code_home
- Commit plan includes explicit override rationale
- Stop hook allows commit

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_structure_override.py` passes.

---

## Phase 6: Polish & Cross-Cutting

### T062: Implement session recorder

**Status**: pending
**Dependencies**: T013

Create `src/intention_audit/session/recorder.py`:

- `record_session(session_id: str, transcript_ref: str, diff_info: DiffInfo, intentions_touched: list[str]) -> SessionRecord`
- Write to `.intent_audit/sessions/<session_id>.json`
- Include mapping summary

**Acceptance**: Session records created with all required fields.

---

### T063: Implement save_session_record MCP tool (persistence endpoint)

**Status**: pending
**Dependencies**: T002, T062

Create `mcp_servers/intention_audit/tools/save_session_record.py`:

**CRITICAL**: This tool is a PERSISTENCE ENDPOINT, not an analyzer.

The tool MUST:
- Accept session record from sub-agent: `{session_id, cwd, record: {...}}`
- Validate against JSON schema
- Write to `.intent_audit/<session_id>/session_record.json`
- Return `{success: true, path: "..."}` or `{success: false, error: "..."}`

The tool MUST NOT:
- Analyze the session (sub-agent does this)
- Compute transcript hashes (sub-agent does this)
- Summarize mapping (sub-agent does this)

**Acceptance**: MCP tool validates and persists session record data passed to it.

---

### T064: Create session-recorder sub-agent definition (PRODUCT)

**Status**: pending
**Dependencies**: T004

Create `src/intention_audit/agents/session-recorder.yaml`:

**CRITICAL**: The sub-agent (LLM) summarizes the session, then calls the MCP tool with structured data.

The sub-agent MUST:
- Read session context (transcript_ref, intentions touched, mapping summary)
- ANALYZE: summarize the session, compute hashes/references
- Build a structured session record
- Call `mcp__intention_audit__save_session_record` with the analyzed data

Sub-agent definition includes:
- Tool access: `mcp__intention_audit__save_session_record`
- Inputs from hook: `session_id`, `cwd`, `transcript_ref`
- Analysis prompt: how to summarize session for audit
- Output: structured session record passed TO the MCP tool

**Note**: This is PRODUCT code - gets copied to target repos' `.claude/agents/` during deployment.

**Acceptance**: YAML definition clearly documents that sub-agent SUMMARIZES, then calls tool with data.

---

### T065: Add session recording to stop hook

**Status**: pending
**Dependencies**: T030, T062

Update `src/intention_audit/hooks/stop_hook.py`:

- After successful commit execution, record session
- Commit session record file as part of final cleanup

**Acceptance**: Session records committed after successful stop.

---

### T066: Implement docs linkage validation

**Status**: pending
**Dependencies**: T011, T012

Create `src/intention_audit/docs/validator.py`:

- `validate_docs_links(root: Intention, plan: CommitPlan) -> list[DocsViolation]`
- Check behavior-affecting intentions have docs links or rationale
- `DocsViolation` dataclass with intent_id, missing_docs_info

**Acceptance**: Docs validator identifies missing links.

---

### T067: Add docs validation to stop hook (optional gate)

**Status**: pending
**Dependencies**: T057, T066

Update `src/intention_audit/hooks/stop_hook.py`:

- Add optional docs validation step
- Configurable: warn-only vs block
- Default: warn-only for MVP

**Acceptance**: Stop hook warns on missing docs links.

---

### T068: Implement full demo scenario E2E test

**Status**: pending
**Dependencies**: T035, T047, T059

Create `tests/e2e/test_demo_scenario.py`:

- Full flow from quickstart.md:
  1. Baseline intention + evidence + docs
  2. Stop gate commits baseline
  3. Regression breaks evidence
  4. Stop gate blocks with context
  5. Repair and commit

**Acceptance**: `uv run pytest -m e2e tests/e2e/test_demo_scenario.py` passes.

---

### T069: Add type hints and docstrings audit

**Status**: pending
**Dependencies**: T067

Audit all source files:

- Verify all public functions have type hints
- Verify all public functions have docstrings (PEP 257)
- Run pyright in strict mode

**Acceptance**: `uv run pyright --verifytypes intention_audit` passes.

---

### T070: Update CLAUDE.md with new structure

**Status**: pending
**Dependencies**: T069

Update project CLAUDE.md:

- Document new directory structure
- Document product vs tooling distinction
- Document sub-agent deployment pattern
- Document testing commands

**Acceptance**: CLAUDE.md reflects current project state.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
     ↓
Phase 2 (Foundational) ← BLOCKS all user stories
     ↓
┌────┴────┬────────────┐
↓         ↓            ↓
Phase 3   Phase 4      Phase 5
(US1)     (US2)        (US3)
└────┬────┴────────────┘
     ↓
Phase 6 (Polish)
```

### Critical Path

1. **Setup (Phase 1)**: No dependencies - can start immediately
2. **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
3. **User Stories (Phases 3-5)**: Can run in parallel after Foundational
4. **Polish (Phase 6)**: Depends on all user stories complete

### Parallel Opportunities Summary

| Phase   | Parallelizable Tasks |
| ------- | -------------------- |
| Phase 1 | T001-T006 (6 tasks)  |
| Phase 2 | T011-T015 (5 tasks)  |
| Phase 3 | T031-T034 (4 tasks)  |
| Phase 4 | T044-T045 (2 tasks)  |
| Phase 5 | T055-T056 (2 tasks)  |

---

## Success Criteria Mapping

| Criterion | Description                             | Validated By |
| --------- | --------------------------------------- | ------------ |
| SC-001    | 100% hunk coverage required             | T035, T036   |
| SC-002    | Intent-Id trailers in commits           | T036         |
| SC-003    | Evidence failure surfaces context       | T048         |
| SC-004    | Structure alignment blocks cross-domain | T060         |

---

## Edge Cases (Deferred Post-MVP)

The following edge cases from spec.md are noted but deferred:

- **Multi-intent hunk**: Requires hunk-level splitting (not file-level)
- **Deleted evidence test**: Test still referenced but file deleted
- **Missing docs**: Warn-only for MVP, block optional
- **Non-Git repo**: Basic error message implemented

---

## Implementation Notes

### Product vs Tooling Summary

| Category | Location | Deployed To |
| -------- | -------- | ----------- |
| Stop hook (PRODUCT) | `src/intention_audit/hooks/stop_hook.py` | Target repos `.claude/hooks/` |
| Sub-agents (PRODUCT) | `src/intention_audit/agents/*.yaml` | Target repos `.claude/agents/` |
| MCP tools (PRODUCT) | `mcp_servers/intention_audit/tools/` | MCP server for target repos |
| Models (PRODUCT) | `src/intention_audit/models/` | Used by hooks/agents |
| Project-local hooks (TOOLING) | `.claude/hooks/` | N/A - for THIS repo only |
| Runtime state | N/A in this repo | Target repos `.intent_audit/` |

### E2E Test Product Installation

Before each E2E test, the `install_product_artifacts` fixture:

1. Copies `src/intention_audit/hooks/stop_hook.py` → sample repo `.claude/hooks/`
2. Copies `src/intention_audit/agents/*.yaml` → sample repo `.claude/agents/`
3. Creates `.intent_audit/` directory structure in sample repo
4. Rebuilds/syncs MCP server for the test run

This simulates a full product deployment to the target repo.

### MCP Tools in E2E Tests

E2E tests use the **real MCP tools** (`mcp_servers/intention_audit/tools/`) for full integration testing. The test harness calls MCP tools directly to simulate what sub-agents would do:

1. Stop hook blocks with "run intention-mapper agent"
2. Test harness calls real `map_intentions` MCP tool
3. Stop hook sees output, proceeds to next check
4. Repeat for each tool in the sequence

This ensures E2E tests exercise the complete, real system.

### Test Strategy

1. **Unit tests**: Test models, utilities in isolation
2. **Integration tests**: Test individual MCP tools against real file system
3. **E2E tests**: Install PRODUCT artifacts into sample repos, call real MCP tools, run stop hook, verify full system behavior

### Existing Stop Hook

`src/intent_audit_stop_hook.py` will be reorganized to `src/intention_audit/hooks/stop_hook.py` and enhanced (not rewritten from scratch).

### Sample Repo Fixtures

- No `.git` directory (created at test time)
- No `.claude/` directory (PRODUCT artifacts installed at test time)
- No `.intent_audit/` directory (created at test time)
- Contains only application code, tests, docs, and pre-populated intentions.yaml
