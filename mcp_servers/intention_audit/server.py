#!/usr/bin/env python3
"""
MCP server for intention audit tools.

This server exposes persistence endpoints for:
- save_intentions: Persist intentions.yaml artifact
- save_commit_plan: Persist commit_plan.yaml artifact
- save_session_record: Persist session record to sessions directory
- save_structure_validation: Persist structure validation results

CRITICAL: The sub-agents (LLMs) do the analysis. These tools only validate
schema and persist the data passed by sub-agents.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_servers.intention_audit.tools.run_evidence_tests import (  # noqa: E402
    run_evidence_tests as _run_evidence_tests,
)
from mcp_servers.intention_audit.tools.save_commit_plan import (  # noqa: E402
    save_commit_plan as _save_commit_plan,
)
from mcp_servers.intention_audit.tools.save_intentions import (  # noqa: E402
    save_intentions as _save_intentions,
)
from mcp_servers.intention_audit.tools.save_session_record import (  # noqa: E402
    save_session_record as _save_session_record,
)
from mcp_servers.intention_audit.tools.save_structure_validation import (  # noqa: E402
    save_structure_validation as _save_structure_validation,
)

server = Server("intention-audit")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available intention audit tools."""
    return [
        Tool(
            name="save_intentions",
            description=(
                "Persist intentions artifact to .intent_audit/<session_id>/<diff_hash>/intentions.yaml. "
                "Called by the intention-mapper sub-agent AFTER analyzing the conversation. "
                "This tool only validates schema and saves data - it does NOT analyze."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier from hook input",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex) from hook output",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "intentions": {
                        "type": "object",
                        "description": (
                            "Structured intention tree data (already analyzed by sub-agent). "
                            "Must have at minimum: {id, title, kind, children: [...]}"
                        ),
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "intentions"],
            },
        ),
        Tool(
            name="save_commit_plan",
            description=(
                "Persist commit plan artifact to .intent_audit/<session_id>/<diff_hash>/commit_plan.yaml. "
                "Called by the commit-planner sub-agent AFTER analyzing the diff and intentions. "
                "This tool only validates schema and saves data - it does NOT analyze."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier from hook input",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex) from hook output",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "plan": {
                        "type": "object",
                        "description": (
                            "Structured commit plan data (already analyzed by sub-agent). "
                            "Must have: {version: 1, ready: bool, commits: [{intent_id, subject, files, ...}]}"
                        ),
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "plan"],
            },
        ),
        Tool(
            name="run_evidence_tests",
            description=(
                "Run evidence tests that a sub-agent requests. "
                "Executes pytest on specified test selectors and persists results to "
                ".intent_audit/<session_id>/<diff_hash>/evidence_results.json. "
                "This tool RUNS tests - it does NOT decide which tests to run (sub-agent does that)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier from hook input",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex) from hook output",
                    },
                    "test_selectors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of pytest test selectors to run "
                            "(e.g., ['tests/auth/test_login.py::test_valid_credentials'])"
                        ),
                    },
                },
                "required": ["session_id", "cwd", "diff_hash", "test_selectors"],
            },
        ),
        Tool(
            name="save_structure_validation",
            description=(
                "Persist structure validation results to .intent_audit/<session_id>/<diff_hash>/structure_validation.json. "
                "Called by a sub-agent AFTER analyzing code_home boundaries and structure alignment. "
                "This tool only validates schema and saves data - it does NOT check boundaries or analyze paths."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier from hook input",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex) from hook output",
                    },
                    "validation": {
                        "type": "object",
                        "description": (
                            "Structure validation results (already analyzed by sub-agent). "
                            "Must have: {violations: [{type, intent_id, ...}], passed: bool, override_rationale: str|null}"
                        ),
                        "properties": {
                            "violations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "intent_id": {"type": "string"},
                                        "functionality_intent_id": {"type": ["string", "null"]},
                                        "violating_paths": {
                                            "type": ["array", "null"],
                                            "items": {"type": "string"},
                                        },
                                        "expected_prefixes": {
                                            "type": ["array", "null"],
                                            "items": {"type": "string"},
                                        },
                                        "details": {"type": ["object", "null"]},
                                        "suggested_fix": {"type": ["string", "null"]},
                                    },
                                    "required": ["type", "intent_id"],
                                },
                            },
                            "passed": {"type": "boolean"},
                            "override_rationale": {"type": ["string", "null"]},
                        },
                        "required": ["violations", "passed"],
                    },
                },
                "required": ["session_id", "cwd", "diff_hash", "validation"],
            },
        ),
        Tool(
            name="save_session_record",
            description=(
                "Persist session record to .intent_audit/sessions/<session_id>.json. "
                "Called by a sub-agent AFTER analyzing the session. "
                "This tool only validates schema and saves data - it does NOT analyze or generate metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier from hook input",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex) from hook output",
                    },
                    "record": {
                        "type": "object",
                        "description": (
                            "Structured session record data (already analyzed by sub-agent). "
                            "Must have: {session_id, timestamp, transcript_ref, diff_base, diff_hash, "
                            "planner_tool, intentions_touched: [...], mapping_summary: {...}, notes?: str}"
                        ),
                    },
                },
                "required": ["session_id", "cwd", "diff_hash", "record"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "save_intentions":
        result = _save_intentions(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            intentions=arguments["intentions"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "save_commit_plan":
        result = _save_commit_plan(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            plan=arguments["plan"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_evidence_tests":
        result = _run_evidence_tests(
            session_id=arguments["session_id"],
            cwd=arguments["cwd"],
            diff_hash=arguments["diff_hash"],
            test_selectors=arguments["test_selectors"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "save_structure_validation":
        result = _save_structure_validation(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            validation=arguments["validation"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "save_session_record":
        result = _save_session_record(
            session_id=arguments["session_id"],
            cwd=arguments["cwd"],
            diff_hash=arguments["diff_hash"],
            record=arguments["record"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Unknown tool: {name}"}),
            )
        ]


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
