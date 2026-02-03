# Evaluation Requirements

## Research Question

"Does enforcing intention structure at commit time improve LLM coding agent output?"

## Hypotheses

- **H1**: More atomic commits (fewer files per commit, semantically coherent changes)
- **H2**: Fewer tangled commits (commits serve single purpose)
- **H3**: Better traceability (clear mapping from intent to implementation)
- **H4**: Less intent drift (final code matches original task specification)

## Experimental Design

### Independent Variable

- **Treatment**: Claude Code with intention consistency framework
- **Control**: Vanilla Claude Code (same model, no framework)

### Dependent Variables

#### Automated Metrics

| Metric                   | Measurement                           | TODO                        |
| ------------------------ | ------------------------------------- | --------------------------- |
| Commit atomicity         | Files per commit, semantic clustering | Define clustering algorithm |
| Test pass rate           | Run test suite                        | Straightforward             |
| Lint/type errors         | ruff, pyright                         | Straightforward             |
| Lines changed per commit | git diff stats                        | Straightforward             |
| Commit count             | Number of commits per task            | Straightforward             |

#### LLM-as-Judge Metrics

| Metric                   | Measurement                                 | TODO                                  |
| ------------------------ | ------------------------------------------- | ------------------------------------- |
| Tangled commit detection | Classify if commit serves multiple purposes | Design prompt, validate against human |
| Commit message accuracy  | Does message match diff?                    | Design rubric                         |
| Intent-to-code alignment | Does code implement stated intention?       | Design prompt                         |

#### Human Evaluation Metrics

| Metric                 | Measurement                       | TODO                              |
| ---------------------- | --------------------------------- | --------------------------------- |
| Intent fidelity        | Did code match original task?     | Design rubric, recruit evaluators |
| Auditability           | Can reviewer follow "why"?        | Design rubric                     |
| Code review difficulty | Time/effort to understand changes | Design protocol                   |

> **TODO**: Review benchmark papers to understand standard metrics in agent evaluation

### Controls

- Same model version (lock API version)
- Same starting codebase state (git SHA)
- Same task prompts (verbatim)
- Same temperature/sampling params
- Same system prompt (minus framework-specific parts)
- Same tool access (file read/write, bash, etc.)

> **TODO**: What other controls are standard? Check benchmark papers.

### Sample Size

- Minimum viable: 5 tasks × 3 runs × 2 conditions = 30 sessions
- Statistical power analysis needed

> **TODO**: How do existing benchmarks handle sample size? What's standard?

## Task Selection

### Criteria

- Complex enough to have multiple sub-intentions
- Clear success criteria (tests, type checks, lint)
- Reproducible starting state (git SHA)
- Diverse (features, fixes, refactors)
- Not too long (tractable for repeated runs)

### Task Categories (provisional)

1. **Feature addition** (e.g., "Add OAuth2 authentication")
2. **Bug fix** (e.g., "Fix race condition in X")
3. **Refactoring** (e.g., "Extract module from monolith")
4. **Test coverage** (e.g., "Add tests for untested module")
5. **Documentation** (e.g., "Add API documentation")

> **TODO**: How do SWE-bench, AgentBench define tasks? What granularity?

### Candidate Task Sources

- Real GitHub issues from open source projects
- Synthetic tasks designed for the study
- Tasks from existing benchmarks (adapted)

> **TODO**: Evaluate trade-offs of each source

## Statistical Analysis

> **TODO**: What statistical tests are standard for agent evaluation?
> - Handling LLM non-determinism (multiple runs)
> - Paired vs unpaired comparisons
> - Effect size reporting
> - Confidence intervals

### Proposed Approach (to validate)

- Multiple runs per condition to estimate variance
- Paired comparison (same task, both conditions)
- Report mean, std dev, effect size (Cohen's d)
- Non-parametric tests if distributions are non-normal

## Evaluation Protocol

### Blinding

- Strip framework artifacts before human evaluation
- Evaluators don't know which condition produced which output
- Randomize presentation order

### Human Evaluation Rubric (draft)

```
COMMIT QUALITY (1-5)
1. Commits are atomic (one logical change)
2. Messages accurately describe changes
3. Sequence is logical and reviewable

INTENT FIDELITY (1-5)
4. Task completed as specified
5. No scope creep
6. Final code matches intent

AUDITABILITY (1-5)
7. Can understand WHY each change was made
8. New developer could follow history
9. Intent is traceable through commits
```

> **TODO**: Validate rubric against existing evaluation frameworks

### LLM-as-Judge Protocol

For each metric:
1. Design prompt with clear criteria
2. Test on subset with known labels
3. Measure agreement with human judgment
4. Iterate until acceptable agreement (κ > 0.6?)

> **TODO**: What agreement threshold is standard?

## Risks and Mitigations

| Risk                       | Mitigation                           | TODO                      |
| -------------------------- | ------------------------------------ | ------------------------- |
| LLM variance swamps signal | Multiple runs, statistical tests     | Power analysis            |
| Framework overhead unfair  | Measure cost alongside quality       | Define cost metrics       |
| Results specific to tasks  | Diverse task selection               | Define diversity criteria |
| Human eval bias            | Blinding, multiple evaluators        | Recruit evaluators        |
| Prompt sensitivity         | Document prompts, test variations    | Sensitivity analysis      |
| Cherry-picked tasks        | Pre-register task selection criteria | Write pre-registration    |

## Cost Metrics

To ensure fair comparison, also measure:

| Metric                | Measurement     |
| --------------------- | --------------- |
| Total tokens consumed | API usage       |
| Wall clock time       | Start to finish |
| Number of API calls   | Round trips     |
| Total cost ($)        | Token costs     |

## Open Questions (require literature review)

1. What's the standard for "code quality" measurement in agent benchmarks?
2. How is non-determinism typically handled?
3. What sample sizes are considered sufficient?
4. Are there existing commit quality metrics we can reuse?
5. How do papers validate LLM-as-judge against human judgment?
6. What's the standard for reporting statistical significance?
7. How do papers handle tasks that fail completely vs partial success?

## Next Steps

1. [ ] Complete literature review of benchmark papers
2. [ ] Extract evaluation patterns from each paper
3. [ ] Refine metrics based on literature
4. [ ] Design task selection protocol
5. [ ] Build evaluation harness
6. [ ] Pilot study with 2-3 tasks
7. [ ] Iterate based on pilot findings
