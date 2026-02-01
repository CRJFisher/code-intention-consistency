# Intention Audit Sub-Agent Definitions

This directory contains **PRODUCT** sub-agent definitions that are deployed to target repositories.

## Deployment Pattern

These YAML files are copied to target repositories' `.claude/agents/` directory during:

1. **Product Installation**: When users install the intention audit trail in their repos
2. **E2E Testing**: When tests set up sample repos for integration testing

## Architecture: Hook → Sub-Agent → MCP Tool

**CRITICAL**: The architecture has clear separation of concerns:

| Component | IS Responsible For | IS NOT Responsible For |
|-----------|-------------------|------------------------|
| **Hook** | Checking for session-keyed artifacts; blocking with sub-agent instructions | Analysis; calling MCP tools |
| **Sub-Agent** | **Analyzing** trajectory/diff (LLM work); calling MCP tools with structured data | Writing files directly |
| **MCP Tool** | Validating schema; persisting data to files | Analysis; decision-making |

The sub-agent (LLM) does the analysis and then calls the MCP tool with the structured result.
The MCP tool only validates and writes - it does NOT analyze.

## Available Sub-Agents

| Agent | Purpose | MCP Tool | Output Artifact |
|-------|---------|----------|-----------------|
| `intention-mapper` | Analyze conversation to identify user intentions | `save_intentions` | `.intent_audit/<session_id>/<diff_hash>/intentions.yaml` |
| `commit-planner` | Map diff changes to intentions and create commit plan | `save_commit_plan` | `.intent_audit/<session_id>/<diff_hash>/commit_plan.yaml` |
| `evidence-checker` | Determine which evidence tests to run | `run_evidence_tests` | `.intent_audit/<session_id>/<diff_hash>/evidence_results.json` |
| `structure-validator` | Check code_home boundary violations | `save_structure_validation` | `.intent_audit/<session_id>/<diff_hash>/structure_validation.json` |
| `session-recorder` | Summarize session for audit trail | `save_session_record` | `.intent_audit/sessions/<session_id>.json` |

## Session-Keyed Artifacts

All artifacts are keyed by `session_id` to prevent stale artifacts from previous sessions causing false positives:

```
.intent_audit/
├── <session_id>/
│   └── <diff_hash>/
│       ├── intentions.yaml
│       ├── commit_plan.yaml
│       ├── evidence_results.json      (Phase 4)
│       └── structure_validation.json  (Phase 5)
└── sessions/
    └── <session_id>.json              (Phase 6 - session record)
```

## Stop Hook Integration

The stop hook:
1. Reads `session_id` from hook input
2. Checks for session-keyed artifacts in `.intent_audit/<session_id>/`
3. When a required artifact is missing, blocks with instructions to spawn the appropriate sub-agent
4. When all artifacts are present, executes the commit plan

## Not Development Tooling

These sub-agents are **not** for developing this repository. They are the product
being built. Development tooling for this repo lives in `.claude/agents/` (if any).
