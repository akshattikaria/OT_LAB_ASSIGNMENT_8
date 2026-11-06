# Viva preparation

1. **What did you optimize?** VQE minimizes a quantum-state Hamiltonian expectation; QAOA minimizes the exact Track B diagonal QUBOs; the PQC minimizes supervised cross-entropy.
2. **Why is this simulation?** All amplitudes/density matrices and noise channels are computed on a CPU. No actual qubit preparation or device measurements occurred.
3. **What is the classical baseline?** All 16/64 bitstrings are independently enumerated, a 4x4 Hamiltonian is diagonalized, and logistic regression learns the toy classification task.
4. **What did QAOA achieve?** Max-Cut mean ground probability rose from 38.96% to 86.42% at p=2. Knapsack remained poor; its ground probability fell with p despite slightly lower mean energy. Depth alone cannot overcome local-search difficulty.
5. **Why keep penalties?** The same objective and offset preserve the B-to-C comparison. A poor heuristic can sample infeasible/high-penalty states even when the exact ground-state penalty proof is valid.
6. **Expected energy versus best sample?** A distribution may occasionally produce an optimum while placing substantial probability on bad states. Expected energy measures the full distribution; best sampled value depends strongly on shots.
7. **Why parameter shift?** For one Pauli rotation, two shifted expectations give the exact derivative of the ideal expectation. Shot estimates remain noisy.
8. **Why not shift cross-entropy?** It is nonlinear in the measured expectation. Shift the expectation and apply the classical chain rule to the loss.
9. **Why not the same formula for QAOA gamma?** Gamma is shared by multiple cost gates and its generator has a different spectrum. This implementation uses derivative-free Powell search.
10. **What makes QNG different?** It scales the gradient using the Fubini–Study metric, respecting state-space geometry. This version uses exact amplitudes and extra state evaluations. It is not a hardware cost demonstration.
11. **What about singular metrics?** Redundant parameters and phase freedom can make the metric singular. Global phase is projected away, then 1e-3 diagonal damping stabilizes inversion.
12. **What does SPSA save?** Two objective calls per update irrespective of dimension, at the expense of gradient-estimation variance. Equal updates are not equal computational budgets.
13. **How are finite shots generated?** Multinomial draws from basis probabilities or equivalent +/-1 binomial draws for a Pauli observable. These are virtual samples, not device shots.
14. **Can estimated energy go below ground?** A noisy finite-sample estimate can. The independently computed exact expectation still obeys the variational bound.
15. **What noise was modeled?** Local depolarization after every primitive gate and independent readout flips. No real device calibration, routing or correlated errors were used.
16. **What is the plateau observation?** Random-circuit gradient variance decreases for the global cost as size grows. Local/shallow controls differ; finite data for this family is not a universal proof.
17. **Does the QNN beat classical learning?** No general claim: mean test accuracy was 87.50% versus 90.625% for logistic regression on an intentionally linear toy task, with unequal model sizes and budgets.
18. **What is independently checked?** Dense gates/exponentials, exact energy identities, finite-difference gradients, metric geometry, physical density properties, raw shot counts and retained-data recomputation.
19. **What AI evidence is included?** Actual prompt excerpts, session model/date, explicit AI assistance, test/audit results and local git history. Full chat exports and a second-tool comparison remain pending.
20. **What should you demonstrate live?** Run tests, run `python -m qopt demo`, open the report, show a poor knapsack distribution, and explain why a local optimizer success flag is not a ground-state certificate.
