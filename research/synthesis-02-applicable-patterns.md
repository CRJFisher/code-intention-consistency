# Synthesis: Applicable Patterns for Intention Audit Trail

This document synthesizes research findings from the literature review and focused research paper to identify patterns directly applicable to the Intention Audit Trail project.

## Executive Summary

The research identifies six major pattern categories with direct applicability to our 5-phase hook architecture:

1. **Intention Tree Data Structures** - Core architecture for linking edits to hierarchies
2. **LLM Intent Detection Techniques** - Enhance sub-agent reasoning
3. **Code-Edit Traceability** - Validate edits match stated intentions
4. **Multi-Agent Coordination** - Validates our pipeline architecture
5. **Hierarchical Planning** - Intent tree construction methods
6. **Information Architecture Evolution** - Long-term consistency tracking

---

## 1. Pattern Catalog

### 1.1 Intention Tree Data Structures

| Pattern                              | Source            | Description                                                                      | Project Applicability                          |
| ------------------------------------ | ----------------- | -------------------------------------------------------------------------------- | ---------------------------------------------- |
| **SessionIntentBench Tree**          | Literature Review | Root (high-level goal) → Branches (sub-goals) → Leaves (atomic actions)          | Core structure for `intentions.yaml` hierarchy |
| **I-Tree Framework**                 | PDF Research      | Hierarchical decomposition with constraint/dependency tracking between nodes     | Model intent dependencies in commit plans      |
| **ReAcTree**                         | Both Sources      | Real-time intention trees with control flow nodes (sequence, fallback, parallel) | Dynamic plan adaptation during session         |
| **HTN (Hierarchical Task Networks)** | Literature Review | Recursive task decomposition with symbolic verification                          | Commit plan validation logic                   |

**Recommendation for Project:**
Adopt a hybrid of SessionIntentBench's tree structure with I-Tree's constraint tracking:

```yaml
# Proposed intentions.yaml structure enhancement
intentions:
  root:
    id: "intent-001"
    description: "Add user authentication feature"
    type: "feature"
    children:
      - id: "intent-001-a"
        description: "Implement login endpoint"
        constraints:
          - depends_on: null
          - blocks: ["intent-001-b"]
      - id: "intent-001-b"
        description: "Add session management"
        constraints:
          - depends_on: ["intent-001-a"]
```

### 1.2 LLM Intent Detection Techniques

| Pattern                        | Source            | Description                                                | Project Applicability                             |
| ------------------------------ | ----------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| **Gen-PINT**                   | Literature Review | Generative intent detection via text-to-text reformulation | intention-mapper prompting strategy               |
| **Adaptive Chain-of-Thought**  | Both Sources      | Step-by-step reasoning before classification               | Sub-agent reasoning traces in session records     |
| **Hybrid Routing**             | Literature Review | Small models for routine, LLMs for ambiguous cases         | Tiered validation (fast checks vs. deep analysis) |
| **RAG Integration**            | Literature Review | Ground detection with organizational context               | Link intents to existing codebase patterns        |
| **"Coding Intent in Context"** | PDF Research      | Three-stage: analyze context → refine intent → generate    | Pre-commit intent verification flow               |

**Recommendation for Project:**
Enhance `intention-mapper.md` sub-agent with explicit CoT prompting:

```markdown
# Enhanced intention-mapper prompt structure
1. ANALYZE: Examine the code diff and surrounding context
2. EXTRACT: Identify clues about intended functionality
3. CLASSIFY: Categorize intent (feature, fix, refactor, docs)
4. DECOMPOSE: Break into sub-intentions if complex
5. VALIDATE: Check against stated user goal
6. OUTPUT: Structured intention tree
```

### 1.3 Code-Edit Traceability

| Pattern                           | Source       | Description                                                         | Project Applicability                             |
| --------------------------------- | ------------ | ------------------------------------------------------------------- | ------------------------------------------------- |
| **Commit Message Classification** | Both Sources | Bug-fix, Feature, Refactor, Documentation taxonomy                  | Intent type classification in hook                |
| **CodeBERT/GraphCodeBERT**        | Both Sources | Embeddings on diffs predict commit intent                           | Future: ML-based intent inference                 |
| **InferROI**                      | PDF Research | Extract resource-oriented intentions from code patterns             | Detect specific edit patterns (e.g., API changes) |
| **SpecRover**                     | Both Sources | Multi-agent system for inferring code intent from project structure | evidence-checker validation approach              |
| **AdverIntent-Agent**             | PDF Research | Generate multiple intent hypotheses, test adversarially             | Handle ambiguous edit intentions                  |

**Recommendation for Project:**
Implement intent classification in evidence-checker:

```python
# src/intention_audit/evidence/intent_classifier.py
INTENT_TYPES = {
    "feature": ["add", "implement", "create", "introduce"],
    "fix": ["fix", "resolve", "correct", "patch", "bug"],
    "refactor": ["refactor", "restructure", "reorganize", "clean"],
    "docs": ["document", "comment", "readme", "update docs"],
    "test": ["test", "spec", "coverage", "assert"],
    "chore": ["config", "dependency", "build", "ci"]
}

def classify_intent(intention_text: str, diff_content: str) -> str:
    """Classify intent type from text and code diff."""
    # Primary: keyword matching on intention text
    # Secondary: diff pattern analysis
    # Tertiary: LLM classification for ambiguous cases
```

### 1.4 Multi-Agent Coordination Patterns

| Pattern                         | Source            | Description                                         | Project Applicability               |
| ------------------------------- | ----------------- | --------------------------------------------------- | ----------------------------------- |
| **SpecRover Pipeline**          | PDF Research      | Reproducer → Context → Patcher → Reviewer           | Validates 5-phase hook architecture |
| **ChatHTN Hybrid**              | Literature Review | Symbolic planner + LLM generation + online learning | Hook orchestration with sub-agents  |
| **TMK (Task-Method-Knowledge)** | Literature Review | Explicit encoding constrains LLM outputs            | Sub-agent template structure        |

**Validation of Current Architecture:**
Our 5-phase pipeline aligns with SpecRover's multi-agent pattern:

| SpecRover Phase   | Our Hook Phase | Agent               |
| ----------------- | -------------- | ------------------- |
| Reproducer        | 1. Intentions  | intention-mapper    |
| Context Retrieval | 2. Commit Plan | commit-planner      |
| Verification      | 3. Evidence    | evidence-checker    |
| Validation        | 4. Structure   | structure-validator |
| Recording         | 5. Session     | session-recorder    |

**Recommendation:**
Add explicit handoff protocols between phases:

```python
# Enhanced phase transition in stop_hook.py
class PhaseResult:
    status: Literal["pass", "fail", "warn"]
    artifacts: dict[str, Any]
    next_phase_context: dict[str, Any]  # Pass forward to next phase
    reasoning_trace: list[str]  # CoT from sub-agent
```

### 1.5 Hierarchical Planning Patterns

| Pattern                          | Source            | Description                                                   | Project Applicability                  |
| -------------------------------- | ----------------- | ------------------------------------------------------------- | -------------------------------------- |
| **HTN Core + LLM Decomposition** | Literature Review | Symbolic planner core, LLM fills gaps                         | commit-planner architecture            |
| **Tree of Thoughts**             | Literature Review | Multiple reasoning branches with BFS/DFS                      | Handle complex multi-file changes      |
| **Behavior Tree Analogy**        | PDF Research      | Control flow (sequence, fallback, parallel) for orchestration | Commit ordering logic                  |
| **Online Learning (ChatHTN)**    | Literature Review | Learn decomposition methods over time                         | Future: learn from successful sessions |

**Recommendation for Project:**
Enhance `commit_plan.yaml` with control flow semantics:

```yaml
# Proposed commit_plan.yaml enhancement
commit_plan:
  strategy: "sequence"  # or "parallel" for independent changes
  commits:
    - id: "commit-1"
      intent_ref: "intent-001-a"
      files: ["src/auth/login.py"]
      control:
        type: "sequence"
        depends_on: []
    - id: "commit-2"
      intent_ref: "intent-001-b"
      files: ["src/auth/session.py"]
      control:
        type: "sequence"
        depends_on: ["commit-1"]
```

### 1.6 Information Architecture Evolution

| Pattern                             | Source            | Description                                           | Project Applicability            |
| ----------------------------------- | ----------------- | ----------------------------------------------------- | -------------------------------- |
| **Intent-Driven Development (IDD)** | Literature Review | Interfaces reconfigure based on detected intent       | Adaptive validation strictness   |
| **TUNA Framework**                  | Literature Review | 6-mode taxonomy for user intentions                   | Classify developer session modes |
| **Software Evolution Tracing**      | Both Sources      | Clustering commits by intent reveals patterns         | Long-term audit analytics        |
| **Tangled Commits Detection**       | Literature Review | Identify commits serving multiple conflicting intents | Prevent scope creep per commit   |

**Recommendation for Project:**
Add session mode detection for adaptive behavior:

```python
# Session modes based on TUNA framework adaptation
SESSION_MODES = {
    "feature_development": {
        "strictness": "high",
        "require_evidence": True,
        "require_docs": True
    },
    "bug_fixing": {
        "strictness": "medium",
        "require_evidence": True,
        "require_docs": False
    },
    "exploration": {
        "strictness": "low",
        "require_evidence": False,
        "require_docs": False
    },
    "refactoring": {
        "strictness": "high",
        "require_evidence": True,
        "require_docs": False
    }
}
```

---

## 2. Recommended Techniques by Hook Phase

### Phase 1: Intentions Check (intention-mapper)

| Technique                    | Priority | Implementation                        |
| ---------------------------- | -------- | ------------------------------------- |
| Chain-of-Thought prompting   | High     | Add reasoning trace to output         |
| Intent type classification   | High     | Classify as feature/fix/refactor/docs |
| Hierarchical decomposition   | Medium   | Auto-decompose complex intents        |
| Constraint tracking (I-Tree) | Medium   | Track dependencies between intents    |

**Enhanced Agent Prompt Pattern:**
```markdown
## Reasoning Protocol
Before outputting intentions, follow this chain of thought:
1. What is the user's stated goal?
2. What code changes are staged/modified?
3. Do the changes align with the goal?
4. Can the goal be decomposed into sub-intentions?
5. What type of intent is this (feature/fix/refactor/docs)?
6. Are there any constraints or dependencies?

Output your reasoning in the `reasoning_trace` field.
```

### Phase 2: Commit Plan Check (commit-planner)

| Technique                | Priority | Implementation                         |
| ------------------------ | -------- | -------------------------------------- |
| HTN-style decomposition  | High     | Break intent into atomic commits       |
| Control flow semantics   | Medium   | Add sequence/parallel/fallback logic   |
| Diff-to-intent alignment | High     | Each commit maps to one intent         |
| Tangled commit detection | Medium   | Warn if commit serves multiple intents |

### Phase 3: Evidence Check (evidence-checker)

| Technique                      | Priority | Implementation                         |
| ------------------------------ | -------- | -------------------------------------- |
| SpecRover validation pattern   | High     | Verify edits match stated intent       |
| InferROI pattern matching      | Medium   | Detect specific code patterns          |
| Test-based verification        | High     | Run tests that prove intent fulfilled  |
| Adversarial hypothesis testing | Low      | For ambiguous cases, test alternatives |

### Phase 4: Structure Validation (structure-validator)

| Technique                 | Priority | Implementation                          |
| ------------------------- | -------- | --------------------------------------- |
| Code home boundary check  | High     | Verify files match expected locations   |
| Dependency graph analysis | Medium   | Check architectural constraints         |
| Pattern consistency       | Medium   | Ensure changes follow existing patterns |

### Phase 5: Session Recording (session-recorder)

| Technique                   | Priority | Implementation                    |
| --------------------------- | -------- | --------------------------------- |
| Reasoning trace capture     | High     | Store CoT from all sub-agents     |
| Intent tree serialization   | High     | Full tree structure for audit     |
| Session mode classification | Medium   | Tag session type for analytics    |
| Evolution tracking metadata | Low      | Enable long-term pattern analysis |

---

## 3. Implementation Priorities

### Priority 1: Core Enhancements (Immediate)

1. **Add reasoning traces to sub-agents**
   - Modify all agent prompts to include CoT reasoning
   - Store traces in session_record.json
   - Files: `src/intention_audit/agents/*.md`

2. **Implement intent type classification**
   - Add classification logic to intention-mapper
   - Use in evidence-checker for validation
   - New file: `src/intention_audit/models/intent_types.py`

3. **Enhance intentions.yaml schema**
   - Add hierarchy support (parent/children)
   - Add constraint tracking
   - Update: `src/intention_audit/models/intentions.py`

### Priority 2: Validation Improvements (Near-term)

4. **Tangled commit detection**
   - Warn when single commit serves multiple intents
   - Add to commit-planner validation
   - Update: `src/intention_audit/hooks/stop_hook.py`

5. **Control flow in commit plans**
   - Add sequence/parallel semantics
   - Validate execution order
   - Update: `src/intention_audit/models/commit_plan.py`

6. **Pattern-based edit validation (InferROI-inspired)**
   - Detect common code patterns (API changes, resource management)
   - Verify patterns match intent type
   - New file: `src/intention_audit/evidence/pattern_detector.py`

### Priority 3: Advanced Features (Future)

7. **Session mode detection**
   - Infer mode from stated intentions
   - Adjust validation strictness
   - New file: `src/intention_audit/session/mode_detector.py`

8. **Multi-hypothesis intent inference**
   - For ambiguous cases, generate alternatives
   - Use evidence tests to disambiguate
   - Enhancement to evidence-checker

9. **Long-term evolution tracking**
   - Aggregate session data over time
   - Detect patterns and anomalies
   - New module: `src/intention_audit/analytics/`

---

## 4. Specific Architecture Suggestions

### 4.1 Enhanced Data Models

```python
# src/intention_audit/models/enhanced_intention.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class IntentType(Enum):
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"

@dataclass
class IntentionNode:
    id: str
    description: str
    intent_type: IntentType
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    constraints: dict[str, list[str]] = field(default_factory=dict)
    reasoning_trace: list[str] = field(default_factory=list)

@dataclass
class IntentionTree:
    root: IntentionNode
    nodes: dict[str, IntentionNode] = field(default_factory=dict)

    def get_leaves(self) -> list[IntentionNode]:
        """Get atomic intentions (no children)."""
        return [n for n in self.nodes.values() if not n.children_ids]

    def validate_constraints(self) -> list[str]:
        """Check all constraints are satisfiable."""
        errors = []
        # Validate no circular dependencies
        # Validate all referenced IDs exist
        return errors
```

### 4.2 Phase Transition Protocol

```python
# src/intention_audit/hooks/phase_protocol.py
from dataclasses import dataclass
from typing import Any, Literal

@dataclass
class PhaseResult:
    phase: str
    status: Literal["pass", "fail", "warn"]
    artifacts: dict[str, Any]
    reasoning_trace: list[str]
    next_phase_context: dict[str, Any]

    def to_session_record(self) -> dict:
        """Format for session recording."""
        return {
            "phase": self.phase,
            "status": self.status,
            "reasoning": self.reasoning_trace,
            "artifacts_summary": list(self.artifacts.keys())
        }
```

### 4.3 Evidence Test Enhancement

```python
# Enhancement to src/intention_audit/evidence/runner.py
def validate_intent_alignment(
    intention: IntentionNode,
    diff: str,
    test_results: list[TestResult]
) -> AlignmentResult:
    """
    Validate that code changes align with stated intention.

    Uses InferROI-inspired pattern matching combined with
    test verification (SpecRover pattern).
    """
    # 1. Extract patterns from diff
    patterns = extract_code_patterns(diff)

    # 2. Check patterns match intent type
    expected_patterns = INTENT_TYPE_PATTERNS[intention.intent_type]
    pattern_match = check_pattern_alignment(patterns, expected_patterns)

    # 3. Verify tests prove intent fulfilled
    intent_tests = filter_tests_for_intent(test_results, intention)
    test_verification = all(t.passed for t in intent_tests)

    # 4. Generate reasoning trace
    reasoning = [
        f"Analyzed diff for {intention.intent_type.value} patterns",
        f"Found patterns: {patterns}",
        f"Pattern alignment: {'pass' if pattern_match else 'fail'}",
        f"Test verification: {'pass' if test_verification else 'fail'}"
    ]

    return AlignmentResult(
        aligned=pattern_match and test_verification,
        reasoning=reasoning
    )
```

---

## 5. Research Gap: Areas for Future Investigation

The research reveals several areas not fully addressed that may be relevant:

1. **Multi-session intention tracking** - How intentions evolve across sessions
2. **Conflict resolution** - When evidence contradicts stated intention
3. **Confidence scoring** - Quantifying certainty of intent classification
4. **Rollback semantics** - What happens when commits violate intentions
5. **Team coordination** - Multiple developers with interacting intentions

---

## References

### From Literature Review (LLM Intent Detection and Modeling.md)
- Gen-PINT: Generative Pre-trained INTent detection (ACL 2024)
- ChatHTN: Hybrid HTN-LLM planning (ArXiv 2025)
- SpecRover: Code intent extraction (ICSE 2025)
- TUNA: Taxonomy of User Needs and Actions (ArXiv 2025)
- SessionIntentBench: E-commerce intention trees (ArXiv 2025)
- Tree of Thoughts: Multi-path reasoning (Hugging Face, 2025)
- TMK/Ivy: Task-Method-Knowledge constrained generation (ArXiv 2025)

### From Focused Research Paper (Detecting Intentions Using LLMs.pdf)
- ReAcTree: Hierarchical LLM agent trees (ArXiv 2025)
- I-Tree: Intention decomposition meta-model (ResearchGate)
- InferROI: Resource-oriented intention inference (ISSTA 2024)
- AdverIntent-Agent: Adversarial intent hypothesis testing (ISSTA 2025)
- "Your Coding Intent is Secretly in the Context" (ArXiv 2025)
- Commit-Level Software Change Intent Classification (MDPI 2024)
- Hierarchical Intention Tracking (ArXiv 2025)
