# Implementation Notes

This file contains detailed implementation notes from batch execution agents.

---

## T042: Unit Tests for Failure Context (2026-02-01)

### Summary

Created comprehensive unit tests for `build_failure_context()` in `src/intention_audit/reporting/failure_context.py`.

### Files Created

- `/Users/chuck/workspace/code-intention-consistency/tests/unit/test_failure_context.py`

### Test Results

**17 tests passed, 0 failed**

### Test Coverage

| Test Class | Test Cases |
|------------|------------|
| `TestBuildFailureContextSingleFailure` | 2 tests - single failure linking and path computation |
| `TestBuildFailureContextMultipleFailures` | 2 tests - aggregation and deduplication |
| `TestBuildFailureContextCrossIntentions` | 1 test - failures across different intentions |
| `TestBuildFailureContextRendering` | 2 tests - dataclass fields and direct instantiation |
| `TestBuildFailureContextMissingDocs` | 2 tests - empty and default supporting_docs handling |
| `TestBuildFailureContextNoFailures` | 2 tests - all-pass and empty results scenarios |
| `TestBuildFailureContextEdgeCases` | 6 tests - unlinked tests, errors, mixed results, copy semantics |

### Key Test Fixtures

1. `sample_tree_with_evidence` - Tree with Goal/Functionality/Implementation hierarchy including evidence_tests and supporting_docs
2. `multi_functionality_tree` - Tree with two separate functionality branches for cross-intention testing

### Implementation Notes

- Tests verify that `build_failure_context()` correctly maps failed test selectors back to their evidenced intentions
- Tests confirm that linked_docs and code_scope are copies (not references) to avoid mutation issues
- Tests cover both assertion failures and error results (tests with error_message set)
- Tests validate graceful handling when no intentions reference a failed test selector

---

## T053: Implement Unit Tests for Boundary Checker (2026-02-01)

### Summary
Created comprehensive unit tests for the `code_home` boundary checker in `src/intention_audit/structure/boundary.py`.

### File Created
- `/Users/chuck/workspace/code-intention-consistency/tests/unit/test_boundary_checker.py`

### Test Coverage
32 tests covering 5 test classes:

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestBoundaryViolation` | 2 | Dataclass instantiation and defaults |
| `TestPathWithinPrefixes` | 6 | Path prefix matching logic |
| `TestFindIntentionById` | 4 | Tree traversal for ID lookup |
| `TestFindFunctionalityAncestor` | 5 | Ancestor search for functionality nodes |
| `TestCheckCodeHomeBoundaries` | 15 | Main boundary checking function |

### Test Cases Implemented
1. **Patch within code_home - no violation**: Files match prefix correctly
2. **Patch outside code_home - violation detected**: Files outside boundary trigger violation
3. **Multiple code_home prefixes**: Array of prefixes all validated correctly
4. **Nested functionality intentions**: Deep tree traversal (4+ levels) working
5. **No code_home defined**: Graceful skip (no violations reported)
6. **Missing functionality ancestor**: Graceful handling (no violations reported)

### Additional Edge Cases Tested
- Partial directory name matches rejected (e.g., `src/featureX` does not match `src/feature`)
- Empty commit plans handled
- Empty file lists handled
- Intent IDs not found in tree handled gracefully
- Multiple violations in single commit aggregated correctly
- Explicit `functionality_intent_id` in CommitEntry used when present

### Code Coverage
The boundary checker module achieved 99% coverage (1 line missed due to a redundant kind check).

---

## T039: Unit Tests for Evidence Runner (2026-02-01)

### Summary

Created comprehensive unit tests for the evidence runner module (`src/intention_audit/evidence/runner.py`).

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/unit/test_evidence_runner.py`

### Test Coverage

The test file contains 19 tests organized into 7 test classes:

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestEvidenceResults` | 3 | Dataclass defaults and summary property |
| `TestTestOutput` | 2 | Passed and failed test output creation |
| `TestRunEvidenceTestsEmptySelectors` | 2 | Empty selector handling |
| `TestRunEvidenceTestsPassingTests` | 2 | Single and multiple passing tests |
| `TestRunEvidenceTestsFailingTests` | 2 | Failing tests and mixed pass/fail |
| `TestRunEvidenceTestsMissingFiles` | 2 | Missing test files and functions |
| `TestRunEvidenceTestsPytestErrors` | 3 | Syntax errors, import errors, fixture errors |
| `TestRunEvidenceTestsRealWorldScenarios` | 3 | Full file selectors, raw output, selector preservation |

### Test Cases Implemented

1. **Empty selectors**: Returns empty results with `all_passed=True`
2. **Passing tests**: Correctly identifies and categorizes passing tests
3. **Failing tests**: Captures failures in `results.failed` with `all_passed=False`
4. **Mixed results**: Handles mix of passing and failing tests correctly
5. **Missing test files**: Gracefully handles nonexistent files (errors captured)
6. **Missing test functions**: Handles missing function references
7. **Syntax errors**: Pytest collection errors handled gracefully
8. **Import errors**: Module import failures captured as errors
9. **Missing fixtures**: Fixture lookup failures handled
10. **Full file selectors**: Works with file-level selectors (not just function-level)
11. **Raw output preservation**: Full pytest output captured in `raw_output`
12. **Selector preservation**: Test selectors preserved in result objects

### Test Approach

All tests use `tmp_path` fixtures with dynamically created test files to ensure isolation. The sample_repos fixtures were avoided because their relative imports don't work when running evidence tests from a different working directory context.

### Results

All 19 tests pass. Evidence runner module achieves 87% coverage (lines 91-113 are timeout and generic exception handlers that are difficult to trigger in unit tests without mocking subprocess).

---

## T074: Main Agent Context Compilation (2026-02-01)

### Summary

Updated stop hook blocking messages to clearly instruct the main agent on context compilation requirements before spawning sub-agents.

### Changes Made

**File:** `src/intention_audit/hooks/stop_hook.py`

#### Missing Intentions Artifact Message (lines 343-377)

Enhanced the blocking message to include structured context compilation instructions:

1. **USER INTENTIONS** section - Instructs main agent to compile:
   - Primary goal(s) stated by user
   - Secondary requests or constraints mentioned
   - Clarifications or refinements from the session

2. **IMPLEMENTATION CONTEXT** section - Instructs main agent to compile:
   - Design decisions not explicitly requested by user
   - Discoveries during implementation (e.g., refactoring needs)
   - Augmentations added (tests, docs, error handling)

3. **SESSION METADATA** section - Provides:
   - session_id
   - diff_hash
   - cwd (project directory)

#### Missing Commit Plan Artifact Message (lines 380-408)

Streamlined this message since intentions artifact already exists at this point:
- Clearer "ACTION REQUIRED" heading
- Consolidated session metadata section
- Clear "NEXT STEP" instruction

### Rationale

The original messages provided technical parameters but lacked guidance on what conversational context the main agent should compile. The enhanced messages:

1. Make explicit what the main agent must do before spawning sub-agents
2. Distinguish between user-stated intentions vs agent-derived implementation decisions
3. Provide consistent formatting with clear section headers

### Testing Notes

These are blocking message format changes only - no behavioral changes to the hook logic. The existing E2E tests validate that blocking messages are returned correctly. Manual verification recommended to ensure the new format is clear to agents in practice.

---

## T071-T073: E2E Output Infrastructure Review (2026-02-01)

### Summary
All three tasks (T071, T072, T073) were reviewed and found to be **already complete**. The E2E output infrastructure is fully implemented and functional.

### T071: Restructure E2E Output Directory
**Status: COMPLETE - No changes needed**

The file `tests/e2e/output_capture.py` contains all required functions:

1. `create_output_dir(test_name: str, base_dir: Path | None = None) -> Path`
   - Creates timestamped output directories at `tests/e2e/outputs/<test-name>/<iso-datetime>/`
   - Uses UTC timestamps in ISO format

2. `save_component(output_dir: Path, name: str, content: str) -> Path`
   - Writes content to named files in the output directory
   - Returns path to saved file

3. `copy_artifacts(output_dir: Path, artifact_dir: Path) -> list[Path]`
   - Copies all files from artifact directory to `<output_dir>/artifacts/`
   - Preserves relative directory structure
   - Returns list of copied file paths

### T072: Remove Transcript Truncation
**Status: COMPLETE - No truncation exists**

The plan referenced truncation at lines 232, 239, 250, etc., but these line numbers appear to be from an earlier implementation or a different version of the file. The current `tests/e2e/transcript_compiler.py` (404 lines) contains **no truncation logic**:

- `_format_user_entry()`: Preserves full tool result content (lines 236-240) and full prompt content (lines 243-248)
- `_format_assistant_entry()`: Preserves full text blocks, full tool inputs as JSON
- Agent summaries are preserved with full content (lines 229-234)

No modifications were required.

### T073: Capture Component-Level Outputs
**Status: COMPLETE - All component capture implemented**

The `tests/e2e/conftest.py` already has comprehensive component capture via the `run_claude_session()` function (lines 547-687):

| Component | File | Captured via |
|-----------|------|--------------|
| Main transcript | `main-transcript.jsonl` | `_copy_transcript_files()` |
| Sub-agent transcripts | `subagent-<id>.jsonl` | `_copy_transcript_files()` |
| Hook output | `hook-output.txt` | `_extract_hook_output()` |
| MCP tool calls | `mcp-calls.json` | `_extract_mcp_calls()` |
| Generated artifacts | `artifacts/*.yaml` | `copy_artifacts()` |
| Git history | `git-log.txt` | `_capture_git_state()` |
| Repo state | `git-status.txt` | `_capture_git_state()` |

The `claude_session_runner` fixture (lines 690-736) provides a clean interface for tests:
```python
def test_example(basic_repo, claude_session_runner):
    exit_code, stdout, stderr = claude_session_runner(
        basic_repo,
        "Create a file and stop",
    )
    # Outputs automatically captured to tests/e2e/outputs/<test_name>/<timestamp>/
```

### Files Reviewed
- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/output_capture.py`
- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/transcript_compiler.py`
- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/conftest.py`
- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/fixtures.py`

### Test Infrastructure Status
- E2E tests are marked with `@pytest.mark.e2e` and excluded by default (via `pyproject.toml`)
- Run with `uv run pytest -m e2e` to execute E2E tests
- 9 E2E tests exist across `TestStopHookBasic`, `TestStopHookMultipleCommits`, and `TestStopHookBasicClaude`

---

## Batch 3: Stop Hook Integration (2026-02-01)

### Summary

Integrated all validation phases into the stop hook: evidence checking (T046), structure validation (T057), session recording (T065), and docs validation (T067). Also ensured T076 (blocking messages) was already complete from T074.

### Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T076 | Update blocking messages | Already done by T074 |
| T046 | Add evidence checking phase | Implemented |
| T057 | Add structure validation phase | Implemented |
| T065 | Add session recording phase | Implemented |
| T067 | Add docs validation (optional gate) | Implemented |

### File Modified

- `src/intention_audit/hooks/stop_hook.py`

### Changes Made

#### Version Bump
- Updated `HOOK_VERSION` from `"0.4.0"` to `"0.5.0"`

#### New Constants
Added artifact file names and sub-agent names:
- `EVIDENCE_RESULTS_FILE_NAME = "evidence_results.json"`
- `STRUCTURE_VALIDATION_FILE_NAME = "structure_validation.json"`
- `SESSION_RECORD_FILE_NAME = "session_record.json"`
- `EVIDENCE_CHECKER_AGENT = "evidence-checker"`
- `STRUCTURE_VALIDATOR_AGENT = "structure-validator"`
- `SESSION_RECORDER_AGENT = "session-recorder"`

#### New Helper Functions

1. `_load_evidence_results(path)` - Load evidence results from JSON
2. `_load_structure_validation(path)` - Load structure validation from JSON
3. `_load_intentions(path)` - Load intentions from YAML via loaders module
4. `_render_evidence_failures(root, evidence_results)` - Render failure context report
5. `_render_structure_violations(validation)` - Render structure violation report
6. `_load_config(project_dir)` - Load hook configuration from `.intent_audit/config.json`

#### New Validation Phases in main()

**Configuration Loading:**
```python
config = _load_config(project_dir)
evidence_enabled = config.get("evidence_checking", True)
structure_enabled = config.get("structure_validation", True)
docs_validation_mode = config.get("docs_validation", "warn")
```

**Phase: Evidence Checking (T046)**
- Checks for `evidence_results.json` artifact
- If missing, blocks with instructions to run `evidence-checker` sub-agent
- If tests failed, renders failure context with intention linkage
- Configurable via `evidence_checking: true/false` in config

**Phase: Structure Validation (T057)**
- Checks for `structure_validation.json` artifact
- If missing, blocks with instructions to run `structure-validator` sub-agent
- If violations exist and no override, renders violation report
- Supports `structure_override_rationale` in commit_plan.yaml
- Configurable via `structure_validation: true/false` in config

**Phase: Session Recording (T065)**
- Checks for `session_record.json` artifact
- If missing, blocks with instructions to run `session-recorder` sub-agent
- Required before commits can proceed

**Phase: Docs Validation (T067)**
- Optional gate, warn-only by default
- Uses `docs_validation` config: `"warn"`, `"block"`, or `"disabled"`
- Loads intention tree and commit plan
- Validates behavior-affecting intentions have docs or rationale
- In warn mode: prints warning but allows proceed
- In block mode: blocks if violations exist

### Hook Workflow After Changes

```
1. Git repo check
2. Staged changes check
3. Relevant changes check → exit 0 if none
4. Compute diff_hash
5. Check intentions.yaml → block if missing
6. Check commit_plan.yaml → block if missing
7. Validate plan structure
8. Validate plan coverage
9. [NEW] Check evidence_results.json → block if missing or failed
10. [NEW] Check structure_validation.json → block if missing or violations
11. [NEW] Check session_record.json → block if missing
12. [NEW] Docs validation (warn-only by default)
13. Execute commits
14. Verify no remaining changes
15. Exit 0
```

### Configuration Options

The hook now reads `.intent_audit/config.json` for optional settings:

```json
{
  "evidence_checking": true,
  "structure_validation": true,
  "docs_validation": "warn"
}
```

### Testing

All 192 unit tests pass. The stop hook now supports the full validation pipeline.

---

## T048: E2E Test for Evidence Regression Scenario (2026-02-01)

### Summary

Created E2E test file to validate the evidence regression blocking workflow. This tests the critical scenario where a code change breaks existing tests and the stop hook correctly blocks the commit.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_evidence_regression.py`

### Test Class

`TestEvidenceRegressionScenario` - 3 tests covering evidence checking flow

### Test Cases

| Test | Purpose |
|------|---------|
| `test_evidence_failure_blocks_commits` | Main regression scenario - code change breaks tests, stop hook blocks |
| `test_evidence_success_allows_commits` | Counterpoint - harmless changes pass evidence tests, stop allows |
| `test_partial_evidence_failure_blocks_commits` | Mixed results (some pass, some fail) still blocks |

### Test Flow (Main Scenario)

1. **Make Breaking Change**: Modify `add()` in demo_repo to return wrong value (`a - b` instead of `a + b`)
2. **Create Artifacts**: Save intentions.yaml and commit_plan.yaml via MCP tools
3. **Run Evidence Tests**: Execute `run_evidence_tests` with add test selectors
4. **Verify Tests Fail**: Confirm `all_passed=False` in evidence results
5. **Create Supporting Artifacts**: Structure validation (passing) and session record
6. **Run Stop Hook**: Execute stop_hook.py as subprocess
7. **Verify Block**: Confirm exit code 2 and error message contains:
   - "evidence tests failed"
   - "action required"
   - "fix" options
   - Reference to failed test selectors

### Helper Functions

Two private helper functions created for test artifact setup:

```python
def _create_session_record_artifact(artifact_dir, session_id, diff_hash):
    """Create minimal session_record.json for test purposes."""

def _create_structure_validation_artifact(artifact_dir):
    """Create passing structure_validation.json for test purposes."""
```

### Dependencies Used

- `mcp_servers.intention_audit.tools.run_evidence_tests` - Run pytest selectors
- `mcp_servers.intention_audit.tools.save_intentions` - Save intentions artifact
- `mcp_servers.intention_audit.tools.save_commit_plan` - Save commit plan artifact
- `tests.e2e.conftest.compute_diff_hash` - Compute diff hash for artifact keying
- `tests.e2e.conftest.run_stop_hook` - Execute stop hook as subprocess
- `tests.e2e.fixtures` - Test data factories (intention_tree, minimal_commit_plan, etc.)

### Sample Repo Used

Uses `demo_repo` fixture which provides:
- Source file: `src/calculator/operations.py` with `add()` and `subtract()` functions
- Test file: `tests/calculator/test_operations.py` with evidence tests
- Existing `intentions.yaml` documenting the calculator functionality intention

### Pytest Mark

All tests decorated with `@pytest.mark.e2e` to allow selective execution:
```bash
uv run pytest -m e2e tests/e2e/test_evidence_regression.py
```

### Verification

File compiles successfully:
```bash
python -m py_compile tests/e2e/test_evidence_regression.py
```

---

## T060: E2E Test for Structure Alignment Block Scenario (2026-02-01)

### Summary

Created E2E test file to validate the structure alignment blocking workflow. This tests the scenario where code changes violate declared `code_home` boundaries and the stop hook correctly blocks the commit with a violation report.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_structure_alignment_block.py`

### Test Class

`TestStructureAlignmentBlock` - 3 tests covering structure validation blocking flow

### Test Cases

| Test | Purpose |
|------|---------|
| `test_changes_outside_code_home_blocked` | Main boundary violation scenario - file in wrong domain triggers block |
| `test_structure_override_allows_proceed` | Override mechanism - explicit rationale bypasses structure check |
| `test_missing_structure_validation_blocks` | Missing artifact scenario - instructs to run structure-validator |

### Test Flow (Main Scenario)

1. **Create Boundary-Violating Change**: Add payment logic file to `src/other_domain/` (outside `src/payments/` code_home)
2. **Create Intentions Artifact**: Define functionality with `code_home: ["src/payments/"]`
3. **Create Commit Plan**: Map the violating file to the payments intention
4. **Run Evidence Tests**: Execute passing tests (evidence is independent of structure)
5. **Create Structure Validation**: Save artifact with `passed=false` and boundary violation
6. **Create Session Record**: Required by hook before commit execution
7. **Run Stop Hook**: Execute stop_hook.py as subprocess
8. **Verify Block**: Confirm exit code 2 and error message contains:
   - "structure validation failed"
   - Violation type ("code_home_boundary" or "boundary")
   - Violating path reference
   - Suggested fixes

### Helper Functions

Four private helper functions created for test artifact setup:

```python
def intention_with_code_home(intent_id, title, code_home, children):
    """Create a functionality intention with code_home defined."""

def goal_intention_tree(root_id, root_title, children):
    """Create a goal intention tree with optional children."""

def structure_violation(violation_type, intent_id, violating_paths, expected_prefixes, ...):
    """Create a structure violation entry."""

def minimal_session_record(session_id, diff_hash):
    """Create a minimal valid session record."""
```

### MCP Tools Used

- `save_intentions` - Persist intentions with code_home definitions
- `save_commit_plan` - Persist commit plan with file mappings
- `run_evidence_tests` - Run evidence tests (passing, independent of structure)
- `save_structure_validation` - Persist structure validation with violations
- `save_session_record` - Persist session record (required by hook)

### Sample Repo Used

Uses `structure_repo` fixture which provides:
- `src/payments/` - Payment domain with code_home boundary
- `src/other_domain/` - Separate domain for boundary violation testing
- `tests/payments/` - Evidence tests for payment functionality
- `intentions.yaml` - Pre-existing intentions with code_home definitions

### Pytest Mark

All tests decorated with `@pytest.mark.e2e` to allow selective execution:
```bash
uv run pytest -m e2e tests/e2e/test_structure_alignment_block.py
```

### Key Assertions

1. **Exit Code 2**: Hook blocks with non-zero exit
2. **Structure Validation Failed**: Message indicates structure check failed
3. **Violation Details**: Includes boundary type, violating paths, expected prefixes
4. **Suggested Fixes**: Message includes actionable fix suggestions
5. **Override Mechanism**: Override rationale in commit_plan bypasses block

### Verification

File compiles successfully:
```bash
python -m py_compile tests/e2e/test_structure_alignment_block.py
```

Ruff linting passes after auto-fix of import sorting.

---

## T059: E2E Test for Structure Alignment Pass Scenario (2026-02-01)

### Summary

Created E2E test file for the structure alignment pass scenario, verifying that file changes WITHIN declared `code_home` boundaries pass validation and commits are created successfully.

### Files Created/Modified

- **Created:** `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_structure_alignment_pass.py`
- **Modified:** `/Users/chuck/workspace/code-intention-consistency/tests/e2e/conftest.py` (added `structure_repo` fixture)

### Fixture Added to conftest.py

Added `structure_repo` fixture that:
- Creates temporary copy of `tests/fixtures/sample_repos/structure_repo/`
- Excludes `__pycache__` and `*.pyc` files during copy
- Initializes git repository with initial commit
- Repository contains `intentions.yaml` with `code_home: ["src/payments/"]` boundary

### Test Class: `TestStructureAlignmentPass`

| Test Method | Description |
|-------------|-------------|
| `test_changes_within_code_home_allowed` | Full flow: modify `src/payments/processor.py`, create all artifacts with `passed=true`, verify commit created with Intent-Id trailer |
| `test_new_file_within_code_home_allowed` | Add new file `src/payments/currency.py`, verify commit created |
| `test_multiple_files_within_code_home_allowed` | Modify multiple files within code_home, verify single commit with all files |

### Helper Functions Created

1. `_create_intentions_for_payments()` - Creates intentions artifact with code_home boundary for src/payments/
2. `_create_commit_plan_for_payments()` - Creates commit plan for payment files with functionality_intent_id
3. `_create_structure_validation_passed()` - Creates structure validation with `passed=true` and empty violations
4. `_create_session_record()` - Creates session record for audit trail with all required fields
5. `_create_config_with_disabled_evidence()` - Disables evidence checking to focus on structure validation

### MCP Tools Used

- `save_intentions` from `mcp_servers/intention_audit/tools/save_intentions.py`
- `save_commit_plan` from `mcp_servers/intention_audit/tools/save_commit_plan.py`
- `save_structure_validation` from `mcp_servers/intention_audit/tools/save_structure_validation.py`
- `save_session_record` from `mcp_servers/intention_audit/tools/save_session_record.py`

### Test Configuration

Tests use `.intent_audit/config.json` with:
```json
{
  "evidence_checking": false,
  "structure_validation": true,
  "docs_validation": "disabled"
}
```

This allows tests to focus on structure validation without requiring evidence tests to pass.

### Test Structure

Each test follows the pattern:
1. Disable evidence checking via config
2. Make file changes WITHIN `src/payments/` (the declared code_home)
3. Create all required artifacts:
   - `intentions.yaml` with `code_home: ["src/payments/"]`
   - `commit_plan.yaml` covering changed files
   - `structure_validation.json` with `passed: true`
   - `session_record.json` for audit trail
4. Run stop hook via `run_stop_hook()` helper
5. Verify exit code 0 (success)
6. Verify commit created with Intent-Id trailer

### Key Implementation Notes

- All file changes are WITHIN the declared `code_home` boundaries (src/payments/)
- Structure validation artifact has `passed: true` (no violations)
- Tests use the `@pytest.mark.e2e` marker
- Tests follow existing patterns from `test_stop_hook_basic.py`
- Uses `datetime.UTC` alias per ruff UP017 recommendation

### Verification

File compiles successfully:
```bash
python -m py_compile tests/e2e/test_structure_alignment_pass.py
```

Ruff linting passes after auto-fix of import sorting.

---

## T049: E2E Test for Evidence Repair Path Scenario (2026-02-01)

### Summary

Created E2E test file for the evidence repair scenario, validating the full workflow where a developer breaks tests, is blocked by the stop hook, fixes the code, creates new artifacts for the new diff_hash, and successfully commits.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_evidence_repair.py`

### Test Coverage

3 tests in `TestEvidenceRepairScenario` class:

| Test | Description |
|------|-------------|
| `test_evidence_repair_allows_commits` | Full repair flow: break code -> blocked -> fix code -> new diff_hash -> new artifacts -> commit succeeds |
| `test_repair_without_new_artifacts_still_blocked` | Validates diff_hash keying: fixing code without new artifacts still blocks |
| `test_repair_with_different_session_id_is_independent` | Validates session_id + diff_hash creates independent artifact paths |

### Test Flow (Main Scenario)

**Phase 1 - Regression (blocked):**
1. Make a breaking change to `add()` function (returns `a - b` instead of `a + b`)
2. Create intentions and commit_plan artifacts
3. Run evidence tests (they fail)
4. Create structure_validation and session_record artifacts
5. Run stop hook -> exits with code 2 (blocked)

**Phase 2 - Repair (allowed):**
6. FIX the code (restore correct `a + b` with comment modification)
7. Recompute diff_hash (it MUST change because code changed)
8. Create NEW artifacts for the new diff_hash (same session_id, different diff_hash key)
9. Run evidence tests (they pass)
10. Create new structure_validation and session_record artifacts
11. Run stop hook -> exits with code 0 (success)
12. Verify commit created with Intent-Id trailer

### Key Implementation Notes

**Diff-Hash Keying Behavior:**
- When code changes, the diff_hash changes
- Artifacts are keyed by `session_id/diff_hash`
- Old artifacts for the broken diff_hash are NOT used after fixing
- NEW artifacts must be created for the new diff_hash
- This prevents stale artifact reuse after code changes

**Artifact Independence Assertion:**
The test includes an explicit assertion:
```python
assert diff_hash_fixed != diff_hash_broken, (
    "After fixing code, diff_hash should change. "
    f"broken={diff_hash_broken}, fixed={diff_hash_fixed}"
)
```

### Helper Functions

```python
def _create_session_record_artifact(session_id, diff_hash, repo_path, intent_id):
    """Create session record using save_session_record MCP tool."""

def _create_structure_validation_passed(session_id, diff_hash, repo_path):
    """Create passing structure validation artifact."""

def _create_config_with_structure_disabled(repo_path):
    """Disable structure validation to focus on evidence checking."""
```

### MCP Tools Used

- `save_intentions` - Persist intentions artifact
- `save_commit_plan` - Persist commit plan artifact
- `run_evidence_tests` - Execute pytest selectors and record results
- `save_structure_validation` - Persist structure validation artifact
- `save_session_record` - Persist session record artifact

### Fixtures Used

From `tests/e2e/conftest.py`:
- `demo_repo` - Calculator repo with passing tests
- `project_root` - Repository root path
- `compute_diff_hash()` - Compute diff hash matching stop_hook implementation
- `run_stop_hook()` - Run stop hook as subprocess

From `tests/e2e/fixtures.py`:
- `intention_tree()` - Create goal intention with children
- `minimal_intention()` - Create minimal intention node
- `minimal_commit_plan()` - Create single-commit plan

### Configuration

Tests use `.intent_audit/config.json` with:
```json
{
  "evidence_checking": true,
  "structure_validation": false,
  "docs_validation": "disabled"
}
```

This focuses on evidence validation workflow without structure validation interference.

### Verification

```bash
python -m py_compile tests/e2e/test_evidence_repair.py  # Compilation successful
uv run ruff check tests/e2e/test_evidence_repair.py     # All checks passed
```

### Test Execution

```bash
uv run pytest -m e2e tests/e2e/test_evidence_repair.py
```

---

## T047: E2E Test for Evidence Passing Scenario (2026-02-01)

### Summary

Created E2E test file for the evidence passing scenario where all artifacts are valid, evidence tests pass, and commits are successfully created.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_evidence_passing.py`

### Test Coverage

3 tests in `TestEvidencePassingScenario` class:

| Test | Description |
|------|-------------|
| `test_evidence_passing_allows_commits` | Full flow with single commit - makes non-breaking change (docstring), creates all artifacts, runs evidence tests that pass, verifies commit created with Intent-Id trailer |
| `test_evidence_passing_with_multiple_commits` | Two-commit flow - modifies two files, creates two-commit plan, verifies both commits created with Intent-Id trailers |
| `test_evidence_passing_with_all_tests_in_file` | File-level evidence test selector - verifies evidence runner handles entire test files correctly |

### Test Flow

Each test follows this pattern:

1. **Make non-breaking change** - Modifications that don't break existing tests (e.g., add docstrings)
2. **Create intentions artifact** - Using `save_intentions` MCP tool
3. **Create commit plan artifact** - Using `save_commit_plan` MCP tool
4. **Run evidence tests** - Using `run_evidence_tests` MCP tool (tests must PASS)
5. **Create structure validation artifact** - Using `save_structure_validation` MCP tool (no violations)
6. **Create session record artifact** - Written directly to artifact directory
7. **Run stop hook** - Should exit 0 (allow commits)
8. **Verify commits** - Check git log for commits with Intent-Id trailers
9. **Verify clean state** - No uncommitted changes remain

### Key Implementation Details

**Session Record Path**: The stop hook expects `session_record.json` in the artifact directory (`.intent_audit/<session_id>/<diff_hash>/session_record.json`), but the `save_session_record` MCP tool writes to `.intent_audit/sessions/<session_id>.json`. The test uses a helper function `_save_session_record_to_artifact_dir()` that writes directly to the artifact directory.

**Demo Repo Fixture**: Tests use the `demo_repo` fixture which has:
- Calculator operations at `src/calculator/operations.py`
- Test file at `tests/calculator/test_operations.py`
- 5+ passing tests for add/subtract operations

**Evidence Tests**: The demo_repo tests are designed to always pass, making them ideal for the "evidence passing" scenario.

### Fixtures Used

From `tests/e2e/conftest.py`:
- `demo_repo` - Temporary copy of demo_repo with git initialized
- `project_root` - Path to repository root
- `compute_diff_hash()` - Compute diff hash matching stop_hook
- `run_stop_hook()` - Run stop hook as subprocess

From `tests/e2e/fixtures.py`:
- `full_commit_entry()` - Create commit entry with optional trailers
- `multi_commit_plan()` - Create multi-commit plan

### Test Results

All 3 tests pass. Tests verify:
- Commits are created by stop hook
- Intent-Id trailers are present
- No uncommitted changes remain after hook execution
- Evidence tests can be run at file-level or function-level

---

## T061: E2E Test for Structure Override Rationale Scenario (2026-02-01)

### Summary

Created E2E test file for the structure override rationale scenario, validating that when `structure_override_rationale` is provided in the commit plan, the stop hook allows commits even when structure validation has violations.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_structure_override.py`

### Test Class

`TestStructureOverrideScenario` - 3 tests covering structure override rationale flow

### Test Cases

| Test | Purpose |
|------|---------|
| `test_override_rationale_allows_commits` | Main scenario - file outside code_home + structure_override_rationale in plan = commit allowed |
| `test_override_rationale_missing_still_blocks` | Control case - file outside code_home + no rationale = commit blocked |
| `test_override_rationale_empty_string_still_blocks` | Edge case - empty string rationale does not bypass check |

### Test Flow (Main Scenario)

1. **Create Boundary-Violating Change**: Add file to `src/other_domain/` (outside `src/payments/` code_home)
2. **Create Intentions Artifact**: Define functionality with `code_home: ["src/payments/"]`
3. **Create Commit Plan WITH structure_override_rationale**: Include explicit justification for cross-boundary placement
4. **Run Evidence Tests**: Execute passing tests (evidence is independent of structure)
5. **Create Structure Validation**: Save artifact with `passed=false` and boundary violation
6. **Create Session Record**: Required by hook before commit execution
7. **Run Stop Hook**: Execute stop_hook.py as subprocess
8. **Verify ALLOWED**: Confirm exit code 0 (success, not blocked)
9. **Verify Commit Created**: Check git log for commit with Intent-Id trailer

### Key Feature Tested

The stop hook reads `structure_override_rationale` from the commit_plan.yaml file (lines 751-754 in stop_hook.py):

```python
# Check for override rationale in commit plan
override_rationale = plan.get("structure_override_rationale")
if override_rationale:
    structure_validation.override_rationale = str(override_rationale)
```

When `override_rationale` is truthy, the structure validation check is bypassed:

```python
if not structure_validation.passed and not structure_validation.override_rationale:
    # Block with violation report
```

### Helper Functions

```python
def intention_with_code_home(intent_id, title, code_home, children):
    """Create a functionality intention with code_home defined."""

def goal_intention_tree(root_id, root_title, children):
    """Create a goal intention tree with optional children."""

def structure_violation(violation_type, intent_id, violating_paths, expected_prefixes, ...):
    """Create a structure violation entry."""

def minimal_session_record(session_id, diff_hash):
    """Create a minimal valid session record."""
```

### MCP Tools Used

- `save_intentions` - Persist intentions with code_home definitions
- `save_commit_plan` - Persist commit plan with `structure_override_rationale` field
- `run_evidence_tests` - Run evidence tests (passing, independent of structure)
- `save_structure_validation` - Persist structure validation with violations
- `save_session_record` - Persist session record (required by hook)

### Sample Repo Used

Uses `structure_repo` fixture which provides:
- `src/payments/` - Payment domain with code_home boundary
- `src/other_domain/` - Separate domain for boundary violation testing
- `tests/payments/` - Evidence tests for payment functionality
- `intentions.yaml` - Pre-existing intentions with code_home definitions

### Pytest Mark

All tests decorated with `@pytest.mark.e2e` to allow selective execution:
```bash
uv run pytest -m e2e tests/e2e/test_structure_override.py
```

### Key Assertions

1. **Exit Code 0 with Override**: Hook allows commits when rationale provided
2. **Exit Code 2 without Override**: Hook blocks without rationale (control case)
3. **Exit Code 2 with Empty Override**: Empty string does not bypass check
4. **Commit Created**: Git log shows commit with Intent-Id trailer
5. **Trailers Present**: Git trailers include intention ID reference

### Verification

File compiles successfully:
```bash
python -m py_compile tests/e2e/test_structure_override.py
```

Ruff linting passes:
```bash
uv run ruff check tests/e2e/test_structure_override.py  # All checks passed
```

---

## T050: E2E Test for Evidence Supersede Path Scenario (2026-02-02)

### Summary

Created E2E test file for the evidence supersede workflow, validating the scenario where an obsolete intention is marked as `superseded` rather than repaired, and a new replacement intention takes its place.

### File Created

- `/Users/chuck/workspace/code-intention-consistency/tests/e2e/test_evidence_supersede.py`

### Test Class

`TestEvidenceSupersedePath` - 3 tests covering the supersede workflow

### Test Cases

| Test | Purpose |
|------|---------|
| `test_supersede_old_intention_allows_commits` | Main scenario - mark old intention as superseded, create new intention with passing tests, commit references NEW intent ID |
| `test_supersede_without_replacement_tests_blocks` | Edge case - superseding without proper replacement evidence behavior |
| `test_commit_trailer_uses_new_intent_id` | Trailer verification - commit message must reference NEW intent ID, not old superseded one |

### Test Flow (Main Scenario)

1. **Make a change that adds new functionality**: Add `multiply()` function to calculator operations
2. **Mark OLD intention as superseded**: Set `status="superseded"` and `superseded_by="NEW_INTENT_ID"` on old intention
3. **Create NEW replacement intention**: Active intention with new `evidence_tests` pointing to new test file
4. **Create commit plan referencing NEW intention**: The `intent_id` and `functionality_intent_id` must reference the NEW intention
5. **Run evidence tests for NEW intention**: Execute `test_multiply.py` tests (they pass)
6. **Create supporting artifacts**: Structure validation (passing) and session record
7. **Run stop hook**: Should exit 0 (allowed) because:
   - Commit references NEW intention
   - NEW intention's evidence tests pass
   - OLD intention is superseded (its tests not evaluated)
8. **Verify commit trailer**: Intent-Id references NEW intention, NOT old superseded one

### Key Concept

The "supersede" workflow differs from the "repair" workflow:

- **Repair**: Fix failing tests so the old intention remains valid
- **Supersede**: Mark old intention as obsolete and create a new intention with updated tests

This is useful when:
- Functionality is intentionally changing (not a bug)
- Old tests no longer represent the intended behavior
- A new design replaces the old design

### Helper Functions Created

```python
def superseded_intention(intent_id, title, kind="functionality", superseded_by=None, evidence_tests=None, code_home=None, children=None):
    """Create an intention marked as superseded."""

def active_intention(intent_id, title, kind="functionality", evidence_tests=None, code_home=None, children=None):
    """Create an active intention with planned status."""

def goal_tree_with_superseded(root_id, root_title, superseded, replacement):
    """Create a goal tree containing both a superseded intention and its replacement."""

def _create_session_record_artifact(artifact_dir, session_id, diff_hash, intentions_touched):
    """Create a session record artifact for test purposes."""

def _create_structure_validation_artifact(artifact_dir):
    """Create a passing structure validation artifact for test purposes."""
```

### MCP Tools Used

- `save_intentions` - Persist intentions with superseded status and replacement
- `save_commit_plan` - Persist commit plan referencing NEW intention
- `run_evidence_tests` - Run evidence tests for NEW intention's test selectors

### Sample Repo Used

Uses `demo_repo` fixture which provides:
- Source file: `src/calculator/operations.py` with `add()` and `subtract()` functions
- Test file: `tests/calculator/test_operations.py` with existing evidence tests
- Existing `intentions.yaml` documenting the calculator functionality intention (INT-DEMO-002)

The test dynamically creates:
- New source: `multiply()` function in operations.py
- New test file: `tests/calculator/test_multiply.py` with tests for multiply

### Intention Schema Extensions

The test uses the following intention fields:
- `status: "superseded"` - Marks intention as obsolete
- `superseded_by: "<NEW_INTENT_ID>"` - References the replacement intention

### Pytest Mark

All tests decorated with `@pytest.mark.e2e` to allow selective execution:
```bash
uv run pytest -m e2e tests/e2e/test_evidence_supersede.py
```

### Key Assertions

1. **Exit Code 0 with Superseded**: Hook allows commits when old intention is superseded and new intention's tests pass
2. **NEW Intent-Id in Trailer**: Commit message trailer must reference the NEW intention ID
3. **OLD Intent-Id NOT in Trailer**: Commit message must NOT reference the superseded intention ID
4. **Evidence Independence**: Superseded intention's evidence tests are not evaluated for the commit

### Verification

```bash
python -m py_compile tests/e2e/test_evidence_supersede.py  # Compilation successful
uv run ruff check tests/e2e/test_evidence_supersede.py     # All checks passed
```

---

## T069: Type Hints and Docstrings Audit (2026-02-01)

### Summary

Fixed pyright type errors in the codebase to achieve 0 errors, 0 warnings.

### Issues Fixed

1. **stop_hook.py:313** - Incorrect import `load_intention_tree` → Fixed to `load_intentions`
2. **stop_hook.py:225** - `_block()` return type `None` → Changed to `NoReturn` to enable type narrowing
3. **docs/validator.py:119** - `IntentionKind` enum passed to string field → Added `str()` conversion

### Verification

```bash
uv run pyright src/intention_audit/
# 0 errors, 0 warnings, 0 informations
```

---

## T070: Update CLAUDE.md (2026-02-01)

### Summary

Updated CLAUDE.md to reflect the current project structure with the intention audit trail implementation.

### Changes Made

1. **Project Structure**: Added comprehensive directory listing for:
   - `src/intention_audit/` - Product code breakdown
   - `mcp_servers/intention_audit/` - MCP tools
   - `tests/` - Test infrastructure
   - `specs/` - Feature specifications

2. **Commands**: Added type checking command (`uv run pyright src/`)

3. **Product vs Tooling Distinction**: Documented what goes to target repos vs what stays in this repo

4. **Hook Architecture**: Added flow diagram showing the 5 validation phases

5. **Configuration**: Documented the `.intent_audit/config.json` options

6. **Recent Changes**: Updated to include the intention audit trail MVP implementation

---

## Implementation Summary (2026-02-01)

### Completed Tasks by Batch

| Batch | Tasks | Status |
|-------|-------|--------|
| Batch 1 | T039, T042, T053, T071-T074 | ✓ Complete |
| Batch 2 | T037, T038, T075 | ✓ Complete (already existed) |
| Batch 3 | T046, T057, T065, T067, T076 | ✓ Complete |
| Batch 4-5 | T047, T048, T059, T060 | ✓ Complete |
| Batch 6 | T049, T050, T061 | ✓ Complete |
| Batch 7 | T068, T069, T070 | ✓ Complete |

### Test Coverage

- **Unit Tests**: 192 tests passing
- **E2E Tests**: 9 test files created
  - test_stop_hook_basic.py (existing)
  - test_commit_trailers.py (existing)
  - test_evidence_passing.py (new)
  - test_evidence_regression.py (new)
  - test_evidence_repair.py (new)
  - test_evidence_supersede.py (new)
  - test_structure_alignment_pass.py (new)
  - test_structure_alignment_block.py (new)
  - test_structure_override.py (new)

### Type Safety

- pyright: 0 errors, 0 warnings on `src/intention_audit/`

---
