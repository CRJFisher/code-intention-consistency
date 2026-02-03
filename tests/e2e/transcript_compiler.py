"""
Compile Claude session transcripts into readable markdown.

Parses:
- Main session transcript from ~/.claude/projects/
- Sub-agent transcripts from <session>/subagents/

Features:
- Chronological ordering of ALL events merged together
- Source indicators: [Main], [Agent:xyz], [Hook], [MCP]
- Clear Task start/completion markers
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _encode_project_path(path: Path) -> str:
    """
    Encode a path the same way Claude Code does for project directories.

    Claude encodes both '/' and '_' as '-'.
    """
    return str(path).replace("/", "-").replace("_", "-")


def _get_project_dir(repo_path: Path) -> Path | None:
    """
    Find the Claude project directory for a repo path.

    Tries multiple path encodings to handle symlinks (e.g., /var -> /private/var).
    """
    claude_projects = Path.home() / ".claude" / "projects"

    # Try resolved path first (handles symlinks like /var -> /private/var)
    paths_to_try = [repo_path.resolve(), repo_path]

    for path in paths_to_try:
        encoded_path = _encode_project_path(path)
        project_dir = claude_projects / encoded_path
        if project_dir.exists():
            return project_dir

    return None


def get_session_transcript_path(session_id: str, repo_path: Path) -> Path | None:
    """
    Find the session transcript file for a given session ID.

    The project path is encoded with dashes replacing slashes.
    Returns None if transcript not found.
    """
    project_dir = _get_project_dir(repo_path)
    if not project_dir:
        return None

    transcript_path = project_dir / f"{session_id}.jsonl"
    if transcript_path.exists():
        return transcript_path

    return None


def get_subagent_transcripts(session_id: str, repo_path: Path) -> dict[str, Path]:
    """
    Find all sub-agent transcript files for a session.

    Returns dict mapping agentId -> transcript path.
    """
    project_dir = _get_project_dir(repo_path)
    if not project_dir:
        return {}

    subagents_dir = project_dir / session_id / "subagents"

    if not subagents_dir.exists():
        return {}

    result = {}
    for jsonl_file in subagents_dir.glob("agent-*.jsonl"):
        # Extract agent ID from filename: agent-afbdcfb.jsonl -> afbdcfb
        match = re.match(r"agent-([a-f0-9]+)\.jsonl", jsonl_file.name)
        if match:
            result[match.group(1)] = jsonl_file

    return result


@dataclass
class TranscriptEntry:
    """A single entry from a transcript with metadata for sorting/grouping."""

    timestamp: datetime
    timestamp_str: str
    source: str  # "main" or "agent-{id}"
    entry_type: str
    raw_entry: dict[str, Any]
    tool_use_id: str | None = None
    # Metadata extracted during parsing
    meta: dict[str, Any] = field(default_factory=dict)


class TranscriptCompiler:
    """Compile session transcripts into markdown with chronological ordering."""

    def __init__(self, test_name: str, output_dir: Path):
        self.test_name = test_name
        self.output_dir = output_dir
        self.session_id: str = ""
        self.start_time: datetime = datetime.now(tz=UTC)
        self.all_entries: list[TranscriptEntry] = []

    def compile_session(self, repo_path: Path, session_id: str) -> bool:
        """
        Compile the full session including sub-agents.

        Returns True if transcript was found and compiled.
        """
        self.session_id = session_id

        # Find main transcript
        transcript_path = get_session_transcript_path(session_id, repo_path)
        if not transcript_path:
            return False

        # Parse main session
        main_entries = self._parse_transcript(transcript_path, source="main")
        self.all_entries.extend(main_entries)

        # Find and parse sub-agent transcripts
        subagent_paths = get_subagent_transcripts(session_id, repo_path)
        for agent_id, agent_path in subagent_paths.items():
            agent_entries = self._parse_transcript(agent_path, source=f"agent:{agent_id}")
            self.all_entries.extend(agent_entries)

        # Sort all entries chronologically
        self.all_entries.sort(key=lambda e: e.timestamp)

        return True

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse ISO timestamp string to datetime."""
        try:
            # Handle various ISO formats
            if "." in ts_str:
                ts_str = ts_str.split(".")[0] + "Z"
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.now(tz=UTC)

    def _parse_transcript(self, path: Path, source: str) -> list[TranscriptEntry]:
        """Parse a JSONL transcript file into entries."""
        entries: list[TranscriptEntry] = []

        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    timestamp_str = raw.get("timestamp", "")
                    timestamp = self._parse_timestamp(timestamp_str)
                    ts_short = timestamp_str[11:19] if len(timestamp_str) > 19 else timestamp_str

                    entry = TranscriptEntry(
                        timestamp=timestamp,
                        timestamp_str=ts_short,
                        source=source,
                        entry_type=raw.get("type", ""),
                        raw_entry=raw,
                    )
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries

    def _get_source_label(self, entry: TranscriptEntry) -> str:
        """Get a human-readable source label for an entry."""
        if entry.source == "main":
            return "Main"
        elif entry.source.startswith("agent:"):
            agent_id = entry.source.split(":")[1]
            return f"Agent:{agent_id}"
        return entry.source

    def _format_entry(self, entry: TranscriptEntry) -> str | None:
        """Format a single transcript entry as markdown with source indicator."""
        raw = entry.raw_entry
        entry_type = entry.entry_type
        ts = entry.timestamp_str
        source = self._get_source_label(entry)

        if entry_type == "user":
            return self._format_user_entry(raw, ts, source)
        elif entry_type == "assistant":
            return self._format_assistant_entry(raw, ts, source)
        elif entry_type == "system":
            return self._format_system_entry(raw, ts, source)
        elif entry_type == "progress":
            return self._format_progress_entry(raw, ts, source)

        return None

    def _format_user_entry(self, entry: dict, ts: str, source: str) -> str | None:
        """Format user entry (prompt or tool result)."""
        message = entry.get("message", {})
        content = message.get("content")
        tool_result = entry.get("toolUseResult")

        # Tool result
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "tool_result":
                    result_content = item.get("content", "")
                    is_error = item.get("is_error", False)
                    status = "Error" if is_error else "Success"

                    # Check for agent completion (tool_result can be dict or list)
                    if isinstance(tool_result, dict) and tool_result.get("isAgent"):
                        agent_id = tool_result.get("agentId", "unknown")
                        duration = tool_result.get("totalDurationMs", 0) / 1000
                        tokens = tool_result.get("totalTokens", 0)
                        return f"""### [{ts}] [{source}] Task Completed
**Agent ID:** {agent_id} | **Duration:** {duration:.1f}s | **Tokens:** {tokens}
**Summary:** {result_content}
"""

                    return f"""### [{ts}] [{source}] Tool Result: {status}
```
{result_content}
```
"""

        # User prompt (initial or for sub-agents)
        if isinstance(content, str) and len(content) > 50:
            return f"""### [{ts}] [{source}] Prompt
```
{content}
```
"""

        return None

    def _format_assistant_entry(self, entry: dict, ts: str, source: str) -> str | None:
        """Format assistant entry (text, thinking, tool_use)."""
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return None

        parts = []
        for item in content:
            block_type = item.get("type")

            if block_type == "text":
                text = item.get("text", "")
                if text.strip():
                    parts.append(f"""### [{ts}] [{source}] Assistant
{text}
""")

            elif block_type == "tool_use":
                tool_name = item.get("name", "unknown")
                tool_input = item.get("input", {})

                # Special handling for Task (sub-agent spawn)
                if tool_name == "Task":
                    subagent_type = tool_input.get("subagent_type", "unknown")
                    prompt = tool_input.get("prompt", "")
                    parts.append(f"""### [{ts}] [{source}] Task Spawned: {subagent_type}
**Sub-agent type:** `{subagent_type}`
**Prompt:**
```
{prompt}
```
""")

                # Special handling for MCP tools
                elif tool_name.startswith("mcp__"):
                    # Parse MCP tool name: mcp__server__tool -> server/tool
                    mcp_parts = tool_name.split("__")
                    if len(mcp_parts) >= 3:
                        server = mcp_parts[1]
                        tool = mcp_parts[2]
                        mcp_label = f"{server}/{tool}"
                    else:
                        mcp_label = tool_name

                    input_json = json.dumps(tool_input, indent=2)
                    parts.append(f"""### [{ts}] [MCP:{mcp_label}] Tool Call
**Input:**
```json
{input_json}
```
""")

                # Regular tool
                else:
                    input_json = json.dumps(tool_input, indent=2)
                    parts.append(f"""### [{ts}] [{source}] Tool: {tool_name}
```json
{input_json}
```
""")

            elif block_type == "thinking":
                # Skip thinking blocks (too verbose)
                pass

        return "\n".join(parts) if parts else None

    def _format_system_entry(self, entry: dict, ts: str, source: str) -> str | None:
        """Format system entry (hooks, errors)."""
        subtype = entry.get("subtype", "")

        if subtype == "stop_hook_summary":
            prevented = entry.get("preventedContinuation", False)
            hook_infos = entry.get("hookInfos", [])
            status = "BLOCKED" if prevented else "Allowed"

            output_lines = []
            for info in hook_infos:
                output_lines.append(f"- {info.get('command', 'unknown')}")

            return f"""### [{ts}] [Hook] Stop {status}
**Prevented continuation:** {prevented}
**Hooks run:**
{chr(10).join(output_lines)}
"""

        elif subtype == "api_error":
            error = entry.get("error", {})
            return f"""### [{ts}] [System] API Error
{json.dumps(error, indent=2)}
"""

        return None

    def _format_progress_entry(self, entry: dict, ts: str, source: str) -> str | None:
        """Format progress entry (hook execution)."""
        data = entry.get("data", {})
        progress_type = data.get("type")

        if progress_type == "hook_progress":
            hook_name = data.get("hookName", "")
            command = data.get("command", "")
            output = data.get("output", "") or data.get("fullOutput", "")

            if output:
                return f"""### [{ts}] [Hook:{hook_name}] Progress
**Command:** `{command}`
**Output:**
```
{output}
```
"""

        return None

    def to_markdown(self) -> str:
        """Generate complete markdown output with chronological ordering."""
        lines = [
            f"# E2E Test: {self.test_name}",
            f"**Run:** {self.start_time.isoformat()}",
            f"**Session ID:** {self.session_id}",
            "",
            "## Source Legend",
            "- `[Main]` - Main Claude session",
            "- `[Agent:xyz]` - Sub-agent with ID xyz",
            "- `[MCP:server/tool]` - MCP tool call",
            "- `[Hook]` / `[Hook:name]` - Hook execution",
            "- `[System]` - System events",
            "",
            "---",
            "",
        ]

        # Format all entries in chronological order
        for entry in self.all_entries:
            formatted = self._format_entry(entry)
            if formatted:
                lines.append(formatted)

        return "\n".join(lines)

    def save(self) -> Path:
        """Save markdown to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Use ISO format: <test-name>-<iso-time>.md
        timestamp = self.start_time.strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{self.test_name}-{timestamp}.md"
        path = self.output_dir / filename
        path.write_text(self.to_markdown())
        return path
