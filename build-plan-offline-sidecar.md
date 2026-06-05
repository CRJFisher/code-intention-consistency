# Build Plan — Offline Side-Agent Architecture

Companion to [architecture.html](architecture.html). This plan turns the proposed architecture into an ordered, dependency-aware implementation sequence. No code is written yet; this is the plan to execute against.

## Locked decisions

- **Soft Stop gate.** The `Stop` hook never hard-blocks a coverage gap. It is an _opportunistic committer_: if fresh artifacts exist for the current `diff_hash`, it commits with `Intent-Id` trailers; otherwise it exits cleanly and lets `SessionEnd` reconcile. The user is never made to wait on analysis or retry a stop.
- **Writes are offline.** All intention analysis and persistence run in a detached `claude-agent-sdk` subprocess triggered fire-and-forget. The session is never blocked by LLM work.
- **One inline read.** `UserPromptSubmit` injects the relevant historical intention slice so the agent can FLAG / REFINE / PASS-THROUGH. No LLM, no MCP, `decision` always `allow`.
- **The writer is the sole author of commits.** A `PreToolUse` guard denies manual commit-creating Bash commands so every commit carries `Intent-Id` trailers and the Stop / SessionEnd committer always has uncommitted changes to own. Without this, manual commits leave a clean tree (nothing to commit) and trailer-less holes in the audit trail.
- **Durable audit = git trailers.** `.intent_audit/` is a rebuildable cache, gitignored in target repos.
- **No surplus, no shims.** The 11 analysis/research tools are deleted, not adapted. Their logic, if ever wanted, returns as config-gated phases inside the single offline writer.

## Soft-gate semantics (definitive)

On `Stop`, the gate recomputes `diff_hash` (reuse `stop_hook._compute_diff_hash`) and reads `run-manifest.json` for that hash:

| State                                    | Action                                                                                                       | Blocks? |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------- |
| Manifest complete + fresh                | Stage hunks per `commit_plan.yaml`, build trailers via `commit_builder.build_commit_message`, commit, exit 0 | No      |
| In-flight (lock held / partial manifest) | Exit 0, emit one transcript line: "intention audit in progress — will reconcile at session end"              | No      |
| Missing (writer not yet run / crashed)   | Exit 0, emit one transcript line: "intention audit pending"                                                  | No      |

`SessionEnd` is the guaranteed reconciliation point: it forces a final writer run on the stable working tree and that run creates any commits the Stop gate left pending. Committing only happens at `Stop` (when the writer kept up) or at `SessionEnd` (catch-up) — never from a mid-session background process that could race the working tree.

This whole scheme depends on one invariant: **the working tree still holds the changes at gate time.** The commit guard (M5b) enforces it by denying manual commits. Deploy the guard _only_ once the committer (M5) exists — a guard shipped alone would block every commit with nothing to commit them.

## Component layout

**Add (product hooks → install to target repos under `.claude/hooks/`):**

- `inject_intent.py` — UserPromptSubmit read-injector
- `commit_guard.py` — PreToolUse (Bash) guard denying manual commit-creating commands
- `writer_launcher.py` — PostToolBatch + SessionEnd trigger shim (non-LLM)

**Add (offline brain):**

- `src/intention_audit/sidecar/writer_agent.py` — detached SDK orchestrator + run-manifest
- `src/intention_audit/sidecar/manifest.py` — run-manifest read/write/checkpoint
- `src/intention_audit/sidecar/wal.py` — write-ahead log + debounce/lock helpers
- the `writer_agent` system prompt (5 phases in one pass)

**Rewrite:**

- `src/intention_audit/hooks/stop_hook.py` — down to the soft opportunistic-committer gate

**Demote (strip decision/gating logic → persist-only):**

- `mcp_servers/intention_audit/tools/{save_intentions,save_commit_plan,run_evidence_tests,save_structure_validation,save_session_record}.py`

**Delete (tools + matching agent specs):**

- tools: `cluster_commits`, `extract_implementation_requirements`, `synthesize_user_requirements`, `verify_intention_tree`, `verify_intention_plan`, `generate_alignment_report`, `compute_drift_score`, `analyze_hunk_intents`, `get_tiered_context`, `validate_confidence`
- agents: `intent-verifier`, `confidence-validator`, `drift-monitor`, `tangle-analyzer`, `alignment-reporter`, `context-manager`, `plan-verifier`, `commit-searcher`, `code-reviewer`, `intent-writer` (and the 5 phase agents fold into the writer prompt)

## Milestones (ordered)

### M1 — Inline read-injection ⭐ first demonstrable slice

**Independent of everything else** — ship and demo this alone.

- Add `inject_intent.py` (UserPromptSubmit).
- Region inference: reuse `stop_hook._get_relevant_changed_paths` / `_parse_porcelain_v1_z` against `git status --porcelain`.
- File→intent index: stream `intentions.yaml`, build `file→[intent_id]` + `intent_id→record`; rebuild only when the file mtime changes (module-level cache).
- Resolve changed files to candidate intents via `structure.boundary._path_within_prefixes` against each node's `code_home`.
- Assemble slice = target node(s) + ancestors-to-root + (optional) last-N `Intent-Id` trailers as a history hint.
- Return `hookSpecificOutput.additionalContext` = slice + the FLAG / REFINE / PASS-THROUGH instruction. If >10k chars, spill to `.intent_audit/<region_hash>.slice.yaml` and inject path + 1-line summary. `decision` always `allow`; any error → empty context + stderr log, never block.
- **Done when:** editing a file under a known `code_home` and submitting a prompt shows the intention slice + guidance in context; an unmapped file injects nothing and never blocks; a malformed `intentions.yaml` degrades silently.

### M2 — Demote the 5 surviving MCP tools to persist-only

Depends on: nothing. Do in parallel with M1.

- Strip any gating/decision logic; keep atomic temp+rename writes + minimal model parse via existing `models/`.
- Each tool: validate schema → write artifact under `<session_id>/<diff_hash>/`. Nothing else.
- **Done when:** each tool is a thin writer with unit tests asserting atomic write + schema validation only.

### M3 — Offline writer (one pass)

Depends on: M2.

- `writer_agent.py`: acquire per-session `.lock`, compute `diff_hash` (reuse `_compute_diff_hash`), read `run-manifest.json` → exit if complete (idempotent).
- Otherwise run 5 phases sequentially in one SDK pass — map → plan → evidence (`pytest`) → structure (`check_code_home_boundaries`) → record — each calling its persist tool and checkpointing into `run-manifest.json`.
- Conservative writes: new nodes get new IDs; existing nodes field-merged (status/links/supersede) only, never deleted. Writes only under `.intent_audit/`; never touch the working tree. Crash → release lock, leave partial manifest for idempotent resume.
- **Test directly first** (invoke as a plain subprocess on a sample repo) before wiring any hook.
- **Done when:** running the writer twice on the same diff is idempotent; a kill mid-phase resumes cleanly on re-run; the working tree is provably untouched.

### M4 — Writer launcher (triggers)

Depends on: M3.

- `writer_launcher.py` wired to `PostToolBatch` (matcher Edit|Write) + `SessionEnd`.
- PostToolBatch: append batch to `wal.jsonl`, (re)arm 2s debounce, spawn detached writer when window elapses and no run is in-flight for the `diff_hash`. Return instantly.
- SessionEnd: force WAL flush + spawn, bounded-wait for in-flight runs to drain (hard timeout so teardown never hangs).
- **Done when:** rapid successive edits coalesce into one writer run (debounce works); no zombie/orphan subprocesses; SessionEnd always returns within its timeout.

### M5 — Soft Stop gate

Depends on: M3 (run-manifest), M2 (commit plan artifact).

- Rewrite `stop_hook.py` to the soft semantics table above, reusing `commit_builder.build_commit_message` and `reporting/failure_context` + `structure_renderer` for any surfaced detail.
- Delete the entire 5-phase spawn orchestration.
- **Done when:** fresh artifacts → commits with correct `Intent-Id`/`Intent-Path` trailers; in-flight/missing → exits 0 with a one-line note, never blocks; gate runtime <1s (no pytest, no LLM).

### M5b — Manual-commit guard (PreToolUse)

Depends on: M5 (must ship together — the guard without a committer blocks all commits).

- Add `commit_guard.py` wired to `PreToolUse`, matcher `Bash`.
- Inspect `tool_input.command`; deny when it creates a commit. MVP set: `git commit`, `git commit-tree`. Hardened set (recommended): also `git merge`, `git rebase`, `git cherry-pick`, `git revert`, `git pull` (can create a merge commit), `git am`. Match across `&&` / `;` chains and `git -C <path> …` forms.
- On match: `permissionDecision: "deny"` with a redirect reason — "Commits are owned by the intention-audit writer and stamped with Intent-Id trailers. Leave changes uncommitted; they commit automatically at stop / session end." Otherwise `allow`.
- Best-effort, not a sandbox: an agent that writes then executes a shell script can still slip a commit through. Document the limitation; catch the direct invocations that matter in practice.
- **Done when:** `git commit -m …`, chained (`x && git commit …`), and `git -C . commit …` are denied with the redirect message; non-commit git commands (`status`, `diff`, `add`, `log`) pass; deploying without M5 is explicitly prevented (guard + committer ship as one change).

### M6 — Delete the cut surface

Depends on: M5 stable.

- Remove the 11 analysis/research tools + their agent specs and registrations in `mcp_servers/intention_audit/server.py`. No shims, no deprecated re-exports.
- Fold any still-wanted logic into config-gated sections of the writer prompt.
- **Done when:** `server.py` registers exactly the 5 persist tools; no dangling imports; tests green.

### M7 — Tests + docs

Depends on: M1–M6.

- Replace 5-phase blocking-loop e2e scenarios with: (a) read-injection slice assertions, (b) writer idempotency/crash-resume, (c) the three soft-gate outcomes.
- Add store artifacts (`.lock`, `wal.jsonl`, `side_agent.log`, `run-manifest.json`) and confirm `.intent_audit/` is gitignored in target repos.
- Update `CLAUDE.md` Hook Architecture to this design (canonical, present-tense).

## Dependency graph

```text
M1 (read-injection) ─────────────────────────────────► demo-able alone
M2 (demote tools) ──► M3 (writer) ──► M4 (launcher)
                          └────────► M5 (soft gate) ──┬─ M5b (commit guard, ships with M5)
                                                      └─► M6 (delete) ──► M7 (tests/docs)
```

Critical path: **M2 → M3 → M5(+M5b) → M6 → M7**. M1 and M4 parallelize off the path. M5b ships in the same change as M5.

## Test strategy

- **Unit:** persist tools (atomic write + schema); manifest checkpoint/resume; WAL debounce/lock; region inference + slice assembly; soft-gate outcome selection; commit-guard command matching (deny commit forms incl. chained / `-C`; allow status/diff/add/log).
- **Integration (no hook):** writer run on each `tests/fixtures/sample_repos/*` — idempotency, crash-resume, working-tree-untouched.
- **E2E (hook-driven):** read-injection visible in context; soft-gate commit-fresh / pass-in-flight / pass-missing; SessionEnd reconciliation creates the catch-up commit.

## Deferred (YAGNI — re-add only if a real need appears)

- Hard-enforcement Stop mode (thin ledger block) — explicitly _not_ built, per the soft-gate decision.
- `FileChanged`-driven index invalidation — mtime-keyed lazy rebuild in `inject_intent.py` is sufficient for MVP.
- Research passes (drift / tangle / alignment / confidence / tiered-context) — config-gated writer sections only if requested.
- Bootstrap mining of pre-existing repos — separate effort; not on the core loop.
