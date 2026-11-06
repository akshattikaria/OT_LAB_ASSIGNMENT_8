# AI failure log

## Observed implementation defects

No qualifying AI implementation failure has been identified in the completed checks so far. This is not a claim that the code is bug-free. The assignment-wide requirement of three genuine AI failures remains outstanding.

Do not invent failures or prompt iterations. For each actual defect, record the original prompt/response or commit, detection, effect, correction, verifying test and corrected commit.

## Designed algorithmic failures, recorded separately

- **Greedy trap:** earlier-deadline greedy takes a cheap slot that a later vehicle needs to meet its narrower window. The input is feasible, but greedy leaves 7 kWh unmet. The checker rejects its incomplete service. Integer optimization finds a feasible schedule. This is a deliberately tested heuristic limitation, not a code bug.
- **Insufficient station capacity:** the control requires six charging slots and can supply four. ILP reports infeasible; heuristics fail full-service validation. This is infeasible input, not an AI error.
- **Time limit:** five canonical mixed-power runs reach the three-second limit with feasible candidates but no zero-gap certificate. This is a computational trade-off and is reported explicitly.
