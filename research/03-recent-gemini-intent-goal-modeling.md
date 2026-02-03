# **Architectures of Intent: A Comprehensive Analysis of Hierarchical Goal Modeling, Rationale Mining, and Agentic Workflows in Software Engineering**

## **1\. Introduction: The Epistemic Crisis in Agentic Software Engineering**

The software engineering (SE) discipline stands at a precipice of a paradigm shift arguably more significant than the transition from assembly to high-level languages. We are witnessing the rapid ascendancy of Large Language Models (LLMs) from passive, autocomplete-style assistants (e.g., GitHub Copilot) to autonomous coding agents capable of executing long-horizon tasks with minimal human intervention.1 This transition drives a fundamental change in the nature of software artifacts: code is no longer the sole manifestation of engineering effort; rather, it is the *output* of a complex, increasingly opaque stochastic reasoning process.

As agents such as Devin, OpenDevin, and advanced configurations of GPT-4 and Claude 3.5 assume roles previously held by junior developers—navigating file systems, debugging errors, and managing dependencies—a critical "epistemic gap" emerges. In traditional human-centric development, the "what" (the code) is inextricably linked to the "why" (the intent) through the developer's cognitive model, commit messages, and documentation. When a human refactors a class, the action is the collapse of a hierarchical intention tree—a series of decisions made to satisfy high-level goals while navigating low-level constraints.

In contrast, current LLM-generated code often manifests as a final artifact detached from the strategic rationale that produced it. Repositories risk becoming "graveyards of intent"—functional but opaque monoliths where the strategic reasoning is lost, making maintenance, refactoring, and auditing increasingly difficult. Recent studies indicate that while LLMs excel at generating functionally correct code for well-defined tasks, they struggle with maintainability and often introduce structural flaws during refactoring because they lack a persistent, grounded representation of *design intent*.1

This report provides an exhaustive analysis of the emerging research landscape designed to bridge this gap. We focus on three converging pillars of innovation:

1. **Intent Inference and Hierarchical Goal Modeling:** Moving beyond flat classification of user utterances to constructing dynamic, evolving **Intention Trees** and **Hierarchical Task Networks (HTNs)** that represent the "mind" of the coding agent.  
2. **Goal Drift and Consistency:** Mechanisms for maintaining adherence to high-level objectives over extended interaction trajectories, preventing the "stochastic parrot" effect where agents lose the plot as context grows.3  
3. **Rationale Mining and Traceability:** Techniques to reverse-engineer intent from developer activity signals (code diffs, tool traces, gaze patterns) to build an auditable **"Why" Layer** that persists alongside the codebase.

The central thesis emerging from this synthesis is that sustainable AI-driven software engineering requires a shift from **flat, autoregressive generation** to **hierarchical, intent-aware state management**. Without a persistent, revisable "intention memory," coding agents degenerate into powerful but unreliable tools that drift from user goals and produce "spaghetti code" that is technically correct but strategically incoherent.

## ---

**2\. Theoretical Foundations: From Flat Classifiers to Intention Trees**

To understand the mechanisms of intent-driven software engineering, we must first distinguish between simple classification and hierarchical modeling. Early intent detection in SE focused on classifying short utterances (e.g., "fix bug" vs. "add feature") into predefined categories. The current frontier involves **Plan Recognition**—inferring a complex, nested tree of goals from a stream of developer activities or natural language instructions.

### **2.1 The Limits of Flat Intent Classification**

Traditional intent detection relies on supervised learning to map an input ![][image1] (e.g., a commit message or query) to a label ![][image2] from a fixed taxonomy. While useful for command-and-control interfaces, this approach fails in complex SE workflows where intents are latent, hierarchical, and evolutionary.

**Latent Intents:** The true goal (e.g., "improve system scalability") is rarely explicitly stated in the code edits, which may only show "changed hash map to B-tree." Research indicates that relying solely on explicit textual descriptions fails to capture the rich semantic dependencies inherent in software evolution.4

**Hierarchical Nature:** A single high-level intent decomposes into multiple sub-intents. For instance, "Update Database Schema" decomposes into "Write Migration Script," "Update ORM Models," and "Refactor Query Logic." A flat classifier cannot represent this structural relationship, treating each action as an isolated event rather than part of a cohesive plan.

**Open-Ended Discovery:** Fixed taxonomies are insufficient for the unbounded nature of software tasks. Recent work on customer intent modeling demonstrates that LLMs can expand generic taxonomies (e.g., 36 intents) into granular, domain-specific trees (e.g., 278 intents).5 In SE, this translates to moving beyond binary labels to rich intention trees that map *Why* (Goal), *How* (Plan), and *What* (Implementation).

### **2.2 The Intention Tree Formalism**

The **Intention Tree** is emerging as a critical data structure for modeling long-horizon sessions. Defined inductively, an intention tree ![][image3] branches over time steps ![][image4], where nodes represent goals and edges represent decomposition relationships.6

In the specific context of software engineering, an Intention Tree models a coding session as:

* **Root Node:** The high-level requirement or User Request (e.g., "Implement OAuth2 Authentication").  
* **Intermediate Nodes:** Architectural decisions and subgoals (e.g., "Configure Security Filter Chain," "Create Auth Controller").  
* **Leaf Nodes:** Concrete atomic actions, such as code edits, shell commands, or file creations.

This structure enables critical capabilities that flat models lack:

1. **Drift Detection:** If an agent's leaf actions (code edits) begin to diverge from the constraints of the parent node (architectural goal), the system can flag a "Goal Drift" event.3  
2. **Revisability:** If a high-level goal changes, the agent can prune the relevant branches of the tree and replan, rather than discarding all work.  
3. **Traceability:** Every line of code can be traced back up the tree to the high-level requirement that necessitated it, providing the foundation for the "Why" layer.8

### **2.3 Hierarchical Task Networks (HTN) in the Era of LLMs**

Hierarchical Task Network (HTN) planning provides the formal scaffolding for this new generation of agents. Unlike classical STRIPS planners that search for a sequence of atomic actions to reach a state, HTN planners decompose **compound tasks** into simpler subtasks using **methods**.9

Recent research proposes a roadmap for integrating LLMs into Hierarchical Planning (HP), identifying a taxonomy of roles the LLM can play 1:

| Role | Description | Strengths | Weaknesses |
| :---- | :---- | :---- | :---- |
| **LLM as Planner** | The LLM directly generates the plan hierarchy (decomposition). | High flexibility, handles open-ended NL tasks. | Prone to hallucination; lacks formal guarantees; struggles with backtracking. |
| **LLM as Heuristic** | The LLM scores potential decompositions for a symbolic planner (e.g., guiding a search algorithm). | Combines creativity of LLM with correctness of formal planners. | High computational cost; dependency on formal domain definitions. |
| **LLM as Translator** | Translates NL requirements into PDDL/HDDL for a classical planner. | Leveraging mature solvers for complex constraints. | "Translation gap"—loss of nuance in converting NL to formal logic. |

The "Neuro-Symbolic" approach, where the LLM serves as a heuristic engine for a symbolic planner, is gaining traction. It allows the system to utilize the LLM's vast semantic knowledge to propose plausible subgoals (e.g., "To fix this bug, you likely need to edit the User class") while the symbolic planner ensures that the sequence of actions respects logical preconditions and effects.11

## ---

**3\. Cognitive Architectures for Intent-Driven Coding**

Implementing these theoretical models requires novel agent architectures that go beyond simple "Chain-of-Thought" prompting. We analyze three cutting-edge frameworks identified in the literature: **Planning-Driven Programming (LPW)**, **HiAgent**, and **Programmatic Skill Networks (PSN)**.

### **3.1 Planning-Driven Programming (LPW): Decoupling Thought from Action**

A major failure mode of current coding agents is that they often rush to implementation without verifying the validity of their plan. They exhibit "system 1" thinking (fast, intuitive) without engaging "system 2" (slow, deliberative). **Planning-Driven Programming (LPW)** 13 addresses this by enforcing a strict two-phase workflow that treats the plan as a verifiable artifact.

**Phase 1: Solution Generation & Verification**

* **Plan Formulation:** The model generates a natural language plan decomposing the problem.  
* **Plan Verification:** Crucially, the plan is *verified* before any code is written. This is often done by prompting the model to "simulate" the plan against visible test cases. The LLM traces the logic of its English-language plan with specific inputs and predicts the outputs.  
* **Correction:** If the predicted output of the plan simulation does not match the test case expectation, the plan is refined iteratively. This catches logic errors at the *design* stage, which is orders of magnitude cheaper than debugging code.

**Phase 2: Code Implementation**

* The verified plan serves as the "specification" for the coding model.  
* If the generated code fails tests, the system uses the *verified plan* as the ground truth to debug the code. This ensures the fix aligns with the strategic intent rather than just patching the syntax to satisfy the compiler.

**Insight:** LPW represents a shift from "correctness by chance" to "correctness by design." By treating the *Plan* as a first-class artifact that must pass its own "tests" (verification steps), LPW reduces the search space for the implementation phase. Empirical results show LPW achieves state-of-the-art performance (e.g., 98.2% on HumanEval with GPT-4o) 13, validating the hypothesis that **hierarchical intent verification** is the bottleneck in current code generation, not raw coding ability.

**The Sampling Variant (SLPW):** The research also introduces a sampling variant, SLPW, which generates multiple solution plans and verifications in parallel. This acknowledges the inherent ambiguity in high-level intent—there may be multiple valid architectural approaches to a problem. SLPW effectively explores the "solution space" at the planning level before committing resources to implementation.16

### **3.2 HiAgent: Hierarchical Working Memory Management**

Cognitive science suggests humans solve complex tasks using "chunking"—grouping information into manageable units to overcome working memory limitations. **HiAgent** 17 applies this principle to LLM agents via **Hierarchical Memory Management**.

Standard agents use a flat context window (or simple RAG), which becomes noisy over long trajectories. As the conversation history grows, relevant details get "drowned out" by irrelevant intermediate steps. HiAgent introduces a structured memory where:

* **Subgoals as Chunks:** Each subgoal in the intention tree acts as a container for memory.  
* **Selective Retention:** For the *current* subgoal, the agent retains detailed action-observation pairs (high resolution). For *completed* subgoals, it retains only a summarized outcome (low resolution).  
* **Global Context:** High-level goals and global invariants are always preserved in a "Long-Term Memory" tier.

**Implication for SE:** This architecture is essential for large-scale refactoring or feature implementation in legacy codebases. An agent working on "Refactor Function A" needs detailed context about Function A's local variables, but only needs to know the *signature* and *contract* (intent) of the previously implemented "Function B," not its internal logic or the specific compiler errors encountered during its implementation. This drastically reduces token consumption and prevents "context pollution," where irrelevant details from past subtasks confuse the model.3

### **3.3 Programmatic Skill Networks (PSN): Evolving Agent Capabilities**

While LPW and HiAgent focus on the *process* of a single session, **Programmatic Skill Networks (PSN)** 19 focus on the *evolution of the agent itself*. PSN treats skills not as fixed prompts or static text, but as an evolving library of executable programs.

Key mechanisms include:

1. **REFLECT (Fault Localization):** When a composition of skills fails, the agent analyzes the execution trace to assign credit/blame to specific skills in the network, rather than discarding the whole plan. This allows for targeted repair of specific "sub-skills."  
2. **Canonical Structural Refactoring:** This is a meta-cognitive capability. The agent identifies redundancy in its skill network (e.g., two skills doing similar things like "read\_csv" and "read\_text\_file") and *refactors its own memory* to merge them into a more abstract, reusable skill (e.g., "read\_file(path, format)").  
3. **Maturity-Aware Gating:** New skills are treated as "unstable" and kept plastic, allowing for rapid modification. Proven skills are "crystallized" to prevent catastrophic forgetting, balancing plasticity and stability.

**Insight:** PSN suggests a future where coding agents are not static models but **dynamic systems** that improve their "professional intuition" over time. An agent that has refactored ten authentication modules will have evolved a highly optimized "Auth-Refactor-Skill" in its network, distinct from a generic coding agent. This mirrors the trajectory of human expertise, where repeated tasks become automatized "subroutines" in the expert's mind.

## ---

**4\. The Dynamics of Goal Drift and Consistency**

As agents operate over longer horizons (e.g., multi-file refactoring, end-to-end feature development), they exhibit **Goal Drift**—a gradual deviation from the original user instruction.3 Maintaining goal integrity is the primary challenge for autonomous agents.

### **4.1 Mechanisms of Drift**

Research identifies two primary forms of drift in LLM agents:

1. **Pattern-Matching Drift (Autoregressive Momentum):** As the context window fills with the agent's recent actions, the LLM becomes biased by its own recent outputs rather than the original system prompt. If an agent makes a suboptimal decision early on (e.g., creating a temporary variable), it tends to "double down" on it to maintain local consistency, even if this violates the high-level goal (e.g., "clean code"). The agent effectively "forgets" the instruction in favor of continuing the pattern it has started.3  
2. **Contextual Overload:** In "needle in a haystack" scenarios, the original goal is lost amidst thousands of tokens of code retrieval results or execution logs.

### **4.2 Detecting and Measuring Drift**

Drift detection requires a **reference anchor**. In workflows like LPW, the *Verified Plan* acts as this anchor. By periodically comparing the *Current State* against the *Plan Node*, the system can calculate a **Drift Score**.

* **Methodology:** Recent studies quantify drift by comparing embedding similarity between the "Expected Outcome" of the current plan step and the "Actual Outcome" of the agent's action.  
* **Bidirectional Drift:** Experiments in controlled environments (e.g., stock trading agents with conflicting objectives) reveal that drift is bidirectional. Agents may drift *towards* easier, pattern-matched behaviors or *away* from constraints when under adversarial pressure.22  
* **Drift via Inaction:** A subtle form of drift involves *inaction*—failing to take necessary steps because they conflict with the "path of least resistance" established by the immediate context.22

### **4.3 Mitigation: The Role of Hierarchical Monitoring**

To combat drift, architectures must implement **Hierarchical Monitoring**. A "Monitor Agent" (separate from the "Worker Agent") maintains the high-level Intention Tree. Before the Worker commits any action, the Monitor verifies alignment.

* *Worker Proposal:* "I will delete this unused variable in the Auth module."  
* *Monitor Check:* "Query Intention Tree. Current Goal is 'Refactor Logging'. Deleting variables in 'Auth' is out of scope and risky. Action Denied."

This "Constitution-based" or "Supervisor-based" control loop is essential for safe autonomous engineering. Research indicates that **strong goal elicitation** (explicitly restating the goal in the prompt at every step) significantly reduces drift compared to weak elicitation, but architectural separation (like HiAgent or Monitor-Worker loops) is more robust for long-horizon tasks.22

## ---

**5\. Mining Rationale: Building the "Auditable Why" Layer**

As agents become primary actors in software repositories, the ability to **mine rationale**—to reconstruct the "why" behind a change—becomes critical for auditing, debugging, and maintaining trust. This section analyzes techniques for **Traceability Recovery** and **Commit Untangling**.

### **5.1 UserTrace: Recovering High-Level Requirements**

Traceability links (e.g., connecting a Requirement ID to specific Lines of Code) are notoriously difficult to maintain and are often missing in legacy or open-source projects. **UserTrace** 8 introduces a multi-agent approach to retroactively generate these links from code repositories.

**The Multi-Agent Workflow:**

1. **Searcher Agent:** Navigates the repository to identify code units related to a potential feature. Unlike simple keyword matching (grep), it uses semantic search to find "implicitly" related files. This addresses "Insight II" from the research: a single requirement often emerges from the aggregation of multiple code units, and cannot be found in a single file.23  
2. **Code Reviewer Agent:** Analyzes the identified code to extract **Implementation Requirements (IRs)**—low-level functional descriptions (e.g., "input validation logic in line 40").  
3. **Writer Agent:** Synthesizes these IRs into **User-Level Requirements (URs)**—high-level goal statements (e.g., "The system shall prevent SQL injection during login").  
4. **Verifier Agent:** Validates the generated URs against the code to ensure factual accuracy, creating a verified trace link.

**Significance:** UserTrace effectively "reverse-engineers" the Intention Tree. By ascending from Code ![][image5] IR ![][image5] UR, it reconstructs the lost planning hierarchy. This allows developers to query the codebase not just for "Where is login() defined?" but "Where is the requirement for secure login implemented?", facilitating **intent-aware impact analysis** during future changes.

### **5.2 ColaUntangle: Disentangling Semantic Intent**

A major challenge in mining developer intent is the **Tangled Commit**: a single commit that bundles multiple unrelated changes (e.g., a bug fix, a refactor, and a feature addition). This obscures intent and breaks the "atomic commit" best practice.

**ColaUntangle** 24 leverages LLMs to decompose these commits based on **Implicit** and **Explicit** dependencies.

* **Explicit Dependencies:** Detectable via static analysis. Includes data flow (variable usage), control flow, and structural references. Handled by an **Explicit Worker Agent**.  
* **Implicit Dependencies:** Semantic similarity and logical association (e.g., renaming a variable in comments vs. code). Handled by an **Implicit Worker Agent**.

**Mechanism of Collaborative Consultation:**

The framework uses a **collaborative consultation** process. The Reviewer Agent synthesizes the outputs of the Explicit and Implicit workers. If they disagree (e.g., the Explicit worker sees no link, but the Implicit worker sees a shared conceptual goal), the Reviewer mediates to reach a consensus.

* *Scenario:* A commit changes a CSS color and optimizes a SQL query.  
* *Analysis:* Explicit analysis finds no link. Implicit analysis finds no semantic link. Result: Split into two commits.  
* *Scenario:* A commit changes a CSS class name and updates the HTML to use the new class.  
* *Analysis:* Implicit analysis finds a strong link ("Name alignment"). Result: Atomic commit preserved.

**Insight:** ColaUntangle demonstrates that **semantics trump structure** in intent inference. Purely structural tools (program slicing) fail to group cosmetic changes with their functional counterparts because there is no data dependency. LLMs bridge this gap by recognizing the "latent goal" that unifies structurally disjoint edits.

### **5.3 Provenance and "AI Slop"**

The aggregation of these tools enables the construction of a persistent **"Why" Layer** atop the physical code. However, mining this layer involves **perils**, particularly in distinguishing human vs. agent activity.2

**The Peril of "AI Slop":** The proliferation of low-quality, high-volume agent code ("slop") can contaminate datasets used to train future models. Researchers warn that without robust provenance tracking, the feedback loop of training models on model-generated code will lead to model collapse.

**Provenance Models:** Standards like **W3C PROV-DM** 28 are being adapted to track the "supply chain" of agent-generated code. This involves recording not just the code, but the *agents* involved, the *prompts* used, and the *decisions* made. Tools like JFrog are beginning to implement "Shadow AI Detection" to create an inventory of AI-generated artifacts.29

## ---

**6\. Multimodal Intent Inference: Beyond Text**

While text (prompts/code) is the primary modality, developer intent is often leaked through **implicit signals** before a single character is typed. The integration of multimodal signals offers a higher-bandwidth channel for intent recognition.

### **6.1 Eye-Tracking and Visual Attention**

Research into **Eye-Tracking** in IDEs reveals that gaze fixations are strong predictors of intent.30

* **Fixation Strategies:** A developer refactoring code exhibits a different gaze pattern (scanning structural elements, jumping between definitions, focusing on signatures) compared to a developer debugging (intense fixation on data flow and variable values).  
* **EyeMulator:** Recent work 31 trains LLMs to *predict* human visual attention (where a human *would* look) and uses this as an attention mask for the model. This "simulated gaze" improves code generation by focusing the LLM on relevant context, mimicking human focus. By integrating gaze data, models can achieve better performance without needing actual eye-tracking hardware during inference, as they have "learned to look."

### **6.2 IDE Interaction Traces**

Beyond gaze, IDE signals such as **scroll speed**, **tab switching**, and **text selection** provide a high-frequency signal of cognitive state.33

* **Uncertainty Detection:** Rapid switching between a function definition and documentation suggests uncertainty or a "learning" intent.  
* **Edit Bursts:** Long pauses followed by rapid typing suggest a "Planning ![][image5] Execution" cycle.  
* **Navigation Paths:** The sequence of files visited builds a "context graph." If a developer visits User.java, AuthController.java, and db\_schema.sql in sequence, the intent "Modify Authentication Schema" can be inferred even before any code is written.

**Insight:** Integrating these multimodal signals allows agents to infer intent *proactively*. If an agent detects "confusion signals" (erratic scrolling), it can intervene with context-aware help ("Do you need documentation for API X?") *before* the developer explicitly asks, shifting from reactive to **anticipatory assistance**.

## ---

**7\. Application: IA-Aware Refactoring and Skill Evolution**

The convergence of hierarchical intent modeling and rationale mining enables a new class of SE tools: **Intent-Aware (IA) Refactoring** and the self-evolution of agent skills.

### **7.1 From "Code Smells" to "Intent Violations"**

Traditional refactoring tools identify syntactic patterns (e.g., Long Method, Duplicated Code). IA-Refactoring identifies **semantic dissonance**—where the code conflicts with the inferred intent.

* *Scenario:* A developer adds a "Quick Fix" to bypass a security check during testing.  
* *Detection:* The agent infers the intent ("Temporary Debugging") from the commit message or IDE signal.  
* *Recommendation:* Instead of flagging a security error immediately (which might annoy the developer during testing), the agent logs a "Technical Debt" item linked to the intent: "Remove bypass before merge."  
* *Automation:* If the developer attempts to merge, the agent (using the Intention Tree) flags the violation: "Intent 'Temporary Debugging' contradicts Goal 'Production Release'."

### **7.2 Structural Refactoring of Agent Skills**

As discussed with **PSN** 19, agents themselves undergo refactoring. This is a meta-application of SE principles to AI. The "Canonical Structural Refactoring" mechanism in PSN allows the agent to maintain a compact and efficient skill library.

* **Deduplication:** The agent notices it has generated five different scripts for "Connect to AWS S3" across different tasks.  
* **Generalization:** It refactors these into a single, parameterized "S3\_Connector" skill.  
* **Validation:** It runs regression tests (using the "Reflect" mechanism) to ensure the new abstract skill works in all previous contexts where the concrete scripts were used.

This **Self-Refactoring** capability is what separates a "Script Kiddie Agent" (which just generates code) from a "Senior Engineer Agent" (which curates a reusable toolkit). It prevents the agent's memory from becoming bloated with redundant, one-off solutions.

## ---

**8\. Governance and the "Why" Layer**

The ability to generate code at scale necessitates a robust governance framework. The "Why" Layer serves as the audit trail for autonomous agents.

### **8.1 Agent Activity Manifests**

To solve the "Peril of Partial Observability" 27, repositories must standardize **Agent Activity Manifests**. These are log files (e.g., stored in a hidden .agent/ directory) that record:

* The **Prompt** that initiated a change.  
* The **Plan** generated by the agent (from LPW).  
* The **Verification Steps** passed.  
* The **Tools** invoked.

This allows a human auditor to replay the agent's "thought process." If a bug is found, the auditor can see *why* the agent made the mistake (e.g., "The plan verification step was skipped," or "The agent hallucinated a library function").

### **8.2 Regulatory Compliance**

For industries like finance and healthcare, "Black Box" code generation is unacceptable. The integration of **Software Provenance** models (like PROV-DM) ensures that every line of code has a pedigree.

* **Attestation:** Agents sign their commits with cryptographic keys linked to their model identity (e.g., "Signed by GPT-4-Turbo-v2").  
* **License Compliance:** "Shadow AI Detection" tools track whether the agent introduced code snippets from copyleft sources.29

## ---

**9\. Conclusion and Future Directions**

The research analyzed in this report points to a fundamental inversion in software engineering: **Intent is becoming the primary artifact; code is becoming a derived byproduct.**

1. **Hierarchy is King:** Flat context windows are insufficient for autonomous SE. Success requires **Hierarchical Task Networks (HTN)** and **Intention Trees** to manage complexity and prevent drift.1  
2. **Verify, Then Trust:** Workflows like **LPW** 13 demonstrate that separating **Planning/Verification** from **Coding** is the only path to reliability. We must treat "Prompt Engineering" as "Specification Engineering."  
3. **Mining the Invisible:** Tools like **UserTrace** 8 and **ColaUntangle** 24 allow us to excavate intent from the digital exhaust of repositories, building the **"Why" Layer** necessary for auditability.  
4. **Agents Must Evolve:** Static models are dead ends. **Programmatic Skill Networks (PSN)** 19 show that agents must possess the ability to refactor their own knowledge, mirroring the continuous learning of human experts.

**Future Outlook (2025-2026):** We anticipate the emergence of **"Intent-Driven IDEs"** where the primary interface is not a text editor, but a collaborative **Plan Editor**. Developers will manipulate the Intention Tree—pruning goals, refining constraints, and reviewing agent-generated strategies—while the agent handles the leaf-node implementation. In this world, the measure of a developer's skill shifts from "lines of code" to "clarity of intent."

### **Summary of Key Technologies Analyzed**

| Technology | Core Function | Key Innovation | Source |
| :---- | :---- | :---- | :---- |
| **LPW** | Planning-Driven Programming | Verification of *Plan* before *Code*; using Plan as debugging oracle. | 13 |
| **UserTrace** | Traceability Recovery | Multi-agent extraction of User Requirements (UR) from code. | 8 |
| **ColaUntangle** | Commit Untangling | Leveraging *Implicit Semantic Dependencies* to split commits. | 24 |
| **HiAgent** | Memory Management | Subgoal-based chunking of working memory to prevent overload. | 17 |
| **PSN** | Skill Evolution | Canonical structural refactoring of the agent's own skill library. | 19 |
| **EyeMulator** | Multimodal Signal | Simulating human gaze to improve LLM attention focus. | 31 |

**Recommendations for Researchers and Practitioners:**

1. **Adopt LPW Workflows:** Move away from "chatting with code" to "planning with code." Enforce verification steps before generation.  
2. **Invest in Rationale Mining:** Deploy tools like UserTrace/ColaUntangle to clean up legacy data. The value of your repository is not just the code, but the *intent graph* embedded within it.  
3. **Monitor for Drift:** Implement hierarchical oversight in agent deployments. Do not let agents operate on infinite context windows without "Goal Anchors."  
4. **Embrace Skill Refactoring:** Design agents that can rewrite their own toolkits. The ability to abstract and consolidate knowledge is the hallmark of intelligence.

By anchoring AI in the "Why," we ensure that the software systems of the future remain comprehensible, maintainable, and aligned with human values, even as the "How" becomes increasingly automated.

#### **Works cited**

1. Hierarchical Evaluation of Software Design Capabilities of Large Language Models of Code, accessed on February 2, 2026, [https://arxiv.org/html/2511.20933v2](https://arxiv.org/html/2511.20933v2)  
2. Promises, Perils, and (Timely) Heuristics for Mining Coding Agent Activity \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.18345v1](https://arxiv.org/html/2601.18345v1)  
3. Evaluating Goal Drift in Language Model Agents, accessed on February 2, 2026, [https://ojs.aaai.org/index.php/AIES/article/download/36541/38679/40616](https://ojs.aaai.org/index.php/AIES/article/download/36541/38679/40616)  
4. Detecting Multiple Semantic Concerns in Tangled Code Commits \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.21298v1](https://arxiv.org/html/2601.21298v1)  
5. From Intent Discovery to Recognition with Topic Modeling and Synthetic Data \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2505.11176v1](https://arxiv.org/html/2505.11176v1)  
6. SessionIntentBench: A Multi-task Inter-session Intention-shift Modeling Benchmark for E-commerce Customer Behavior Understanding \- arXiv, accessed on February 2, 2026, [https://arxiv.org/pdf/2507.20185](https://arxiv.org/pdf/2507.20185)  
7. An Active Learning Approach for Improving the Accuracy of Automated Domain Model Extraction | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/330207683\_An\_Active\_Learning\_Approach\_for\_Improving\_the\_Accuracy\_of\_Automated\_Domain\_Model\_Extraction](https://www.researchgate.net/publication/330207683_An_Active_Learning_Approach_for_Improving_the_Accuracy_of_Automated_Domain_Model_Extraction)  
8. UserTrace: User-Level Requirements Generation and Traceability Recovery from Software Project Repositories \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2509.11238v1](https://arxiv.org/html/2509.11238v1)  
9. University of Groningen HTN planning: Overview, comparison, and beyond Georgievski, I.; Aiello, M., accessed on February 2, 2026, [https://pure.rug.nl/ws/files/83768215/HTN\_planning\_Overview\_comparison\_and\_beyond.pdf](https://pure.rug.nl/ws/files/83768215/HTN_planning_Overview_comparison_and_beyond.pdf)  
10. A Roadmap to Guide the Integration of LLMs in Hierarchical Planning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2501.08068v2](https://arxiv.org/html/2501.08068v2)  
11. A Roadmap to Guide the Integration of LLMs in Hierarchical Planning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2501.08068](https://arxiv.org/html/2501.08068)  
12. A decision-making framework using MCTS as a hierarchical task network and deep learning connector \- PMC \- NIH, accessed on February 2, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12553875/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12553875/)  
13. \[2411.14503\] Planning-Driven Programming: A Large Language Model Programming Workflow \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/2411.14503](https://arxiv.org/abs/2411.14503)  
14. Planning-Driven Programming: A Large Language Model Programming Workflow | OpenReview, accessed on February 2, 2026, [https://openreview.net/forum?id=Fr6bjeqRec](https://openreview.net/forum?id=Fr6bjeqRec)  
15. Planning-Driven Programming: A Large Language Model Programming Workflow \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2411.14503v2](https://arxiv.org/html/2411.14503v2)  
16. Paper page \- Planning-Driven Programming: A Large Language Model Programming Workflow, accessed on February 2, 2026, [https://huggingface.co/papers/2411.14503](https://huggingface.co/papers/2411.14503)  
17. HiAgent: Hierarchical Working Memory Management for Solving Long-Horizon Agent Tasks with Large Language Model \- ACL Anthology, accessed on February 2, 2026, [https://aclanthology.org/2025.acl-long.1575.pdf](https://aclanthology.org/2025.acl-long.1575.pdf)  
18. HiAgent: Hierarchical Working Memory Management for Solving Long-Horizon Agent Tasks with Large Language Model | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/394270885\_HiAgent\_Hierarchical\_Working\_Memory\_Management\_for\_Solving\_Long-Horizon\_Agent\_Tasks\_with\_Large\_Language\_Model](https://www.researchgate.net/publication/394270885_HiAgent_Hierarchical_Working_Memory_Management_for_Solving_Long-Horizon_Agent_Tasks_with_Large_Language_Model)  
19. Evolving Programmatic Skill Networks \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.03509v1](https://arxiv.org/html/2601.03509v1)  
20. arxiv.org, accessed on February 2, 2026, [https://arxiv.org/abs/2601.03509](https://arxiv.org/abs/2601.03509)  
21. Programmatic Skill Induction \- Emergent Mind, accessed on February 2, 2026, [https://www.emergentmind.com/topics/programmatic-skill-induction](https://www.emergentmind.com/topics/programmatic-skill-induction)  
22. Technical Report: Evaluating Goal Drift in Language Model Agents \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2505.02709v1](https://arxiv.org/html/2505.02709v1)  
23. UserTrace: User-Level Requirements Generation and Traceability Recovery from Software Project Repositories \- arXiv, accessed on February 2, 2026, [https://www.arxiv.org/pdf/2509.11238](https://www.arxiv.org/pdf/2509.11238)  
24. LLM-Driven Collaborative Model for Untangling Commits via Explicit and Implicit Dependency Reasoning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2507.16395v2](https://arxiv.org/html/2507.16395v2)  
25. LLM-Driven Collaborative Model for Untangling Commits via Explicit and Implicit Dependency Reasoning \- ChatPaper, accessed on February 2, 2026, [https://chatpaper.com/paper/169086](https://chatpaper.com/paper/169086)  
26. LLM-Driven Collaborative Model for Untangling Commits via Explicit and Implicit Dependency Reasoning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/pdf/2507.16395](https://arxiv.org/pdf/2507.16395)  
27. Promises, Perils, and (Timely) Heuristics for Mining Coding Agent Activity \- arXiv, accessed on February 2, 2026, [https://arxiv.org/pdf/2601.18345](https://arxiv.org/pdf/2601.18345)  
28. PROV-DM: The PROV Data Model | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/262599623\_PROV-DM\_The\_PROV\_Data\_Model](https://www.researchgate.net/publication/262599623_PROV-DM_The_PROV_Data_Model)  
29. JFrog Adds Ability to Track Usage of AI Coding Tools \- DevOps.com, accessed on February 2, 2026, [https://devops.com/jfrog-adds-ability-to-track-usage-of-ai-coding-tools/](https://devops.com/jfrog-adds-ability-to-track-usage-of-ai-coding-tools/)  
30. Approach to Eye Tracking Scanpath Analysis with Multimodal Large Language Model, accessed on February 2, 2026, [https://www.mdpi.com/2673-3951/6/4/164](https://www.mdpi.com/2673-3951/6/4/164)  
31. EyeMulator: Improving Code Language Models by Mimicking Human Visual Attention \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2508.16771v1](https://arxiv.org/html/2508.16771v1)  
32. GazeCopilot: Evaluating Novel Gaze-Informed Prompting for AI-Supported Code Comprehension and Readability \- arXiv, accessed on February 2, 2026, [https://arxiv.org/pdf/2511.08177](https://arxiv.org/pdf/2511.08177)  
33. Tracing Software Developers' Eyes and Interactions for Change Tasks \- IFI UZH, accessed on February 2, 2026, [https://www.ifi.uzh.ch/seal/people/kevic/researchprojects/taskcontext/FSE2015.pdf](https://www.ifi.uzh.ch/seal/people/kevic/researchprojects/taskcontext/FSE2015.pdf)  
34. Designing A Multi-modal IDE with Developers: An Exploratory Study on Next-generation Programming Tool Assistance Peng Kuang Lund, accessed on February 2, 2026, [https://ppig.org/files/2024-PPIG-35th-kuang.pdf](https://ppig.org/files/2024-PPIG-35th-kuang.pdf)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAYCAYAAAAs7gcTAAAAiklEQVR4XmNgGAUDASYCcSoSvwOIa5D4YCAOxJeg7Fwg/gXE/6H8s0DcA2WDAUwCBHigfH0gtoCyI5DkGYyQ2GUMqJo5kNgY4BMDqmK8AKRwMbogDAgwQBQoMyDcq4UkfxWJzTCTAaKAE4jPQdmKUDmQJ1dA2WDAyABRAMKuDBAbYPw6JHWjgHwAAGFEHDJYgssXAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAYCAYAAADDLGwtAAAAo0lEQVR4XmNgGAXUBrOAOBVdEAjMkTm/gJgZiP8DsSOSeApUDAzmMUAUgQBI0AsmAQRvoGJgUAulu5EFoQDEX48mBhZ8gcSHOcUQSQwMQIJBSPwyqBgKEMci+BGLGBiABPWgbB0ofwNCGgFgQQHCk6C0FooKIJBC4+9kwGKtIFRwGpTPCOV7wFVAgTQQf4ey+RkgiiIR0qjAEojXAHEbusQgAAA0siUQO3ZjXQAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAYCAYAAADKx8xXAAAAmElEQVR4XmNgGDlgMxD/JwHDAYgThiwAFUNRBAQayGJCDBAbkQETA0TBBTRxEHgEY2wFYkYkCRAoYIBo9EcTZwPiPhgnH0kCBt4zYDoTBASAWBxdEBlg8x9BwMwA0XQGXYIQKGeAaPRGlyAEPjOQ4UwQIMt/oOAmy3+zGSAaE9DEsYIgIP7GAIm7t1AM8ucvBjKcPAoGBAAAiastbKanIo0AAAAASUVORK5CYII=>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAYCAYAAAA20uedAAAAcklEQVR4XmNgGOTgGxCfQheEgf9AXIAuCAL6DBBJJmRBGyD2AuLdUElfKB8MioC4BCrxFsoHYRQAksxFFwQBXQaIJCO6BAisYYBIYgUgiXfogjAAkgQ5CgaOILHBkipQ9k9kCRDoYYAo+AHELGhywwEAAMS4F/hUVNxNAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAAAVUlEQVR4XmNgGAWjgKpgL7oAJeAfugAlwAaIy9AFKQHngNgcXRAETMjEt4B4HwMa8CMTX4NiFgYKwUQg9kYXJAcoAnEnuiC54BO6ACXgMLrAKBhuAACnlhESw2iRqwAAAABJRU5ErkJggg==>