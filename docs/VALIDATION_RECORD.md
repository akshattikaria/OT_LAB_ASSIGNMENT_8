# Validation record

Run date: 2026-11-03. Python and library/platform versions, available CPU count, affinity and cgroup quota are recorded in results/environment.json. All computation ran on CPU. No physical quantum hardware, GPU, quantum SDK or calibrated device was used.

## Correctness tests

Command: `python -m unittest discover -s tests -v`.

Result: **32 tests passed**. Actual output is retained in unit_test_output.txt. Independent dense Kronecker gates and SciPy matrix exponentials check state evolution and QAOA. Finite differences check VQE gradients, state-space geometry and nonlinear classifier loss gradients. Other tests check bit order, Born counts, quantum measurement bases, metric rank/phase removal, density trace/positivity and channel endpoints, SPSA budgets and input integrity.

## Full recorded experiment

Command used for the main raw data:

```bash
python -u -c 'from qopt.experiment import run_benchmark; run_benchmark("results")'
python -m qopt report results
```

Protocol: seeds 0–4; 80 ideal VQE updates; QAOA p=1,2, at most 600 objective calls/run; canonical seed 0 for post-training sampling/noise; three seeds for 60-update shot training and PQC classification; 64 random parameter draws per circuit-size/depth plateau configuration.

| Experiment | Count |
| --- | --- |
| Ideal VQE runs | 20 |
| QAOA runs | 20 |
| Finite-shot VQE training runs | 12 |
| PQC classifier runs and separate datasets | 3 |
| Sampled QAOA distributions | 1,600 |
| Fixed-parameter noise cases | 20 |
| Noise size/depth controls | 18 |
| Gradient summaries (two costs) | 20 |
| Parameter draws across ten circuit configurations | 640 |

The n=2 shallow and growing-depth configurations coincide intentionally. Every seed and local optimizer result is kept; there is no best-seed substitution. All 20 QAOA runs reported local optimizer convergence; none thereby proves a global ground state. In particular, knapsack quality is poor and remains visible.

## Retained-data audit

Command: `python -m qopt.audit results`.

Result: **passed; 15,607 numerical comparisons**. The machine-readable record is results/audit.json.

- 496 retained VQE iterates independently reevaluated with the dense Hamiltonian; true expectations satisfy the variational bound.
- 4,898 QAOA objective calls reevaluated from retained angles, plus final distributions and metrics.
- All 1,600 shot-count vectors checked for nonnegative integer counts, correct totals, energies, ground probabilities, feasibility and best observed feasible values.
- All three held-out PQC and classical predictions recomputed from saved data/parameters.
- All 1,280 retained cost-gradient records and their variance/RMS/shot-error summaries checked. First/middle/last parameter points for every summary additionally resimulated and central-finite-differenced: 60 points, including deliberately shared controls.
- All four Track B exports verified byte-for-byte against recorded SHA-256 hashes; direct/QUBO/Ising energies agree on all 80 bitstrings.

Twenty-six retained finite-shot energy estimates fell below the exact ground energy. This is a sampling outcome, not a violation by the true circuit expectation. Four separately sampled Pauli terms are counted in every VQE shot budget.

Noise trace/Hermiticity/positivity and endpoint behavior are covered by unit tests. Fixed-noise records also retain minimum density eigenvalues, fidelities and purities. Gate-noise and readout-only controls distinguish prepared states from observed measurements. No false physical-device validation is claimed.

## CLI and report checks

`python -m qopt demo` completed. With 40 QNG updates it returned energy -1.3661718747900906, versus exact -1.36619037896906, and reported its objective/metric costs.

The public CLI also completed a reduced benchmark in a separate scratch output directory: seed 0, ten updates, QAOA cap 80 and eight plateau samples. That run did not replace main data. The report contains seven embedded PNGs, eleven headings and five tables, with no external image dependencies. Key plots (VQE, QAOA, noise and plateau diagnostics) were visually inspected for labels, clipping and faithful data presentation.

Previous A/B/E delivery archives were hash-checked and unchanged. No public repository was selected or published. Local history and an archive integrity check accompany the final package.

## Limits

This is a small synthetic simulator demonstration. Exact-amplitude metric access, exponentially stored QAOA energies and CPU timings cannot support hardware scalability or speedup claims. The plateau study establishes a finite-family observation, not a general theorem. Classical/PQC models and optimizer hyperparameters are not equally capacity/budget matched. See the report for numerical outcomes and docs/COVERAGE.md for remaining assignment work.
