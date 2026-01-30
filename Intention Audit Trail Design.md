# Intention Audit Trail Design

## Use Cases
- For any line/function/file, show the current set of intentions that should hold (blame -> commit trailers -> intention tree).
- Check whether code still supports past intentions, and flag likely regressions or stale assumptions.
- Link code, docs, and tests under a shared intention so changes to one can flag the others as stale.
- Query by intention to find where it is currently realized (code locations, docs, tests).
- Show the longitudinal intention hierarchy for a file/module/repo over time.
- Provide agentic lifecycle checkpoints that preserve coordination and consistency as the code evolves.

## Overview
The goal is to capture and maintain an "intention audit trail" across agentic coding sessions. Each intention is a goal-directed, testable change in behavior or structure that is expressed in conversation and realized by concrete edits. The system records intentions, links them to code changes, and maintains evidence that the intentions still hold, so that downstream queries and audits remain reliable over time.

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
- Retire or supersede intentions by status, not deletion.

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

Commit example:
```
feat: retry payments on Stripe 429s

Introduce retry/backoff logic in PaymentClient.

Intent-Id: INT-2026-01-26-0003
Intent-Path: Improve payment robustness/Handle Stripe 429 rate limits/Add retry logic in PaymentClient
Intent-Confidence: 0.94
```

If a hunk serves multiple intentions, include multiple `Intent-Id` trailers or label primary/secondary:
```
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

### Evidence tests and linkage
Supported linkage options:
- Test naming convention that embeds `INT-YYYY-MM-DD-NNNN`.
- Test annotation or decorator containing the intention ID.
- Central manifest mapping intention IDs to tests.

At commit time, the agent must:
- ensure each newly implemented intention has at least one evidence test
- run linked tests when modifying code in that intention's scope

### Structural alignment with intention hierarchy
Rules:
- Intention branches should map to module/folder boundaries where practical.
- New intentions must evaluate whether a new file/module or rename is needed.
- File and folder names should reflect the dominant intention subtree.

Agent workflow:
- On new intention: identify candidate home based on intention path + existing structure.
- If no clear home: create or rename structure to match the new branch.
- If a file accumulates mixed intentions: split along intention boundaries.

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

4. Pre-commit checkpoint
   - Run tests tied to prior and new intentions.
   - Update `intentions.yaml` statuses and evidence mappings.
   - Commit with trailers that encode the intention set.

5. Background maintenance
   - Periodic intention health checks (tests still exist and pass).
   - Structure alignment review for files whose intention sets drifted.

### Optional graph index
Derived index to answer global queries efficiently.

Nodes:
- Intention, Commit, File, Function, Test, ConversationTurn

Edges:
- REALIZED_BY, TOUCHES, EVIDENCED_BY, MENTIONED_IN, SUPERSEDES

Build process:
- parse git log for trailers
- read `intentions.yaml` per commit
- extract file/symbol/test mappings
- materialize edges

The index can be rebuilt from Git at any time and is not a source of truth.

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
You said:
What if we added another layer to the intention parsing and reconstruct an *intention tree*, then we could just use git as the storage medium and commit code-chunks (which have been linked to a single intention leaf node) with commit messages which encode the intention tree node address (including the full context)?
ChatGPT said:

Thought for 16s
I really like this direction - it turns “intention tracking” into a structured Git discipline rather than a whole new storage layer.

Let me walk through:

What an “intention tree in Git” could look like

How an agentic workflow could use it (micro-commits per leaf)

What you gain (incl. git blame → intention)

Where it bites you (hard bits / design gotchas)

How you might still layer an index/graph on top without abandoning “git as source of truth”

1. Intention tree: concrete representation
Think of the intention tree as a first-class artefact in the repo, versioned like everything else.

1.1 Tree structure
One simple representation:

# intentions.yaml
root:
  id: INT-2026-01-26-0001
  title: Improve payment robustness
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
        - id: INT-2026-01-26-0004
          title: Add tests for 429 retry behaviour
          kind: tests
          status: planned
    - id: INT-2026-01-26-0005
      title: Add structured logging for payment failures
      kind: observability
      status: planned
Each node has:

id – stable, opaque, never derived from text (because the text will change)

title / kind / status etc

children[] – giving you the tree

You can keep extra metadata in here (linked tickets, owner, created timestamp), but the key thing is that there’s a canonical ID and a tree path.

1.2 Intention address
Address = {tree version, node id} or path.

Some options:

Path address: ImprovePaymentRobustness/Handle429/AddRetryLogic

ID address: INT-2026-01-26-0003

Path + ID: path for humans, ID for machines.

You probably want commit messages to carry just the ID (low entropy, robust), and then reconstruct the path by looking into intentions.yaml at that commit.

2. Agent workflow: micro-commits per leaf intention
Your idea:

“...commit code-chunks (linked to a single intention leaf node) with commit messages which encode the intention tree node address”

That’s nicely workable if you structure the agent like this:

2.1 At each “stop” / “apply edits” event
Analyse conversation + diff to update intentions.yaml:

Extract/refine the tree (possibly using the LLM)

Add or update nodes: create new leaf intentions if needed, update statuses.

Agent edits intentions.yaml as just another file.

For each leaf intention that’s being implemented in this batch:

Group hunks that belong to that leaf (you’re already doing intention→hunk linking).

Produce a separate micro-commit whose diff is only those hunks.

Each of those commits gets a structured message, for example:

Add retry logic for Stripe 429s

- Introduce max_retries and backoff in PaymentClient._do_request
- Retry on HTTP 429 responses from Stripe

Intent-Id: INT-2026-01-26-0003
Intent-Path: ImprovePaymentRobustness/Handle429/AddRetryLogic
Intent-Confidence: 0.94
The trailers are machine-readable, the subject/body stay nice for humans.

Optionally, a final “session” commit that just updates intentions.yaml if it changed.

The important discipline: each commit’s diff only reflects one leaf intention. That’s what guarantees that “commit → intention” is a total function.

If the agent absolutely must mix intentions (e.g. small opportunistic refactors), you either:

split the changes into multiple commits; or

label the commit with multiple Intent-Id trailers (less clean, but sometimes pragmatic).

3. What you gain from the Git-first approach
3.1 No separate DB as source of truth
Everything lives in Git:

intention tree (intentions.yaml)

intention→code link (commit trailers + diff)

You inherit all the nice things:

atomicity (intention + code change in one commit)

distributed replication

auditability / immutable history (modulo rebases)

3.2 Intention-aware blame “for free”
You now get a powerful primitive:

For each line in a file:

git blame → commit → parse Intent-Id → look up in intentions.yaml at that commit.

That gives:

“Who/what intention is responsible for this line?”

For a whole function or file, you can aggregate:

unique Intent-Ids,

their paths/titles,

their dates and actors.

You effectively get:

a reverse index from code to intentions without a graph DB, just by:

reading Git history,

resolving IDs.

3.3 Cross-file linking is trivial
If commits are intention-scoped:

Any doc updates, tests, config changes, etc that support the same leaf all share the same Intent-Id.

A simple git log --grep 'Intent-Id: INT-...' gives you all artefacts touched by that intention.

You can:

quickly see how an intention was implemented across code + docs.

detect when a later change touches one but not the other (e.g. later commits on the code path but no later commits on the doc path under that intention ID) and raise a “doc may be stale” warning.

3.4 Separation of concerns: Git as log, tooling as lens
You’ve now separated:

Log & source of truth → Git

Interpretation & query → tools/plugins (LLM, Neo4j, CLI, VS Code)

So other devs/agents/tools don’t need your DB to at least see intentions: they see:

intentions.yaml in the repo root

structured trailers in commits

And then richer tools can be layered on later.

4. Hard bits / design gotchas
This design is promising, but here’s where the dragons lie.

4.1 Intention tree evolution and IDs
You’ve now got two evolving things:

the code

the intention tree

Some failure modes:

you rename or restructure the tree (e.g. merge two high-level nodes)

older commits still reference the old path / semantics

Mitigations:

Make Intent-Id opaque and stable; path is derived from the tree at that point in history:

To interpret a commit’s intention, you check out that commit and read intentions.yaml at that revision.

When you need to deprecate/supersede an intention:

Don’t delete; mark it:

id: INT-2026-01-26-0003
status: superseded
superseded_by: INT-2026-02-10-0010
Queries can respect this.

That way, the semantic meaning at each commit is frozen in that commit’s version of the tree.

4.2 Rebase / squash and auditability
If people rebase/squash aggressively:

you may:

lose individual micro-commits,

end up with one big commit that mixes multiple intentions,

or merge trailing structured messages into mush.

Possible approaches:

Encourage an “intentional history” branch that you don’t squash, and a squashed main branch for humans if you care.

Or accept that rewriting history rewrites the audit trail (same as any Git-based traceability).

If this is mainly agent-driven on a protected branch, you can enforce policies:

“no merge commits without structured trailers”

“no squash merges that drop Intent-Id trailers”

4.3 Granularity & noise
Micro-commit per intention leaf is elegant, but:

you might easily get too many commits (e.g. minor edits, single-line tweaks).

this can be noisy for humans when reading git log.

Mitigations:

Provide tooling to:

collapse intention micro-commits into “intention summaries” (e.g. a script that groups commits by Intent-Id for log views),

or filter logs:

git log --format='%h %s' --grep='Intent-Id: INT-...'

Educate devs/agents to:

batch small edits per leaf until a meaningful state is reached before committing.

4.4 Commits that logically belong to multiple leaf intentions
Reality:

a single change sometimes honestly serves two intentions (e.g. refactor + bug fix).

You have three options:

Avoid it: enforce the agent to split the diff into two commits.

Multi-tag: allow multiple Intent-Id trailers:

Intent-Id: INT-2026-01-26-0003
Intent-Id: INT-2026-01-26-0007
Then your blame → intent mapping becomes line → set of intentions.

Primary/secondary roles:

Intent-Primary: INT-0003
Intent-Secondary: INT-0007
(2) is simplest; you can always show a primary/secondary in the UI based on confidence scores from the LLM.

4.5 Non-agent edits
Humans will:

commit directly via CLI/IDE

forget to tag Intent-Id,

or create entirely new intentions ad hoc.

You need a story:

At minimum, allow manual tagging:

git commit -m "..." -m "Intent-Id: INT-..."

or a CLI wrapper/alias.

For untagged commits:

treat them as Intent-Id: INT-UNCLASSIFIED-<commit-hash> and later allow an LLM or human to attach them to existing intentions (update intentions.yaml retrospectively).

5. Git as source of truth, optional graph as index
You can still have your cake and eat it:

Source of truth: Git repo (code + intentions.yaml + trailers)

Derived index for fast queries: a graph DB or SQLite

A small daemon / CLI could:

git fetch

Iterate new commits:

parse trailers to get Intent-Ids

read intentions.yaml from that commit (or nearest ancestor where it exists)

extract tree structure & node metadata

index edges:

intention ↔ commit ↔ files ↔ functions

Answer rich queries:

“Show me the intention tree for branch X”

“For file F, show all intentions that have touched it, grouped by subtree”

“Find stale intentions whose code was modified by other intentions in the last N days”

If the index is ever blown away, you can always rebuild entirely from the Git log.

6. Concrete design sketch
Just to make it very tangible, something like:

intentions.yaml at repo root, versioned

Commits look like:

feat: retry payments on Stripe 429s

Introduce retry/backoff logic in PaymentClient and add basic tests.

Intent-Id: INT-2026-01-26-0003
Intent-Path: ImprovePaymentRobustness/Handle429/AddRetryLogic
Intent-Status: implemented
Intent-Actor: agent
Agent workflow per apply-edits:

LLM updates intentions.yaml (maybe adding INT-0003, INT-0004).

Agent groups hunks by leaf ID (INT-0003, INT-0004).

For each leaf:

apply hunks

commit with trailers.

Commit intentions.yaml changes if any.

Tooling:

intent log <path/to/file> → show intention tree nodes responsible for that file, sorted by recency.

intent show INT-2026-01-26-0003 → show subtree, related commits, affected files/functions.

If you’d like, next step could be to nail down:

a precise trailer schema and

a minimal intentions.yaml format,

so you can hack a tiny CLI to prove this out on a toy repo before wiring it into Claude/code.

You said:
as an antidote to the issue where successive commits to a code block cause it to overwrite the previous intention notes, how about the following:
for every code block being edited, the agent sees the prior intentions for that block and if they are all still supported (or no longer relevant to this block), then a commit gets made which includes all of the prior intentions (that are still relevant) as well as the latest addition. 
This would enable a fast audit trail 'query' for a given code line (using blame). 
What do you think?There's another issue with the git-based storage approach which is that it would be hard to query by *intention* i.e. to find where the edits currently for a given intention OR it would be difficult to query for 'show me the longitudinal intention hierarchy of this file/repo'. Maybe we would always need an additional graph db, in which case we might as well simplify and just use a graph db?
ChatGPT said:

Thought for 12s
I think your “copy-forward intentions” idea is actually quite elegant, and it does fix the “blame only shows the last intention” problem – but it comes with some trade-offs that push you back towards “Git as source-of-truth log + graph index on top”, rather than Git instead of a graph.

Let me break it down.

1. Copying prior intentions forward on each edit
You’re proposing:

For a given code block being edited:

Look up all prior intentions relevant to that block.

Ask: “Are these still supported / still relevant for this block?”

If yes, carry them forward.

Then, create a commit whose metadata includes:

all still-relevant prior intentions, plus

the new intention(s) being realised by this edit.

So for any given line, git blame on the latest commit touching that line will show:

the full set of intentions that are supposed to be true of that code now.

That’s nice because:

Fast, local audit query: blame → commit → intention set

No additional storage system needed to answer “What’s the full intention set for this line today?”

I think that’s a very workable mental model.

Where it shines
“Current view” queries are trivial

“Why does this line exist?” → blame once → list of intentions.

You don’t need to traverse history or do any fancy joining: the latest commit holds the union of intentions.

You get a natural mechanism for dropping intentions:

If the agent/human decides an intention is no longer relevant for this block, they don’t copy it forward, so it falls out of the current intention set.

So as long as you’re mostly asking “what are the intentions as of now for this bit of code”, it’s actually a very tidy approach.

2. But… verifying “still supported” is the hard part
The subtle problem is in the line:

“if they are all still supported (or no longer relevant to this block)”

Determining that is non-trivial:

To know an intention is “still supported” you’re basically re-checking:

does the current behaviour still match the intended behaviour?

are the constraints/tests still satisfied?

To know an intention is “no longer relevant”, you’re asking:

has this behaviour been removed, moved, generalised, or superseded?

You can approximate this with an LLM given:

original intention text,

the previous code,

the new code.

…but that’s expensive and sometimes flaky. You risk:

Intention inflation
Old intentions keep being carried forward out of caution, so intention sets bloat and lose discriminative value.

Silent loss
The model/human wrongly decides something is “no longer relevant”, so an actually-important intention drops out of the audit trail for that code.

So to actually make the copy-forward scheme trustworthy, you still want:

at least a light-weight index of “which intentions have ever applied to which symbols/blocks”, so that if something looks off you can re-evaluate; and

probably some background process that periodically re-checks old intentions against the current code.

Which starts to look very graph-y.

3. Querying by intention & longitudinal history with just Git
You’ve identified the two big query types that are painful if you only use Git:

“Show me where this intention is currently realised”

You can do:

git log --grep 'Intent-Id: X' to find all commits mentioning it.

For each such commit, look at the diff to see which files/lines were touched.

That’s OK for small repos, but:

it’s O(number of commits),

it doesn’t directly tell you “where does this intention currently live?” without simulating the whole history.

“Show me the longitudinal intention hierarchy of this file/repo”

This is worse from raw Git:

You’d need to:

traverse history,

build up a timeline of intentions attached to each file/symbol,

track when intentions appear, evolve, get superseded.

This is exactly the sort of thing a graph DB or dedicated index is good at.

So yes, you can do both entirely off Git (it’s just data), but:

the query cost and complexity get high,

you end up rewriting a poor man’s graph index in your tooling anyway.

Which gets you to your question:

“Maybe we would always need an additional graph db, in which case we might as well simplify and just use a graph db?”

4. Why I’d still keep Git and a graph index
I’d separate concerns like this:

Git as the canonical log of:

code,

intention tree (e.g. intentions.yaml),

intention claims on each commit (trailers / metadata, possibly with copy-forward policy).

Graph DB (or similar) as a cached index over Git:

nodes: Intention, CodeBlock, Commit, File, ConversationTurn, etc.

edges: REALISES, TOUCHES, SUPERCEDES, MENTIONED_IN, etc.

The reasons it’s still worth having both:

Versioning & distribution
Git gives you:

offline availability,

safe branching/merging,

history tied to code.
Your graph DB won’t automatically track historical snapshots the way Git does.

Rebuildability & safety
If the graph index is purely derived from Git:

you can blow it away and rebuild any time;

no fear of divergence – Git is the single source of truth.

Operational separation

Small / local workflows (e.g. “why is this line here?”) → use blame + commit trailers (your copy-forward scheme).

Heavy / global questions (longitudinal histories, impact analysis, recommendations) → hit the graph index.

You’re not really adding conceptual complexity by having a graph – you’re acknowledging you need an efficient querying layer anyway, and designing it explicitly rather than hiding it inside ad-hoc Git scripts.

If you went graph-only and stopped encoding intentions into Git at all, you’d lose:

the nice coupling between code and intention history,

the ability for anyone with just a clone and git log to at least see what was intended,

the safety that comes from having intention info travel with the code.

5. A hybrid that matches your goals
Putting it together:

Keep the copy-forward idea for:

current-per-line intention sets,

fast, local blame-based “why is this here?” queries.

Use Git as SoT by:

storing intentions.yaml as the tree,

adding trailers with (possibly multiple) intention IDs to commits,

optionally copying forward prior intentions when editing the same block.

Maintain a graph index that is:

entirely derived from Git (no independent writes),

updated incrementally as new commits arrive,

used for:

“where is intention X live now?”

“what’s the intention history of this file/module?”

“which intentions are likely stale/conflicting?”

That way:

the UX you care about (blame → full intention set) is preserved,

you don’t lose the expressiveness and query power of a proper graph,

and you’ve kept a clean separation: Git for history, graph for querying.

If you’d like, next we can sketch a really concrete layout for:

what exactly gets copied forward into commits (e.g. Intent-Ids: [...] vs a structured Intent-Set trailer), and

how the graph indexer would look at a repository and construct the longitudinal intention hierarchy for a file.

You said:
For the "still supported" issue, what if we added two more elements: 
1. (Just as has been the software engineering practice to the present day) we ALSO store an intention trail as tests. Each of these tests is our *evidence* that a given intention is still supported.
2. The intention hierarchy should be reflected in the folder/file/named-scope naming semantic structure. One of the downstream use cases would include: every new intention should consider whether the intention hierarchy has been altered sufficiently in order to justify updating the folder/file/named-scope naming structure e.g. creating a new file to house some new branch of functionality (because it no longer fits the semantics of the original file)

Zooming out, what I'm trying to achieve here is a set of key points in the agent-coding lifecycle where specific checks and tests are carried out in order to maintain the coordination throughout the code base and through time. The intention encoding and storage allows us query for these intention links at points in the agentic-coding lifecycle and maintain strong information consistency.
ChatGPT said:

Thought for 8s
I think you’re homing in on the right abstraction: intentions as contracts that are backed by tests and reflected in structure, with the agent acting as a protocol enforcer.

Let me riff on your two additions and then zoom out into the “coordination checkpoints” you’re aiming for.

1. Tests as intention evidence
You can make “still supported” mostly non-mysterious if:

An intention is considered supported iff its associated tests pass on the current code.

So each intention leaf should be tied to one or more concrete checks:

classic unit/integration tests

property-based tests

golden-file/snapshot tests

static checks (type-checking, linters, schema validators)

possibly “observability tests” (assertions on metrics/log shape)

1.1 How to encode that linkage
A simple pattern:

Every intention has an ID: INT-2026-01-26-0003

Every test that is primarily evidence for that intention says so in metadata.

For example:

In the test name:

def test_INT_2026_01_26_0003_retries_on_429():
    ...
Or as an annotation / docstring:

@intention("INT-2026-01-26-0003")
def test_retry_on_429():
    """Intent: Payment retries on HTTP 429 from Stripe"""
Or via a small manifest:

# intentions_tests.yaml
INT-2026-01-26-0003:
  - tests/payments/test_retry_on_429.py::test_retry_on_429
Then your lifecycle rule becomes:

When an agent/human claims “this intention is implemented”:

at least one linked test must exist; and

those tests must pass in CI (and ideally locally).

When editing code that touches an intention’s scope:

The agent looks up all intentions linked to that code and pulls in their test set.

Before committing, it runs those tests (or the relevant subset) and only asserts “still supported” if they pass.

So “copy-forward prior intentions” is no longer just an LLM judgement; it’s:

“All tests linked to these intentions passed after my edit, so it’s safe to carry them forward for this block.”

You still might have some intentions that are under-tested, but the semantics of “still supported” are at least grounded in something objective.

2. Intention hierarchy reflected in structure
This is the second big lever: semantics in names and boundaries.

You can treat the intention tree as a kind of “conceptual architecture”, and assert:

The code structure (folders/files/classes/functions) should reflect the current intention hierarchy.

That implies a couple of invariants:

High-level intention branches correspond to modules / domains.

Sibling intentions often map to sibling modules / classes.

A file’s name and folder path should roughly describe the dominant intention subtree it contains.

2.1 Lifecycle rule: structure alignment check
Whenever a new intention is introduced or an existing one changes scope, the agent should ask questions like:

“Does this intention still ‘fit’ into the existing module/file?”

“Has this file become semantically overloaded? Do we need to split or rename?”

“Should we introduce a new folder/file to reflect this branch in the hierarchy?”

Concretely:

For a new leaf intention:

The agent finds candidate homes based on:

existing intentions with similar semantics,

file/folder names,

call graph locality.

If no good home exists, it proposes a new module/file with a name derived from the intention path.

For a file whose intention set has drifted:

It might:

propose renaming the file/folder,

or splitting it along intention boundaries.

This gives you:

a feedback loop where intentions drive architecture, not just comment strings;

a mechanism for preventing God files where heterogeneous intentions accumulate over time.

3. Zoomed-out: intention-aware coordination checkpoints
You said:

“a set of key points in the agent-coding lifecycle where specific checks and tests are carried out in order to maintain the coordination throughout the code base and through time.”

Let’s make that explicit. Imagine an “intention-aware agent” with these checkpoints:

3.1 When a new goal appears (user message)
Create/update intention tree:

parse the conversation and update intentions.yaml (or your in-repo structure),

locate where in the existing hierarchy this sits,

tag it with an ID.

Structure check:

ask: does this new leaf sit comfortably in existing folders/files?

if not, plan structural changes as part of the work (new file/module, rename, etc.).

3.2 Planning phase
For each leaf intention to implement now:

Identify candidate code locations (files/symbols) and tests:

existing tests that already serve as evidence,

gaps where tests don’t exist yet.

Produce a plan triple:

Intention: INT-... (NL description)
Code targets: [list of files / functions]
Evidence tests: [existing tests] + [tests we will add]
If there are no tests yet, the plan includes “write tests X, Y”.

3.3 Editing phase
Before applying edits to a code block:

Pull in the block’s current intention set:

from blame + commit metadata, plus tree context.

Guardrail:

the agent must treat these as constraints:

“Whatever I do, I must not violate these intentions unless I explicitly retire/supersede them.”

I.e. the agent isn’t just doing “change code to satisfy new intention”, it’s doing:

“Change code so that (existing intention set ∪ new intentions) still holds, as evidenced by tests.”

If that’s impossible, it must:

mark some intention as deprecated/superseded in the tree; and

adjust tests accordingly.

3.4 Pre-commit checkpoint
Before committing:

Test checkpoint:

run:

tests linked to any intention touched by this edit,

plus tests for the new intention.

if they fail:

either fix,

or explicitly annotate the intention as regressed / under change.

Intention metadata update:

update the tree with:

statuses (planned → implemented),

structural changes (if we moved folders/files to reflect new hierarchy),

“supported by tests” lists.

Commit metadata:

commit message trailers include:

the per-block intention sets being carried forward (for quick blame),

any intentions newly added or deprecated.

At this point, your “copy-forward” logic is backed by real evidence: you only copy forward an intention into the commit’s intentional set for a block if its evidence tests passed.

3.5 Background / longitudinal maintenance
Periodically, or on certain events (e.g. big refactor, release):

Run intention health checks:

For each intention:

Do its tests still exist and pass?

Have its associated code locations drifted?

For each file/module:

Has its dominant intention subtree changed enough that its name/placement is misleading?

This maintains the longitudinal consistency you care about.

4. Does this reduce the need for a graph DB?
It changes what the graph is for.

With:

tests as evidence; and

intention hierarchy reflected in structure;

you can answer many local questions with just:

code,

tests,

intentions.yaml,

blame.

But for global and longitudinal questions (“show the intention history of this repo/file”, “find all currently-live code for intention X”, “where are top-level intention branches most entangled?”), a graph index is still useful.

The difference is:

The graph DB becomes a derived coordination index, not the primary home of business logic:

nodes: Intentions, Tests, Files, Functions, Commits

edges: EVIDENCED_BY, TOUCHES, SUPERCEDES, HOUSE_IN_STRUCTURE, etc.

It can be rebuilt from:

Git history (commits + trailers),

intentions.yaml,

test metadata.

So you haven’t over-complicated your storage story:

Git + files = canonical representation of code, intentions, and evidence.

Graph = acceleration structure that lets you ask rich coordination questions efficiently.

5. Where this gets really interesting
Once you have:

intention tree,

test linkage,

structure linkage,

you can start having the agent do genuinely coordination-heavy things:

Before adding a new feature, it can:

scan the intention tree and say “this is really just a sub-case of INT-XYZ, maybe extend that instead of proliferating a new branch”.

Before renaming a module, it can:

check which intentions conceptually live there and whether the new name still matches.

Before deleting a test, it can:

check which intentions lose evidence and ask for explicit approval or replacement tests.

Basically: you get a protocol where the agent is not just “editing code that passes local tests”, but “maintaining a long-lived, intention-aware contract between code, tests, and structure”.

If you’d like to take this further, a good next move would be to:

define a minimal schema for an intention (ID, NL description, linked tests, linked modules), and

sketch the exact annotations in tests and commit messages

so you could try a tiny prototype in a toy repo and see how it feels in practice.




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info. See Cookie Preferences.
