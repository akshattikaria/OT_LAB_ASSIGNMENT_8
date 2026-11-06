# Track B prompt and verification record

Date: 2026-11-03. Tool: ChatGPT. Model exposed by this implementation session: `gpt-6.1-sol`.

## Original user prompt (verbatim)

> continue

Visible context: Track A core experiments had been delivered, Track E was preserved, and the next announced track was B, discrete optimization.

## AI response excerpt

> I’ll continue with Track B: discrete optimization. I’ll compare greedy, dynamic programming, Branch-and-Bound, and ILP on a selection problem, then build and verify a QUBO/Ising version for use in Track C.

Relevant generated implementation excerpt (`discopt/solvers.py`):

```python
table[i]=table[i-1]
if weight<=p.capacity:
    table[i,weight:]=np.maximum(table[i,weight:],table[i-1,:p.capacity+1-weight]+value)
```

Full generated source, exact inputs, outputs and original/corrected QUBO code are preserved in the bundled git history. This file is an excerpt record, not a claimed full chat export.

## Debugging and revisions

No additional user revision prompt was issued during this turn. The assistant found an oversized-coefficient energy discrepancy, retained the failing original and added a numeric-range guard/regression test. See docs/AI_FAILURE_LOG.md and docs/COMMIT_INDEX.md.

Actual debugging update excerpt:

> I also found a precision issue with very large QUBO coefficients: the expanded energy can lose a small objective difference. I’m adding a range check and a regression test so it rejects those inputs explicitly.

The issue was fixed before the main benchmark. Search-limit outcomes and weak-penalty failures were retained, not rewritten as successful optima.

## Verification

30 tests passed, including 100 random small exact-method comparisons and 20 constrained QUBOs. Every main candidate is audited and checked against a DP reference. All 64 knapsack states and 16 Max-Cut states have matching direct/QUBO/Ising energies. Feature selection uses validation data only for choosing the subset; an adversarial test changes test labels without changing selected features.

The recorded suite contains 1,275 method runs. Code, raw results, reports, hashes, environment and exported Track C models are included. AI-assisted commit subjects use `[AI:ChatGPT]`.

## Remaining disclosure

Full chat exports/screenshots can be obtained from the actual conversation. No second AI tool or manual student correction is claimed. One new genuine failure is recorded; the combined assignment still needs one further genuine case beyond Track A's earlier case. Public repository publication is pending.
