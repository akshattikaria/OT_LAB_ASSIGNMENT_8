# Track E prompt and verification record

Date: 2026-10-31. Tool: ChatGPT. Implementation model reported by this session: `gpt-6-astra`.

## User selection (verbatim)

> Which main case study would you like to build?
> EV charging scheduler — my recommendation

This is the user's response to the displayed options, preserved rather than rewritten as an invented detailed prompt.

## Accepted scope (assistant excerpt)

> Track E is decided: “Smart EV Charging Scheduling under Power and Departure Constraints.”
>
> We’ll optimize when each vehicle charges, aiming to reduce electricity cost while supplying its required energy before departure.

The scope specified known session information, assigned plugs, fixed-rate slots, a baseline, greedy, integer optimization and independent checks. A separate four-vehicle synthetic example was shown before implementation.

## Implementation request (verbatim)

> start

## AI response excerpt

> I’ll build the Track E experiment with a reproducible dataset, baseline, greedy scheduler, integer optimizer, and an independent correctness checker. Then I’ll run comparisons and package the code with its results.

Relevant generated code (`evcharge/solvers.py`):

```python
result = milp(c=c,integrality=np.ones(len(edges)),bounds=Bounds(0,1),
              constraints=LinearConstraint(matrix,lower,upper),
              options={"time_limit":float(time_limit),"mip_rel_gap":0.0,"presolve":True})
```

Full generated source is preserved in the repository history. This file is an excerpt record, not a claimed full chat export or screenshot.

## Revisions

No further user revision prompt was issued during this implementation turn. The assistant added diagnostic controls, validation, paired comparisons and timeout reporting while executing the accepted scope. These are assistant-driven choices.

After the benchmark, the report was refined to explicitly disclose five canonical timeouts and their exclusion from comparisons labelled against a proven optimum. The solver code and measured data were not changed to hide those cases.

## Verification and trace

- 29 tests passed, including an oracle comparison over 80 seeded small inputs.
- Each benchmark candidate is independently audited; cheaper incomplete service is not treated as improvement.
- 75 main inputs and four controls, three repetitions per method, yield 711 recorded method runs.
- Code, exact data, results, environment and plots are included.
- Commit references: `docs/COMMIT_INDEX.md`. AI-assisted commits use `[AI:ChatGPT]`.

## Remaining disclosure

The user can export this actual conversation for full chat-export evidence. No second AI-tool comparison has occurred. No three qualifying AI-code failures have been fabricated. Earlier model information and any uncertainty are recorded in the README.
