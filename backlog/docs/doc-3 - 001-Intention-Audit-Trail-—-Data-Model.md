---
id: doc-3
title: 001 Intention Audit Trail — Data Model
type: spec
created_date: '2026-06-02 12:09'
---


# Data Model: Intention Audit Trail MVP

**Date**: 2026-01-27  
**Spec**: `specs/main/spec.md`

## Entities

### Intention
Represents a goal/functionality/implementation/tests/docs node in the intention tree.

**Fields**
- `id` (string, stable): `INT-YYYY-MM-DD-NNNN`
- `title` (string)
- `kind` (enum): `goal | functionality | implementation | tests | docs | observability`
- `status` (enum): `planned | in_progress | implemented | superseded | deprecated`
- `children` (array[Intention])
- `created_at` (optional ISO timestamp)
- `rationale` (optional string)
- `constraints` (optional string or array[string])
- `superseded_by` (optional `id`)

**Linkage fields**
- `evidence_tests` (optional array[string]): test selectors (e.g. `tests/x.py::test_y`)
- `supporting_docs` (optional array[string]): doc paths with anchors (e.g. `docs/x.md#section`)

**Structure alignment fields (functionality nodes)**
- `code_home` (optional array[string]): repo-relative path prefixes that define the module boundary for this functionality.
- `named_scopes` (optional array[string]): naming conventions for classes/modules/symbol prefixes (future).

### CommitPlan
Planner output used by the stop hook to validate and deterministically produce commits.

**Fields**
- `version` (number): `1`
- `ready` (boolean)
- `diff_base` (string): e.g. `HEAD`
- `diff_hash` (string): normalized hash for the diff the plan was built for
- `commits` (array[CommitEntry])

### CommitEntry
Represents a single intention-scoped commit the stop hook will create.

**Fields**
- `intent_id` (string): leaf intention to realize
- `intent_path` (string, optional): derived human path
- `functionality_intent_id` (string): closest `kind:functionality` ancestor
- `functionality_intent_path` (string, optional)
- `subject` (string)
- `body` (string, optional)
- `intent_confidence` (number, optional)
- `evidence_tests` (array[string], optional)
- `supporting_docs` (array[string], optional)
- `patch` (string): unified diff that applies cleanly

### SessionRecord
Committed audit record for a session, normalized and safe to keep in-repo.

**Fields**
- `session_id` (string)
- `timestamp` (ISO string)
- `transcript_ref` (string): hash/identifier for the underlying transcript (not necessarily a path)
- `diff_base` (string)
- `diff_hash` (string)
- `planner_tool` (string): MCP tool name + version
- `intentions_touched` (array[string]): intention IDs referenced
- `mapping_summary` (object): counts + mapping overview
- `notes` (optional): any unresolved ambiguity or overrides used

### EvidenceTestLink (logical relation)
Relationship of intention → tests (may be embedded in `intentions.yaml`, in plan entries, and/or duplicated into commit trailers).

### SupportingDocLink (logical relation)
Relationship of intention → docs (may be embedded in `intentions.yaml`, in plan entries, and/or duplicated into commit trailers).

## Integrity rules (MVP)
- Each `CommitPlan` must cover 100% of diff hunks exactly once (via `patch` union).
- Every `CommitEntry.intent_id` must exist in `intentions.yaml`.
- Every `CommitEntry` must have a valid `functionality_intent_id` that exists and is `kind:functionality`.
- If evidence execution is enabled, impacted `evidence_tests` must pass before stop/commit.
- Patches must remain within `code_home` for their functionality intention unless a structure fix/override is recorded.

## Output Serialization

### intentions.yaml Structure

```yaml
root:
  id: INT-2026-01-30-0001
  title: "Add user authentication"
  kind: goal
  status: implemented
  children:
    - id: INT-2026-01-30-0002
      title: "Login functionality"
      kind: functionality
      status: implemented
      code_home:
        - src/auth/
      children:
        - id: INT-2026-01-30-0003
          title: "Create login endpoint"
          kind: implementation
          status: implemented
          # Commits should reference THIS level (leaf implementation)
```

### commit_plan.yaml Structure (MVP: file-scoped)

```yaml
version: 1
ready: true
diff_base: HEAD
diff_hash: "abc123def456..."
commits:
  - intent_id: INT-2026-01-30-0003  # Reference LEAF intention
    functionality_intent_id: INT-2026-01-30-0002
    intent_path: "Add user authentication/Login functionality/Create login endpoint"
    subject: "feat(auth): add login endpoint"
    body: "Implement POST /auth/login with JWT token generation"
    files:
      - src/auth/login.py
      - src/auth/jwt.py
```

### Leaf Intention Rule

Commit entries MUST reference leaf-level intentions (`kind: implementation`, `tests`, `docs`).
Goal and functionality intentions are for hierarchy only - they provide context but should not be directly referenced in commit `intent_id` fields.

**Hierarchy levels:**
- `goal` - High-level objective (root of tree)
- `functionality` - Domain feature (has `code_home`, provides structure)
- `implementation` - Technical work (**reference this in commits**)
- `tests` - Test additions (**reference this in commits**)
- `docs` - Documentation changes (**reference this in commits**)
- `observability` - Logging/metrics (**reference this in commits**)

