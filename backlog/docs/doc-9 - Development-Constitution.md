---
id: doc-9
title: Development Constitution
type: note
created_date: "2026-06-02 12:09"
---

<!--
Sync Impact Report
- Version change: 0.1.0 → 1.0.0
- Rationale: Complete replacement - product requirements → development practices
- Modified principles: ALL (complete rewrite)
  - OLD (0.1.0): Intention-First Development, Evidence-Backed Intentions, Functionality Drives Structure, Supporting Information Is Linked, Deterministic Gates
  - NEW (1.0.0): Design Document Authority, Dependency Management via uv, Test Infrastructure with Sample Repositories, Hook Development Standards, MCP Planner Contract Adherence, Intention-Driven Development (Bootstrap Strategy), Python Code Quality Standards
- Added sections:
  - Canonical Design Documents
  - Canonical Code Artifacts
  - Canonical Test Artifacts
  - Development Workflow & Quality Gates (5 gates)
  - Pre-Bootstrap vs Post-Bootstrap Development
- Removed sections:
  - All product requirement sections (moved to product specification domain)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check updated)
  - ✅ .specify/templates/tasks-template.md (Phase 1 sample tasks updated)
  - ✅ CLAUDE.md (commands section updated with uv)
  - ⚠ .specify/templates/spec-template.md (no changes needed - already mandates user scenarios & testing)
- Follow-up items:
  - pyproject.toml creation (separate task)
  - tests/fixtures/sample-repos/ creation (separate task)
  - Bootstrap decision (deferred until MVP functional)
-->

# code-intention-consistency Development Constitution

**Version**: 1.0.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-01-30

## Purpose

This constitution governs **how to develop THIS repository** (the code-intention-consistency tool). It establishes development practices, quality standards, and governance for building the Intention Audit Trail system.

**Note**: This is distinct from the product requirements (what the tool enforces on user repositories), which are documented in the MVP Plan.

---

## Core Principles

### I. Design Document Authority (NON-NEGOTIABLE)

The "Intention Audit Trail MVP Plan.md" is the singular authoritative design document for this repository's development.

**Requirements**:

- All implementation work MUST align with the MVP Plan's architecture, data contracts, and acceptance criteria
- When conflicts arise between design documents, the MVP Plan takes precedence
- Changes to core architecture MUST be reflected in the MVP Plan first, then implementation follows
- Implementation MUST match stop hook behavior, MCP planner contracts, and consistency checks defined in MVP Plan

**Rationale**: A single source of truth prevents divergence between intent and implementation during rapid iteration. The MVP Plan contains the complete system design including stop hook behavior, MCP planner contracts, and consistency checks.

### II. Dependency Management via `uv` (NON-NEGOTIABLE)

All Python dependency management MUST use `uv`.

**Requirements**:

- Maintain `pyproject.toml` with all runtime and development dependencies declared
- Commit `uv.lock` to version control for deterministic builds
- Clearly separate development dependencies from runtime dependencies
- Hook execution MUST use `uvx run python` (as configured in `.claude/settings.json`)

**Rationale**: `uv` provides deterministic, fast dependency resolution. This is critical for a hook that runs on every stop - it must be reliable across environments. The hook must execute quickly without blocking the agent unnecessarily.

### III. Test Infrastructure with Sample Repositories (NON-NEGOTIABLE)

Testing the intention audit trail requires **nested Git repositories** as test fixtures.

**Requirements**:

- Maintain `tests/fixtures/sample-repos/` containing nested `.git` projects for testing hook behavior
- Evidence tests MUST verify stop hook enforcement (coverage checks, evidence execution, structural alignment)
- Contract tests MUST validate MCP planner tool inputs/outputs against schemas in MVP Plan
- Integration tests MUST demonstrate MVP demo scenario (regression detection with intention context surfacing)
- Each test MUST be runnable independently and clean up its state
- Test fixtures MUST NOT be committed to the main repository's Git history (use `.git/info/exclude` or nested `.gitignore`)

**Rationale**: The stop hook operates on Git working tree state. Realistic testing requires actual Git repositories with commits, branches, and working tree changes. This is unique infrastructure for this particular project and cannot be mocked effectively.

### IV. Hook Development Standards (NON-NEGOTIABLE)

The stop hook at `.claude/hooks/intent_audit_stop_hook.py` is critical infrastructure.

**Requirements**:

- Hook MUST remain **stdlib-only** (no external dependencies) for maximum portability
- Error messages MUST be comprehensive and guide the agent to resolution with actionable next steps
- Hook MUST follow MVP's file-level commit granularity (no hunk-splitting in MVP)
- Hook MUST use deterministic validation (no LLM calls in the hook itself)
- Hook MUST maintain version compatibility information via `HOOK_VERSION` constant
- Hook changes MUST be tested against sample repository fixtures before committing
- Error messages MUST provide **actionable next steps** with concrete examples

**Rationale**: The hook is the enforcement boundary. It must be simple, fast, and never break. User experience depends on clear, helpful error messages when the agent is blocked. Dependencies would slow execution and create portability issues.

### V. MCP Planner Contract Adherence (NON-NEGOTIABLE)

The MCP planner tool interface MUST match the contract specified in the MVP Plan.

**Requirements**:

- **Inputs**: `transcript_path`, `repo_root`, `diff_base`, current `intentions.yaml`
- **Outputs**: Updated `intentions.yaml`, `.intent_audit/sessions/<session_id>.json`, `.intent_audit/commit_plan.yaml`
- Schema validation MUST enforce `commit_plan.yaml` version 1 format with `ready`, `commits[]`, and all required fields
- All planner development MUST include contract tests verifying input parsing and output schema compliance
- Changes to the contract MUST update both hook validation logic and MVP Plan documentation simultaneously

**Rationale**: The stop hook and MCP planner are tightly coupled through the commit plan schema. Contract violations break the entire system. Clear interface boundaries enable parallel development and prevent integration issues.

### VI. Intention-Driven Development (Bootstrap Strategy)

This repository SHOULD dogfood its own intention audit trail system once the MVP is functional.

**Pre-bootstrap** (current state):

- Track high-level intentions manually in design documents
- Use conventional commit messages with clear scope (`feat:`, `fix:`, `test:`, `docs:`)
- Prepare for bootstrap by organizing code according to functionality intentions (as defined in MVP Plan)
- Mark the bootstrap transition point explicitly (after MVP acceptance criteria are met)

**Bootstrap timing**: Deferred until MVP is functional and tool maturity assessed. Build MVP first, then decide based on:

- MVP acceptance criteria met (from MVP Plan)
- Demo scenario works end-to-end
- Sample repository tests pass with high coverage
- Team consensus on readiness

**Post-bootstrap**: After bootstrap, this repository MUST use its own stop hook and maintain `intentions.yaml` following all principles from the product constitution (evidence-backed intentions, structural alignment, etc.)

**Rationale**: Dogfooding validates the tool's usability and surfaces design issues. However, forcing it too early creates circular dependencies. The bootstrap strategy creates a clear transition point when the tool is stable enough to enforce its own requirements.

### VII. Python Code Quality Standards

All Python code MUST meet these standards.

**Requirements**:

- Target Python 3.12+ language features
- Include type hints for all public interfaces following PEP 484
- Pass `ruff check .` with zero warnings (configuration in `pyproject.toml`)
- Use standard library where possible to minimize dependencies
- Include docstrings for all public functions/classes following PEP 257

**Exceptions**:

- Test code MAY relax type hint requirements for internal test helpers
- Test fixtures and test contracts MUST be type-hinted for clarity

**Rationale**: The stop hook is critical infrastructure - it must be maintainable and debuggable. Type hints catch errors early and serve as inline documentation. Ruff provides consistent formatting and catches common bugs. Minimizing dependencies reduces attack surface and improves portability.

---

## Additional Constraints & Canonical Artifacts

### Canonical Design Documents

- **Primary**: `Intention Audit Trail MVP Plan.md` (architecture, contracts, acceptance criteria)
- **Supporting**: `Intention Audit Trail Design Document.md`, `Intention Audit Trail Design.md` (historical context)
- **Future**: Spec-kit generated artifacts in `specs/` directory (once features are added)

### Canonical Code Artifacts

- **Stop hook**: `.claude/hooks/intent_audit_stop_hook.py` (enforcement boundary, ~550 lines stdlib-only)
- **Hook configuration**: `.claude/settings.json` (defines `uvx run python` execution)
- **Reference implementations**: `intentions.yaml.example`, `examples/commit_plan.yaml`

### Canonical Test Artifacts (To Be Created)

- `tests/fixtures/sample-repos/` (nested Git repositories for testing)
- `tests/test_stop_hook.py` (hook validation tests)
- `tests/test_planner_contract.py` (MCP tool schema tests)
- `tests/test_demo_scenario.py` (MVP demo: regression with intention context)

### Future Build Artifacts

- `pyproject.toml` (dependency declarations, tool configurations - separate task)
- `uv.lock` (locked dependency versions - separate task)
- `src/` (implementation code when MCP planner is built)

---

## Development Workflow & Quality Gates

The development workflow MUST include these checkpoints.

### Gate 1: Design Review

**Before** implementing any new feature:

- Review alignment with MVP Plan (Principle I)
- Identify conflicts with existing design
- Update MVP Plan if architecture changes
- Document decision rationale

### Gate 2: Test-First Development

**Before** implementing functionality:

- Write evidence tests that demonstrate the requirement
- Verify tests FAIL initially (red-green-refactor)
- Implement until tests pass
- Do not skip tests for "internal" functionality - the hook is all internal and must be tested

### Gate 3: Hook Integration Testing

**Before** committing hook changes:

- Run full test suite against sample repositories
- Manually test the hook with a real coding session
- Verify error messages are actionable and include concrete examples
- Check that `HOOK_VERSION` is updated if behavior changes

### Gate 4: MCP Planner Contract Validation

**Before** releasing planner changes:

- Run contract tests verifying input/output schemas match MVP Plan
- Test against the stop hook's validation logic
- Verify the demo scenario still works end-to-end
- Update hook validation if contract expands

### Gate 5: Bootstrap Readiness

**Before** enabling dogfooding:

- MVP acceptance criteria met (from MVP Plan section)
- Demo scenario works end-to-end
- Sample repositories have complete test coverage
- Team consensus on bootstrap transition

---

## Governance

### Supremacy

This constitution governs development practices for THIS repository. It does not govern what the tool enforces on user repositories (see MVP Plan for product requirements).

### Amendment Process

1. Propose change with rationale (GitHub issue or design doc)
2. Review impact on existing development workflow
3. Update this constitution with version bump following semantic versioning
4. Run spec-kit synchronization to update dependent templates
5. Commit with message: `docs: amend constitution to vX.Y.Z (summary)`

### Versioning Policy

- **MAJOR**: Remove/redefine a NON-NEGOTIABLE principle; change testing framework; change dependency manager; incompatible governance change
- **MINOR**: Add new principle; expand requirements significantly; add new quality gate
- **PATCH**: Clarify wording; fix typos; add examples; reorganize without changing requirements

### Compliance Expectations

- Design documents MUST be reviewed before implementation starts (Gate 1)
- All code changes MUST have evidence tests (Gate 2)
- Hook changes MUST be tested with sample repositories (Gate 3)
- MCP planner changes MUST be validated against contract (Gate 4)
- Work is considered "done" only when it passes all applicable quality gates

### Bootstrap Governance

Once dogfooding begins, this constitution remains the **development practice constitution** and governs how we build the tool. At that point, the tool's product requirements (currently in MVP Plan) will also apply to this repository's development workflow. Both governance layers will coexist:

- **Development constitution** (this document): governs how we build the tool
- **Product constitution** (MVP Plan + tool enforcement): governs what the tool enforces

---

## Notes for Developers

### Getting Started

```bash
# Install dependencies (when pyproject.toml exists)
uv sync

# Run tests (when tests exist)
uv run pytest

# Lint code
uv run ruff check .
```

### Key Reminders

- The stop hook runs on EVERY agent stop - keep it fast
- Test fixtures need nested `.git` directories - don't commit them to main history
- MVP Plan is the source of truth - update it first for architecture changes
- Type hints are mandatory for public APIs - they serve as documentation
- Bootstrap timing is deferred - build MVP first, dogfood later

### Development vs Product

This constitution describes **how to develop this codebase**. The MVP Plan describes **what the tool enforces on user repositories**. Keep these separate:

- Adding a test requirement to THIS constitution = "our tests must do X"
- Adding a test requirement to MVP Plan = "user repositories must do X"
