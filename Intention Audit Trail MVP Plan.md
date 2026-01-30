## Intention Audit Trail — MVP Plan (Stop Hook + MCP Planner)

### Summary
The MVP is an **audit-trail / consistency-engine** for agentic coding sessions, enforced by a **Claude Code `Stop` hook**. The stop hook blocks the agent from stopping until a **complete, intention-scoped commit plan** exists. The agent then calls an **MCP server tool** (the “planner”) that analyzes the agent’s own trajectory (conversation + diffs) and produces:

- A versioned **intention tree**
- A complete **intention→edit mapping**
- Explicit links from intentions to **evidence tests** and **supporting docs**
- A **patch-level commit plan** that the stop hook can execute to create one (or more) intention-scoped commits with standardized trailers

This makes intention metadata **mandatory, checkable, and Git-native**.

---

### MVP goals
- **Full coverage**: every code change in the working tree is assigned to an intention leaf (no “unclaimed” edits).
- **Intention-scoped commits**: changes are committed as **one logical intention per commit** whenever possible.
- **Evidence + documentation linkage**:
  - Every intention that claims behavior/structure has associated **evidence tests**.
  - Every intention that changes externally-relevant behavior has associated **supporting documentation** (or an explicit “no-docs” rationale).
- **Git-first traceability**:
  - `git blame` → commit → `Intent-Id` trailer → `intentions.yaml` at that commit.
- **Hook-powered enforcement**:
  - The stop hook is the single “gate” that ensures the metadata exists and is consistent before commits are created.

### Non-goals (explicitly out of MVP)
- A full UI (editor extension) for browsing intention graphs.
- A durable graph database as the primary source of truth.
- Perfect automatic intention extraction (the planner can ask for clarifications later; MVP can bias toward conservative, explicit trees).
- High-fidelity per-symbol refactoring analysis (optional later).

---

## Architecture: Stop hook ↔ MCP planner “self-audit” loop

### Key idea: “Stop-hook → MCP-server-call trick”
Claude Code `Stop` hooks can **block stopping**. When blocked, Claude continues and sees the hook’s message in context. The hook message instructs Claude to call a specific MCP tool.

In other words:
- The stop hook is deterministic enforcement (no judgment; just checks and execution).
- The MCP tool is “the analyzer” (LLM-enabled, trajectory-aware, produces metadata + plan).

### Runtime loop
1. **Agent edits code**
2. Agent attempts to stop
3. **Stop hook runs**:
   - If required metadata files are missing or incomplete: **block** and instruct the agent to call the MCP planner tool.
   - If metadata is complete and valid: **execute plan → stage patches → commit** with correct trailers, then allow stop.
4. If blocked, the agent calls the MCP planner tool, writes the output files, then continues.
5. On the next stop, the hook validates and commits.

---

## Canonical on-disk artifacts (the “consistency engine” ingredients)

### 1) `intentions.yaml` (canonical, versioned in Git)
The repo’s stable intention hierarchy.

**Requirements (MVP):**
- Stable opaque IDs: `INT-YYYY-MM-DD-NNNN`
- Tree structure with `children`
- Explicit lifecycle statuses (do not delete; supersede/retire)
- Links to evidence and docs live on the intention nodes

**Minimum fields:**
- `id`, `title`, `kind`, `status`, `children`

**Recommended fields:**
- `rationale`, `constraints`, `scope_notes`
- `evidence_tests`: test selectors or references
- `supporting_docs`: doc paths/anchors
- `superseded_by` / `supersedes`

#### Intention kinds: **functionality vs implementation** (MVP taxonomy)
The MVP explicitly distinguishes **functionality intentions** from **implementation intentions**:

- **Functionality intentions** (domain semantics)
  - What: the “what/why” at the domain boundary — behavior contracts, domain capabilities, user-facing behavior, invariants.
  - Role: these are the intentions that **should be reflected in folder/file/named-scope semantics** (DDD-style). They define *what a module is about*.
  - Expected shape: typically higher in the tree (goal → functionality → …).
  - Recommended `kind`: `functionality` (and optionally `feature` for higher-level domain features).

- **Implementation intentions** (mechanism/approach)
  - What: the “how” — refactors, performance tweaks, internal API changes, dependency changes, local restructuring that realizes a functionality intention.
  - Role: these do **not** drive top-level naming semantics; they must “live under” a functionality intention and remain consistent with that module’s meaning.
  - Expected shape: typically leaves that are directly realized by commits.
  - Recommended `kind`: `implementation`

Additional kinds that the MVP treats as first-class “linked artifacts”:
- **Tests**: `tests` (evidence as code)
- **Docs**: `docs` (supporting information as text)
- **Observability**: `observability` (optional)

#### Structural alignment (DDD-style invariant)
To keep the codebase semantically coordinated over time:

- A **functionality intention subtree** defines the *semantic meaning* of the module boundary.
- Files/folders/named-scopes should reflect the **dominant functionality intention** they enclose.
- Implementation intentions may evolve, but they should remain inside the functionality module boundary unless the functionality meaning has changed (in which case the structure must change too).

Recommended `intentions.yaml` metadata for functionality nodes:
- `code_home` (required-for-enforcement in MVP): list of repo-relative path prefixes that represent where this functionality “lives” (e.g. `["src/payments/"]`).
- Optional: `named_scopes` conventions (class/module prefixes) if you want to extend enforcement beyond filesystem.

### 2) `.intent_audit/sessions/<session_id>.json` (committed audit record)
A normalized record of the agent’s trajectory and what the planner inferred. This provides an audit trail even if the original Claude transcript file is not committed.

**MVP content (suggested):**
- `session_id`, `timestamp`
- `transcript_ref`: a safe reference (e.g., hash of transcript content, not necessarily absolute path)
- `diff_base`: git commit hash (e.g., HEAD at planning time)
- `diff_hash`: normalized hash of the diff the plan was built for
- Extracted intention episodes and the final intention IDs used
- Mapping summary: hunks grouped by intention

### 3) `.intent_audit/commit_plan.yaml` (derived, disposable, used for enforcement)
The executable plan the stop hook validates and runs. This is the **bridge** between analysis and deterministic committing.

**MVP requirements:**
- Patch-level grouping (hunks, not whole files) so a single file can be split into multiple intention commits safely.
- Full coverage of current diff.
- One commit entry per intention leaf (preferred).
- Explicit inclusion of evidence and docs (either as edits in the patch or explicit links in metadata).

### 4) Optional `intentions_evidence.yaml` / `intentions_docs.yaml` (if not embedded)
If you don’t want evidence/docs embedded in `intentions.yaml`, store them separately as canonical mappings. MVP can choose either approach; the key is that the stop hook enforces that links exist.

---

## Data contracts (schemas)

### A) Commit message trailers (required)
Each intention-scoped commit includes machine-readable trailers:

```
Intent-Id: INT-YYYY-MM-DD-NNNN
Intent-Path: Goal/Feature/Leaf (optional but helpful)
Intent-Functionality-Id: INT-YYYY-MM-DD-NNNN (recommended)
Intent-Functionality-Path: Domain/Capability/... (optional)
Intent-Confidence: 0.xx (optional)
Intent-Evidence: tests/...::selector (repeatable, optional if stored in intentions.yaml)
Intent-Docs: docs/...#anchor (repeatable, optional if stored in intentions.yaml)
```

### B) `.intent_audit/commit_plan.yaml` (MVP schema)
The plan must be fully deterministic for the hook to execute.

```json
{
  "version": 1,
  "ready": true,
  "diff_base": "HEAD",
  "diff_hash": "sha256:....",
  "commits": [
    {
      "intent_id": "INT-2026-01-26-0003",
      "intent_path": "Goal/Feature/Leaf",
      "functionality_intent_id": "INT-2026-01-26-0002",
      "functionality_intent_path": "Domain/Capability",
      "subject": "feat: short summary",
      "body": "optional longer explanation",
      "intent_confidence": 0.94,

      "evidence_tests": [
        "tests/payments/test_retry_on_429.py::test_retry_on_429"
      ],
      "supporting_docs": [
        "docs/payments.md#rate-limits"
      ],

      "patch": "unified diff text that applies cleanly"
    }
  ]
}
```

Notes:
- `patch` is the primary execution unit (preferred for MVP).
- Evidence/docs may be duplicated in commit trailers or stored canonically in `intentions.yaml`. MVP can do both; the hook should enforce at least one consistent source of truth.
- `functionality_intent_id` should identify the closest **functionality-kind ancestor** of the leaf `intent_id`. It is used for **structural alignment checks**.

---

## Consistency checks enforced by the stop hook (MVP)

### 1) Required metadata files exist
If missing, the hook blocks and instructs the agent to call the MCP planner tool to generate them:
- `intentions.yaml`
- `.intent_audit/commit_plan.yaml`
- `.intent_audit/sessions/<session_id>.json` (recommended for audit; can be required in MVP)

### 2) Full intention→edit coverage
The plan must cover **100%** of the current working diff:
- Every hunk in the working diff appears in exactly one commit entry’s `patch`.
- No hunk duplication across commits.

### 3) Intention IDs are valid and consistent
- Every `commit_plan.commits[].intent_id` must exist in `intentions.yaml`.
- The intention node should be a **leaf** for intention-scoped commits (or explicitly marked as allowing direct realization).

### 4) Evidence tests are linked (and optionally executed)
The stop hook enforces that:
- Every intention that changes code behavior/structure has at least one linked evidence test (either:
  - in `commit_plan.commits[].evidence_tests`, and/or
  - on the intention node in `intentions.yaml`).

Recommended enforcement levels:
- **Link-only enforcement (minimum)**: evidence links must exist.
- **Evidence execution (stronger)**: run `evidence_tests` for any intention whose code is modified, and block if failing.

### 5) Documentation is linked
The stop hook enforces that:
- Each intention either:
  - links at least one doc in `supporting_docs` / `Intent-Docs`, or
  - provides an explicit rationale field like `docs_rationale: "no docs needed"` (policy choice).

### 6) Structural alignment (functionality intentions drive names)
The stop hook enforces that implementation work stays semantically aligned with the **functionality intention** that “owns” the module boundary.

Minimum viable enforcement (filesystem-based):
- For each commit entry, determine the associated **functionality intention** (from `functionality_intent_id`).
- Require that all paths touched by the commit’s `patch` fall under at least one `code_home` prefix declared on that functionality node in `intentions.yaml`.

If a patch touches paths outside the declared `code_home`, the stop hook blocks unless the plan also includes one of:
- A **structure fix** (rename/move/split patch) that brings code back under the appropriate functionality module boundary, or
- An explicit **structure override** rationale (policy choice; discouraged except for transitional refactors).

This is the MVP embodiment of the design doc’s “structural alignment with intention hierarchy”, and matches the DDD intuition that **package/module names describe domain capability**, not implementation technique.

### 7) Commit discipline
- Clean index precondition (so the hook can stage deterministically).
- Commit message must include required trailers.
- Prefer one intention leaf per commit; multi-intent commits require explicit justification fields (policy choice).

---

## MCP planner tool responsibilities (what the agent calls)

### Tool name (placeholder)
Choose a name that is explicit about outputting a commit plan, for example:
- `mcp__intention_audit__plan_intention_commits`

### Inputs (minimum)
- `transcript_path` (from Claude hook input)
- `repo_root`
- `diff_base` and/or raw diff (`git diff`)
- Current `intentions.yaml` (if present)

### Outputs (required)
The planner must write/update:
- `intentions.yaml` (create/update tree; IDs; statuses; evidence/docs links)
- `.intent_audit/sessions/<session_id>.json` (normalized audit record)
- `.intent_audit/commit_plan.yaml` (ready-to-execute patch plan)

### Planner algorithm (MVP)
1. **Extract intentions from trajectory**
   - Segment conversation into episodes.
   - Propose/update intention tree nodes and assign IDs.
   - Ensure every implementation intention has a **functionality ancestor** (create/re-home if needed).
2. **Compute edit scopes**
   - Parse current diff into hunks (scope-edits).
3. **Link hunks to leaf intentions**
   - Use file/symbol overlap + semantic similarity + time proximity.
   - Resolve overlaps into a primary intention per hunk.
4. **Attach evidence + docs**
   - Identify or create tests that evidence each intention.
   - Identify docs that explain/support the intention (or record a rationale).
5. **Plan structure alignment**
   - For each intention leaf, compute its `functionality_intent_id` (closest `kind: functionality` ancestor).
   - Ensure all touched code paths are compatible with that functionality node’s `code_home`.
   - If incompatible, include rename/move/split patches (or an explicit override rationale, if policy allows).
6. **Generate patch-level commit plan**
   - One commit entry per leaf intention (preferred).
   - Each entry includes `patch`, commit message text, and trailers metadata.
7. **Write session audit record**
   - Record mapping, confidence, and any unresolved uncertainties.

---

## MVP workflow (what “done” looks like)

### Happy path
1. Agent edits code/tests/docs.
2. Agent tries to stop → stop hook blocks: “generate intention tree + commit plan”.
3. Agent calls MCP planner tool in a sub-agent.
4. Planner writes/updates:
   - `intentions.yaml`
   - `.intent_audit/sessions/<session_id>.json`
   - `.intent_audit/commit_plan.yaml` (ready=true)
5. Agent tries to stop again → stop hook validates:
   - full coverage
   - evidence/doc links present
   - (optional) evidence tests pass
6. Stop hook applies patches and creates intention-scoped commits with trailers.
7. Agent stops; repository now contains a complete intention audit trail for the session.

---

## MVP demo scenario (testable target)

### Purpose
Demonstrate the **consistency-checking** behavior of the tool by creating an intentional “regression” where an intention-linked **evidence test fails** at stop-time, and the stop hook surfaces the intention-linked **code + docs + prior intent context** so the agent can repair or supersede intentionally.

### Scenario: regression on an intention-backed behavior
1. **Initial state (baseline)**
   - Create a small module with a clearly documented behavior and a unit test:
     - Code: `src/feature_x/...`
     - Test: `tests/feature_x/test_behavior_y.py::test_behavior_y`
     - Doc: `docs/feature_x.md` describing Behavior Y
   - Create an intention leaf in `intentions.yaml`:
     - `INT-...`: “Behavior Y holds under condition Z”
     - Link:
       - `evidence_tests`: `tests/feature_x/test_behavior_y.py::test_behavior_y`
       - `supporting_docs`: `docs/feature_x.md#behavior-y`
   - Run the stop-hook→planner→auto-commit flow so the baseline is committed as intention-scoped commits.

2. **Introduce a change that breaks the evidence**
   - Modify the code in a way that breaks Behavior Y (or changes it without updating the test/doc).
   - Attempt to stop.

3. **Expected MVP behavior**
   - The stop hook runs the evidence tests for intentions impacted by the diff (policy: **evidence execution enabled for this demo**).
   - The evidence test fails → the stop hook **blocks stopping** and prints a structured “intention failure context” report containing:
     - **Which evidence test failed**
     - **Which intention(s) that test evidences** (by `Intent-Id` + title + path)
     - **Linked code scope** (at minimum: file paths touched; ideally: symbol names if the planner recorded them)
     - **Linked supporting docs** (paths + anchors)
     - **Most recent commits** associated with the intention (via `Intent-Id` trailers)
     - **Allowed next actions** for the agent:
       - Fix code to restore the intention and make the evidence pass, or
       - If behavior is intentionally changed: mark the intention `superseded`, update docs, and either update/replace the evidence test or delete it with an explicit superseding intention.

4. **Resolution and proof**
   - Agent uses the surfaced context to either repair or supersede.
   - Agent re-attempts stop:
     - If repairing: evidence passes and intention-scoped commits are produced.
     - If superseding: `intentions.yaml` reflects the superseding relationship and the updated evidence/docs are committed with new `Intent-Id`s.

### Minimal “intention failure context” output (MVP requirement)
When blocking due to failing evidence, the stop hook should include (at least):
- **Failed test selector(s)**: `tests/...::test_name`
- **Intentions evidenced**:
  - `Intent-Id`, title, (optional) `Intent-Path`
- **Linked artifacts**:
  - `supporting_docs` entries (file + anchor)
  - `code scope` entries (at least file paths; symbols optional)

This ensures the agent is not just told “tests failed”, but is given the intention-aware context needed to make an informed repair vs supersede decision.

---

## MVP acceptance criteria
- The agent cannot stop with outstanding changes unless:
  - every hunk is mapped to an intention leaf, and
  - evidence/doc link requirements are satisfied.
- The stop hook can deterministically turn the plan into commits.
- Each commit is traceable via `Intent-Id` trailers to the correct node in `intentions.yaml`.
- Evidence tests and supporting docs are explicitly linked to each intention.
 - The demo scenario works end-to-end:
   - a failing evidence test blocks stopping, and
   - the stop hook surfaces intention-linked context (code/docs/tests) sufficient for repair or superseding.

---

## Open decisions (to finalize before implementation)
- **Evidence policy**: link-only vs “run tests at stop” (or configurable).
- **Docs policy**: when docs are required and what counts as “supporting docs”.
- **Plan granularity**: strict hunk-level only, or allow file-level for trivial cases.
- **Session record privacy**: whether to store raw conversation text or only normalized summaries + hashes.
- **Multi-intent hunks**: split vs allow primary/secondary intention tagging.
- **Structural alignment enforcement**: record-only vs enforce module/file naming alignment at stop.

