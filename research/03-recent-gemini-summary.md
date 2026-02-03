The following research synthesis covers the most recent developments (2024–2026) at the intersection of **intent inference**, **hierarchical planning**, and **rationale mining** in software engineering.

The field has shifted from simple "next-token prediction" to **agentic workflows** where the unit of analysis is no longer a line of code, but a **hierarchical plan**.

### **Executive Summary: The Shift to Intent-Aware Agents (2025–2026)**

Recent literature (late 2024–early 2026\) suggests a convergence toward **"Cognitive Architectures for SE"**. Researchers are moving beyond classifying intent as a single label (e.g., "Refactoring") to modeling it as a **dynamic, revisable tree structure**. The key breakthrough is using LLMs not just to generate code, but to maintain a persistent "memory" of the *plan* that allows for drift detection (when code diverges from the plan) and disentanglement (separating a bug fix from a style change in the same commit).

### ---

**1\. Intent Detection: Disentangling "What" from "How"**

*Focus: Inferring latent intent from context and separating tangled work.*

* **Tangled Change Detection via CoT (May 2025\)**  
  * **Paper:** *LLM-Based Detection of Tangled Code Changes for Higher-Quality Method-Level Bug Datasets* (arXiv:2505.08263)  
  * **Key Finding:** This research addresses the "tangled intent" problem—where developers mix bug fixes with refactoring or features in a single commit.  
  * **Methodology:** Using Chain-of-Thought (CoT) prompting, the model analyzes both the **commit message** (stated intent) and the **code diff** (actual behavior) to identify discrepancies. It effectively "untangles" the commit, attributing specific lines of code to distinct intents (e.g., "Lines 10-15 are a bug fix," "Lines 20-25 are a style update").  
  * **Relevance:** This is the foundation for your "auditable why layer"—attributing specific edits to specific goals rather than a blanket commit message.  
* **Latent Intent Inference from Context (Aug 2025\)**  
  * **Paper:** *Your Coding Intent is Secretly in the Context and You Should Deliberately Infer It Before Completion* (arXiv:2508.09537)  
  * **Key Finding:** Instead of jumping straight to code generation, this work introduces a **"pre-computation" step** where the model explicitly infers the developer's latent goal from the surrounding code context and interaction history.  
  * **Application:** This supports "drift detection" by establishing a baseline intent *before* any code is written. If the subsequent code generation deviates from this inferred intent, the system can flag a potential hallucination or logic error.

### ---

**2\. Hierarchical Goal Modeling: HTN & Plan Recognition**

*Focus: Representing intent as evolving trees rather than flat labels.*

* **LLM-Driven Hierarchical Task Network (HTN) Planning (Jan 2026\)**  
  * **Context:** *Hierarchical Task Network Planning \- Emergent Mind / GPT-HTN-Planner*  
  * **Key Finding:** New frameworks are combining symbolic HTN planners with LLMs. The LLM acts as the "heuristic generator," decomposing high-level natural language goals (e.g., "Implement user auth") into sub-goals (e.g., "Create database schema," "Write API endpoint").  
  * **Mechanism:** Crucially, these systems now include **Verifier/Method Learners**. If an LLM proposes a decomposition, a symbolic verifier checks if the sub-tasks logically achieve the parent goal.  
  * **Relevance:** This fulfills your requirement for a "revisable intention tree." The HTN structure provides a persistent memory of *the plan*. If a developer changes a requirement, the tree can be "pruned" and "regrafted" at the appropriate node without discarding the entire context.

### ---

**3\. Mining Rationale & Persistent Memory**

*Focus: Creating an auditable "Why" layer and guiding future dev.*

* **Mining Coding Agent Activity (Jan 2026\)**  
  * **Paper:** *Promises, Perils, and (Timely) Heuristics for Mining Coding Agent Activity* (arXiv:2601.18345)  
  * **Key Finding:** As coding agents (like Devin or specialized copilot agents) become autonomous, they leave "traces" in repositories that are distinct from human commits.  
  * **Opportunity:** The paper proposes mining these traces to build a **"rationale history."** unlike a human who might forget to write a commit message, an agent's internal "thought process" (its internal prompts and reasoning steps) can be logged.  
  * **Application:** This data can be transformed into an **auditable log** that explains *why* a piece of code exists, linking it back to the specific requirement or user instruction that spawned it.  
* **Persistent Memory for Long-Horizon Work (Aug 2025\)**  
  * **Context:** *Persistent Memory in LLM Agents* (Emergent Mind Synthesis)  
  * **Key Finding:** New architectures distinguish between **Episodic Memory** (current session context) and **Persistent Memory** (long-term knowledge graph).  
  * **Relevance:** For your "drift detection" and "IA-aware refactoring," persistent memory allows the system to remember *rejected* plans or *past* constraints. If a developer tries to re-introduce a pattern that was previously refactored out, the persistent memory can flag it, citing the historical rationale.

### ---

**Synthesis: The "Intent-Aware" Architecture**

Based on these works, the state-of-the-art architecture for the workflow you described is coalescing around this loop:

1. **Ingest:** Developer NL instruction \+ Code Context.  
2. **Decompose (HTN layer):** LLM generates a hierarchical plan (Intention Tree).  
3. **Trace (Mining layer):** Each node in the tree is linked to specific files/functions.  
4. **Monitor (Drift Detection):** As the developer edits, the system compares the *actual* diffs against the *expected* changes from the Intention Tree.  
5. **Refine (Disentanglement):** If the developer adds unrelated code (e.g., a quick bug fix in a feature branch), the system detects the semantic mismatch (via CoT) and suggests splitting the intention tree into two distinct branches.

### **Next Step**

Would you like me to draft a **system architecture diagram** or a **pseudo-code workflow** for the "Drift Detection" module, specifically showing how to combine the *HTN decomposition* with the *Code Diff Disentanglement* logic?