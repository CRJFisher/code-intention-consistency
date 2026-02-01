"""
Failure context renderer for human-readable reports.

Renders IntentionFailureContext objects to human-readable format for display
in hook blocking messages.
"""

from __future__ import annotations

from intention_audit.reporting.failure_context import IntentionFailureContext


def render_failure_context(contexts: list[IntentionFailureContext]) -> str:
    """
    Render failure contexts as a human-readable report.

    Formats the failure contexts in a clear, structured format suitable
    for both humans and LLMs reading blocking messages.

    Args:
        contexts: List of IntentionFailureContext objects to render.

    Returns:
        Formatted string for display in hook blocking message.
        Returns a message indicating no failures if the list is empty.

    Example output:
        ```
        Evidence Test Failures Linked to Intentions
        ============================================

        ## Intention: INT-2026-01-30-0003
        **Title:** Create login endpoint
        **Path:** Add user authentication / Login functionality / Create login endpoint

        **Failing Tests:**
        - tests/auth/test_login.py::test_valid_credentials
        - tests/auth/test_login.py::test_invalid_password

        **Linked Documentation:**
        - docs/auth.md#login-flow

        **Code Scope:**
        - src/auth/

        ---

        ## Intention: INT-2026-01-30-0005
        ...
        ```
    """
    if not contexts:
        return "No evidence test failures linked to intentions."

    lines: list[str] = []

    # Header
    lines.append("Evidence Test Failures Linked to Intentions")
    lines.append("=" * 44)
    lines.append("")

    for i, context in enumerate(contexts):
        # Intention header
        lines.append(f"## Intention: {context.intention_id}")
        lines.append(f"**Title:** {context.intention_title}")
        lines.append(f"**Path:** {context.intention_path}")
        lines.append("")

        # Failing tests
        lines.append("**Failing Tests:**")
        if context.failed_tests:
            for test in context.failed_tests:
                lines.append(f"- {test}")
        else:
            lines.append("- (none)")
        lines.append("")

        # Linked documentation
        lines.append("**Linked Documentation:**")
        if context.linked_docs:
            for doc in context.linked_docs:
                lines.append(f"- {doc}")
        else:
            lines.append("- (none)")
        lines.append("")

        # Code scope
        lines.append("**Code Scope:**")
        if context.code_scope:
            for scope in context.code_scope:
                lines.append(f"- {scope}")
        else:
            lines.append("- (none)")

        # Add separator between contexts (but not after the last one)
        if i < len(contexts) - 1:
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)
