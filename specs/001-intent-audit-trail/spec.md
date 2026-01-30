# Feature Specification: Intention Audit Trail MVP (Stop Hook + MCP Planner)

**Feature Branch**: `[main]`  
**Created**: 2026-01-27  
**Status**: Draft  
**Input**: User description: "Build an intention audit trail / consistency-engine enforced by a Claude Code Stop hook that blocks until the agent (via an MCP planner tool) produces intention metadata, evidence/docs links, and an intention-scoped commit plan."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Intention-scoped auto-commit gate (Priority: P1)

As a user, I want the agent to be unable to stop with uncommitted changes unless every edit is mapped to an intention leaf (and commit plan exists), so that every change is traceable by intention over time.

**Why this priority**: This is the core enforcement loop; without it, the audit trail is optional and will drift.

**Independent Test**: Make an edit, try to stop; confirm the stop gate blocks until a complete plan exists, then commits are created with intention trailers.

**Acceptance Scenarios**:
1. **Given** a repo with the stop hook enabled and an uncommitted change, **When** the agent attempts to stop, **Then** the stop hook blocks and instructs the agent to call the MCP planner tool and produce required artifacts.
2. **Given** a complete `.intent_audit/commit_plan.yaml` covering all diff hunks, **When** the agent attempts to stop, **Then** the hook executes the plan and produces one or more commits with `Intent-Id` trailers.

---

### User Story 2 - Evidence regression surfaces intention context (Priority: P1)

As a user, when a linked evidence test fails at stop time, I want the tool to surface the intention-linked code/docs/tests so the agent can either restore support or explicitly supersede/retire the intention.

**Why this priority**: This demonstrates the “consistency-checking” capability beyond bookkeeping.

**Independent Test**: Establish baseline intention + evidence test + doc; introduce a breaking change; confirm the stop gate blocks and reports intention context.

**Acceptance Scenarios**:
1. **Given** an intention with linked evidence test(s), **When** a code change breaks the evidence, **Then** the stop hook blocks and prints an “intention failure context” report linking failed tests → intention → docs/code scope.
2. **Given** the agent fixes code (or supersedes the intention and updates evidence/docs), **When** the agent attempts to stop again, **Then** the stop gate passes and commits are produced with the updated intention metadata.

---

### User Story 3 - Functionality-driven structure alignment (Priority: P2)

As a user, I want functionality intentions (domain semantics) to define module boundaries so that folder/file/named-scope meaning stays aligned with the intention hierarchy.

**Why this priority**: Prevents long-lived semantic drift (DDD alignment).

**Independent Test**: Produce a commit plan whose patch touches files outside the owning functionality `code_home`; verify the stop hook blocks with a structural alignment message.

**Acceptance Scenarios**:
1. **Given** a functionality intention node with `code_home: ["src/payments/"]`, **When** a planned patch under that functionality touches `src/other_domain/...`, **Then** the stop hook blocks until the plan includes a move/rename/split or an explicit override rationale.

---

### Edge Cases
- What happens when edits cannot be cleanly assigned to a single intention (multi-intent hunk)?
- What happens when a test is deleted but still referenced as evidence?
- What happens when docs are missing for a behavior-changing intention?
- What happens when repo is not a Git repo (no trailers/blame)?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST maintain a canonical intention tree in `intentions.yaml` with stable IDs.
- **FR-002**: System MUST block stopping when there are uncommitted changes and no complete intention→edit mapping exists.
- **FR-003**: System MUST generate/consume a patch-level commit plan (`.intent_audit/commit_plan.yaml`) that covers 100% of diff hunks exactly once.
- **FR-004**: System MUST encode intention metadata into commit messages via trailers (at least `Intent-Id`).
- **FR-005**: System MUST link evidence tests to intentions (either on intention nodes and/or in the commit plan/trailers).
- **FR-006**: System MUST link supporting docs to intentions that affect externally-relevant behavior (or record a rationale for no docs).
- **FR-007**: System MUST distinguish functionality intentions vs implementation intentions; structure alignment checks MUST be based on functionality intentions’ module boundaries.
- **FR-008**: When evidence execution is enabled, system MUST block stopping if impacted evidence tests fail and MUST surface intention-linked context to support repair vs supersede decisions.

### Key Entities *(include if feature involves data)*
- **Intention**: `id`, `title`, `kind`, `status`, links to evidence/docs, hierarchy.
- **CommitPlan**: list of intention-scoped commits including patches and metadata.
- **SessionRecord**: normalized audit record for a session (trajectory hash, diff hash, mapping summary).
- **EvidenceTestLink**: mapping from intention IDs to test selectors.
- **SupportingDocLink**: mapping from intention IDs to doc paths/anchors.

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: For any non-empty working diff, the agent cannot stop unless 100% of hunks are mapped to intention commits.
- **SC-002**: Produced commits contain `Intent-Id` trailers and can be traced via `git blame` to `intentions.yaml` at the blamed commit.
- **SC-003**: In the demo regression scenario, a failing evidence test blocks stopping and surfaces intention-linked code/docs/test context sufficient to decide “repair vs supersede”.
- **SC-004**: Structure alignment check blocks cross-domain patches unless structure changes or explicit override is recorded.

