# Intention Audit Trail Design Document

## Use Cases

- For any line/function/file, show the current set of intentions that should hold (blame -> commit trailers -> intention tree).
- Check whether code still supports past intentions, and flag likely regressions or stale assumptions.
- Link code, docs, and tests under a shared intention so changes to one can flag the others as stale.
- Query by intention to find where it is currently realized (code locations, docs, tests).
- Show the longitudinal intention hierarchy for a file/module/repo over time.
- Provide agentic lifecycle checkpoints that preserve coordination and consistency as the code evolves.

## Overview

The goal is to capture and maintain an "intention audit trail" across agentic coding sessions. Each intention is a goal-directed, testable change in behavior or structure that is expressed in conversation and realized by concrete edits. The system records intentions, links them to code changes, and maintains evidence that the intentions still hold, so that downstream queries and audits remain reliable over time.

## Why Git-first (benefits)

- Atomicity: intention + code change can be captured in the same commit.
- Auditability/distribution: intention history travels with the repo (offline availability, branching/merging), and can be read with just Git + the working tree.
- Intention-aware blame: `git blame` -> commit -> `Intent-Id` -> `intentions.yaml` at that commit.
- Cross-artifact linking: docs/tests/config updated under the same `Intent-Id` are easy to locate (e.g. `git log --grep`).
- Separation of concerns: Git stores the canonical log; tooling (CLI/UI/index) provides the query lens.

## Key Components

1. Intention model and tree
   - Intentions are structured nodes with stable IDs and metadata, arranged in a hierarchy.
   - The tree is versioned in-repo to keep intentions tied to code history.

2. Capture and session records
   - Deterministic lifecycle hooks capture conversation + diffs per session.
   - A normalized session record provides stable input to analysis.

3. Intention extraction and linking
   - A local LLM extracts candidate intentions and links them to diffs.
   - A linking pass maps each hunk to one or more intentions.

4. Git-based storage and commit discipline
   - Intention tree stored in `intentions.yaml`.
   - Commit trailers encode intention IDs and optionally the intention path.
   - Micro-commit per leaf intention when possible.
   - Copy-forward of still-relevant intentions for blame-friendly audit queries.

5. Evidence via tests
   - Each intention is backed by tests that serve as evidence of support.
   - Tests are linked to intention IDs using annotations or a manifest.

6. Structural alignment with intention hierarchy
   - Folder/file/scope naming reflects intention branches.
   - New intentions trigger checks for structural changes (new file/module or renames).

7. Optional graph index (derived)
   - A graph index provides fast global queries and longitudinal views.
   - It is fully derived from Git, not a separate source of truth.

8. Query and UI surface
   - Blame-based local query for "why is this line here?"
   - Intention-first queries for impact analysis and staleness detection.

## Implementation Details

### Intention schema and tree

`intentions.yaml` is the canonical, versioned representation.

Example:

```yaml
root:
  id: INT-2026-01-26-0001
  title: Improve payment robustness
  kind: goal
  status: in_progress
  children:
    - id: INT-2026-01-26-0002
      title: Handle Stripe 429 rate limits
      kind: feature
      status: in_progress
      children:
        - id: INT-2026-01-26-0003
          title: Add retry logic in PaymentClient
          kind: implementation
          status: implemented
          evidence_tests:
            - tests/payments/test_retry_on_429.py::test_retry_on_429
        - id: INT-2026-01-26-0004
          title: Add tests for 429 retry behavior
          kind: tests
          status: implemented
```

Guidelines:

- Intent IDs are opaque and stable.
- Paths are derived from the tree at a given commit.
- Retire or supersede intentions by status, not deletion (e.g. `status: superseded`, `superseded_by: INT-...`).
- Prefer the node ID as the durable "address" (commit trailers carry `Intent-Id`); the path is primarily for humans and can be reconstructed from `intentions.yaml` at the commit being inspected.
- Optional node metadata can include: actor/owner, created timestamp, rationale, constraints, scope, and links to tickets/docs.

### Capture layer and session records

On each agent lifecycle event (e.g., stop hook):

- capture conversation turns since last event
- capture diffs from working tree or git head
- record symbol context when available

SessionRecord sketch:

```json
{
  "session_id": "SESSION-2026-01-26-0007",
  "timestamp": "2026-01-26T17:42:31Z",
  "conversation_turns": [
    { "role": "user", "text": "..." },
    { "role": "assistant", "text": "..." }
  ],
  "code_diffs": [
    {
      "file": "src/payments/client.py",
      "hunks": [
        {
          "hunk_id": "HUNK-001",
          "before_range": [10, 25],
          "after_range": [10, 34],
          "diff_text": "@@ ...",
          "symbols_touched": ["PaymentClient.charge", "PaymentClient._do_request"]
        }
      ]
    }
  ]
}
```

### Intention extraction and linking

Process:

1. Segment conversation into episodes (topic changes, goal shifts).
2. Extract candidate intentions with a strict schema:
   - id, actor, kind, title, rationale, constraints, scope
3. Link intentions to hunks using a combined score:
   - filename and symbol overlap
   - embedding similarity of intent text vs diff text
   - time/sequence proximity
4. Assign each hunk a primary intention and optional secondary intentions.

### Commit discipline and trailers

Each commit should map to one leaf intention when possible.

Key discipline: a commit's diff should reflect a single leaf intention so that `commit -> intent` is a total function. If `intentions.yaml` changes independently of code hunks, you can optionally add a separate "session metadata" commit that only updates `intentions.yaml`.

Commit example:

```text
feat: retry payments on Stripe 429s

Introduce retry/backoff logic in PaymentClient.

Intent-Id: INT-2026-01-26-0003
Intent-Path: Improve payment robustness/Handle Stripe 429 rate limits/Add retry logic in PaymentClient
Intent-Confidence: 0.94
```

Optional additional trailers (if useful for tooling/UI): `Intent-Status`, `Intent-Actor` (note: the canonical status still lives in `intentions.yaml`).

If a hunk serves multiple intentions, include multiple `Intent-Id` trailers or label primary/secondary:

```text
Intent-Primary: INT-2026-01-26-0003
Intent-Secondary: INT-2026-01-26-0007
```

### Copy-forward intention sets (blame-friendly audit)

When editing a block:

1. Resolve prior intentions for the block (via blame + commit trailers).
2. Identify relevant intention tests (from `intentions.yaml` or test annotations).
3. Run those tests and required tests for new intentions.
4. Copy forward only intentions whose evidence tests pass.
5. Add new intentions and commit with the full set in trailers.

This makes "still supported" evidence-driven rather than purely LLM-judged.

It also supports a fast "current view" query (blame -> latest commit -> intention set); intentions can fall out of the current set by not being copied forward when they are no longer relevant to the edited block.

Trade-offs to account for:

- Verifying "still supported" is hard without objective evidence; tests are the preferred backing signal.
- Risk: intention inflation (old intentions kept out of caution, so intention sets bloat).
- Risk: silent loss (an intention incorrectly dropped as "no longer relevant").

### Evidence tests and linkage

Support policy (recommended): an intention is considered "supported" iff all linked evidence checks pass on the current code (subject to coverage limits).

Supported linkage options:

- Test naming convention that embeds `INT-YYYY-MM-DD-NNNN`.
- Test annotation or decorator containing the intention ID.
- Central manifest mapping intention IDs to tests.

Evidence types can include:

- Unit/integration tests
- Property-based tests
- Golden-file/snapshot tests
- Static checks (type-checking, linters, schema validators)
- "Observability tests" (assertions on log/metric shape)

Example manifest (`intentions_tests.yaml`):

```yaml
INT-2026-01-26-0003:
  - tests/payments/test_retry_on_429.py::test_retry_on_429
```

At commit time, the agent must:

- ensure each newly implemented intention has at least one evidence test
- run linked tests when modifying code in that intention's scope

### Structural alignment with intention hierarchy

Rules:

- Intention branches should map to module/folder boundaries where practical.
- Sibling intentions often map to sibling modules/classes where practical.
- New intentions must evaluate whether a new file/module or rename is needed.
- File and folder names should reflect the dominant intention subtree.

Agent workflow:

- On new intention: identify candidate home based on intention path + existing structure (including similar existing intentions, naming, and call-graph locality).
- If no clear home: create or rename structure to match the new branch.
- If a file accumulates mixed intentions: split along intention boundaries.

Structure alignment checklist (when introducing a new intention or changing scope):

- Does this intention still fit the existing module/file semantics?
- Has a file become semantically overloaded (mixed intentions) such that a split is warranted?
- Should a new folder/file be created, or existing ones renamed, to reflect the dominant intention subtree?

### Lifecycle checkpoints

1. New goal detection
   - Update intention tree and assign IDs.
   - Assess structural alignment.

2. Planning phase
   - For each leaf intention: identify code targets and evidence tests.
   - Record planned tests if none exist.

3. Editing phase
   - Resolve prior intention set for touched blocks.
   - Treat existing intentions as constraints unless explicitly deprecated.
   - If constraints cannot be maintained, explicitly supersede/deprecate the intention in the tree and update/replace evidence tests accordingly.

4. Pre-commit checkpoint
   - Run tests tied to prior and new intentions.
   - If tests fail, either fix the code/tests or explicitly annotate affected intentions as regressed/under change.
   - Update `intentions.yaml` statuses and evidence mappings.
   - Commit with trailers that encode the intention set.

5. Background maintenance
   - Periodic intention health checks (tests still exist and pass).
   - Structure alignment review for files whose intention sets drifted.

### Optional graph index

Derived index to answer global queries efficiently.

Nodes:

- Intention, Commit, File, Function, CodeBlock (optional), Test, ConversationTurn

Edges:

- REALIZED_BY, TOUCHES, EVIDENCED_BY, MENTIONED_IN, SUPERSEDES

Build process:

- parse git log for trailers
- read `intentions.yaml` per commit
- extract file/symbol/test mappings
- materialize edges

The index can be rebuilt from Git at any time and is not a source of truth.

Git-only queries are acceptable for small repos (e.g. `git log --grep 'Intent-Id: ...'`) but become expensive for "where does intention X live now?" and longitudinal histories; the derived index exists to make those queries fast while keeping Git as the canonical record. Build the index incrementally from new commits and treat it as disposable/rebuildable.

Example queries that are much easier with an index (graph DB or SQLite) than raw Git traversal:

- "Show me the intention tree for branch X."
- "For file F, show all intentions that have touched it, grouped by subtree."
- "Find potentially stale intentions whose code was modified by other intentions in the last N days."

### Query/UI tooling sketches (optional)

- `intent log <path>`: show intention nodes responsible for a file/function, grouped by subtree and recency.
- `intent show <Intent-Id>`: show the intention subtree, related commits, and affected files/functions/tests.
- Staleness heuristics: if code changes under an intention without corresponding updates to linked docs/tests, flag as potentially stale.

## Coordination-heavy agent behaviors (optional)

- Before adding a new intention/feature, scan the intention tree to see if it is a sub-case of an existing intention (prefer extending vs proliferating new branches).
- Before renaming/moving a module, check which intentions conceptually "live" there and whether the new name/placement still matches the dominant intention subtree.
- Before deleting or substantially changing a test, check which intentions lose evidence and require explicit replacement evidence or an explicit decision to accept reduced coverage.
- General framing: the agent isn't just "editing code that passes tests", it's maintaining a long-lived, intention-aware contract between code, tests, and structure.

## Hard bits / design gotchas (details)

### Intention tree evolution and stable IDs

- The code and the intention tree both evolve; tree restructuring can make paths unstable.
- Mitigation: keep `Intent-Id` opaque and stable; treat `Intent-Path` as derived. To interpret a commit, read `intentions.yaml` at that commit.
- Deprecation/superseding should be explicit and non-destructive (e.g. `status: superseded`, `superseded_by: ...`), so history remains interpretable.

### Rebase / squash and auditability

- Aggressive rebase/squash can drop micro-commits, mix multiple intentions into one commit, or lose structured trailers.
- Options:
  - Maintain an "intentional history" branch that preserves micro-commits (and optionally keep a squashed branch for humans).
  - Enforce policies on protected branches (e.g. no merges without `Intent-Id` trailers; no squash merges that drop trailers).
  - Accept that rewriting history rewrites the audit trail (as with any Git-based traceability scheme).

### Granularity & noise

- Micro-commit-per-leaf is elegant but can create too many commits for humans.
- Mitigations:
  - Batch small edits per leaf until a meaningful state is reached.
  - Provide views that group commits by `Intent-Id` (intention summaries) and/or filter logs by trailers.

### Changes spanning multiple leaf intentions

- Preferred: split the diff into separate commits, one per leaf intention.
- If unavoidable: allow multi-tagging (multiple `Intent-Id` trailers) or primary/secondary role tags (potentially informed by confidence scoring).

### Non-agent edits and remediation

- Provide a low-friction manual tagging path (e.g. `git commit -m "..." -m "Intent-Id: INT-..."`) or a wrapper/alias.
- For untagged commits: treat them as `Intent-Id: INT-UNCLASSIFIED-<commit-hash>` and later attach them to existing intentions (including retrospective updates to `intentions.yaml`).

### Git-only query limitations (why the derived index matters)

- `git log --grep 'Intent-Id: X'` can find commits for an intention, but answering "where does X currently live?" often requires simulating history across those diffs.
- Longitudinal histories (intention appearance/evolution/superseding per file/symbol) are similarly expensive from raw Git; a derived graph/SQLite index makes these queries practical while remaining rebuildable from Git.

## Outstanding Issues

- Intention granularity: avoid intentions that are too coarse or too fragmented.
- Overlapping intentions: provide a clean policy for multi-intent hunks.
- Silent agent intentions: handle changes not mentioned in conversation.
- "Still supported" verification: tests reduce uncertainty but coverage gaps remain.
- Copy-forward inflation: avoid accumulating stale intentions on busy files.
- Tree evolution: renames, merges, and superseding should not break history.
- Rebase/squash policies: history rewriting can degrade the audit trail.
- Non-agent edits: missing trailers or intention updates require remediation.
- Performance: local LLM context limits and cost for large diffs.
- Evaluation: lack of ground-truth datasets for intention-to-code linking.
- Structure alignment: heuristics may misjudge when to split or rename.
- Query complexity: Git-only queries are slow for longitudinal views without an index.
