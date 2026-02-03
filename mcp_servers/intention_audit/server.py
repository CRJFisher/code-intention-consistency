#!/usr/bin/env python3
"""
MCP server for intention audit tools.

This server exposes persistence endpoints for:
- save_intentions: Persist intentions.yaml artifact
- save_commit_plan: Persist commit_plan.yaml artifact
- save_session_record: Persist session record to sessions directory
- save_structure_validation: Persist structure validation results
- verify_intention_plan: Persist plan verification results

CRITICAL: The sub-agents (LLMs) do the analysis. These tools only validate
schema and persist the data passed by sub-agents.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.intention_audit.tools.analyze_hunk_intents import (
    analyze_hunk_intents as _analyze_hunk_intents,
)
from mcp_servers.intention_audit.tools.cluster_commits import (
    cluster_commits as _cluster_commits,
)
from mcp_servers.intention_audit.tools.compute_drift_score import (
    compute_drift_score as _compute_drift_score,
)
from mcp_servers.intention_audit.tools.extract_implementation_requirements import (
    extract_implementation_requirements as _extract_implementation_requirements,
)
from mcp_servers.intention_audit.tools.generate_alignment_report import (
    generate_alignment_report as _generate_alignment_report,
)
from mcp_servers.intention_audit.tools.get_tiered_context import (
    get_tiered_context as _get_tiered_context,
)
from mcp_servers.intention_audit.tools.get_tiered_context import (
    save_tiered_context as _save_tiered_context,
)
from mcp_servers.intention_audit.tools.run_evidence_tests import (
    run_evidence_tests as _run_evidence_tests,
)
from mcp_servers.intention_audit.tools.save_commit_plan import (
    save_commit_plan as _save_commit_plan,
)
from mcp_servers.intention_audit.tools.save_intentions import (
    save_intentions as _save_intentions,
)
from mcp_servers.intention_audit.tools.save_session_record import (
    save_session_record as _save_session_record,
)
from mcp_servers.intention_audit.tools.save_structure_validation import (
    save_structure_validation as _save_structure_validation,
)
from mcp_servers.intention_audit.tools.synthesize_user_requirements import (
    synthesize_user_requirements as _synthesize_user_requirements,
)
from mcp_servers.intention_audit.tools.validate_confidence import (
    validate_confidence as _validate_confidence,
)
from mcp_servers.intention_audit.tools.verify_intention_plan import (
    verify_intention_plan as _verify_intention_plan,
)
from mcp_servers.intention_audit.tools.verify_intention_tree import (
    verify_intention_tree as _verify_intention_tree,
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
        Tool(
            name="verify_intention_plan",
            description=(
                "Persist plan verification results to .intent_audit/<session_id>/<diff_hash>/plan_verification.json. "
                "Called by the plan-verifier sub-agent AFTER analyzing intention plan coherence. "
                "Based on LPW research: verify plans before coding to catch issues early. "
                "This tool only validates schema and saves data - it does NOT analyze plans."
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
                    "verification": {
                        "type": "object",
                        "description": (
                            "Plan verification results (already analyzed by sub-agent). "
                            "Must have: {passed: bool, issues: [{type, severity, intent_id, message, ...}]}"
                        ),
                        "properties": {
                            "passed": {"type": "boolean"},
                            "issues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "severity": {"type": "string"},
                                        "intent_id": {"type": "string"},
                                        "message": {"type": "string"},
                                        "related_intent_ids": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "conflicting_paths": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "suggested_fix": {"type": ["string", "null"]},
                                        "details": {"type": ["object", "null"]},
                                    },
                                    "required": ["type", "severity", "intent_id", "message"],
                                },
                            },
                            "error_count": {"type": "integer"},
                            "warning_count": {"type": "integer"},
                            "info_count": {"type": "integer"},
                            "override_rationale": {"type": ["string", "null"]},
                        },
                        "required": ["passed", "issues"],
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "verification"],
            },
        ),
        Tool(
            name="generate_alignment_report",
            description=(
                "Persist alignment report to .intent_audit/<session_id>/<diff_hash>/alignment_report.json. "
                "Called by the alignment-reporter sub-agent AFTER comparing declared vs inferred intentions. "
                "Based on NeuroSync research: bidirectional comparison enables early correction of drift. "
                "This tool only validates schema and saves data - it does NOT analyze or compare."
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
                    "report": {
                        "type": "object",
                        "description": (
                            "Alignment report (already analyzed by sub-agent). "
                            "Must have: {aligned: bool, comparisons: [{status, confidence, ...}]}"
                        ),
                        "properties": {
                            "aligned": {"type": "boolean"},
                            "comparisons": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "declared_intent_id": {"type": ["string", "null"]},
                                        "inferred_intent_id": {"type": ["string", "null"]},
                                        "declared_title": {"type": ["string", "null"]},
                                        "inferred_title": {"type": ["string", "null"]},
                                        "status": {"type": "string"},
                                        "confidence": {"type": "number"},
                                        "declared_files": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "inferred_files": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "message": {"type": ["string", "null"]},
                                        "suggested_action": {"type": ["string", "null"]},
                                    },
                                    "required": ["status", "confidence"],
                                },
                            },
                            "alignment_score": {"type": "number"},
                            "coverage_score": {"type": "number"},
                            "confidence_avg": {"type": "number"},
                        },
                        "required": ["aligned", "comparisons"],
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "report"],
            },
        ),
        Tool(
            name="compute_drift_score",
            description=(
                "Persist drift detection results to .intent_audit/<session_id>/drift_history.json. "
                "Called by the drift-monitor sub-agent AFTER analyzing goal drift patterns. "
                "Based on research: active drift monitoring enables early correction. "
                "This tool only validates schema and saves data - it does NOT compute scores."
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
                    "drift_data": {
                        "type": "object",
                        "description": (
                            "Drift history data (already analyzed by sub-agent). "
                            "Must have: {session_id, root_intention_id, scores: [...], alerts: [...]}"
                        ),
                        "properties": {
                            "session_id": {"type": "string"},
                            "root_intention_id": {"type": "string"},
                            "scores": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {"type": "string"},
                                        "score": {"type": "number"},
                                        "files_checked": {"type": "integer"},
                                    },
                                },
                            },
                            "alerts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "type": {"type": "string"},
                                        "severity": {"type": "string"},
                                        "drift_score": {"type": "number"},
                                        "threshold": {"type": "number"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["id", "type", "severity", "message"],
                                },
                            },
                            "current_score": {"type": "number"},
                            "trend": {"type": ["string", "null"]},
                        },
                        "required": ["session_id", "root_intention_id"],
                    },
                },
                "required": ["session_id", "cwd", "drift_data"],
            },
        ),
        Tool(
            name="analyze_hunk_intents",
            description=(
                "Persist hunk analysis results to .intent_audit/<session_id>/<diff_hash>/hunk_analysis.json. "
                "Called by the tangle-analyzer sub-agent AFTER analyzing hunks for intent mixing. "
                "Based on ColaUntangle research: dual-worker analysis for tangled commit detection. "
                "This tool only validates schema and saves data - it does NOT analyze diffs."
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
                    "analysis": {
                        "type": "object",
                        "description": (
                            "Hunk analysis results (already analyzed by sub-agent). "
                            "Must have: {passed: bool, hunk_mappings: [...], tangles: [...]}"
                        ),
                        "properties": {
                            "passed": {"type": "boolean"},
                            "total_hunks": {"type": "integer"},
                            "files_analyzed": {"type": "integer"},
                            "hunk_mappings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "hunk_index": {"type": "integer"},
                                        "start_line": {"type": "integer"},
                                        "end_line": {"type": "integer"},
                                        "intent_id": {"type": "string"},
                                        "intent_confidence": {"type": "number"},
                                    },
                                    "required": [
                                        "file_path",
                                        "hunk_index",
                                        "start_line",
                                        "end_line",
                                        "intent_id",
                                    ],
                                },
                            },
                            "tangles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "type": {"type": "string"},
                                        "severity": {"type": "string"},
                                        "hunk_indices": {
                                            "type": "array",
                                            "items": {"type": "integer"},
                                        },
                                        "intent_ids": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "message": {"type": "string"},
                                    },
                                    "required": [
                                        "file_path",
                                        "type",
                                        "severity",
                                        "hunk_indices",
                                        "intent_ids",
                                        "message",
                                    ],
                                },
                            },
                        },
                        "required": ["passed"],
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "analysis"],
            },
        ),
        Tool(
            name="get_tiered_context",
            description=(
                "Retrieve tiered memory context from .intent_audit/<session_id>/tiered_context.json. "
                "Based on HiAgent research: hierarchical memory chunking for sub-agents. "
                "Returns active (full detail), recent (summaries), and archive (IDs only) tiers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "intent_id": {
                        "type": "string",
                        "description": "Optional specific intention to focus context on",
                    },
                },
                "required": ["session_id", "cwd"],
            },
        ),
        Tool(
            name="save_tiered_context",
            description=(
                "Persist tiered memory context to .intent_audit/<session_id>/tiered_context.json. "
                "Called by the context-manager sub-agent AFTER computing tiered context. "
                "Based on HiAgent research: hierarchical memory chunking. "
                "This tool only validates schema and saves data - it does NOT compute context."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "context": {
                        "type": "object",
                        "description": (
                            "Tiered context data (already computed by sub-agent). "
                            "Must have: {session_id, active_intention_path, active?, recent?, archive?}"
                        ),
                        "properties": {
                            "session_id": {"type": "string"},
                            "active_intention_path": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "active": {
                                "type": "object",
                                "properties": {
                                    "intent_id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "type": {"type": "string"},
                                },
                            },
                            "recent": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "intent_id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "type": {"type": "string"},
                                        "status": {"type": "string"},
                                    },
                                },
                            },
                            "archive": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "intent_id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "type": {"type": "string"},
                                        "status": {"type": "string"},
                                    },
                                },
                            },
                            "total_intentions": {"type": "integer"},
                            "active_tier_size": {"type": "integer"},
                            "recent_tier_size": {"type": "integer"},
                            "archive_tier_size": {"type": "integer"},
                        },
                        "required": ["session_id"],
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Optional diff hash for diff-specific storage",
                    },
                },
                "required": ["session_id", "cwd", "context"],
            },
        ),
        Tool(
            name="cluster_commits",
            description=(
                "Persist commit clustering results to .intent_audit/bootstrap/commit_clusters.json. "
                "Called by the commit-searcher sub-agent AFTER analyzing git history. "
                "First stage of the UserTrace-inspired bootstrap mining pipeline. "
                "This tool only validates schema and saves data - it does NOT analyze commits."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "clusters_data": {
                        "type": "object",
                        "description": (
                            "Commit clusters (already analyzed by sub-agent). "
                            "Must have: {clusters: [{cluster_id, commits, semantic_label, ...}]}"
                        ),
                    },
                    "since_date": {
                        "type": "string",
                        "description": "Optional date filter used during mining",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Optional branch filter used during mining",
                    },
                },
                "required": ["cwd", "clusters_data"],
            },
        ),
        Tool(
            name="extract_implementation_requirements",
            description=(
                "Persist implementation requirements to .intent_audit/bootstrap/implementation_requirements.json. "
                "Called by the code-reviewer sub-agent AFTER extracting IRs from commit clusters. "
                "Second stage of the bootstrap mining pipeline. "
                "This tool only validates schema and saves data - it does NOT analyze diffs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "requirements_data": {
                        "type": "object",
                        "description": (
                            "Implementation requirements (already analyzed by sub-agent). "
                            "Must have: {requirements: [{ir_id, cluster_id, description, ...}]}"
                        ),
                    },
                },
                "required": ["cwd", "requirements_data"],
            },
        ),
        Tool(
            name="synthesize_user_requirements",
            description=(
                "Persist synthesized intentions to .intent_audit/bootstrap/draft_intentions.yaml. "
                "Called by the intent-writer sub-agent AFTER synthesizing URs from IRs. "
                "Third stage of the bootstrap mining pipeline. "
                "This tool only validates schema and saves data - it does NOT synthesize."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "intentions_data": {
                        "type": "object",
                        "description": (
                            "Synthesized intentions (already analyzed by sub-agent). "
                            "Must have: {intentions: [{intent_id, title, type, ...}]}"
                        ),
                    },
                },
                "required": ["cwd", "intentions_data"],
            },
        ),
        Tool(
            name="verify_intention_tree",
            description=(
                "Persist verified intention tree to .intent_audit/bootstrap/intentions.yaml. "
                "Called by the intent-verifier sub-agent AFTER validating and linking intentions. "
                "Final stage of the bootstrap mining pipeline. "
                "This tool only validates schema and saves data - it does NOT verify code linkage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "verified_data": {
                        "type": "object",
                        "description": (
                            "Verified intention tree (already analyzed by sub-agent). "
                            "Must have: {intentions: [{intent_id, title, type, ...}]}"
                        ),
                    },
                },
                "required": ["cwd", "verified_data"],
            },
        ),
        Tool(
            name="validate_confidence",
            description=(
                "Persist confidence validation results to .intent_audit/<session_id>/<diff_hash>/confidence_validation.json. "
                "Called by the confidence-validator sub-agent AFTER checking confidence tiers. "
                "Based on research: Low-confidence mappings need additional scrutiny. "
                "This tool only validates schema and saves data - it does NOT evaluate confidence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier",
                    },
                    "diff_hash": {
                        "type": "string",
                        "description": "Hash of uncommitted changes (16-char hex)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory of the project",
                    },
                    "validation": {
                        "type": "object",
                        "description": (
                            "Confidence validation results (already analyzed by sub-agent). "
                            "Must have: {passed: bool, checks: [{intent_id, confidence, tier, requirement, ...}]}"
                        ),
                        "properties": {
                            "passed": {"type": "boolean"},
                            "checks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "intent_id": {"type": "string"},
                                        "confidence": {"type": "number"},
                                        "tier": {"type": "string"},
                                        "requirement": {"type": "string"},
                                        "passed": {"type": "boolean"},
                                    },
                                },
                            },
                            "thresholds": {
                                "type": "object",
                                "properties": {
                                    "high_threshold": {"type": "number"},
                                    "medium_threshold": {"type": "number"},
                                },
                            },
                            "needs_human_confirmation": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["passed"],
                    },
                },
                "required": ["session_id", "diff_hash", "cwd", "validation"],
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

    elif name == "verify_intention_plan":
        result = _verify_intention_plan(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            verification=arguments["verification"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "generate_alignment_report":
        result = _generate_alignment_report(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            report=arguments["report"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "compute_drift_score":
        result = _compute_drift_score(
            session_id=arguments["session_id"],
            cwd=arguments["cwd"],
            drift_data=arguments["drift_data"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "analyze_hunk_intents":
        result = _analyze_hunk_intents(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            analysis=arguments["analysis"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_tiered_context":
        result = _get_tiered_context(
            session_id=arguments["session_id"],
            cwd=arguments["cwd"],
            intent_id=arguments.get("intent_id"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "save_tiered_context":
        result = _save_tiered_context(
            session_id=arguments["session_id"],
            cwd=arguments["cwd"],
            context=arguments["context"],
            diff_hash=arguments.get("diff_hash"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "cluster_commits":
        result = _cluster_commits(
            cwd=arguments["cwd"],
            clusters_data=arguments["clusters_data"],
            since_date=arguments.get("since_date"),
            branch=arguments.get("branch"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "extract_implementation_requirements":
        result = _extract_implementation_requirements(
            cwd=arguments["cwd"],
            requirements_data=arguments["requirements_data"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "synthesize_user_requirements":
        result = _synthesize_user_requirements(
            cwd=arguments["cwd"],
            intentions_data=arguments["intentions_data"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "verify_intention_tree":
        result = _verify_intention_tree(
            cwd=arguments["cwd"],
            verified_data=arguments["verified_data"],
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "validate_confidence":
        result = _validate_confidence(
            session_id=arguments["session_id"],
            diff_hash=arguments["diff_hash"],
            cwd=arguments["cwd"],
            validation=arguments["validation"],
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
