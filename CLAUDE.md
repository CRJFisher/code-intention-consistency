# code-intention-consistency Development Guidelines

Last updated: 2026-06-02

## Active Technologies

- Python 3.12 + Claude Code hooks + MCP server tooling
- Dependency management: `uv`
- Testing: pytest with sample Git repositories
- Linting: ruff
- Type checking: pyright

## Project Structure

```text
src/intention_audit/           # Intention Audit product code
  hooks/                       # Stop hook (install to target repos)
    stop_hook.py               # Main enforcement hook
  agents/                      # Sub-agent definitions (install to target repos)
    intention-mapper.md
    commit-planner.md
    evidence-checker.md
    structure-validator.md
    session-recorder.md
  models/                      # Data models + structural validators
  evidence/                    # Evidence test runner
  structure/                   # Code home boundary checker
  reporting/                   # Failure context rendering
  docs/                        # Docs linkage validation
  session/                     # Session recording

mcp_servers/intention_audit/   # MCP tools (called by sub-agents)
  tools/
    save_intentions.py
    save_commit_plan.py
    run_evidence_tests.py
    save_structure_validation.py
    save_session_record.py

tests/
  unit/                        # Unit tests (192 tests)
  e2e/                         # E2E tests (marked @pytest.mark.e2e)
  fixtures/sample_repos/       # Sample repos for testing
    basic_repo/                # Basic test repo
    demo_repo/                 # Demo with evidence tests
    structure_repo/            # Repo with code_home boundaries

backlog/                       # Task and spec management (backlog.md)
  tasks/                       # Feature/bug tasks
  docs/                        # Specs, plans, data models, design notes
  decisions/                   # Decision records
.claude/hooks/                 # Project-local hooks for THIS repo
```

## Task & Spec Management

This project uses [backlog.md](https://backlog.md) for tasks and specifications,
driven through the connected `backlog` MCP server.

- Tasks live in `backlog/tasks/` (statuses: To Do, In Progress, Done).
- Specifications, plans, data models, and design notes live in `backlog/docs/`.
- The original 001-intent-audit-trail spec set is preserved as `doc-1` through
  `doc-8`; the development constitution is `doc-9`. The artifact JSON schemas are
  reference contracts under `backlog/docs/contracts/`.

## Commands

```bash
uv sync                        # Install dependencies
uv run pytest                  # Run unit tests only (E2E excluded by default)
uv run pytest -m e2e           # Run E2E tests
uv run pytest -v               # Verbose test output
# Linting (ruff) and type checking (pyright) run automatically via Claude Code hooks
```

## Code Style

Python 3.12: Follow PEP 8, type hints required for public APIs, docstrings required (PEP 257)

## Import Guidelines

This project uses `uv` with editable installs. All packages are importable directly:

- `from intention_audit.models.X import Y`
- `from mcp_servers.intention_audit.tools.X import Y`

**Never use sys.path manipulation.** If imports don't work, run `uv sync` to install packages.

A Stop hook (`check_sys_path_imports.py`) blocks commits containing `sys.path.insert`, `sys.path.append`, or `sys.path +=` patterns.

## Product vs Tooling Distinction

**Product** (to install in target repos):

- `src/intention_audit/hooks/stop_hook.py` → `.claude/hooks/`
- `src/intention_audit/agents/*.md` → `.claude/agents/`
- MCP server tools registered via MCP configuration

**Tooling** (for developing THIS repo):

- `.claude/hooks/` - Project-local hooks
- `tests/` - Test infrastructure

## Hook Architecture

```
User makes changes → Stop hook runs →
  1. Check intentions.yaml → blocks if missing → intention-mapper sub-agent
  2. Check commit_plan.yaml → blocks if missing → commit-planner sub-agent
  3. Check evidence_results.json → blocks if missing/failed → evidence-checker sub-agent
  4. Check structure_validation.json → blocks if missing/violated → structure-validator sub-agent
  5. Check session_record.json → blocks if missing → session-recorder sub-agent
  6. Execute commits with Intent-Id trailers
```

## Configuration

The hook reads `.intent_audit/config.json` for optional settings:

```json
{
  "evidence_checking": true,
  "structure_validation": true,
  "docs_validation": "warn"
}
```

## Recent Changes

- 001-intent-audit-trail: Full implementation of intention audit trail MVP
  - Stop hook with 5 validation phases
  - Sub-agents for intention mapping, commit planning, evidence checking, structure validation, session recording
  - E2E test coverage for all scenarios

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
