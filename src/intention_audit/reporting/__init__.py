"""Failure context building and rendering for intention audit reports."""

from intention_audit.reporting.failure_context import (
    IntentionFailureContext,
    build_failure_context,
)
from intention_audit.reporting.renderer import render_failure_context
from intention_audit.reporting.structure_renderer import (
    format_suggested_fixes,
    render_structure_violations,
)

__all__ = [
    "IntentionFailureContext",
    "build_failure_context",
    "format_suggested_fixes",
    "render_failure_context",
    "render_structure_violations",
]
