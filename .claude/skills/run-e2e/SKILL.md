---
name: run-e2e
description: Run and investigate e2e tests that call Claude CLI. Use when user wants to run e2e tests, check test output, or debug intention audit flow.
allowed-tools: Bash, Read, Glob
---

# E2E Test Runner

Run end-to-end tests that invoke the actual Claude CLI and analyze their output.

## Running Tests

### Single Test (Recommended for Investigation)

```bash
uv run pytest tests/e2e/test_stop_hook_basic.py::TestStopHookBasicClaude::test_full_flow_single_file -v -s -m e2e
```

### All E2E Tests

```bash
uv run pytest -m e2e -v -s
```

### Specific Test Class

```bash
uv run pytest tests/e2e/test_stop_hook_basic.py::TestStopHookBasicClaude -m e2e -v -s
uv run pytest tests/e2e/test_commit_trailers.py::TestCommitTrailersClaude -m e2e -v -s
```

## Output Location

Each test run creates a timestamped output directory:

```
tests/e2e/outputs/<test-name>/<iso-timestamp>/
```

## Output Files Reference

| File | Description |
|------|-------------|
| `main-transcript.jsonl` | Raw main Claude session (JSONL format) |
| `subagent-{id}.jsonl` | Sub-agent transcripts (one per spawned agent) |
| `<test-name>-<timestamp>.md` | **Compiled readable markdown transcript** |
| `mcp-calls.json` | All MCP tool calls with inputs and outputs |
| `git-log.txt` | Git history after test completion |
| `git-status.txt` | Final repository state |
| `artifacts/` | Copy of `.intent_audit/` directory |

### Artifacts Directory Structure

```
artifacts/
  {session_id}/
    {diff_hash}/
      intentions.yaml        # Intention tree mapping
      commit_plan.yaml       # Planned commits with intent IDs
      evidence_results.json  # Test execution results
      structure_validation.json
      session_record.json
  sessions/
    {session_id}.json        # Session summary record
```

## Investigation Workflow

### 1. Find Latest Output

```bash
ls -lt tests/e2e/outputs/
```

### 2. Read the Compiled Transcript

The `.md` file is the most useful for understanding the flow:

```bash
cat tests/e2e/outputs/test_full_flow_single_file/<timestamp>/<test-name>-<timestamp>.md
```

This shows:
- User prompts and assistant responses
- Tool calls and results
- Sub-agent spawning and completion
- MCP tool invocations
- Hook feedback messages

### 3. Examine Artifacts

```bash
# List all artifact files
find tests/e2e/outputs/<test-name>/<timestamp>/artifacts -type f

# View intentions mapping
cat tests/e2e/outputs/.../<session_id>/<diff_hash>/intentions.yaml

# View commit plan
cat tests/e2e/outputs/.../<session_id>/<diff_hash>/commit_plan.yaml
```

### 4. Check Git State

```bash
# View commits with Intent-Id trailers
cat tests/e2e/outputs/<test-name>/<timestamp>/git-log.txt

# Check final working tree status
cat tests/e2e/outputs/<test-name>/<timestamp>/git-status.txt
```

### 5. Review MCP Calls

```bash
cat tests/e2e/outputs/<test-name>/<timestamp>/mcp-calls.json | python3 -m json.tool
```

## Test Classes Reference

### True E2E Tests (Call Claude CLI)

- `TestStopHookBasicClaude` in `tests/e2e/test_stop_hook_basic.py`
  - `test_full_flow_single_file` - Complete intention audit flow
  - `test_no_changes_allows_stop` - Empty diff scenario

- `TestCommitTrailersClaude` in `tests/e2e/test_commit_trailers.py`
  - `test_intent_id_trailer_via_claude` - Verifies Intent-Id trailers

### How Tests Work

Tests use `claude -p` (headless mode) with:
- Model: `claude-haiku-4-5-20251001` (fast, cheap)
- MCP config: Auto-generated with intention-audit server
- Permission mode: `bypassPermissions`
- Output format: `stream-json`

## Debugging Tips

### Test Taking Too Long?

- Check if Claude is in a loop (read the markdown transcript)
- Sub-agents run sequentially; each adds ~10-20 seconds

### Missing Output Files?

- Test may have failed before completion
- Check pytest output for errors
- Look at partially written transcript files

### Hook Not Triggering?

- Ensure `.claude/hooks/` config exists in test repo
- Check `stop_hook.py` is properly referenced

### MCP Tool Errors?

- Review `mcp-calls.json` for error responses
- Check that MCP server is properly configured
