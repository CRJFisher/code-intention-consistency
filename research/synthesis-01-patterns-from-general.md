# Intent patterns/techniques synthesis (applied to this repo)
Date: 2026-02-02  
Sources: `research/Detecting Intentions Using LLMs.pdf`, `research/LLM Intent Detection and Modeling.md`

## Why this matters for this project
Your core loop is: **trajectory (agentic coding session) → inferred intentions → code edits → intention-tree linkage → long-term consistency + information architecture (IA) steering**.

The two research docs consistently point at one overarching strategy: **stop treating intent as a single label** and instead treat it as a **hierarchical, revisable structure** (an intention tree / HTN / behavior-tree-like plan) that can be inferred from context and updated as evidence (edits/tests) arrives.

## Patterns that are most applicable (ranked)

### 1) Generative intent detection (text-to-text) instead of fixed-label classification
**From research:** Gen-PINT-style framing: detect intent by generating a label/description given task instructions + examples, rather than selecting from a rigid label set.

**Why it maps well here**
- You will constantly see “long tail” intents in real coding sessions (novel feature names, refactor rationales, emergent subgoals).
- For your intention-tree, you need intents that can be **described**, not just classified.

**Technique**
- Make intent inference an instruction-following task that outputs:
  - a compact `intent_summary`
  - a structured `intent_type` (from a small internal taxonomy)
  - a `scope` (repo / package / module / file / symbol)
  - an `expected_evidence` checklist (tests, docs, structure changes)

**Implementation sketch for this repo**
- Define a stable “outer schema” for intent nodes (YAML/JSON), but allow free-form natural language for the node title/description.
- Keep a small taxonomy for the parts you *need* stable (e.g. `feat|fix|refactor|docs|chore`, plus “meta” intents like “investigate”, “plan”, “validate”).

---

### 2) Multi-stage “infer intent first, then act” (explicit intent extraction before code generation)
**From research:** “Your Coding Intent is Secretly in the Context…”: stepwise extraction of intent signals from surrounding code/context improves downstream code generation; also reflected in decomposed workflow architectures.

**Why it maps well here**
- You want **reliable intention→edit linkage**, not just good code output.
- If you extract intent *after* edits, you’ll miss “why” signals that existed *before* the edit (prompt, current file, nearby code smells, earlier plan).

**Technique**
- For each “edit event” (or small batch), run:
  1. **context summarization** (cheap model / deterministic summarizer)
  2. **intent inference** (strong model; produce structured output)
  3. **edit classification** (diff hunks → what changed)
  4. **linkage** (choose parent node(s), decide if new node needed)
  5. **consistency check** (does this drift from the intended tree?)

**Implementation sketch**
- Treat “trajectory” as an append-only event log with derived artifacts:
  - `events.jsonl` (prompts, tool calls, file reads, diffs)
  - `intentions.jsonl` (one record per inferred intent unit)
  - `intent_tree.json` (current best tree)
- Your existing “stop hook” architecture already matches this: it enforces recording + evidence; you can extend those phases to include “intent linkage” and “drift checks”.

---

### 3) Decomposition + hierarchical routing (small model first, big model only when ambiguous)
**From research:** Decomposed workflow intent extraction; hybrid routing where smaller models handle routine cases and LLM handles ambiguous/out-of-scope.

**Why it maps well here**
- A full session can have hundreds of micro-events; you need cost/latency control.
- Many events are mechanically classifiable (formatting, imports, renames) and don’t need heavy reasoning.

**Technique**
- Split inference into:
  - **micro-intent** per event (cheap): “rename”, “fix type error”, “update test snapshot”, etc.
  - **macro-intent** per segment (expensive): “implement structure validation override flow”, “refactor evidence runner architecture”, etc.
- Escalate to a stronger model when:
  - multiple files/concerns change (“tangled”)
  - commit-plan conflicts with observed diffs
  - edits span multiple existing intention branches

---

### 4) Intention trees as explicit structures (HTN / behavior-tree control flow)
**From research:** HTNs and intention trees (I-Tree, ChatHTN, ReAcTree) + control-flow nodes (sequence/fallback/parallel).

**Why it maps well here**
- Your “intention tree” isn’t just parent/child; you’ll need edges like:
  - **sequence**: do A then B
  - **parallel**: update code + docs + tests
  - **fallback**: try approach A, else approach B
  - **AND/OR refinement** (classic goal modeling)

**Technique**
- Model intention nodes with:
  - `children` plus a `decomposition_type` (e.g. `and`, `or`, `sequence`, `parallel`, `fallback`)
  - explicit “leaf actions” that map to evidence: diffs/tests/docs changes

**Implementation sketch**
- Start simple: `and|or|sequence` is usually enough for coding work.
- Add `parallel` once you want “expected evidence” to be multiple independent deliverables (tests + docs).

---

### 5) “Tangled intents” require multi-label linkage + hypothesis search (not a single parent)
**From research:** Tangled commits and “entangled sessions”; AdverIntent-Agent generating multiple intent hypotheses and using tests/evidence to select.

**Why it maps well here**
- Real agentic work frequently interleaves tasks (fix a linter, then implement feature, then adjust docs).
- If you force a single parent node per edit, your tree will become misleading quickly.

**Technique**
- Allow:
  - **multi-parent linkage** (one edit contributes to multiple intents), or
  - **split** an edit batch into multiple intent-attributed hunks.
- Use a “hypothesis set” when ambiguous:
  - propose top-K candidate parent intents
  - score with signals (paths touched, symbols, prior nearby intents, commit plan)
  - validate with evidence (tests, static checks, hook outputs)

**Implementation sketch**
- Keep linkage as a *distribution*, not a hard choice:
  - `link_candidates: [{intent_id, score, rationale}]`
  - pick a `primary_intent_id`, but store alternates for auditability.

---

### 6) Retrieval-augmented intent grounding (RAG over prior intents, IA, and “valid process” definitions)
**From research:** Hybrid architectures combining retrieval with LLM reasoning to reduce hallucination and align with valid business processes.

**Why it maps well here**
- You want the agent to “see the intention tree that led to the current IA” before extending it.
- Grounding reduces invented narratives about why the code is shaped a certain way.

**Technique**
- Retrieve:
  - closest intent nodes by embedding similarity to current edit + context summary
  - relevant “structure boundaries” / module ownership rules
  - previous “architectural decisions” (if you store them as intent nodes or ADR-like children)
- Then ask the model: “Given retrieved nodes, where does this belong?”

---

### 7) Commit/change intent classification as a secondary signal (maintenance taxonomy)
**From research:** Classifying commit intent (corrective/adaptive/perfective) from diffs; commit messages are incomplete so infer from code changes.

**Why it maps well here**
- Your product already enforces structured planning/evidence; “diff-based intent classification” can be a robust backstop.
- Useful for drift detection: “plan says feat, diff looks like refactor”.

**Technique**
- Train/use a lightweight diff classifier (or LLM with strict rubric) to tag each change batch as:
  - `feat|fix|refactor|docs|chore|test`
- Compare to declared intent; raise a “tangled/drift” flag when mismatch is high.

---

## How these patterns directly support “IA + refactor when adding new feature”
The research implicitly suggests a strong framing for your IA feature:

- **New feature = new sub-intent in the tree**
- The act of linking it forces a question: “does this belong under an existing branch, or does the tree need restructuring?”
- Use the intention tree as an *executable design memory*:
  - “What previous intents shaped this module boundary?”
  - “Are we adding too many unrelated children under one node?” (signal for refactor)
  - “Is a new cross-cutting concern emerging?” (introduce a new parent node that reorganizes existing children)

Concrete heuristics (pragmatic, implementable):
- **Branch overload**: if a node accumulates many children across unrelated files/areas, suggest extracting a new sub-module / refactor.
- **Scope mismatch**: if edits touch files outside the declared scope for a node repeatedly, suggest updating IA or moving code to fit boundaries.
- **Repeated fallback**: if “fallback/patch-around” patterns occur (multiple quick fixes), suggest a deeper refactor intent node.

## Recommended “minimum viable” intention-tree data model (from the patterns above)
Start with:
- `intent_id`, `title`, `description`
- `intent_type`: `feat|fix|refactor|docs|test|chore|investigate|plan|validate`
- `scope`: repo/package/module/file/symbol (+ paths/symbols)
- `parents`: allow 0..N
- `decomposition_type`: `and|or|sequence` (optional, for nodes with children)
- `evidence_expected`: tests/docs/structure checks
- `evidence_observed`: links to diffs, test outputs, hook artifacts
- `link_candidates` + `link_rationale` (for auditability)

This keeps the *structure* stable while letting intent text be generative and high-coverage.

## What to carry forward into your implementation roadmap
If you implement only a few things from this research first, make them these:
- **(A) Explicit “intent first” extraction stage per edit segment** (before finalizing plans/commits).
- **(B) Tree linkage as a ranked-choice problem with RAG grounding** (store candidates + rationale).
- **(C) Support tangled intents** (multi-parent or hunk-level attribution).
- **(D) Encode decomposition/control-flow types** once you need better planning and “expected evidence” reasoning.

## Notes on what seems less directly applicable (for now)
- Affective / emotion-aware intent detection: valuable for end-user chat, but your domain is coding trajectories; probably not worth prioritizing.
- Intent-based networking analogies: conceptually useful (“high-level intent → low-level config”), but not directly actionable beyond reinforcing the translation pipeline you’re already building.

