# Genuine failures: assignment-wide status

No genuine implementation defect was discovered in Track C's mathematical tests and retained-data audit. No failure is manufactured to satisfy the assignment count. Thirty-two tests include planned checks for common mistakes; those counterexamples are tests, not bugs observed in this implementation.

Two genuine numerical defects were previously documented and corrected:

| Track | Actual defect | Correction and evidence |
| --- | --- | --- |
| A | Cancellation in sqrt(1+x²)−1 erased small values near zero | Rationalized formula; original/fixed commits and regression in the Track A package |
| B | Expanded large floating-point QUBO coefficients erased a reward difference | Declared coefficient-range guard, reproduction, original/fixed commits and regression in the Track B package |

The minimum of three genuine cases remains outstanding by one. QAOA's poor knapsack outcome, generic noise degradation and shot-estimation error are measured algorithm/model limitations; they do not count as implementation defects. All work here is AI-assisted, with no manual student correction or independent second-tool use claimed.
