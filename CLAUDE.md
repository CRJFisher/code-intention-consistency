# code-intention-consistency Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-30

## Active Technologies

- Python 3.12 + Claude Code hooks + MCP server tooling (planner)
- Dependency management: `uv`
- Testing: pytest with sample Git repositories
- Linting: ruff

## Project Structure

```text
src/                           # Implementation code (to be created)
tests/                         # Test suite (to be created)
  fixtures/sample-repos/       # Nested Git repositories for testing hooks
.claude/hooks/                 # Stop hook implementation
.specify/                      # Spec-kit infrastructure
```

## Commands

uv sync                # Install dependencies
uv run pytest          # Run tests
uv run ruff check .    # Lint code

## Code Style

Python 3.12: Follow PEP 8, type hints required for public APIs, docstrings required (PEP 257)

## Recent Changes

- main: Adopted development constitution v1.0.0, established uv dependency management, defined test infrastructure requirements

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
