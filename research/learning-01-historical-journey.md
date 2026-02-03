# Intent Inference in Software Engineering: A Historical Journey (Learning Notes)

This learning module synthesizes two foundational research notes in this repo:
- [`research/02-fundamental-gemini-intent-hierarchy.md`](02-fundamental-gemini-intent-hierarchy.md) (Gemini): a “systems view” of modern intent inference + hierarchical planning + rationale mining.
- [`research/02-fundamental-chatgpt-intent-inference.pdf`](02-fundamental-chatgpt-intent-inference.pdf) (ChatGPT): a “lineage view” connecting classic AI plan recognition to software-change intent and today’s LLM-based techniques.

The goal is not to be an exhaustive literature review; it’s to build an intuition for how the field got here, what problems each era tried to solve, and why the ideas converge naturally into an **auditable “Why Layer”**—the core motivation of the Intention Audit Trail project in this repository.

---

## Learning objectives

By the end, you should be able to:
1. Distinguish **intent detection** (what the user wants) from **plan recognition** (how goals decompose and evolve over time).
2. Explain why software engineering needs *hierarchical* intent models (not just flat labels).
3. Describe the emerging “Why Layer” stack: **inference → planning → rationale → drift detection → auditability**.
4. Map these ideas onto concrete, Git-first workflows like this repo’s **intention → edits → commits** discipline.

---

## A timeline of ideas (and the problems they were responding to)

These “eras” are approximate, and are meant as a mental model: the field overlaps and loops back on itself (especially the current return to explicit planning structures).

### Era 1 (1980s–1990s): Symbolic foundations — “Explain behavior with plans”

**Core problem:** Given observed actions, infer the latent goal and the plan structure that explains them.

Key ideas highlighted in the sources:
- **Plan recognition / intent recognition** as inference over hierarchical plan structures (often framed as abduction).
- **Hierarchical Task Network (HTN) planning**: represent how high-level tasks decompose into sub-tasks until primitive actions.
- Early applications of plan-based assistants to software development workflows (monitor actions, infer process context).
- **Intentional Programming** (1990s): treat “intentions” as first-class nodes; code becomes a projection/compilation of those intentions.

**Why it matters for software today:** Programming tasks naturally decompose (feature → modules → functions → tests). The symbolic era provides the language for “intent as a structure”, not a label.

### Era 2 (2000s–mid 2010s): Mining software artifacts — “Infer intent from commits and repos”

**Core problem:** Reconstruct developer intent and rationale from noisy, incomplete artifacts (diffs, commit messages, issue trackers).

Key ideas highlighted:
- **Software Change Intent** taxonomies (bug fix vs feature vs refactor, etc.) and automated classifiers.
- Recognition that “what changed” is easy, while “why it changed” is often missing or vague.
- Early and mid-2010s work on **tangled changes**: developers interleave multiple intents, making history hard to interpret. Tools emerge to cluster fine-grained changes into intent-consistent units.

**Why it matters:** This is the beginning of a “Why Layer” mindset, but it’s limited by coarse granularity (commit-level) and weak linkage (message keywords, heuristics).

### Era 3 (mid 2010s–early 2020s): Data-driven modeling — “Represent intent in richer signals”

**Core problem:** Flat artifact mining misses context and developer cognition.

Key ideas highlighted:
- Move toward **richer signals** and representations: sequence models over actions, embeddings over code/text, and the beginnings of behavior-aware assistance.
- Recognition that software work is *episodic* and *interleaved* (exploration, debugging, implementation, refactoring), not a single linear task.

**Why it matters:** This is the precondition for “latent inference” from interaction traces—precursor to telemetry- and multimodal-driven intent inference.

### Era 4 (2023–2025): LLM era — “Understand intent in NL + code + context”

**Core problem:** LLMs are strong at local synthesis but struggle with long-horizon coherence and auditability.

Key ideas highlighted across the two documents:

**(A) Intent inference gets semantic (not just keyword-based)**
- LLM-based classifiers that read diffs + context can infer change intent more reliably than shallow heuristics.
- LLMs can also map review comments or natural language instructions into structured “edit intents” and drive refinement steps.

**(B) Planning becomes explicit again (neuro-symbolic renaissance)**
- Hierarchical planning returns in a modern form: combine LLM flexibility with symbolic structure (HTN-like decompositions, intention trees, plan repair).
- The **Repository Planning Graph (RPG)** idea reframes long-horizon code generation as graph construction + dependency-ordered implementation to scale beyond a single context window (as described in the Gemini synthesis).

**(C) Intent inference becomes multimodal**
- Beyond prompts: IDE telemetry, temporal signals (run tests, read stack traces), and even gaze/vision are framed as “sensors” for latent intent.
- A key outcome is better *control*: deciding when to intervene, when to suppress suggestions, and how to select relevant context.

**Why it matters:** The field stops treating “intent” as a one-shot label. Instead, intent is an evolving object with structure, state, and evidence.

### Era 5 (emerging): “Why Layer” systems — intent memory, drift detection, audit trails

**Core problem:** As AI agents generate more code, repositories risk becoming fast-moving but hard to justify, maintain, or regulate.

Key ideas highlighted:
- Build a **Persistent Intention Memory** by unifying:
  - future plan representations (HTN/RPG-like models), and
  - past rationale mined or captured from artifacts.
- Use intention memory for **drift detection** (design vs implementation), living documentation, and higher-quality refactoring recommendations.
- Treat the repository as an auditable decision log, not only a code snapshot.

**Why it matters:** This is the practical bridge from research to tooling—exactly where this repository sits.

---

## Concept map: how the modern stack fits together

This synthesis (especially from the Gemini document) suggests a layered architecture:

1. **Intent inference**
   - Inputs: prompts, code context, diffs, IDE telemetry, test outcomes, (optionally) visual artifacts.
   - Output: a *candidate intention* (plus confidence and scope).

2. **Hierarchical goal modeling**
   - Organize intentions into an evolving tree (goal → functionality → implementation/tests/docs).
   - Support interruption/resumption and plan repair.

3. **Planning substrate**
   - HTN-like decompositions for “how to do it”.
   - Graph planning (RPG) for dependency-aware, repository-scale execution.

4. **Rationale capture/mining (“Why Layer”)**
   - Link edits and decisions to motivation, alternatives, and constraints.
   - Enrich with traceability to issues/requirements/tests.

5. **Governance capabilities**
   - Drift detection, disentangling mixed work, audit queries (“why is this line here?”), and compliance-grade evidence.

---

## How this repo operationalizes the “Why Layer” (Git-first)

This project is a deliberately pragmatic take on the above stack:

### What it implements today (MVP)

- **A versioned intention tree** (`intentions.yaml`) that models intent hierarchically.
- **A stop hook** that enforces “intentions → commit plan → evidence → structure validation → session record”.
- **Commit trailers** (`Intent-Id`, `Intent-Path`) that bind code history to the intention tree via Git itself.

This is a concrete answer to the historical “why gap” problem:
- Git already preserves *who/what/when*.
- The project adds durable, blame-friendly linkage for *why*.

### How to interpret it as a research-derived system

Map the research terms to implementation terms:

| Research term                       | Practical artifact in this repo                              |
| ----------------------------------- | ------------------------------------------------------------ |
| Intention tree / hierarchical goals | `intentions.yaml` + `Intention` model                        |
| Commit intent attribution           | `commit_plan.yaml` + trailers                                |
| Rationale capture                   | intention node `rationale` (and long-term “supporting_docs”) |
| Evidence of intent holding          | `evidence_tests` + `evidence_results.json`                   |
| Structural alignment / drift checks | `structure_validation.json` + code-home boundaries           |
| Session trace                       | `session_record.json`                                        |

The “learning” point: the project doesn’t try to solve everything with inference. It uses *workflow enforcement* to make the data available and auditable—so that better inference and planning can be layered on later.

---

## Study guide (suggested reading order inside this repo)

1. `research/02-fundamental-chatgpt-intent-inference.pdf`
   - Read for lineage: plan recognition → HTN → commit intent → tangled changes → rationale decomposition → LLM-era intent classification.
2. `research/02-fundamental-gemini-intent-hierarchy.md`
   - Read for systems view: multimodal intent sensing → HTN/RPG planning → rationale mining → drift detection → auditability.
3. [`Intention Audit Trail Design Document.md`](../Intention%20Audit%20Trail%20Design%20Document.md)
   - Read for productization: how “Why Layer” becomes Git-first artifacts and enforcement points.
4. [`src/intention_audit/hooks/stop_hook.py`](../src/intention_audit/hooks/stop_hook.py)
   - Read for mechanics: what’s enforced, what files are required, and how commits get bound to intentions.

If you want the “schema lens” first:
- [`src/intention_audit/models/intention.py`](../src/intention_audit/models/intention.py) (the intention tree node model)

---

## Exercises (to internalize the journey)

1. **From session to intention tree**
   - Take a recent change you made and write a 3-level intention tree:
     - goal → functionality → implementation/tests/docs.
   - Add `rationale` and at least one `evidence_tests` entry for each leaf.

2. **Commit untangling thought experiment**
   - Pick a “tangled” change you’ve done in the past.
   - List diff hunks and cluster them into intents. Compare your clustering to what you’d want Git history to show.

3. **Drift detection scenario**
   - Define one architectural rule as an “intention” (e.g., “module A must not import module B”).
   - Describe what evidence would prove it (tests, static checks, boundary validations) and how you’d flag violations.

---

## Glossary (quick anchors)

- **Intent detection**: infer what the developer wants (often from NL + context).
- **Plan recognition**: infer the plan structure that explains observed actions.
- **HTN**: a formalism for goal decomposition into subtasks/actions.
- **Intention tree**: a persistent hierarchical representation of goals/subgoals and execution state.
- **RPG (Repository Planning Graph)**: a graph representation of repository units and dependencies used to guide scalable generation.
- **Why Layer**: structured, auditable rationale linking code to intentions, evidence, and decisions over time.
- **Drift detection**: detect divergence between intended design/constraints and actual implementation as the repo evolves.

---

## Project map (where the ideas show up in code)

- Stop hook enforcement: [`src/intention_audit/hooks/stop_hook.py`](../src/intention_audit/hooks/stop_hook.py)
- Intention tree data model: [`src/intention_audit/models/intention.py`](../src/intention_audit/models/intention.py)
- High-level product rationale: [`Intention Audit Trail Design Document.md`](../Intention%20Audit%20Trail%20Design%20Document.md)
