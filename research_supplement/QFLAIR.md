# Q-FLAIR — scoped source implementation and paired control

Primary source: Jäger, Elsässer and Torabian, *Quantum feature-map learning with reduced resource overhead*, arXiv:2510.03389v2 / Phys. Rev. Research 8, 023247 (2026). Author code: https://github.com/phels23/Q-FLAIR at commit 4f331783fc5bda5492fa3fffff0a845b0805eb39.

## What is implemented

The QNN specialization follows Section III, Algorithm 1 and Appendix A.1: start from an empty circuit; append a candidate Pauli rotation; reconstruct each training output from zero and ±π/2 angles; classically select the feature and weight yielding the lowest log loss; select the best gate; repeat until the loss improvement is below 0.001 or the declared 12-gate safety cap. The zero-angle output is reused. At the empty ansatz the same two shifts are shared across all rows. A constant π feature supplies weight-only rotations, as described in Appendix A.1.

The two-qubit gate pool is the declared subset IX, IY, XI, YI, XX, YY, XZ, ZX. The output is the all-zero projector probability, following the author QNN code. The stable representation u cos(α)+v sin(α)+c is algebraically equivalent to the author's amplitude/phase representation. Tests compare it with the unchanged author reconstruction functions, independent matrix exponentials and Qiskit circuits. The two extracted author functions and original Apache-2.0 license are in author_checks/; the rest of this port is original AI-assisted code.

## Experiment and fair control

Two predefined synthetic tasks (linear separation and XOR) are tested with 4 and 12 input features over seeds 11, 41 and 59. Each case uses 64 balanced training and 64 disjoint test rows. Higher-dimensional cases retain the same signal coordinates and row identities. Min/max scaling and the classifier threshold use training rows only. The exact raw data and row IDs are saved.

Each Q-FLAIR run is paired with direct search on the identical gate pool, feature choices, 41-point [-1,1] weight grid, stopping rule and gate cap. Thus the comparison isolates analytical reconstruction instead of silently changing search quality or budget. All 12 pairs match their training loss and test probabilities. A fixed logistic-regression baseline uses the same split and scaled features. No test labels select the circuit or threshold.

Training circuit-output counts refer to logical black-box oracle evaluations, with initial-state and zero-angle reuse made explicit. Simulator vectorization and state caching accelerate both implementations. Classical candidate scoring still grows with feature count; the comparison does not establish a quantum hardware speedup or asymptotic CPU speedup. Training and inference wall times are retained separately. Half the cases reach the 12-gate cap; XOR outcomes are mixed and higher-dimensional noise can worsen generalization.

The author's paper uses different datasets, a larger gate pool and finer parameter sampling. This experiment does not reproduce its MNIST accuracies, QSVM method, real IBM execution, scaling benchmark or quantum-advantage claims. Those results are not attributed to this submission.

## Verification and reproduction

```
python -m unittest research_supplement.test_qflair -v
python -m research_supplement.qflair --audit
python -m research_supplement.qflair --out research_supplement/qflair-rerun.json
```

The nine tests cover rotations, author-equivalent reconstruction, exhaustive candidate comparisons, full paired training, query budgets, leakage, Qiskit circuit order, log-loss input handling and nested/disjoint datasets. The retained-result audit independently replays all selected circuits through matrix exponentials and recomputes data identities, losses, decisions and query accounts.

An initial audit caught a Python-list/NumPy-array type mismatch in the loss reader. Labels are now converted explicitly and a list-input regression is included. The initial output remains under diagnostics/qflair_before_audit_list_fix.json; corrected code was rerun for the primary results. No original A–J measurement was changed.
