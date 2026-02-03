# **Neuro-Symbolic Intent Architecture: A Framework for Auditable, Intent-Driven Software Evolution**

## **1\. Introduction: The Crisis of Intent in Algorithmic Software Generation**

The trajectory of software engineering is undergoing a fundamental phase shift, moving from an imperative paradigm—where human developers explicitly author every syntactic element—to an intent-driven model where developers articulate high-level objectives and Artificial Intelligence (AI) agents execute the implementation. This shift, driven by the emergent capabilities of Large Language Models (LLMs), promises to solve the scalability limits of human cognition. However, it simultaneously exacerbates a critical, often overlooked vulnerability in the software lifecycle: the loss of the "Why."

As code generation speed accelerates, the "gulf of evaluation" between a developer’s cognitive intent and the resulting software artifact widens. Current Generative AI tools excel at local synthesis (predicting the next token or function) but frequently fail at global coherence (maintaining architectural integrity over thousands of files). They generate code that is syntactically correct but semantically untethered from the long-term architectural vision, leading to "Tangled Commits," "Design-Implementation Drift," and opaque repositories where the rationale for critical design decisions is lost in a flood of machine-generated syntax.

This report presents an exhaustive analysis of the fundamental research required to bridge this gap. We explore the convergence of **Multimodal Intent Inference**, **Hierarchical Goal Modeling**, and **Rationale Mining** to construct a new architectural layer: the "Why Layer." This layer serves as a persistent, revisable, and auditable memory of intent, enabling systems that do not merely write code, but understand the hierarchical plans, trade-offs, and evolving goals that drive software evolution.

The analysis synthesizes findings from recent literature on:

1. **Intent Detection**: Moving beyond explicit prompting to infer latent objectives from fine-grained IDE telemetry, eye-tracking, and multimodal contexts.  
2. **Hierarchical Planning**: The renaissance of Hierarchical Task Networks (HTNs) and the development of Repository Planning Graphs (RPGs) to enable long-horizon, neuro-symbolic planning that scales to tens of thousands of lines of code.  
3. **Rationale Mining**: The extraction of design logic from unstructured artifacts to build an auditable history, enabling "Intent-Aware" refactoring and automated drift detection.

## ---

**2\. The Sensorium of Intent: From Explicit Prompts to Latent Inference**

The traditional interaction model for AI coding assistants relies on the "Explicit Prompt"—a natural language instruction typed by the developer. Research indicates this model is insufficient for complex software engineering tasks due to the high cognitive load of articulating context and the inherent ambiguity of natural language. The future of intent detection lies in **Latent Inference**, where the system deduces objectives from a multimodal sensorium of signals before the developer even types a query.

### **2.1 The Limitations of Explicit Prompting and Context Engineering**

The effectiveness of an LLM is strictly bounded by its context window and the quality of the prompt. In enterprise environments, developers work on specialized, complex tasks where the necessary context—architectural constraints, implicit dependencies, legacy patterns—is rarely fully articulated in a single prompt.

#### **2.1.1 The Ambiguity of Natural Language**

Studies analyzing developer interactions with tools like Google's "Transform Code" reveal that frequent re-prompting is a primary indicator of intent misalignment.1 Developers often provide underspecified instructions (e.g., "fix this error"), assuming the agent shares their mental model of the execution state. Without access to the implicit context (e.g., the stack trace in the terminal, the dependency graph of the module), the agent hallucinates a plausible but incorrect solution. This creates a cycle of "prompt engineering fatigue," where the cognitive effort of guiding the AI exceeds the cost of writing the code manually.2

#### **2.1.2 Multimodal Contextualization**

To transcend text-based limitations, research is pivoting toward **Multimodal Intent Inference**. Modern software development is inherently multimodal, involving code (text), diagrams (visual), and execution states (temporal).

* **Visual Intent**: LLMs with vision capabilities (e.g., GPT-4V, Gemini) can now ground code generation in visual artifacts. Agents can process UI sketches, architectural diagrams, or flowcharts to infer frontend intent (e.g., "implement this login screen with these specific spacing constraints") or backend logic (e.g., "build a microservice topology matching this whiteboard sketch").3  
* **Structural Context**: Feeding raw file contents often overwhelms the context window. Effective intent inference requires "Context Engineering"—abstracting the codebase into skeletal representations, call graphs, or UML-like structures that convey the *shape* of the system without the noise of implementation details.4

### **2.2 Telemetry as "Digital Body Language"**

A more profound layer of intent can be mined from **IDE Telemetry**. Just as human body language betrays internal emotional states, the micro-interactions of a developer—cursor movements, scrolling velocity, typing cadence—betray their cognitive state.

#### **2.2.1 Hierarchical Activity Recognition in the IDE**

By viewing software development as a hierarchy of activities (from "typing a character" to "refactoring a module"), systems can use low-level event streams to predict high-level goals.5

* **Event Aggregation**: Raw events (e.g., FileOpen, ScrollDown, TabSwitch) are aggregated into "atomic actions" (e.g., InspectClass, RunTest).  
* **Sequence Modeling**: Sequences of atomic actions form "Activity Signatures." For instance, a sequence of EditCode ![][image1] RunTest ![][image1] ReadStackTrace ![][image1] EditCode is a strong signature of a **Debugging** activity. Conversely, rapid file switching with long dwell times and no edits signals **Exploration/Comprehension**.7

By inferring the current activity mode, the agent can adapt its assistance strategy proactively. If the user is in "Exploration" mode, the agent might proactively generate summaries or dependency graphs. If in "Debugging" mode, it might prioritize stack trace analysis over code completion.2

#### **2.2.2 The "Control Model" for Intervention**

A critical application of telemetry-based inference is the **Control Model**, which governs the timing of AI intervention. Standard "Copilot" experiences often suffer from the "Triggering Problem"—interrupting the developer's flow with irrelevant suggestions. Recent research introduces "Control Models" trained on telemetry features such as typing speed, caret scope, and time-since-last-edit.9

* **The Trigger Model**: Predicts *when* a suggestion is desired. High typing speeds typically indicate a "Flow State" or active recall, where interruptions are detrimental. A pause following a complex method signature indicates uncertainty, a high-probability moment for intervention.11  
* **The Filter Model**: Predicts suggestion acceptance. Even if the model generates a completion, the filter model (a lightweight classifier) checks if the suggestion aligns with the user's inferred intent. If the telemetry suggests the user is deleting code (refactoring), a suggestion to add new boilerplate is suppressed.10

**Table 1: Telemetry Signals and Inferred Cognitive States**

| Telemetry Signal Cluster | Inferred Cognitive State | Predicted High-Level Intent | Recommended Agent Action |
| :---- | :---- | :---- | :---- |
| **High Velocity**: Rapid typing, linear cursor movement, minimal backspacing. | **Flow / Execution** | Implementing known logic (e.g., boilerplate, standard algorithms). | **Suppress** active interruptions. Provide phantom text completion only. |
| **High Latency**: Long pauses, frequent scrolling up/down within file, hovering over variables. | **Uncertainty / Recall** | API discovery, understanding local context, or architectural recall. | **Trigger** documentation retrieval or inline code explanation. |
| **Oscillation**: Rapid switching between Source and Test files, or Source and Terminal. | **Validation / Debug** | Verifying behavior, fixing regressions, or TDD cycle. | **Trigger** test execution helper or error log analysis. |
| **Deletion Dominance**: High volume of deletions, block selections, renaming operations. | **Restructuring / Refactor** | Improving code quality, removing technical debt. | **Suppress** generation. **Trigger** "Intent-Aware Refactoring" suggestions. |

### **2.3 The Biological Signal: Eye Tracking and Visual Attention**

Pushing the boundary of intent detection, research integrating **Eye Tracking** with IDEs offers the highest fidelity of cognitive state estimation. "Gaze" is a direct physiological proxy for attention, revealing what the developer is processing before they interact with the input devices.12

#### **2.3.1 Mapping Gaze to Architectural Goals**

By correlating gaze coordinates with screen elements (code lines, project explorer, debug variables), the system can construct a **Focus Set**—a weighted map of the code elements currently in the developer's working memory.13

* **Implicit Context Selection**: If a developer stares at Function A for 30 seconds and then starts typing in Function B, the system infers a dependency. Even if Function A is in a different file and not explicitly referenced, the agent includes it in the LLM's context window because the user's gaze indicated its relevance.14  
* **Scanpath Analysis**: The trajectory of the eyes (scanpath) reveals comprehension strategies. A linear scanpath suggests structured reading. An erratic, jumping scanpath suggests confusion or high cognitive load, potentially signaling a need for the agent to offer a simplification or summary of the complex code block.15

#### **2.3.2 Cognitive Load and Pupilometry**

Pupil dilation and blink rates serve as physiological indicators of **Cognitive Load**. Research shows that knowing whether code is AI-generated affects a developer's scrutiny; higher cognitive load is often observed when debugging AI-generated code due to lack of trust.16 By monitoring these signals, an intelligent environment can detect when a developer is overwhelmed. If cognitive load spikes during a code review task, the system might automatically break the diff into smaller, logical chunks to facilitate processing.18

## ---

**3\. Cognitive Architectures: Hierarchical Goal Modeling and Planning**

Once intent is inferred, it must be translated into a plan. For simple tasks, linear "Chain of Thought" (CoT) prompting is sufficient. However, for software engineering tasks that span thousands of lines of code and multiple modules, linear planning fails. The field is increasingly adopting **Hierarchical Goal Modeling** to represent intents as evolving, structured trees rather than transient sequences.

### **3.1 The Limits of Flat Planning in Software Engineering**

LLMs typically suffer from a "context horizon" problem. When generating a large repository, a flat generation model often loses track of earlier decisions, leading to circular dependencies or hallucinated imports. CoT does not natively support backtracking, state persistence, or modular reuse of planning logic.19

### **3.2 Hierarchical Task Networks (HTNs)**

**Hierarchical Task Network (HTN)** planning is a formalism that decomposes high-level goals into progressively smaller subtasks until primitive actions are reached. This structure mirrors the natural decomposition of software architectures (System ![][image1] Module ![][image1] Class ![][image1] Function).20

#### **3.2.1 Neuro-Symbolic HTN Generation**

Writing HTN domains (the rules of decomposition) is traditionally a manual, expert-intensive task. Current research focuses on **Neuro-Symbolic** approaches where LLMs automate the creation of these domains.22

* **LLM as Domain Author**: The LLM parses requirements and documentation to generate the HTN *methods* (e.g., "To CreateMicroservice, first DefineAPI, then ImplementController, then WriteTests").24  
* **Symbolic Planner as Executive**: A symbolic planner (e.g., JSHOP, PyHOP) executes the decomposition. This enforces logical soundness: the planner ensures that preconditions (e.g., "Database must be initialized") are met before scheduling dependent tasks. This hybrid approach combines the creativity of LLMs with the reliability of symbolic logic.25

#### **3.2.2 The Intention Tree as Dynamic Memory**

In agent frameworks (such as BDI \- Belief-Desire-Intention), the execution state is maintained in an **Intention Tree**.27

* **Root Node**: The ultimate objective (e.g., "Migrate User Auth to OAuth2").  
* **Branch Nodes**: Active strategies (e.g., "Update Database Schema").  
* **Leaf Nodes**: The primitive action currently being executed (e.g., "Run SQL migration script").

Crucially, this tree supports **Interruption and Resumption**. If an agent is executing a refactoring plan (Branch A) and encounters a compilation error (an event), it can pause Branch A, spawn a new Branch B ("Fix Compilation Error"), resolve it, and then resume Branch A with its context intact.28 This "stack-based" intention management is essential for long-running autonomous agents that must deal with emergent failures without losing their high-level goal.29

### **3.3 The Repository Planning Graph (RPG)**

A specific instantiation of hierarchical planning for code generation is the **Repository Planning Graph (RPG)**, notably implemented in the **ZeroRepo** framework.19

#### **3.3.1 Structure of the RPG**

The RPG serves as a "blueprint" that disentangles the "what" (requirements) from the "how" (implementation). It models the repository as a directed graph where:

* **Nodes** represent functional units at varying granularities:  
  * *Directory Nodes*: High-level modules.  
  * *File Nodes*: Compilation units.  
  * *Function/Class Nodes*: Logical units of code.  
* **Edges** represent relationships:  
  * *Composition Edges*: Hierarchy (Folder contains File).  
  * *Dependency Edges*: Data flow and import relationships (Function A calls Function B).31

#### **3.3.2 Graph-Guided Code Generation**

The RPG enables **Topological Generation**. Instead of generating code line-by-line from the top of a file, the agent generates code by traversing the dependency graph.33

1. **Proposal Phase**: The agent builds the graph structure first, defining filenames and function signatures without bodies.  
2. **Implementation Phase**: The agent visits nodes in topological order (dependencies first). When generating Function B (which calls Function A), the agent has the *ground truth* signature and behavior of Function A available in its context, because A has already been generated.31

**Impact on Scalability**: Empirical results show that graph-driven frameworks like ZeroRepo can generate coherent repositories of over **36,000 lines of code** (LOC), compared to \~3,500 LOC for flat-context baselines like Claude Code.19 The graph structure allows the agent to "page in" only the relevant subgraph for the current task, effectively extending the context window indefinitely.

**Table 2: Comparison of Planning Formalisms in Software Agents**

| Feature | Chain-of-Thought (CoT) | Hierarchical Task Network (HTN) | Repository Planning Graph (RPG) |
| :---- | :---- | :---- | :---- |
| **Structure** | Linear sequence of text steps. | Tree of Tasks and Methods. | Directed Acyclic Graph (DAG) of code units. |
| **State Tracking** | Implicit (in text history). | Explicit (Tree state, preconditions). | Explicit (Node completion status). |
| **Dependency Mgmt** | Weak (hallucinated references). | Strong (preconditions). | Strong (topological sort). |
| **Scalability** | Low (\< 5k LOC). Context saturation. | Medium (Task complexity limits). | High (\> 30k LOC). Modular context loading. |
| **Recovery** | Difficult (restart often required). | Backtracking/Plan Repair possible. | Granular re-generation of specific nodes. |

## ---

**4\. The "Why" Layer: Mining and Reconstructing Rationale**

While HTNs and RPGs manage future intents, a robust software lifecycle requires understanding *past* intents. The "Why Layer" is an auditable record of design rationale, linking every line of code back to a high-level goal or requirement.

### **4.1 The "Why" Gap in Version Control**

Standard version control systems (Git) record *who* made a change and *what* changed, but rarely *why*. Commit messages are notoriously poor proxies for rationale, often being empty, vague, or disconnected from the specific code edits.34 This lack of rationale makes "Drift Detection" impossible—one cannot know if a code change is a violation of design if the design intent was never recorded.

### **4.2 Mining Rationale from Developer Activity**

Research into **Rationale Mining** seeks to reconstruct this missing layer from secondary artifacts.

#### **4.2.1 Design Rationale Mining (DRMiner)**

Techniques like **DRMiner** leverage LLMs to parse unstructured issue logs, pull requests, and chat logs to extract design rationales.35

* **Entity Extraction**: The model identifies text segments representing *Issues*, *Alternatives*, *Decisions*, and *Arguments*.  
* **Knowledge Graph Construction**: These entities are linked into a graph. For example, a decision node ("Use Redis") is linked to an argument node ("Need sub-millisecond latency") and an alternative node ("Rejected Memcached due to persistence reqs").36  
* **Utility**: Experiments show that feeding this mined rationale to Automated Program Repair (APR) agents significantly improves their ability to fix bugs without regressing intended behaviors.35

### **4.3 Disentangling Tangled Commits**

A major obstacle to building a clean "Why Layer" is the **Tangled Commit**—a single commit that bundles multiple unrelated changes (e.g., a bug fix, a refactor, and a feature addition). This obscures intent and creates a noisy history.37

#### **4.3.1 Hierarchical Clustering for Commit Untangling**

State-of-the-art research employs **Hierarchical Clustering** and code-aware embeddings to disentangle these commits into atomic units.39

1. **Granular Representation**: The commit is decomposed into "diff hunks" (contiguous blocks of changed lines).  
2. **Semantic Embedding**: Each hunk is embedded using a model like CodeBERT, capturing both its textual semantics and its syntactic role (e.g., "method declaration" vs "variable assignment").  
3. **Clustering**: A hierarchical clustering algorithm groups hunks based on semantic similarity and structural dependency (e.g., a change to a function clusters with the change to its unit test).40  
4. **Intent Labeling**: An LLM analyzes each cluster to assign a specific intent label (e.g., Cluster 1 \= "Refactor Authentication", Cluster 2 \= "Fix NPE in Logging").

This process creates "Virtual Atomic Commits," allowing the system to attribute specific intents to specific code edits, even if the human developer failed to separate them.41

### **4.4 Intent-Driven Traceability Link Recovery**

To make the "Why Layer" fully auditable, code must be traceable back to requirements. **Traceability Link Recovery (TLR)** is evolving from keyword matching to intent-based linking.

* **Neuro-Symbolic Linking**: In generative workflows (like ZeroRepo), traceability is established *by construction*. Since Function X was generated to satisfy Requirement Node Y in the RPG, the link is explicit and persistent.19  
* **Deep Learning for Legacy Code**: For existing codebases, "Two-Tower" embedding models map the semantic space of requirements documents to the semantic space of code, recovering links based on latent intent (e.g., linking "Secure Data Transmission" to ssl\_context.load\_cert\_chain()).43

## ---

**5\. Persistent Intention Memory and Drift Detection**

The unification of the **Future Plan** (HTN/RPG) and the **Past Rationale** (Mined History) creates a new system capability: **Persistent Intention Memory**. This memory is the baseline for detecting **Drift**.

### **5.1 Intention-Aware Memory Structures**

This memory is not a static database but a living model of the software's purpose.44

* **Long-Term Memory**: Stores the **RPG** and the **Rationale Knowledge Graph**. It answers: "What is the architectural pattern of this module?" or "Why did we choose this library?".45  
* **Short-Term Memory**: Stores the active **Intention Tree**. It answers: "What task is the agent currently performing?"

### **5.2 Detecting Design-Implementation Drift (DID)**

**Concept Drift** in ML refers to changes in data distribution. In software, **Design-Implementation Drift (DID)** occurs when the code evolves in a way that violates the original design intent or documentation.46

#### **5.2.1 Mechanism of Drift Detection**

With a persistent RPG, drift detection becomes an automated variance analysis.

* **Reference State**: The RPG defines the allowed dependencies (e.g., "The PaymentService must only communicate with StripeAPI via the GatewayInterface").  
* **Observed State**: The agent analyzes a new Pull Request and detects a direct HTTP call from PaymentService to StripeAPI.  
* **Drift Signal**: The agent flags this as **Structural Drift**. Unlike a linter which checks syntax, this checks *intent*. The agent can comment: "This change introduces a direct coupling that violates the architectural constraint defined in the RPG. Rationale for restriction: 'Enable easy switching of payment providers'".48

#### **5.2.2 Living Documentation and Self-Correction**

This enables **Living Documentation**. Documentation is no longer a static text file that rots; it is a view of the RPG.

* **Auto-Updating**: If the drift is accepted (e.g., the architecture *should* change), the agent updates the RPG. This update automatically propagates to the generated documentation, ensuring the "docs" always match the code.49  
* **Drift-Driven Maintenance**: The agent can proactively schedule maintenance tasks. If it detects "Semantic Drift" (e.g., a function's implementation no longer matches its docstring), it adds a "Update Documentation" task to its own Intention Tree.51

## ---

**6\. Applications: Intent-Aware Refactoring and Auditable Evolution**

The ultimate utility of the "Why Layer" is to support the continuous, safe evolution of the codebase.

### **6.1 Intent-Aware Refactoring**

Standard refactoring tools (like those in IDEs) are purely syntactic (e.g., "Rename Variable"). **Intent-Aware Refactoring** leverages the inferred goal to guide complex transformations.52

* **Scenario**: A developer highlights a monolithic class and prompts "Cleanup."  
* **Inference**: The system analyzes the class and detects high coupling. It retrieves the "Single Responsibility Principle" from its method library.  
* **Goal Modeling**: It constructs an HTN for RefactorToStrategyPattern.  
* **Plan Execution**: It decomposes this into ExtractInterface, CreateStrategyClasses, and InjectDependency.  
* **Guidance**: Instead of silently changing code, the agent presents the plan: *"I recommend extracting the validation logic into a Strategy pattern to improve testability. Step 1: Extract IValidator interface..."*.51

### **6.2 Regulatory Compliance and Auditability**

In regulated industries (Finance, Healthcare, Aerospace), the "Why Layer" provides a mandatory **Audit Trail**.

* **Query**: "Why was the encryption algorithm changed in release 2.4?"  
* **System Response**: "Change traced to Commit a1b2c. Intent: 'Compliance with new NIST standards'. Rationale linked to Jira Ticket SEC-99. Approved by Agent SecurityBot after verifying Test-EncryptionStrength.".53

This turns the repository into a transparent, queryable database of decisions, fulfilling the requirement for **Auditable AI**.

## ---

**7\. Conclusion**

The integration of **Multimodal Intent Inference**, **Hierarchical Goal Modeling**, and **Rationale Mining** represents the next frontier in software engineering. We are moving beyond "smart" text editors to **Cognitive Integrated Development Environments (C-IDEs)** that act as true collaborators.

By representing software not just as a collection of text files, but as a **Repository Planning Graph** backed by a **Persistent Intention Memory**, we enable systems that:

1. **Scale**: Manage complexity through hierarchical abstraction and graph-based context loading.  
2. **Persist**: Maintain architectural coherence over long time horizons.  
3. **Collaborate**: Infer developer needs from telemetry and gaze, reducing the cognitive load of prompting.  
4. **Audit**: Provide a transparent "Why Layer" that links every line of code to its originating intent.

This architecture ensures that as software systems grow in complexity and autonomy, they remain aligned with the human purposes they serve. The "Why" is no longer lost; it is encoded, tracked, and verified as rigorously as the "What."

#### **Works cited**

1. Prompting LLMs for Code Editing: Struggles and Remedies \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2504.20196v1](https://arxiv.org/html/2504.20196v1)  
2. Understanding and supporting how developers prompt for LLM-powered code editing in practice \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2504.20196v2](https://arxiv.org/html/2504.20196v2)  
3. Multimodal text and image prompting | Solutions for Developers, accessed on February 2, 2026, [https://developers.google.com/solutions/ai-images](https://developers.google.com/solutions/ai-images)  
4. A Survey on Code Generation with LLM-based Agents \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2508.00083v1](https://arxiv.org/html/2508.00083v1)  
5. \[1503.01820\] Latent Hierarchical Model for Activity Recognition \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/1503.01820](https://arxiv.org/abs/1503.01820)  
6. HARE: Unifying the Human Activity Recognition Engineering Workflow \- MDPI, accessed on February 2, 2026, [https://www.mdpi.com/1424-8220/23/23/9571](https://www.mdpi.com/1424-8220/23/23/9571)  
7. (PDF) Predicting Future Developer Behavior in the IDE Using Topic Models \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/319438855\_Predicting\_Future\_Developer\_Behavior\_in\_the\_IDE\_Using\_Topic\_Models](https://www.researchgate.net/publication/319438855_Predicting_Future_Developer_Behavior_in_the_IDE_Using_Topic_Models)  
8. Improving Event Aggregation in Automation of Software Development Workflows \- Simple search, accessed on February 2, 2026, [https://liu.diva-portal.org/smash/get/diva2:1981358/FULLTEXT01.pdf](https://liu.diva-portal.org/smash/get/diva2:1981358/FULLTEXT01.pdf)  
9. \[Literature Review\] Control Models for In-IDE Code Completion \- Moonlight, accessed on February 2, 2026, [https://www.themoonlight.io/review/control-models-for-in-ide-code-completion](https://www.themoonlight.io/review/control-models-for-in-ide-code-completion)  
10. Pre-Filtering Code Suggestions using Developer Behavioral Telemetry to Optimize LLM-Assisted Programming | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/397934998\_Pre-Filtering\_Code\_Suggestions\_using\_Developer\_Behavioral\_Telemetry\_to\_Optimize\_LLM-Assisted\_Programming](https://www.researchgate.net/publication/397934998_Pre-Filtering_Code_Suggestions_using_Developer_Behavioral_Telemetry_to_Optimize_LLM-Assisted_Programming)  
11. Predicting Developer Acceptance of AI-Generated Code Suggestions \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.21379v1](https://arxiv.org/html/2601.21379v1)  
12. MAP3D: An explorative approach for automatic mapping of real-world eye-tracking data on a virtual 3D model \- NIH, accessed on February 2, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11318232/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11318232/)  
13. Eye-Tracking Advancements in Architecture: A Review of Recent Studies \- MDPI, accessed on February 2, 2026, [https://www.mdpi.com/2075-5309/15/19/3496](https://www.mdpi.com/2075-5309/15/19/3496)  
14. A Study of Visual Studio Usage in Practice | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/303513617\_A\_Study\_of\_Visual\_Studio\_Usage\_in\_Practice](https://www.researchgate.net/publication/303513617_A_Study_of_Visual_Studio_Usage_in_Practice)  
15. Developer Behaviors in Validating and Repairing LLM-Generated Code Using IDE and Eye Tracking \- Ningzhi Tang, accessed on February 2, 2026, [https://www.nztang.com/assets/files/papers/tang\_vlhcc24.pdf](https://www.nztang.com/assets/files/papers/tang_vlhcc24.pdf)  
16. Developer Behaviors in Validating and Repairing LLM-Generated Code Using IDE and Eye Tracking | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/384979102\_Developer\_Behaviors\_in\_Validating\_and\_Repairing\_LLM-Generated\_Code\_Using\_IDE\_and\_Eye\_Tracking](https://www.researchgate.net/publication/384979102_Developer_Behaviors_in_Validating_and_Repairing_LLM-Generated_Code_Using_IDE_and_Eye_Tracking)  
17. A Study on Developer Behaviors for Validating and Repairing LLM-Generated Code Using Eye Tracking and IDE Actions, accessed on February 2, 2026, [https://par.nsf.gov/servlets/purl/10576279](https://par.nsf.gov/servlets/purl/10576279)  
18. Estimating Developers' Cognitive Load at a Fine-grained Level Using Eye-tracking Measures \- University of St.Gallen, accessed on February 2, 2026, [https://www.alexandria.unisg.ch/server/api/core/bitstreams/f02d1ea1-90ab-4b04-967f-72ea6e579d89/content](https://www.alexandria.unisg.ch/server/api/core/bitstreams/f02d1ea1-90ab-4b04-967f-72ea6e579d89/content)  
19. RPG: A Repository Planning Graph for Unified and Scalable Codebase Generation, accessed on February 2, 2026, [https://openreview.net/forum?id=VAQq3Y8tIF](https://openreview.net/forum?id=VAQq3Y8tIF)  
20. Hierarchical Task Networks (HTNs): Structure, Algorithms, and Applications in AI, accessed on February 2, 2026, [https://www.geeksforgeeks.org/artificial-intelligence/hierarchical-task-networks-htns-structure-algorithms-and-applications-in-ai/](https://www.geeksforgeeks.org/artificial-intelligence/hierarchical-task-networks-htns-structure-algorithms-and-applications-in-ai/)  
21. Hierarchical Task Network (HTN) Planning in AI \- GeeksforGeeks, accessed on February 2, 2026, [https://www.geeksforgeeks.org/artificial-intelligence/hierarchical-task-network-htn-planning-in-ai/](https://www.geeksforgeeks.org/artificial-intelligence/hierarchical-task-network-htn-planning-in-ai/)  
22. A Roadmap to Guide the Integration of LLMs in Hierarchical Planning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2501.08068v1](https://arxiv.org/html/2501.08068v1)  
23. Leveraging LLMs for HTN Domain Model Generation via Prompt Engineering, accessed on February 2, 2026, [https://elib.uni-stuttgart.de/server/api/core/bitstreams/f5ac9d58-c234-4470-9e0f-e4d7b912ef06/content](https://elib.uni-stuttgart.de/server/api/core/bitstreams/f5ac9d58-c234-4470-9e0f-e4d7b912ef06/content)  
24. Towards a General Framework for HTN Modeling with LLMs | Request PDF \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/397934786\_Towards\_a\_General\_Framework\_for\_HTN\_Modeling\_with\_LLMs](https://www.researchgate.net/publication/397934786_Towards_a_General_Framework_for_HTN_Modeling_with_LLMs)  
25. Hierarchical Task Network Planning \- Emergent Mind, accessed on February 2, 2026, [https://www.emergentmind.com/topics/hierarchical-task-network-htn-planning-framework](https://www.emergentmind.com/topics/hierarchical-task-network-htn-planning-framework)  
26. Neuro-Symbolic AI Agents for Software Project Scheduling \- Diva Portal, accessed on February 2, 2026, [https://uu.diva-portal.org/smash/get/diva2:1982332/FULLTEXT01.pdf](https://uu.diva-portal.org/smash/get/diva2:1982332/FULLTEXT01.pdf)  
27. Angerona \- A Multiagent Framework for Logic Based Agents with application to Secrecy Preservation \- SFB 876, accessed on February 2, 2026, [https://sfb876.tu-dortmund.de/PublicPublicationFiles/kruempelmann\_janus\_2014a.pdf](https://sfb876.tu-dortmund.de/PublicPublicationFiles/kruempelmann_janus_2014a.pdf)  
28. Proceedings of the 16th Workshop \`\`From Object to Agents'' \- CEUR-WS.org, accessed on February 2, 2026, [https://ceur-ws.org/Vol-1382/WOA15proceedings.pdf](https://ceur-ws.org/Vol-1382/WOA15proceedings.pdf)  
29. A Survey of Research in Distributed, Continual Planning \- AAAI Publications, accessed on February 2, 2026, [https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/download/1475/1374](https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/download/1475/1374)  
30. RPG: A Repository Planning Graph for Unified and Scalable Codebase Generation \- Microsoft Research, accessed on February 2, 2026, [https://www.microsoft.com/en-us/research/publication/rpg-a-repository-planning-graph-for-unified-and-scalable-codebase-generation/](https://www.microsoft.com/en-us/research/publication/rpg-a-repository-planning-graph-for-unified-and-scalable-codebase-generation/)  
31. RPG: A Repository Planning Graph for Unified and Scalable Codebase Generation \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2509.16198v2](https://arxiv.org/html/2509.16198v2)  
32. ZeroRepo: Graph-Guided Repo Generation \- Emergent Mind, accessed on February 2, 2026, [https://www.emergentmind.com/topics/zerorepo-framework](https://www.emergentmind.com/topics/zerorepo-framework)  
33. RPG for Code: How AI Assembles Entire Projects Using Graphs | by Dataism Lab | Medium, accessed on February 2, 2026, [https://medium.com/@dataism/rpg-for-code-how-ai-assembles-entire-projects-using-graphs-c304ac8cf7b3](https://medium.com/@dataism/rpg-for-code-how-ai-assembles-entire-projects-using-graphs-c304ac8cf7b3)  
34. On Automatically Generating Commit Messages via Summarization of Source Code Changes, accessed on February 2, 2026, [https://www.cs.wm.edu/\~denys/pubs/SCAM14-ChangeScribe-CR.pdf](https://www.cs.wm.edu/~denys/pubs/SCAM14-ChangeScribe-CR.pdf)  
35. A Novel Approach for Automated Design Information Mining from Issue Logs \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2405.19623v1](https://arxiv.org/html/2405.19623v1)  
36. A Novel Approach for Automated Design Information Mining from Issue Logs \- arXiv, accessed on February 2, 2026, [https://arxiv.org/pdf/2405.19623](https://arxiv.org/pdf/2405.19623)  
37. \[2601.21298\] Detecting Multiple Semantic Concerns in Tangled Code Commits \- arXiv, accessed on February 2, 2026, [https://www.arxiv.org/abs/2601.21298](https://www.arxiv.org/abs/2601.21298)  
38. Detecting Multiple Semantic Concerns in Tangled Code Commits \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.21298v1](https://arxiv.org/html/2601.21298v1)  
39. LLM-Driven Collaborative Model for Untangling Commits via Explicit and Implicit Dependency Reasoning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2507.16395v1](https://arxiv.org/html/2507.16395v1)  
40. Atomizer: An LLM-based Collaborative Multi-Agent Framework for Intent-Driven Commit Untangling \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.01233v1](https://arxiv.org/html/2601.01233v1)  
41. Towards Generating the Rationale for Code Changes \- IEEE Xplore, accessed on February 2, 2026, [https://ieeexplore.ieee.org/iel8/11025805/11025854/11025863.pdf](https://ieeexplore.ieee.org/iel8/11025805/11025854/11025863.pdf)  
42. Building AI Agents to Automate Software Test Case Creation | NVIDIA Technical Blog, accessed on February 2, 2026, [https://developer.nvidia.com/blog/building-ai-agents-to-automate-software-test-case-creation/](https://developer.nvidia.com/blog/building-ai-agents-to-automate-software-test-case-creation/)  
43. INDIRECT: Intent-Driven Requirements-to-Code Traceability \- IEEE Xplore, accessed on February 2, 2026, [https://ieeexplore.ieee.org/document/8802673/](https://ieeexplore.ieee.org/document/8802673/)  
44. Toward Autonomous LLM-Based AI Agents for Predictive Maintenance: State of the Art, Challenges, and Future Perspectives \- MDPI, accessed on February 2, 2026, [https://www.mdpi.com/2076-3417/15/21/11515](https://www.mdpi.com/2076-3417/15/21/11515)  
45. LLM Agents \- Prompt Engineering Guide, accessed on February 2, 2026, [https://www.promptingguide.ai/research/llm-agents](https://www.promptingguide.ai/research/llm-agents)  
46. What is concept drift in ML, and how to detect and address it \- Evidently AI, accessed on February 2, 2026, [https://www.evidentlyai.com/ml-in-production/concept-drift](https://www.evidentlyai.com/ml-in-production/concept-drift)  
47. Capturing and Understanding the Drift Between Design, Implementation, and Documentation, accessed on February 2, 2026, [https://www.inf.usi.ch/phd/raglianti/publications/Romeo2024a.pdf](https://www.inf.usi.ch/phd/raglianti/publications/Romeo2024a.pdf)  
48. AI-Assisted Design Documentation: How to Build Living Style Guides That Update Themselves | by Jamieson Rothwell | Beyond the Pixels \- Medium, accessed on February 2, 2026, [https://medium.com/ux-management/ai-assisted-design-documentation-how-to-build-living-style-guides-that-update-themselves-e0c4fd81433b](https://medium.com/ux-management/ai-assisted-design-documentation-how-to-build-living-style-guides-that-update-themselves-e0c4fd81433b)  
49. When Documentation Lies: Detecting Drift Between Code and Reality \- Hackernoon, accessed on February 2, 2026, [https://hackernoon.com/when-documentation-lies-detecting-drift-between-code-and-reality](https://hackernoon.com/when-documentation-lies-detecting-drift-between-code-and-reality)  
50. ruvnet/claude-flow: The leading agent orchestration platform for Claude. Deploy intelligent multi-agent swarms, coordinate autonomous workflows, and build conversational AI systems. Features enterprise-grade architecture, distributed swarm intelligence, RAG integration, and native Claude Code support via MCP protocol. Ranked \#1 in agent-based \- GitHub, accessed on February 2, 2026, [https://github.com/ruvnet/claude-flow](https://github.com/ruvnet/claude-flow)  
51. Which Product Automates Refactor Suggestions in JetBrains IDEs? \- Byte, accessed on February 2, 2026, [https://byteable.ai/blog/which-product-automates-refactor-suggestions-in-jetbrains-ides](https://byteable.ai/blog/which-product-automates-refactor-suggestions-in-jetbrains-ides)  
52. AI Code Refactoring: Tools, Tactics & Best Practices, accessed on February 2, 2026, [https://www.augmentcode.com/tools/ai-code-refactoring-tools-tactics-and-best-practices](https://www.augmentcode.com/tools/ai-code-refactoring-tools-tactics-and-best-practices)  
53. The Complete B2B Handbook to Smart Contract Development: From Fundamentals to Future-Proof Solutions \- Vegavid Technology, accessed on February 2, 2026, [https://vegavid.com/blog/smart-contract-development-enterprise-guide](https://vegavid.com/blog/smart-contract-development-enterprise-guide)  
54. Causal AI Decision Intelligence: Why It Will Emerge in 2026 \- theCUBE Research, accessed on February 2, 2026, [https://thecuberesearch.com/why-causal-ai-decision-intelligence-2026/](https://thecuberesearch.com/why-causal-ai-decision-intelligence-2026/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAAAVUlEQVR4XmNgGAWjgKpgL7oAJeAfugAlwAaIy9AFKQHngNgcXRAETMjEt4B4HwMa8CMTX4NiFgYKwUQg9kYXJAcoAnEnuiC54BO6ACXgMLrAKBhuAACnlhESw2iRqwAAAABJRU5ErkJggg==>