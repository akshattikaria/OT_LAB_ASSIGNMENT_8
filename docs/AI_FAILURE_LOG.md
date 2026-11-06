# Genuine implementation defect: QUBO coefficient precision

Date: 2026-11-03. Tool/model: ChatGPT, session-reported `gpt-6.1-sol`.

## Original and reproduction

Original commit: `527dad2de9a3a89f29323bdc58558f5a9a8ab6e4`.

The original float encoder accepted any input allowed by the broad knapsack schema, even when penalty expansion created enormous coefficients. A valid diagnostic input used one item of value 1 and cost 1, capacity 1,000,000,000 and P=2. Selecting the item and slack 999,999,999 gives direct energy -1 because the constraint residual is zero. The expanded float matrix evaluated that state as 0.0, losing the objective difference to cancellation. The observation is recorded in `precision_bug_observation.json`.

This was an actual AI-generated numeric-range defect. It was detected before the recorded main benchmark; it was not a weak-penalty experiment or fabricated solver failure.

## Fix and verification

Corrected commit: `3d170da82844171f67691db27df5ffa1c5c53c9b`.

QUBO validation now rejects total absolute matrix/offset magnitude above 2^45 with an explicit range error. Energy evaluation also invokes validation. The original knapsack input can still be handled by an appropriate classical method; this particular floating-point quantum encoder has a narrower, declared supported range.

Regression test: `test_large_coefficient_cancellation_is_rejected`. All 30 tests pass. Every state in the two exported tiny QUBOs is checked against direct and Ising energies. No unsafe large model is silently rescaled or claimed exact.

Lesson: algebraic equivalence does not guarantee numerically equivalent expanded energies. Validate coefficient scales and preserve objective differences before comparing optimization outputs.

## Other outcomes, not counted as defects

The density-greedy counterexample, seven node-limited Branch-and-Bound candidates and insufficient-penalty minima are intentional algorithm/parameter limitations. They are reported honestly and not counted as additional AI bugs.

This track contributes one genuine case. Track A earlier documented one separate numerical cancellation defect. The assignment-wide minimum of three remains outstanding by one case; no third failure is fabricated.
