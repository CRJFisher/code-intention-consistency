"""
Structure violation renderer for human-readable reports.

This module renders structure validation violations to a human-readable format
suitable for display in hook blocking messages.
"""

from __future__ import annotations

from intention_audit.models.structure_validation import (
    StructureValidation,
    StructureViolation,
)


def format_suggested_fixes(violation: StructureViolation) -> list[str]:
    """
    Generate suggested fix options for a violation.

    Based on the violation type, suggests appropriate resolutions:
    - Move/rename file to within code_home
    - Create new functionality intention
    - Split commit to separate intentions
    - Add explicit override rationale

    Args:
        violation: The structure violation to generate fixes for.

    Returns:
        List of suggested fix strings.
    """
    fixes: list[str] = []

    if violation.type == "code_home_boundary":
        # Suggest moving files to within the expected boundary
        if violation.expected_prefixes:
            primary_prefix = violation.expected_prefixes[0]
            for path in violation.violating_paths[:3]:  # Limit examples
                # Extract filename from path
                filename = path.rsplit("/", 1)[-1] if "/" in path else path
                fixes.append(f"Move file to {primary_prefix}{filename}")

            if len(violation.violating_paths) > 3:
                fixes.append(f"... and {len(violation.violating_paths) - 3} more file(s)")

        # Suggest creating a new functionality for the domain
        if violation.violating_paths:
            # Extract domain from first violating path
            first_path = violation.violating_paths[0]
            if "/" in first_path:
                domain_parts = first_path.split("/")
                if len(domain_parts) >= 2:
                    domain_path = "/".join(domain_parts[:2])
                    fixes.append(f"Create new functionality intention for {domain_path}/")

        fixes.append("Add override rationale to commit plan if intentional")

    elif violation.type == "missing_code_home":
        fixes.append("Add code_home field to the functionality intention")
        fixes.append("Specify the directory prefix(es) where implementation should reside")

    elif violation.type == "orphan_files":
        fixes.append("Create functionality intention to cover these files")
        fixes.append("Associate files with an existing functionality intention")
        fixes.append("Add override rationale if files are intentionally orphaned")

    elif violation.type == "cross_boundary":
        fixes.append("Split commit into separate commits per functionality boundary")
        fixes.append("Update functionality code_home to include the overlapping paths")
        fixes.append("Add override rationale to commit plan if intentional")

    else:
        # Generic suggestions for unknown violation types
        if violation.suggested_fix:
            fixes.append(violation.suggested_fix)
        else:
            fixes.append("Review the violation and update intentions or files accordingly")
            fixes.append("Add override rationale to commit plan if intentional")

    return fixes


def render_structure_violations(validation: StructureValidation) -> str:
    """
    Render structure violations as a human-readable report.

    Args:
        validation: The structure validation result to render.

    Returns:
        Formatted string for display in hook blocking message.
        Returns a success message if there are no violations.
    """
    # Handle empty violations gracefully
    if not validation.violations:
        return (
            "Structure Alignment: PASSED\n\nAll changes are within expected code_home boundaries."
        )

    # Handle override case
    if validation.override_rationale:
        override_msg = (
            "Structure Alignment: OVERRIDDEN\n\n"
            f"Override rationale: {validation.override_rationale}\n\n"
            f"Note: {len(validation.violations)} violation(s) were found but overridden."
        )
        return override_msg

    lines: list[str] = []

    # Header
    lines.append("Structure Alignment Violations")
    lines.append("=" * 30)
    lines.append("")

    # Summary
    lines.append(f"Found {len(validation.violations)} violation(s)")
    lines.append("")

    # Render each violation
    for idx, violation in enumerate(validation.violations, start=1):
        lines.append(f"## Violation {idx}: {violation.type}")
        lines.append(f"**Intent ID:** {violation.intent_id}")

        if violation.functionality_intent_id:
            lines.append(f"**Functionality Intent ID:** {violation.functionality_intent_id}")

        lines.append("")

        # Show violating paths
        if violation.violating_paths:
            lines.append("**Violating Paths:**")
            for path in violation.violating_paths:
                lines.append(f"- {path}")
            lines.append("")

        # Show expected boundary
        if violation.expected_prefixes:
            lines.append("**Expected Boundary:**")
            for prefix in violation.expected_prefixes:
                lines.append(f"- {prefix}")
            lines.append("")

        # Show additional details
        if violation.details:
            lines.append("**Details:**")
            for key, value in violation.details.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        # Generate and show suggested fixes
        fixes = format_suggested_fixes(violation)
        if fixes:
            lines.append("**Suggested Fixes:**")
            for fix_idx, fix in enumerate(fixes, start=1):
                lines.append(f"{fix_idx}. {fix}")
            lines.append("")

        # Separator between violations
        if idx < len(validation.violations):
            lines.append("---")
            lines.append("")

    return "\n".join(lines)
