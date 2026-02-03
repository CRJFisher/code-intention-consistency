# Synthesis: Integrating Recent Intent Inference Research into Intention Audit Trail

This document synthesizes:
- `research/03-recent-chatgpt-intent-inference.pdf` (ChatGPT deep research)
- `research/03-recent-gemini-intent-goal-modeling.md` (Gemini deep research)

into a concrete, high-level plan for incorporating the best ideas into this project’s existing architecture:
**deterministic stop hook → sub-agent analysis → MCP persistence tools → deterministic commit execution**.

For background and a “lineage view” of how this field evolved (plan recognition → LLM-era intent inference → auditable why-layers), see:
- `research/learning-01-historical-journey.md`

## 0. Current System “Shape” (Baseline)

The repo already implements a strong separation of concerns:

- **Stop hook (`src/intention_audit/hooks/stop_hook.py`)**: deterministic gate + reporting; never does LLM work.
- **Sub-agents (`src/intention_audit/agents/`)**: do the reasoning and emit structured artifacts.
- **MCP tools (`mcp_servers/intention_audit/tools/`)**: persistence endpoints only (validate + write).
- **Artifacts** (session + diff keyed): `intentions.yaml`, `commit_plan.yaml`, `evidence_results.json`, `structure_validation.json`, `session_record.json`.

This matches the dominant “research direction” well: keep the enforcement core deterministic, and push intent inference / goal modeling into an explicit, inspectable plan layer.

## 1. Key Research Ideas (Compressed)

### 1.1 From the ChatGPT deep-research PDF (2023–2026 themes)

1. **Make intent structures explicit and editable before coding** (e.g., NeuroSync’s “task graph” alignment loop).
2. **Hierarchical decomposition improves long-horizon work** (e.g., CoLadder blocks; plan → design → implement pipelines).
3. **Version-control intent linking is essential**: commit messages/rationales are a “why layer”.
4. **Detect and manage tangled changes**: mixed intents in a single change should be surfaced and split (or explicitly justified).
5. **Persistent intention memory enables drift detection**: long-lived intent structures can detect “lost the plot” edits.

### 1.2 From the Gemini deep-research report (systems view)

1. **HTN / intention-tree state is the primary artifact**: code is downstream.
2. **LPW-style workflow**: plan first, verify plan, then commit/codify; use verification as the reliability mechanism.
3. **Rationale mining / traceability recovery**: derive “why” from diffs + tests + tool traces to keep repos auditable.
4. **Commit untangling via dependency reasoning**: separate concerns using explicit + implicit dependencies (beyond file scope).
5. **Memory management + skill evolution**: store reusable patterns and refactor them over time (agent “toolkit refactoring”).

## 2. Integration Strategy: Two Loops, One Artifact Spine

Add two explicit feedback loops around the artifacts the stop hook already enforces.

### Loop A: **Alignment Loop** (before committing)

Goal: catch misunderstanding early by externalizing the model’s inferred intent structure.

- Produce an **Intention Tree** (already present) *plus* an explicit **Task Graph** (new artifact) that encodes:
  - leaf tasks (commit-sized units),
  - dependencies (sequence/parallel constraints),
  - mappings to files/hunks/tests/docs,
  - confidence + open questions.
- Require a “confirm/edit” step in the agent workflow (not the hook) before finalizing the commit plan.

### Loop B: **Traceability + Drift Loop** (over time)

Goal: keep intent durable across sessions and detect drift/tangles as the code evolves.

- Store a **persistent intent registry** (tracked in-repo, separate from `.intent_audit/`) to act as the long-lived “intent memory”.
- Use each new session’s artifacts to:
  - link commits back to persistent intentions,
  - detect when new diffs contradict/violate an existing intent’s constraints,
  - surface “supersede vs repair” decisions explicitly.

## 3. Concrete Additions to the Data Model

### 3.1 New artifact: `task_graph.json` (session + diff keyed)

Purpose: represent the “NeuroSync/CoLadder style” explicit plan structure that can be validated and edited.

Suggested shape (high-level):
- nodes: `{task_id, intent_id, title, kind, files/hunks, outputs, evidence_tests, supporting_docs, confidence}`
- edges: `{from_task_id, to_task_id, type: depends_on|blocks|enables, rationale}`

This is intentionally *parallel* to `intentions.yaml`: the tree is the semantic hierarchy; the graph is the execution structure.

### 3.2 Extend `intentions.yaml` for drift resistance (schema v2, additive)

Add optional fields that can be validated without needing LLM reasoning:
- `acceptance_criteria`: list of checks (human-readable; may reference tests/docs)
- `constraints`: list of invariants (security, compatibility, performance, structure)
- `depends_on`: list of intention IDs (semantic deps)
- `confidence` + `open_questions`: to force ambiguity to be explicit

### 3.3 Add a **tracked** “Intent Registry” (persistent memory)

To avoid `.intent_audit/` being gitignored, introduce a new tracked directory (name TBD):
- `intent_registry/intentions.yaml` (canonical, long-lived)
- `intent_registry/intent_index.json` (fast lookup; optional)
- `intent_registry/links/` (optional: stable links to docs/tests/modules)

Sessions write to `.intent_audit/…`, but the **resulting commits** can update the registry as an explicit, reviewed change (docs-like workflow).

## 4. How This Maps onto Existing Hook Phases

### Phase 1: Intentions check → “editable intention model”

Upgrade `intention-mapper` to output:
- hierarchical intention tree (existing),
- initial task graph proposal (new),
- ambiguity report (open questions, low confidence areas),
- suggested `code_home` for functionality nodes based on changed paths (already conceptually present).

### Phase 2: Commit plan check → “HTN/graph execution plan”

Upgrade `commit-planner` to:
- use the task graph to determine commit ordering and grouping,
- detect tangles and force either:
  - hunk-level split (future), or
  - explicit override metadata: “tangled but accepted (why)”.

### Phase 3: Evidence check → “plan verification (LPW)”

Add a “verify plan” mindset:
- validate that planned tasks reference acceptance criteria (tests/docs) where required,
- run evidence and attach results to leaf intentions (existing),
- record “repair vs supersede” decisions as first-class output.

### Phase 4: Structure validation → “intent-aware architecture invariants”

Extend structure validation beyond `code_home`:
- allow declaring cross-cutting refactors as explicit top-level “structure intents” (so they don’t look like drift),
- detect “tangent” edits: changes outside declared task graph / code_home without justification.

### Phase 5: Session recording → “activity manifest”

Evolve `session_record.json` into an “Agent Activity Manifest”:
- which intentions/tasks were touched,
- what verification ran (tests, lint, typecheck),
- what changed at a semantic level (brief, human-readable rationale summary),
- links to task graph + intention tree versions.

## 5. Roadmap (Pragmatic Milestones)

### Milestone A (low risk): Add explicit “Task Graph” + rationale capture

- Add `task_graph.json` artifact + MCP tool `save_task_graph` (persistence only).
- Update `intention-mapper` guidance to produce a task graph draft.
- Update `session-recorder` guidance to include task graph reference + “rationale summary”.

Success criteria:
- Humans can review/edit the task graph before commits are produced.
- Session record reliably points to “what/why/how verified” without needing to read raw diffs.

### Milestone B (medium): Plan verification and drift/tangle detection

- Add deterministic validations that consume:
  - `intentions.yaml` constraints/acceptance criteria,
  - `task_graph.json` dependencies,
  - evidence + structure results.
- Add a “tangle detector” policy:
  - warn on mixed-intent commits (MVP),
  - block on severe tangles in strict modes (future config).

Success criteria:
- The system blocks or warns *before* committing when changes don’t match the declared intent structure.

### Milestone C (higher): Hunk-level commit planning + untangling

- Extend commit planning from file-scoped to hunk-scoped:
  - represent hunks in the task graph and commit plan,
  - apply dependency-based splitting (explicit + implicit).
- Update stop hook deterministic applier accordingly.

Success criteria:
- A single file can be split across intention commits safely.
- The hook can still apply commits deterministically.

### Milestone D (longer): Persistent intent registry (“intention memory”)

- Introduce tracked `intent_registry/` and conventions for:
  - adding new intentions,
  - superseding existing intentions,
  - maintaining links to code_home/docs/tests.
- Add optional checks that ensure commit trailers reference registry IDs.

Success criteria:
- Intents survive beyond a single session and support drift detection across weeks/months.

## 6. Design Constraints to Preserve

To keep the project aligned with its core promise (auditability + determinism):

- Keep the **stop hook** free of probabilistic reasoning; treat it as a validator/executor.
- Treat sub-agent outputs as **inspectable artifacts** (editable, versionable, testable).
- Keep MCP tools as **persistence endpoints** only; no analysis inside tools.
- Prefer additive schema evolution (v1 compatible) until hunk-level work is ready.

## 7. Suggested Next Step for This Repo

Implement Milestone A first:
- minimal schema for `task_graph.json`,
- persistence tool + validation scaffold,
- update sub-agent docs to emit and use the task graph,
- add 1–2 e2e tests that assert the stop hook blocks until the task graph exists (optionally behind a config flag).
