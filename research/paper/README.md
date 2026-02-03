# Intention Consistency Research Paper

## Working Title

"Enforcing Intention Structure at Commit Time: Does It Improve LLM Coding Agent Output?"

## Thesis

By requiring LLM coding agents to declare intentions upfront and validate commits against those intentions, we can produce more atomic commits, reduce tangled changes, improve traceability, and minimize intent drift compared to unconstrained agent workflows.

## Current Phase

**Literature Review / Evaluation Design**

- [ ] Review existing benchmarks (SWE-bench, HumanEval, AgentBench)
- [ ] Learn standard evaluation methodologies
- [ ] Define metrics and rubrics
- [ ] Design experimental protocol
- [ ] Implement evaluation harness
- [ ] Run experiments
- [ ] Analyze results
- [ ] Write paper

## Key Documents

| Document | Purpose |
|----------|---------|
| [Evaluation Requirements](evaluation/requirements.md) | Experimental design skeleton with TODOs |
| [Benchmarks to Study](evaluation/benchmarks-to-study.md) | Literature review tracking |
| [Research Index](../index.md) | Background research and synthesis |

## Major Open Questions

1. **Metrics**: What's the standard for measuring "code quality" in agent benchmarks? Can we reuse existing metrics or must we define new ones?

2. **Sample Size**: How many tasks/runs do we need for statistical significance given LLM variance?

3. **Task Selection**: What tasks best demonstrate the framework's value? How to balance difficulty and diversity?

4. **LLM-as-Judge Validation**: How do we validate that LLM judges agree with human judgment for our metrics?

5. **Cost Accounting**: How to fairly account for the overhead of the intention framework?

## Related Work

See [research/index.md](../index.md) for the literature review on:
- Intent detection with LLMs
- Intention trees and hierarchical planning
- Software change rationale mining
