# **The Cognitive Architecture of Digital Volition: A Comprehensive Analysis of Intent Detection, Taxonomy, and Hierarchical Modelling in the Age of Large Language Models**

## **Executive Summary**

The capability of computational systems to discern, categorize, and model human intent represents one of the most significant frontiers in modern artificial intelligence and human-computer interaction. As of 2024 and 2025, the paradigm of intent analysis has shifted radically from keyword-based heuristic systems to sophisticated, generative architectures driven by Large Language Models (LLMs). This transformation has necessitated new taxonomies for understanding user needs within software environments and advanced data structures—specifically intention trees and hierarchical task networks (HTNs)—to map the complex, multi-step cognition of human agents.

This report provides an exhaustive examination of the current state of research and literature regarding three critical pillars of this domain: the detection of intentions using LLMs, the classification of intentions within web and software interfaces, and the structural modelling of intention trees. By synthesizing high-impact research from 2024 and 2025, including breakthrough frameworks such as Gen-PINT, ChatHTN, SpecRover, and the Taxonomy of User Needs and Actions (TUNA), this document offers a definitive reference for researchers and practitioners navigating the intersection of cognitive modelling and software engineering.

## ---

**1\. Detecting Intentions via Large Language Models (LLMs)**

The detection of user intent has historically been treated as a discriminative classification problem—mapping an input utterance to a predefined label. However, the advent of Large Language Models has redefined this task as a generative reasoning process. The literature from 2024 and 2025 highlights a move away from simple pattern matching toward systems that "understand" intent through contextual decomposition, instruction tuning, and chain-of-thought reasoning.

### **1.1 The Paradigm Shift: From Discriminative to Generative Detection**

Traditional intent detection relied heavily on supervised learning models like BERT, which required extensive labeled datasets to function effectively. While these models achieved high precision in closed domains, they struggled with the "long tail" of user queries and zero-shot scenarios where new intents emerge dynamically. The rigidity of fixed label spaces meant that any "Out-of-Scope" (OOS) query resulted in prediction failures or confident errors.

Recent advancements argue for a generative approach. The **Gen-PINT** (Generative Pre-trained INTent detection) framework represents a pivotal development in this space.1 Unlike discriminative models that output a probability distribution over fixed classes, Gen-PINT reformulates intent detection as a text-to-text generation task. By leveraging instruction tuning, the model is taught to generate the intent label itself based on a "task definition" and "demonstrations" provided in the context window.1

This generative methodology offers several distinct advantages:

1. **Semantic Generalization:** Generative models can infer labels that were not present in their training set by understanding the semantic relationship between the query and the provided class descriptions.  
2. **Instruction Following:** By treating intent detection as an instruction-following task, systems can be rapidly adapted to new domains (e.g., banking, healthcare, e-commerce) simply by changing the prompt instructions, rather than retraining the model weights.1  
3. **Cross-Task Transfer:** The ability of LLMs to perform zero-shot classification suggests that models tuned on general instruction datasets (like FLAN-T5 or GPT-4) can perform intent detection with near-state-of-the-art accuracy without task-specific fine-tuning.2

#### **1.1.1 Zero-Shot and Few-Shot Capabilities**

The literature emphasizes the efficacy of LLMs in zero-shot and few-shot settings. Research benchmarks from 2024 indicate that while small language models (SLMs) are becoming increasingly capable, large frontier models still dominate in complex reasoning tasks required for disambiguating subtle intents.3

For instance, in domain-specific applications such as healthcare (e.g., detecting depression or chronic conditions from self-reports), LLMs used as zero-shot classifiers have shown robustness comparable to traditional supervised models, with the added benefit of explainability.4 The use of models like GPT-3.5 and GPT-4 allows for the extraction of nuanced medical intents (e.g., "Change in medication regimen" vs. "Self-report adverse pregnancy outcomes") without the need for thousands of labeled training examples.4

However, the computational cost of these inferences remains a bottleneck. Hybrid approaches proposed in 2025 suggest using smaller, efficient models for routing routine queries and reserving LLMs for ambiguous or "out-of-scope" (OOS) intents that require deep semantic analysis.5 This hierarchical routing optimizes for both cost and accuracy, using the LLM essentially as a "supervisor" for the smaller models.

### **1.2 Chain-of-Thought (CoT) and Reasoning-Based Detection**

A critical limitation of standard prompting is the "black box" nature of the output. To address this, researchers have adopted **Chain-of-Thought (CoT)** prompting to enhance intent detection accuracy, particularly for complex or multi-faceted user queries.6

CoT prompting encourages the LLM to generate a step-by-step reasoning trace before concluding with the final intent label. This mimics the human cognitive process of "System 2" thinking—slow, deliberative, and logical.8

* **Mechanism:** Instead of simply asking "What is the intent of this query?", a CoT prompt might ask the model to "Analyze the user's request, identify the key entities, determine the temporal constraints, and then classify the intent."  
* **Impact:** Studies show that CoT significantly improves performance on complex tasks, such as math word problems or multi-turn dialogue analysis, by allowing the model to decompose the problem.9 In the context of intent detection, CoT allows the model to explicitly state its interpretation of ambiguous phrases (e.g., "I'm looking for a bank" could mean a financial institution or a river edge) before committing to a classification.10

Furthermore, **Decomposed Workflow** architectures have emerged in 2025\. These systems break down a user's interaction trajectory into individual screen summaries or events. A small multimodal LLM summarizes each interaction, and these summaries are then fed into a larger model to predict the general intent of the trajectory.11 This decomposition outperforms standard end-to-end fine-tuning by isolating the "atomic" units of user behavior, making the final intent prediction more robust to noise.11

### **1.3 Instruction Tuning and Architectural Innovations**

Instruction tuning—fine-tuning models on datasets of tasks formatted as instructions—has become a cornerstone of modern intent detection. By training models to follow meta-instructions (e.g., "Classify this text into one of the following categories: A, B, C"), researchers have created systems that generalize better to unseen intents than traditional BERT-based classifiers.2

The **Gen-PINT** model explicitly utilizes this by including a "Task Definition" in its input schema, which describes the intent detection task and the target format.1 This aligns the pre-trained model's internal representations with the specific constraints of the classification task, effectively "programming" the model via natural language to act as a specific type of classifier.

Moreover, recent work has explored **Hybrid Architectures** that combine the retrieval capabilities of vector databases with the reasoning of LLMs. In these setups, RAG (Retrieval-Augmented Generation) is used to fetch relevant intent definitions or similar past examples, which are then used by the LLM to ground its classification. This reduces hallucinations and ensures that the detected intent aligns with the organization's valid business processes.13

### **1.4 Affective and Multi-Modal Intent Detection**

Intent is rarely purely informational; it is often laden with emotion, urgency, and sarcasm. Research from 2024-2025 highlights the necessity of joint modelling for **emotion and intent**.

Recent studies have shown that sarcasm detection is inextricably linked to accurate intent classification. A 2025 study highlighted that sarcasm often inverts the literal meaning of an utterance, causing standard intent classifiers to fail catastrophically (e.g., "Great, another delay" being classified as positive feedback).15 By constructing tasks that perform sarcasm detection, semantic classification, and emotion classification simultaneously, models can achieve a more holistic understanding of the user's state of mind. This multi-task learning approach helps the model differentiate between a genuine query for help and a frustrated rhetorical question.15

## ---

**2\. Taxonomies of Intentions in Website and Software Environments**

As software becomes more "agentic" and conversational, the simple categorization of user intent (e.g., "login," "search," "buy") has proven insufficient. The research landscape in 2024-2025 has produced granular taxonomies that capture the nuance of human-computer interaction, distinguishing between the *user's* psychological needs, the *developer's* implementation intent, and the *software agent's* autonomous goals.

### **2.1 The Taxonomy of User Needs and Actions (TUNA)**

A landmark contribution to this field is the **Taxonomy of User Needs and Actions (TUNA)**, proposed by Shelby, Diaz, and Prabhakaran in 2025\.16 This framework was developed to address the limitations of existing taxonomies which failed to capture the social and meta-conversational aspects of interacting with generative AI agents.

TUNA organizes user intentions into a high-level hierarchy with distinct "Modes" and "Strategies," providing a comprehensive map of how users interact with modern software.

#### **2.1.1 Modes of Interaction**

1. **Information Seeking:** The traditional search behavior. Strategies include *Retrieval* (finding specific facts), *Discovery* (exploring new topics), and *Clarification*.16  
2. **Information Processing & Synthesis:** Beyond finding data, users want software to manipulate it. Request types include *Summarization*, *Distillation*, and *Information Structuring*.16  
3. **Content Creation & Transformation:** A major category for Generative AI. This includes *Generation* (creative or functional writing) and *Modification* (editing, translating, paraphrasing).16  
4. **Social Interaction:** A novel addition acknowledging that users treat AI agents as social entities. Strategies include *Sociability* (banter, etiquette) and *Shared Understanding*.16  
5. **Meta-Conversation:** Users negotiating the terms of the interaction itself. Request types include *System Management* (asking the AI to change its persona or style) and *Conversation Management* (correcting the AI's previous outputs).16  
6. **Procedural Guidance & Execution:** This mode covers the "how-to" aspects of software, including *Method Recommendation*, *Feasibility Assessment*, and *Error Solution*.16

This taxonomy is critical because it moves beyond the transactional view of software usage. It recognizes that "social banter" or "emotional expression" are valid user intents that software must handle to build trust and engagement.16

The following table summarizes the high-level structure of the TUNA taxonomy as derived from the 2025 literature:

| Mode | Strategy | Request Types |
| :---- | :---- | :---- |
| **Information Seeking** | Retrieval, Discovery, Clarification | Direct fact question, concept search, refinding request, unknown-item search. |
| **Content Creation** | Generation, Modification | Creative/functional content generation, editing, translation, paraphrasing, reformatting. |
| **Social Interaction** | Sociability, Shared Understanding | Social banter, etiquette, emotional expression, requesting acknowledgment. |
| **Meta-Conversation** | System Management, Conversation Mgmt | Persona directive, stylistic constraint, regeneration request, history query. |
| **Procedural Guidance** | Execution, Guidance | Error solution, autonomous task completion, logical reasoning, calculation. |

### **2.2 Classic vs. Modern Web Intents**

While TUNA represents the cutting edge, foundational SEO and web intent models remain relevant for navigational structures. The classic "Navigational, Informational, Transactional" model has been refined to include **Commercial** (researching before buying) and **Local** (finding services nearby) intents.18

* **Navigational:** The user wants to go to a specific place (e.g., "Login page").  
* **Informational:** The user seeks knowledge (e.g., "How to reset password").  
* **Commercial Investigation:** The user is comparing options (e.g., "Best CRM software 2025").  
* **Transactional:** The user is ready to act (e.g., "Subscribe now").  
* **Local Intent:** A newer category driven by mobile usage, focusing on physical proximity (e.g., "near me" searches).20

In modern software engineering, recognizing these intents allows for **Intent-Driven Design (IDD)**. IDD proposes that software interfaces should be fluid, reconfiguring themselves based on the user's detected intent rather than forcing the user to navigate static menus.21 For example, if a user's intent is detected as "Commercial Investigation," the software might dynamically generate a comparison table of features, rather than just showing a standard product list.

### **2.3 Developer Intent vs. User Intent**

A unique sub-field of intent research focuses on **Developer Intent**—the purpose behind the code itself. Understanding developer intent is crucial for automated program repair and software maintenance.

#### **2.3.1 SpecRover and Code Intent Extraction**

**SpecRover**, a system introduced in 2024/2025, represents a breakthrough in extracting "code intent" to fix bugs. It uses LLMs to analyze issue descriptions (User Intent) and the codebase to infer the "Developer Intent" (what the code *should* have done).23

The SpecRover workflow operates as a multi-agent system:

1. **Reproducer Agent:** Reads the issue and attempts to write a test case that fails, proving the bug exists.  
2. **Context Retrieval Agent:** Scans the codebase to understand the surrounding functions and logic.  
3. **Patching Agent:** Proposes a fix based on the inferred intent.  
4. **Reviewer Agent:** Validates if the proposed patch aligns with the original intent of the software and passes the regression tests.26

This highlights the **Intent Gap** in software engineering: the discrepancy between the user's desire ("I want to save this file") and the developer's implementation ("Write bytes to disk"). LLMs are now being used to bridge this by generating specifications and "docstrings" that explicitly state the intent of code blocks, allowing for better automated reasoning.27

#### **2.3.2 Commit Message Classification**

Understanding developer intent also extends to version control. Classifying **Commit Messages** is a form of intent detection used to monitor software evolution. Using taxonomies like Swanson's (Corrective, Adaptive, Perfective), researchers use models like DistilBERT and LLMs to classify commits into categories such as "Fix" (corrective), "Feat" (adaptive), or "Refactor" (perfective).28 This allows organizations to track if their engineering effort is going towards new features (Intent: Innovation) or bug fixes (Intent: Maintenance).

### **2.4 Agentic Intentions and Autonomy**

As software evolves into "Agents," the concept of intent becomes recursive: the software itself possesses "Agentic Intentions." Nwana's typology of software agents remains the foundational classification, updated for the AI era.31

**Key Attributes of Agentic Intent:**

1. **Autonomy:** The agent operates without direct intervention.  
2. **Proactivity:** The agent exhibits goal-directed behavior (taking initiative).  
3. **Social Ability:** The agent interacts with other agents or humans.  
4. **Adaptability:** The agent improves over time.

In 2025, **"Agentic Patterns"** have emerged as a design standard. These patterns describe how agents should break down high-level goals into sub-intentions.33 For instance, a "Supply Chain AI" agent might have a high-level intent to "Optimizing Inventory," which it autonomously decomposes into sub-intents like "Forecast Demand," "Place Orders," and "Negotiate Shipping".35 This requires the software to maintain an internal "intention tree," modeling its own plans and the user's desires simultaneously.

### **2.5 API Intent and Description Classification**

At the interface level, classifying the intent of **APIs** is critical for automated service discovery. Research from 2024 demonstrates that LLMs (specifically GPT-4) can perform zero-shot classification of OpenAPI Specifications (OAS) to determine the "API Intent".13 By analyzing the text descriptions within the API documentation, models can label APIs with high accuracy (e.g., "Payment Processing," "Data Visualization"), even outperforming supervised models like BERT in small-data regimes.13 This "API Intent" is the bridge between the software's capability and the external developer's need.

### **2.6 Intent-Based Networking (IBN)**

In the domain of cybersecurity and infrastructure, **Intent-Based Networking (IBN)** translates high-level business goals (Commander's Intent) into low-level network configurations.36

* **Concept:** Instead of manually configuring routers, an administrator states an intent: "Ensure secure, high-bandwidth video conferencing for the executive team."  
* **Mechanism:** The IBN software automatically translates this intent into policies (QoS rules, firewall settings) across the network fabric.37  
* **Security:** This is evolved into "Intent-Driven Security," where the system proactively reconfigures perimeters based on the intent to "Neutralize Threat X".38

## ---

**3\. Modelling Intention Trees: Hierarchies, Goals, and Plans**

The most complex aspect of intent research is not just detecting a single intent, but modelling the *structure* of intentions—how high-level goals decompose into sub-goals and atomic actions. This is the domain of **Intention Trees** and **Hierarchical Task Networks (HTNs)**.

### **3.1 Hierarchical Task Networks (HTN) and LLMs**

HTN planning is a classic symbolic AI approach where tasks are recursively decomposed. In 2025, researchers have successfully hybridized HTN with LLMs to create systems that are both flexible (thanks to LLMs) and reliable (thanks to HTN structure).

#### **3.1.1 ChatHTN: The Hybrid Planner**

**ChatHTN** is a pioneering system that integrates symbolic HTN planning with the generative capabilities of ChatGPT.39

* **The Problem:** LLMs are prone to hallucinations and cannot guarantee "soundness" (correctness) in planning. Symbolic HTNs are sound but brittle—if a method is missing from their library, they fail.  
* **The Solution:** ChatHTN uses a symbolic planner as the core. When it encounters a task it doesn't know how to decompose (a "missing method"), it queries the LLM to generate a decomposition.  
* **Online Learning:** Crucially, ChatHTN *learns* from these LLM generations. It verifies the LLM's output and, if valid, adds the new method to its symbolic library for future use.39  
* **Mechanism:** The system interleaves planning and generation. It tries to plan symbolically; if stuck, it calls the LLM; the LLM provides a "method" (a recipe for decomposing the task); the planner verifies if this method uses valid primitive actions; if yes, it memoizes it. This reduces the number of expensive LLM calls over time as the system "learns" the domain.41  
* **Limitations:** Current implementations often learn linear sequences rather than recursive structures, limiting their ability to handle loops or complex branching without further refinement.41

### **3.2 The Ivy System and TMK Models**

Another significant advancement is the **Ivy** system, which uses **Task-Method-Knowledge (TMK)** models to constrain LLM generation.42

* **TMK Structure:** TMK models explicitly encode:  
  * **Tasks:** The goals to be achieved.  
  * **Methods:** The procedural steps to achieve them.  
  * **Knowledge:** The causal relations and states involved.44  
* **Constrained Generation:** Unlike ChatHTN which asks the LLM to "invent" a plan, Ivy uses the TMK model as a scaffold. The LLM is responsible for generating the *natural language explanation*, but it is forced to follow the strict logic of the TMK hierarchy. This ensures that the explanation captures the "how" (procedure), "why" (teleology), and "what if" (causality) correctly.43  
* **Pedagogical Value:** Evaluations show that TMK-constrained LLMs produce significantly better educational explanations for procedural skills than unconstrained models, as they maintain the structural integrity of the goal hierarchy.43 This is crucial for "AI Coaches" in educational software.

### **3.3 Tree of Thoughts (ToT) Prompting**

While HTN and TMK are explicit data structures, **Tree of Thoughts (ToT)** is a prompting technique that induces an implicit intention tree within the LLM's inference process.8

* **Concept:** ToT generalizes Chain-of-Thought by allowing the model to explore multiple "thoughts" (intermediate steps) at each decision point. It creates a tree where each node is a partial solution.  
* **Search Algorithms:** The model can traverse this tree using Breadth-First Search (BFS) or Depth-First Search (DFS), evaluating the promise of each branch before proceeding.  
* **Relevance to Intent:** ToT is essentially "System 2" planning for LLMs. It allows the model to look ahead and backtrack, which is essential for complex intent recognition tasks where the initial interpretation might need to be revised as more context becomes available.8 For example, in a tangled user session, the model can explore Branch A ("User wants to buy") and Branch B ("User is researching"), evaluating which branch better fits the subsequent actions.

### **3.4 SessionIntentBench: Intention Trees in Data**

To evaluate these models, we need data that reflects the hierarchical nature of intent. **SessionIntentBench**, introduced in mid-2025, provides a massive dataset of "intention trees" derived from e-commerce sessions.47

* **Structure:** Instead of labeling a session with a single intent (e.g., "buy shoes"), the benchmark constructs a tree.  
  * *Root:* The high-level goal (e.g., "Update Summer Wardrobe").  
  * *Branches:* Sub-goals (e.g., "Find Sandals," "Compare Prices," "Check Reviews").  
  * *Leaves:* Atomic actions (e.g., clicks, views, add-to-cart).  
* **Construction Pipeline:** The dataset was built using an automated pipeline:  
  1. **Attribute Extraction:** Identifying product features (price, brand).  
  2. **Intention Inference:** Prompting models to infer intention shifts between time steps (e.g., shifting focus from "Brand A" to "Cheaper Price").  
  3. **Tree Enrichment:** Structuring these inferences into a tree.  
  4. **Human Annotation:** Validating the structure.47  
* **Scale:** With over 1.9 million intention entries, it is the largest benchmark of its kind, enabling the training of models that can predict not just *what* a user wants now, but *what they will want next* based on their trajectory through the intention tree.48

### **3.5 Visualizing Intention Trees**

Research also addresses the difficulty of visualizing these complex structures. **Action Graphs** derived from demonstrations can be converted into HTNs using algorithms analogous to series/parallel reduction in resistor networks.49 This allows for the automated discovery of the "hidden" hierarchical structure in flat logs of user behavior. By converting a messy graph of actions into a clean HTN tree, software can better predict future actions and identify where a user is "stuck" in their high-level plan.49

## ---

**4\. Synthesis and Future Outlook**

The convergence of these three areas—LLM detection, software taxonomies, and hierarchical modelling—points toward a unified future for intelligent software.

### **4.1 The Unification of Detection and Planning**

We are moving away from separate "classifier" and "planner" components. Systems like **ChatHTN** and **Gen-PINT** suggest a future where the *detector* is also the *planner*. The LLM detects the user's high-level intent and immediately instantiates a hierarchical plan (HTN) to fulfill it, dynamically generating the necessary sub-intents.

### **4.2 Dynamic User Interfaces and IDD**

The taxonomies from 2025 (TUNA) combined with intent-driven development (IDD) enable **Generative UI**. Instead of static dashboards, software will use intention trees to generate interfaces on the fly. If the system detects a "Meta-Conversation" intent (from TUNA), it might surface controls to adjust its own personality. If it detects a "Data Synthesis" intent, it might spawn a visualization widget. This represents the ultimate realization of IDD: software that re-architects itself in real-time to match the user's "Immutable Skeleton" of intent.50

### **4.3 The Challenge of "Tangled" Intents**

A remaining challenge highlighted in 2025 literature is **"Tangled Commits"** or entangled user sessions, where a single interaction serves multiple conflicting intents.51 While multi-label classification helps, true disentanglement requires sophisticated intention tree modelling that can represent parallel branches of thought—a capability that Tree of Thoughts (ToT) prompting is beginning to unlock.

In conclusion, the research of 2024-2025 demonstrates that detecting intent is no longer about simple classification. It is about **reconstructing the user's cognitive state** via hierarchical modelling, using LLMs as the bridge between unstructured human language and structured software logic. The integration of rigorous taxonomies like TUNA with generative planners like ChatHTN provides the blueprint for the next generation of "Intent-Aware" systems.

#### **Works cited**

1. From Discrimination to Generation: Low-Resource Intent Detection with Language Model Instruction Tuning \- ACL Anthology, accessed on February 2, 2026, [https://aclanthology.org/2024.findings-acl.605.pdf](https://aclanthology.org/2024.findings-acl.605.pdf)  
2. LINGUIST: Language Model Instruction Tuning to Generate Annotated Utterances for Intent Classification and Slot Tagging \- ACL Anthology, accessed on February 2, 2026, [https://aclanthology.org/2022.coling-1.18.pdf](https://aclanthology.org/2022.coling-1.18.pdf)  
3. Small Language Models are Good Too: An Empirical Study of Zero-Shot Classification, accessed on February 2, 2026, [https://arxiv.org/html/2404.11122v1](https://arxiv.org/html/2404.11122v1)  
4. Evaluating large language models for health-related text classification tasks with public social media data \- NIH, accessed on February 2, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11413434/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11413434/)  
5. Intent Recognition and Out-of-Scope Detection using LLMs in Multi-party Conversations, accessed on February 2, 2026, [https://arxiv.org/html/2507.22289v1](https://arxiv.org/html/2507.22289v1)  
6. Chain-of-Thought Prompting: Step-by-Step Reasoning with LLMs | DataCamp, accessed on February 2, 2026, [https://www.datacamp.com/tutorial/chain-of-thought-prompting](https://www.datacamp.com/tutorial/chain-of-thought-prompting)  
7. How Chain of Thought (CoT) Prompting Helps LLMs Reason More Like Humans | Splunk, accessed on February 2, 2026, [https://www.splunk.com/en\_us/blog/learn/chain-of-thought-cot-prompting.html](https://www.splunk.com/en_us/blog/learn/chain-of-thought-cot-prompting.html)  
8. Understanding and Implementing the Tree of Thoughts Paradigm \- Hugging Face, accessed on February 2, 2026, [https://huggingface.co/blog/sadhaklal/tree-of-thoughts](https://huggingface.co/blog/sadhaklal/tree-of-thoughts)  
9. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/2201.11903](https://arxiv.org/abs/2201.11903)  
10. Detecting misbehavior in frontier reasoning models \- OpenAI, accessed on February 2, 2026, [https://openai.com/index/chain-of-thought-monitoring/](https://openai.com/index/chain-of-thought-monitoring/)  
11. Small models, big results: Achieving superior intent extraction ..., accessed on February 2, 2026, [https://research.google/blog/small-models-big-results-achieving-superior-intent-extraction-through-decomposition/](https://research.google/blog/small-models-big-results-achieving-superior-intent-extraction-through-decomposition/)  
12. Instruction Tuning: Adapting Language Models to Follow Explicit Instructions \- Interactive | Michael Brenndoerfer, accessed on February 2, 2026, [https://mbrenndoerfer.com/writing/instruction-tuning-adapting-language-models-to-follow-explicit-instructions](https://mbrenndoerfer.com/writing/instruction-tuning-adapting-language-models-to-follow-explicit-instructions)  
13. Enhancing API Labelling with BERT and GPT: An Exploratory Study \- BIG Conferences \- TU Wien, accessed on February 2, 2026, [https://conferences.big.tuwien.ac.at/biweek2024/pdfs/biweek2024\_paper\_168.pdf](https://conferences.big.tuwien.ac.at/biweek2024/pdfs/biweek2024_paper_168.pdf)  
14. \[2507.04623\] Hierarchical Intent-guided Optimization with Pluggable LLM-Driven Semantics for Session-based Recommendation \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/2507.04623](https://arxiv.org/abs/2507.04623)  
15. A Survey on Multi-modal Intent Recognition: Recent Advances and New Frontiers \- ACL Anthology, accessed on February 2, 2026, [https://aclanthology.org/2025.findings-emnlp.823.pdf](https://aclanthology.org/2025.findings-emnlp.823.pdf)  
16. Taxonomy of User Needs and Actions \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2510.06124v1](https://arxiv.org/html/2510.06124v1)  
17. Using Large Language Models to Generate, Validate, and Apply User Intent Taxonomies, accessed on February 2, 2026, [https://www.researchgate.net/publication/391504490\_Using\_Large\_Language\_Models\_to\_Generate\_Validate\_and\_Apply\_User\_Intent\_Taxonomies](https://www.researchgate.net/publication/391504490_Using_Large_Language_Models_to_Generate_Validate_and_Apply_User_Intent_Taxonomies)  
18. User Intent \- VWO, accessed on February 2, 2026, [https://vwo.com/glossary/user-intent/](https://vwo.com/glossary/user-intent/)  
19. User Intent Analysis: What It Is, Why It Matters, & How to Do It \- Nightwatch.io, accessed on February 2, 2026, [https://nightwatch.io/blog/user-intent-analysis/](https://nightwatch.io/blog/user-intent-analysis/)  
20. User intent \- Wikipedia, accessed on February 2, 2026, [https://en.wikipedia.org/wiki/User\_intent](https://en.wikipedia.org/wiki/User_intent)  
21. Emerging Developer Patterns for the AI Era \- Andreessen Horowitz, accessed on February 2, 2026, [https://a16z.com/nine-emerging-developer-patterns-for-the-ai-era/](https://a16z.com/nine-emerging-developer-patterns-for-the-ai-era/)  
22. accessed on February 2, 2026, [https://dev.to/smolinari/intent-driven-development-idd-is-our-current-future-5fh4\#:\~:text=Intent%20Driven%20Development%20is%20the,the%20Architect%20defining%20the%20destination.](https://dev.to/smolinari/intent-driven-development-idd-is-our-current-future-5fh4#:~:text=Intent%20Driven%20Development%20is%20the,the%20Architect%20defining%20the%20destination.)  
23. SpecRover: Code Intent Extraction via LLMs \- Abhik Roychoudhury, accessed on February 2, 2026, [https://abhikrc.com/pdf/ICSE25.pdf](https://abhikrc.com/pdf/ICSE25.pdf)  
24. SpecRover: Code Intent Extraction via LLMs \- arXiv, accessed on February 2, 2026, [https://www.arxiv.org/pdf/2408.02232](https://www.arxiv.org/pdf/2408.02232)  
25. (PDF) SpecRover: Code Intent Extraction via LLMs \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/382885291\_SpecRover\_Code\_Intent\_Extraction\_via\_LLMs](https://www.researchgate.net/publication/382885291_SpecRover_Code_Intent_Extraction_via_LLMs)  
26. SpecRover: Code Intent Extraction via LLMs \*Joint first authors, ordered alphabetically. \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2408.02232v1](https://arxiv.org/html/2408.02232v1)  
27. Your Coding Intent is Secretly in the Context and You Should Deliberately Infer It Before Completion \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2508.09537v1](https://arxiv.org/html/2508.09537v1)  
28. Commit-Level Software Change Intent Classification Using a Pre-Trained Transformer-Based Code Model \- MDPI, accessed on February 2, 2026, [https://www.mdpi.com/2227-7390/12/7/1012](https://www.mdpi.com/2227-7390/12/7/1012)  
29. Multi-label Classification of Commit Messages using Transfer Learning | Semantic Scholar, accessed on February 2, 2026, [https://www.semanticscholar.org/paper/Multi-label-Classification-of-Commit-Messages-using-Sarwar-Zafar/44992ae2c3dd74f9dfb5b4847df20b17e7e01aeb](https://www.semanticscholar.org/paper/Multi-label-Classification-of-Commit-Messages-using-Sarwar-Zafar/44992ae2c3dd74f9dfb5b4847df20b17e7e01aeb)  
30. A First Look at Conventional Commits Classification \- IEEE Xplore, accessed on February 2, 2026, [https://ieeexplore.ieee.org/iel8/11029684/11029718/11029726.pdf](https://ieeexplore.ieee.org/iel8/11029684/11029718/11029726.pdf)  
31. Nwana's typology and the rise of software agents \- AWS Prescriptive Guidance, accessed on February 2, 2026, [https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-foundations/nwana-typology.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-foundations/nwana-typology.html)  
32. (PDF) Taxonomy of Software Agents \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/publication/361809065\_Taxonomy\_of\_Software\_Agents](https://www.researchgate.net/publication/361809065_Taxonomy_of_Software_Agents)  
33. Agentic Patterns and Implementation with Agentforce | Salesforce Architects, accessed on February 2, 2026, [https://architect.salesforce.com/fundamentals/agentic-patterns](https://architect.salesforce.com/fundamentals/agentic-patterns)  
34. Agentic Design Patterns: What They Actually Are (Beyond the Textbooks) | by Rohit Sharma, accessed on February 2, 2026, [https://levelup.gitconnected.com/agentic-design-patterns-what-they-actually-are-beyond-the-textbooks-fa3eebd01ed8](https://levelup.gitconnected.com/agentic-design-patterns-what-they-actually-are-beyond-the-textbooks-fa3eebd01ed8)  
35. The AI Revolution is Here: Understanding the Power of AI Agents, accessed on February 2, 2026, [https://www.lumenova.ai/blog/ai-agents-revolution/](https://www.lumenova.ai/blog/ai-agents-revolution/)  
36. Comparison of the delay performance of IS2N with different consensus... \- ResearchGate, accessed on February 2, 2026, [https://www.researchgate.net/figure/Comparison-of-the-delay-performance-of-IS2N-with-different-consensus-nodes-and-OpenFLow\_fig5\_371888494](https://www.researchgate.net/figure/Comparison-of-the-delay-performance-of-IS2N-with-different-consensus-nodes-and-OpenFLow_fig5_371888494)  
37. Three Emerging Innovative Technologies Required for Cyber Operations to Execute Commander's Intent at Machine Speed \- Digital Commons @ USF \- University of South Florida, accessed on February 2, 2026, [https://digitalcommons.usf.edu/cgi/viewcontent.cgi?article=1069\&context=mca](https://digitalcommons.usf.edu/cgi/viewcontent.cgi?article=1069&context=mca)  
38. Trusted access to 6G testbeds through a security intent-driven Software-Defined Perimeter framework, accessed on February 2, 2026, [https://6g-bricks.eu/wp-content/uploads/2024/10/Trusted\_access\_to\_6G\_testbeds\_through\_a\_security\_intent\_driven\_software\_defined\_perimeter\_framework.pdf](https://6g-bricks.eu/wp-content/uploads/2024/10/Trusted_access_to_6G_testbeds_through_a_security_intent_driven_software_defined_perimeter_framework.pdf)  
39. Online Learning of HTN Methods for integrated LLM-HTN Planning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2511.12901v1](https://arxiv.org/html/2511.12901v1)  
40. ChatHTN: Interleaving Approximate (LLM) and Symbolic HTN Planning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2505.11814v1](https://arxiv.org/html/2505.11814v1)  
41. ChatHTN Planner: Hybrid HTN & LLM Integration \- Emergent Mind, accessed on February 2, 2026, [https://www.emergentmind.com/topics/chathtn-planner](https://www.emergentmind.com/topics/chathtn-planner)  
42. \[2511.20942\] Improving Procedural Skill Explanations via Constrained Generation: A Symbolic-LLM Hybrid Architecture \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/2511.20942](https://arxiv.org/abs/2511.20942)  
43. Improving Procedural Skill Explanations via Constrained Generation: A Symbolic-LLM Hybrid Architecture \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2511.20942v1](https://arxiv.org/html/2511.20942v1)  
44. Integrating Cognitive AI with Generative Models for Enhanced Question Answering in Skill-based Learning \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2407.19393v2](https://arxiv.org/html/2407.19393v2)  
45. Using Tree-of-Thought Prompting to boost ChatGPT's reasoning \- GitHub, accessed on February 2, 2026, [https://github.com/dave1010/tree-of-thought-prompting](https://github.com/dave1010/tree-of-thought-prompting)  
46. Tree of Thoughts (ToT) \- Prompt Engineering Guide, accessed on February 2, 2026, [https://www.promptingguide.ai/techniques/tot](https://www.promptingguide.ai/techniques/tot)  
47. SessionIntentBench: A Multi-task Inter-session Intention-shift Modeling Benchmark for E-commerce Customer Behavior Understanding \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2507.20185v1](https://arxiv.org/html/2507.20185v1)  
48. \[2507.20185\] SessionIntentBench: A Multi-task Inter-session Intention-shift Modeling Benchmark for E-commerce Customer Behavior Understanding \- arXiv, accessed on February 2, 2026, [https://arxiv.org/abs/2507.20185](https://arxiv.org/abs/2507.20185)  
49. Learning Hierarchical Task Networks with Preferences from Unannotated Demonstrations, accessed on February 2, 2026, [https://proceedings.mlr.press/v155/chen21d/chen21d.pdf](https://proceedings.mlr.press/v155/chen21d/chen21d.pdf)  
50. Intent Driven Development (IDD) is our Current Future \- DEV Community, accessed on February 2, 2026, [https://dev.to/smolinari/intent-driven-development-idd-is-our-current-future-5fh4](https://dev.to/smolinari/intent-driven-development-idd-is-our-current-future-5fh4)  
51. Detecting Multiple Semantic Concerns in Tangled Code Commits \- arXiv, accessed on February 2, 2026, [https://arxiv.org/html/2601.21298v1](https://arxiv.org/html/2601.21298v1)