# Benchmarks and Papers to Study

> **Note**: This is a provisional starting list to seed the literature review.
> The goal is to learn evaluation standards, not to exhaustively survey the field.
> Expect this list to grow and be refined as we dig deeper.

## Code Generation Benchmarks

### HumanEval (OpenAI, 2021)

- **What**: Function-level code generation from docstrings
- **Why study**: Foundational benchmark, understand basic eval methodology
- **Questions to answer**:
  - How do they measure correctness?
  - How do they handle partial solutions?
  - What is pass@k and how is it computed?
- **Link**: https://github.com/openai/human-eval
- **Paper**: "Evaluating Large Language Models Trained on Code"

### MBPP (Google, 2021)

- **What**: Mostly Basic Programming Problems
- **Why study**: Larger scale than HumanEval, different task distribution
- **Questions to answer**:
  - Task difficulty distribution
  - Evaluation metrics beyond pass@k
  - How do they handle edge cases?
- **Paper**: "Program Synthesis with Large Language Models"

### SWE-bench (Princeton, 2024)

- **What**: Real GitHub issues → code patches
- **Why study**: Closest to our setting (real repos, multi-file changes)
- **Questions to answer**:
  - How do they define task success?
  - How do they handle non-determinism?
  - What's their sample size / statistical approach?
  - How are tasks selected and validated?
- **Link**: https://www.swebench.com/
- **Paper**: "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?"

### SWE-bench Verified

- **What**: Human-verified subset of SWE-bench
- **Why study**: Addresses quality concerns in original
- **Questions to answer**:
  - Verification methodology
  - How much does verification change results?
  - What were the quality issues in original?

### CodeContests (DeepMind, 2022)

- **What**: Competitive programming problems
- **Why study**: Different task type, rigorous evaluation
- **Questions to answer**:
  - How do they handle multiple valid solutions?
  - Test case generation methodology

## Agent Benchmarks

### AgentBench (Tsinghua, 2023)

- **What**: Multi-environment agent evaluation (code, web, game, etc.)
- **Why study**: Broader agent evaluation methodology
- **Questions to answer**:
  - How do they handle multi-step tasks?
  - Metrics beyond task completion
  - How do they measure intermediate progress?
- **Paper**: "AgentBench: Evaluating LLMs as Agents"

### WebArena (CMU, 2023)

- **What**: Web agent benchmark
- **Why study**: Task specification methodology for complex tasks
- **Questions to answer**:
  - How are complex tasks specified?
  - Success criteria for open-ended tasks
  - Reproducibility methodology

### OSWorld (2024)

- **What**: OS-level agent benchmark
- **Why study**: Multi-step task evaluation in realistic environments
- **Questions to answer**:
  - How do they handle state management?
  - Partial credit methodology

### DevBench (2024)

- **What**: Development lifecycle benchmark
- **Why study**: Covers full development workflow
- **Questions to answer**:
  - How do they evaluate process vs outcome?
  - Multi-stage task evaluation

## Commit/Change Quality Research

### Tangled Commits Literature

- **What**: Papers on detecting/measuring tangled commits
- **Why study**: Directly relevant to our H2 (fewer tangled commits)
- **Questions to answer**:
  - Existing metrics for commit atomicity
  - How is "tangled" operationally defined?
  - Automated detection approaches
- **Papers to find**:
  - "Untangling Fine-Grained Code Changes" (Barnett et al.)
  - "Flexeme: Untangling Commits Using Lexical Distances"
  - Research on composite/tangled commits

### Commit Message Quality

- **What**: Papers on commit message generation/evaluation
- **Why study**: Relevant to our metrics on message accuracy
- **Questions to answer**:
  - Existing rubrics for message quality
  - Automated vs human evaluation
  - What makes a "good" commit message?
- **Papers to find**:
  - "On the generation of commit messages" literature
  - Commit message style guides as implicit standards

### Code Review Research

- **What**: Studies on code review effectiveness
- **Why study**: Auditability and reviewability metrics
- **Questions to answer**:
  - What makes changes easy to review?
  - Quantitative measures of review difficulty
  - Relationship between commit quality and review effort

## LLM Evaluation Methodology

### LLM-as-Judge Papers

- **What**: Research on using LLMs to evaluate other LLMs
- **Why study**: We plan to use LLM judges for some metrics
- **Questions to answer**:
  - Validation methodology
  - Agreement thresholds with human judgment
  - Known biases and mitigations
- **Papers to find**:
  - "Judging LLM-as-a-Judge" (EMNLP 2024)
  - G-Eval and related papers

### Inter-rater Reliability

- **What**: Standard methodology for human evaluation
- **Why study**: Need to design valid human evaluation
- **Questions to answer**:
  - Cohen's kappa thresholds
  - Number of evaluators needed
  - Training protocols

## Extraction Template

For each paper reviewed, extract:

1. **Task definition**: How are tasks specified?
2. **Success criteria**: Binary? Graded? Multiple metrics?
3. **Sample size**: How many tasks? How many runs per task?
4. **Non-determinism**: How is LLM variance handled?
5. **Statistical methods**: What tests? Effect sizes? Confidence intervals?
6. **Human evaluation**: If any, what protocol? How many evaluators?
7. **Limitations acknowledged**: What do authors identify?
8. **Reproducibility**: Can we replicate their setup?

## Review Status

| Paper/Topic | Priority | Status | Notes |
|-------------|----------|--------|-------|
| SWE-bench | High | TODO | Closest to our setting |
| SWE-bench Verified | High | TODO | Quality improvements |
| HumanEval | Medium | TODO | Foundational methodology |
| MBPP | Medium | TODO | Scale considerations |
| AgentBench | Medium | TODO | Agent-specific methodology |
| Tangled commits | High | TODO | Need to find specific papers |
| Commit quality | High | TODO | Need to find specific papers |
| LLM-as-Judge | High | TODO | Critical for our methodology |
| CodeContests | Low | TODO | Different task type |
| WebArena | Low | TODO | Different domain |
| OSWorld | Low | TODO | Different domain |

## Reading Notes

*(Add notes as papers are reviewed)*

### Template

```markdown
## [Paper Title] (Author, Year)

**Read date**: YYYY-MM-DD

### Summary
(2-3 sentence summary)

### Key Findings for Our Work
- Finding 1
- Finding 2

### Methodology Details
- Tasks: ...
- Metrics: ...
- Sample size: ...
- Statistical approach: ...

### Applicable to Our Study
- [ ] Metric we can reuse
- [ ] Protocol we can adapt
- [ ] Statistical method to apply

### Questions Remaining
- ...
```
