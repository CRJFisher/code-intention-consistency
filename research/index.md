# Research Index

## Purpose

Literature review and state-of-the-art research to support the Intention Audit Trail project.
This research explores patterns for:
- Detecting developer intentions using LLMs
- Modeling intentions as hierarchical trees (intention trees, HTNs)
- Mining rationale from code changes to build an auditable "why" layer
- Linking intentions to concrete code edits

### TODO

- Literature Review:
  - [x] Find all the most recent, highest impact research and literature
  - [ ] Link to 
- [ ] Generate novel research and write up as a paper
  - [ ] Evaluate and measure the effectiveness of the new method

## Research Prompts

### Prompt 1: General Sweep (2026-02-02)
> Please find all the most recent, highest impact research and literature on:
> 1. detecting intentions by using LLMs
> 2. the sorts of intentions that are inside software
> 3. modelling intention trees

- [01-general-chatgpt-intent-detection.pdf](01-general-chatgpt-intent-detection.pdf) (ChatGPT)
- [01-general-gemini-intent-modeling.md](01-general-gemini-intent-modeling.md) (Gemini)

### Prompt 2: Most Fundamental Research (2026-02-02)
> Please find the most fundamental research in LLM-driven intent inference and hierarchical
> goal modeling for software engineering workflows, at the intersection of (1) intent detection
> (inferring latent "what the developer is trying to achieve" from natural-language instructions
> plus surrounding code/interaction context), (2) goal/plan recognition and hierarchical planning
> formalisms (representing those intents as evolving intention trees / HTN-like decompositions
> over long trajectories rather than single labels), and (3) mining software change rationale
> from developer activity signals (diffs, tool-use traces, tests, commit plans) to build an
> auditable "why" layer that can guide future development. Going beyond classifying intents in
> dialogues or sessions to attributing intents to concrete code edits and towards maintaining a
> persistent, revisable intention-tree memory that supports drift detection, disentangling tangled
> work, and IA-aware refactoring recommendations as the codebase evolves.

- [02-fundamental-chatgpt-intent-inference.pdf](02-fundamental-chatgpt-intent-inference.pdf) (ChatGPT)
- [02-fundamental-gemini-intent-hierarchy.md](02-fundamental-gemini-intent-hierarchy.md) (Gemini)

### Prompt 3: Most Recent Research (2026-02-02)
> (Same as Prompt 2, but with "most recent" instead of "most fundamental")

- [03-recent-chatgpt-intent-inference.pdf](03-recent-chatgpt-intent-inference.pdf) (ChatGPT Deep Research)
- [03-recent-gemini-intent-goal-modeling.md](03-recent-gemini-intent-goal-modeling.md) (Gemini Deep Research)
- [03-recent-gemini-summary.md](03-recent-gemini-summary.md) (Gemini regular query - concise summary)

## Synthesis Documents

Analysis and distillation of research findings for application to this project:

- [synthesis-01-patterns-from-general.md](synthesis-01-patterns-from-general.md) - Initial pattern extraction from general sweep
- [synthesis-02-applicable-patterns.md](synthesis-02-applicable-patterns.md) - Comprehensive patterns mapped to project architecture
- [synthesis-03-integration-plan.md](synthesis-03-integration-plan.md) - High-level integration plan for recent intent inference research

## Learning Materials

- [learning-01-historical-journey.md](learning-01-historical-journey.md) - Historical journey: plan recognition → LLM-era intent inference → auditable "Why Layer"
- [learning-02-visual-reference.md](learning-02-visual-reference.md) - Diagram-heavy visual reference guide (Mermaid timelines, flowcharts, comparison tables)



## Paper Work

Active work toward a research paper on intention consistency enforcement:

- [Paper README](paper/README.md) - Roadmap and status
- [Evaluation Requirements](paper/evaluation/requirements.md) - Experimental design
- [Benchmarks to Study](paper/evaluation/benchmarks-to-study.md) - Literature review tracking

## Sources

- **ChatGPT** (Deep Research): Outputs as PDF
- **Gemini** (Deep Research): Outputs as Markdown
