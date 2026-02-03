# Visual Reference Guide: Intent Inference History & Architecture

A diagram-heavy companion to [learning-01-historical-journey.md](learning-01-historical-journey.md). **Minimal prose—maximum visualization.**

---

## 1. Historical Timeline

```mermaid
timeline
    title Intent Inference: Historical Journey
    section Symbolic Era
        1986 : Kautz & Allen
             : Plan Recognition as Abduction
    section Intentional Programming
        1990s : Simonyi
              : Intentional Programming
              : (1.7M+ nodes @ Microsoft)
    section Mining Era
        2000s : Jun Hong - Goal Graphs
              : Software Change Intent Taxonomies
              : (bug fix / feature / refactor)
    section Tangled Commits
        2015 : Dias et al.
             : EpiceaUntangler
             : Tangled Commit Detection
    section LLM Revolution
        2023+ : LLMCC (+33% F1)
              : Intention-based Code Refinement
              : Multimodal Context Engineering
    section Neuro-Symbolic
        Now : Why Layer + Audit Trails
            : Repository Planning Graphs
            : Persistent Intention Memory
```

---

## 2. The Modern Intent Stack

```mermaid
block-beta
    columns 1
    block:governance["5. GOVERNANCE LAYER"]
        g1["Audit Queries"]
        g2["Compliance"]
        g3["Drift Alerts"]
    end
    block:whylayer["4. WHY LAYER"]
        w1["Rationale Mining"]
        w2["Traceability"]
        w3["Intent Memory"]
    end
    block:planning["3. PLANNING SUBSTRATE"]
        p1["HTN Decomposition"]
        p2["RPG Graphs"]
        p3["Commit Plans"]
    end
    block:goals["2. HIERARCHICAL GOAL MODELING"]
        h1["Intention Trees"]
        h2["Task Networks"]
        h3["Plan Repair"]
    end
    block:inference["1. INTENT INFERENCE"]
        i1["NL Prompts"]
        i2["IDE Telemetry"]
        i3["Code Context"]
    end
```

---

## 3. Planning Formalism Comparison

| Feature | Chain-of-Thought (CoT) | Hierarchical Task Network (HTN) | Repository Planning Graph (RPG) |
|---------|------------------------|----------------------------------|----------------------------------|
| **Structure** | Linear text sequence | Tree of Tasks + Methods | DAG of code units |
| **State Tracking** | Implicit (in history) | Explicit (tree state, preconditions) | Explicit (node completion) |
| **Dependency Mgmt** | Weak (hallucinated refs) | Strong (preconditions) | Strong (topological sort) |
| **Scalability** | Low (< 5k LOC) | Medium (task complexity limits) | High (> 30k LOC) |
| **Recovery** | Restart often required | Backtracking / plan repair | Granular node re-generation |
| **Best For** | Simple tasks, explanations | Multi-step procedures | Repository-scale generation |

---

## 4. Research-to-Implementation Mapping

| Research Concept | This Project's Implementation | Artifact |
|-----------------|------------------------------|----------|
| Intention tree / hierarchical goals | `Intention` model with `IntentionKind` enum | `intentions.yaml` |
| Commit intent attribution | Commit entries with `intent_id` + trailers | `commit_plan.yaml` |
| Rationale capture | `rationale` field + `supporting_docs` | Intention nodes |
| Evidence of intent holding | `evidence_tests` selectors | `evidence_results.json` |
| Structural alignment / drift | `code_home` boundary checking | `structure_validation.json` |
| Session trace / audit | Normalized session records | `session_record.json` |
| Plan repair | Stop hook blocking + sub-agent spawning | `stop_hook.py` |

---

## 5. Project Pipeline Flowchart

```mermaid
flowchart TD
    A[User makes changes] --> B{intentions.yaml?}
    B -->|missing| C["🤖 intention-mapper<br/>sub-agent"]
    C --> B
    B -->|exists| D{commit_plan.yaml?}
    D -->|missing| E["🤖 commit-planner<br/>sub-agent"]
    E --> D
    D -->|exists| F{evidence_results.json?}
    F -->|missing/failed| G["🤖 evidence-checker<br/>sub-agent"]
    G --> F
    F -->|passed| H{structure_validation.json?}
    H -->|missing/violated| I["🤖 structure-validator<br/>sub-agent"]
    I --> H
    H -->|passed| J{session_record.json?}
    J -->|missing| K["🤖 session-recorder<br/>sub-agent"]
    K --> J
    J -->|exists| L[Execute Commits<br/>with Intent-Id trailers]

    style A fill:#e1f5fe
    style L fill:#c8e6c9
    style C fill:#fff3e0
    style E fill:#fff3e0
    style G fill:#fff3e0
    style I fill:#fff3e0
    style K fill:#fff3e0
```

---

## 6. Intent Hierarchy Visualization

```mermaid
graph TD
    G["🎯 GOAL<br/>Implement Feature X"]
    G --> F1["📦 FUNCTIONALITY<br/>Backend API"]
    G --> F2["📦 FUNCTIONALITY<br/>Database Layer"]

    F1 --> I1["⚙️ IMPLEMENTATION<br/>endpoint handler"]
    F1 --> T1["🧪 TESTS<br/>API integration tests"]

    F2 --> I2["⚙️ IMPLEMENTATION<br/>migration script"]
    F2 --> D1["📄 DOCS<br/>schema documentation"]

    style G fill:#ffeb3b
    style F1 fill:#4fc3f7
    style F2 fill:#4fc3f7
    style I1 fill:#81c784
    style I2 fill:#81c784
    style T1 fill:#ba68c8
    style D1 fill:#ff8a65
```

**IntentionKind enum values:**
- `goal` — Top-level objective
- `functionality` — Cohesive capability (has `code_home`)
- `implementation` — Code changes
- `tests` — Test code
- `docs` — Documentation
- `observability` — Logging/metrics

---

## 7. HTN Decomposition Example

```mermaid
graph TD
    T1["🎯 Create Microservice<br/>(compound task)"]
    T1 --> T2["📋 Define API<br/>(compound)"]
    T1 --> T3["⚙️ Implement Controller<br/>(compound)"]
    T1 --> T4["🧪 Write Tests<br/>(compound)"]

    T2 --> A1["✏️ Write OpenAPI spec<br/>(primitive)"]
    T2 --> A2["✏️ Generate client stubs<br/>(primitive)"]

    T3 --> A3["✏️ Create route handlers<br/>(primitive)"]
    T3 --> A4["✏️ Add middleware<br/>(primitive)"]

    T4 --> A5["✏️ Unit tests<br/>(primitive)"]
    T4 --> A6["✏️ Integration tests<br/>(primitive)"]

    style T1 fill:#ffeb3b
    style T2 fill:#4fc3f7
    style T3 fill:#4fc3f7
    style T4 fill:#4fc3f7
    style A1 fill:#81c784
    style A2 fill:#81c784
    style A3 fill:#81c784
    style A4 fill:#81c784
    style A5 fill:#81c784
    style A6 fill:#81c784
```

**HTN concepts:**
- **Compound task** — Decomposes into subtasks via *methods*
- **Primitive task** — Directly executable action
- **Method** — Recipe for decomposition (preconditions + subtasks)

---

## 8. Repository Planning Graph (RPG) Structure

```mermaid
graph TD
    subgraph "RPG Node Types"
        D["📁 Directory Node<br/>(high-level module)"]
        F["📄 File Node<br/>(compilation unit)"]
        C["🔧 Class/Function Node<br/>(logical unit)"]
    end

    subgraph "RPG Edge Types"
        E1["Composition Edge<br/>(containment)"]
        E2["Dependency Edge<br/>(imports/calls)"]
    end

    D -->|contains| F
    F -->|contains| C
    C -.->|depends on| C
```

**RPG enables:**
- Topological generation (dependencies first)
- Modular context loading (only relevant subgraph)
- Scalability to 36k+ LOC (vs ~3.5k for flat context)

---

## 9. Telemetry → Cognitive State → Agent Action

| Telemetry Signal | Cognitive State | Developer Intent | Agent Action |
|-----------------|-----------------|------------------|--------------|
| Rapid typing, linear cursor, minimal backspace | **Flow / Execution** | Implementing known logic | **Suppress** interruptions |
| Long pauses, frequent scrolling, hovering | **Uncertainty / Recall** | API discovery, context recall | **Trigger** docs/explanation |
| Source↔Test↔Terminal oscillation | **Validation / Debug** | TDD cycle, fixing regressions | **Trigger** test helper |
| High deletions, block selections, renames | **Restructuring / Refactor** | Removing tech debt | **Suppress** generation, suggest refactors |

---

## 10. Key Papers Reference

| Year | Authors/Title | Contribution |
|------|---------------|--------------|
| 1986 | Kautz & Allen | Plan recognition as abduction |
| 1990s | Simonyi (Microsoft) | Intentional Programming |
| 2000s | Jun Hong | Goal graphs for SW engineering |
| 2015 | Dias et al. | EpiceaUntangler (tangled commits) |
| 2021 | Al-Safwan & Servant | Rationale decomposition (15 fields) |
| 2023 | LLMCC | +33% F1 on commit intent classification |
| 2024 | ZeroRepo/RPG | 36k+ LOC coherent generation |
| 2024 | DRMiner | LLM-based rationale extraction |
| 2024 | Atomizer | LLM-driven commit untangling |

---

## 11. Glossary Quick-Reference

| Term | Definition |
|------|------------|
| **Intent detection** | Infer what the developer wants (from NL + context) |
| **Plan recognition** | Infer the plan structure explaining observed actions |
| **HTN** | Hierarchical Task Network — goal decomposition formalism |
| **Intention tree** | Persistent hierarchical representation of goals + execution state |
| **RPG** | Repository Planning Graph — DAG of code units for scalable generation |
| **Why Layer** | Auditable rationale linking code → intentions → evidence → decisions |
| **Drift detection** | Detect divergence between intended design and actual implementation |
| **Tangled commit** | Single commit bundling multiple unrelated changes |
| **Code home** | Declared path prefixes where a functionality's code must reside |
| **Evidence test** | Test selector proving an intention is satisfied |

---

## 12. Artifact Directory Structure

```
.intent_audit/
└── <session_id>/
    └── <diff_hash>/
        ├── intentions.yaml          # Intention tree
        ├── commit_plan.yaml         # File→intent mapping
        ├── evidence_results.json    # Test run results
        ├── structure_validation.json # code_home checks
        └── session_record.json      # Audit trail
```

---

## See Also

- [learning-01-historical-journey.md](learning-01-historical-journey.md) — Prose-based historical narrative
- [02-fundamental-gemini-intent-hierarchy.md](02-fundamental-gemini-intent-hierarchy.md) — Full Gemini research synthesis
- [02-fundamental-chatgpt-intent-inference.pdf](02-fundamental-chatgpt-intent-inference.pdf) — ChatGPT research lineage
- [synthesis-02-applicable-patterns.md](synthesis-02-applicable-patterns.md) — Patterns mapped to architecture
