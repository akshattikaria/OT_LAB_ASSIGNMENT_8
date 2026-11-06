# Track C: Quantum Optimization

Open **results/report.html** after extracting this folder. It contains the report and seven embedded figures and works offline. Code, raw data, tests and explanations are included. Tracks E, A and B remain separate packages.

This is a **CPU simulator study** using an explicit NumPy statevector/density implementation, verified against independent dense-matrix calculations. No Qiskit, PennyLane, physical quantum processor or calibrated device was used. Synthetic noise is declared; no quantum advantage is claimed.

## Implemented

- VQE on a dimensionless two-qubit Pauli Hamiltonian; exact classical eigensolver reference.
- Parameter-shift gradient descent and Adam, SPSA, and damped quantum natural gradient (QNG).
- QAOA at p=1,2 on the unchanged four-bit Max-Cut and six-bit constrained-knapsack models exported from Track B.
- Finite-shot Born sampling, finite-shot VQE training, local depolarization and readout-noise controls.
- Global/local cost and shallow/growing-depth gradient-concentration experiments over 2–10 qubits.
- A trainable data-encoded PQC/QNN classifier with a classical logistic reference and held-out evaluation.

## Run

Recorded environment: Python 3.12.14. Dependencies are pinned in requirements.txt. Run from this extracted folder:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m qopt demo
```

Full benchmark (choose a new output folder):

```bash
python -m qopt benchmark --out results-rerun --seeds 0 1 2 3 4 --steps 80 --qaoa-maxfev 600 --barren-samples 64
python -m qopt.audit results-rerun
```

Smaller smoke protocol:

```bash
python -m qopt benchmark --out results-quick --seeds 0 --steps 10 --qaoa-maxfev 80 --barren-samples 8
```

Regenerate report without training again:

```bash
python -m qopt report results
```

Nonempty output folders are refused to preserve evidence. Seeds reproduce inputs and randomness; runtime and numerical convergence may vary across systems. The independent audit is optional for a rerun, but was run on the delivered results.

## Recorded evidence

- **32 tests passed**, covering dense gate/circuit oracles, gradient finite differences, metric geometry, noise endpoints, shot counts and the Track B input hashes.
- 20 ideal VQE runs, 20 QAOA runs, 12 finite-shot VQE runs and three PQC classifiers.
- 1,600 sampled distributions; 20 fixed-parameter noise cases and 18 size/depth noise controls.
- 20 gradient summaries from 640 parameter draws across ten size/depth configurations, each evaluated for two costs; 64 samples/configuration. Both n=2 depth controls intentionally coincide.
- Independent audit recomputes every retained VQE iterate and QAOA objective call, all sampled metrics and gradient summaries, plus selected finite-difference gradient checks. Exact counts are in results/audit.json.

QNG reached a mean exact energy gap of about 5.91e-10 after 80 updates, but required 2,657 simulator state preparations/run, including 1,360 metric preparations. SPSA used 177 objective calls/run versus 1,297 for the shift methods. This is unequal resource use, not a hardware ranking.

Max-Cut ground-state sampling probability averaged 38.96% at p=1 and 86.42% at p=2. Constrained knapsack remained far from its exact minimum: mean expected energy 105.92 at p=1 and 101.98 at p=2, versus -6. Its mean ground-state probability fell from 12.26% to 3.13%. These poor outcomes are retained. Local optimizer success is not global optimality.

The PQC averaged 87.50% test accuracy; regularized logistic regression averaged 90.625% across three toy datasets. Models have different parameter counts and budgets. These small synthetic observations do not establish general superiority.

## Files

| Path | Purpose |
| --- | --- |
| qopt/simulator.py | Little-endian gates, statevectors, density matrices, Pauli measurement and channels |
| qopt/models.py | VQE Hamiltonian, parameter-shift, Fubini–Study metric and Track B QAOA |
| qopt/optimizers.py | ShiftGD, ShiftAdam, SPSA and QNG |
| qopt/qnn.py | Encoded PQC classifier and logistic reference |
| qopt/experiment.py | Fixed experiment protocol, counters and raw results |
| qopt/report.py, qopt/audit.py | Report generation and retained-data audit |
| tests/test_quantum.py | 32 independent mathematical and integration checks |
| inputs/track_b/ | Four unchanged Track B exports, with all classical bitstring energies |
| results/protocol.json, environment.json | Actual budgets, conventions and runtime environment |
| results/*_runs.json | Retained parameters, traces, distributions, statuses and CPU times |
| results/shot_study.json, noise_study.json | Sample counts and synthetic-noise results |
| results/barren_plateaus.json | Angles, shifted expectations, shot gradients and summaries |
| results/qnn_data/ | Separate training/test arrays for every classifier run |
| docs/FORMULATION.md, VIVA_GUIDE.md | Mathematics and explanations |
| docs/COVERAGE.md, VALIDATION_RECORD.md | Requirement mapping, validation and limitations |
| prompts/C/001_continue.md | Actual visible prompt and response excerpts |
| history.bundle | Local commit history; recover with git clone history.bundle track-c-history |

## AI disclosure and remaining assignment work

| Tool | Session-reported model | Date | Use |
| --- | --- | --- | --- |
| ChatGPT | gpt-6.1-sol | 2026-11-03 | Track C formulation, code, tests, experiments, audit and report |
| ChatGPT | gpt-6.1-sol | 2026-11-03 | Earlier Track B work |
| ChatGPT | gpt-6.1-sol | 2026-10-31 | Earlier Track A work and chapter planning |
| ChatGPT | gpt-6-astra | 2026-10-31 | Earlier Track E case study |

All implementation here is AI-assisted. No manual student edits or second independent AI-tool comparison are claimed. NumPy supplies linear algebra, SciPy supplies classical Powell and logistic L-BFGS search, and Matplotlib supplies plots. Core gates, measurement rules, gradients, metric, SPSA and models are explicit implementations. QNG reads exact simulator amplitudes; it is not a device metric estimator.

Two genuine numerical defects were documented and fixed in A/B. No third genuine AI defect was found in this milestone, so the assignment-wide minimum of three remains pending. Planned counterexamples and poor optimizer results are not counted as AI bugs. Full conversation exports/screenshots and the second-tool comparison remain pending; this archive contains only actual excerpts.

The next milestone is **Track D: submodular, parallel and distributed optimization**, followed by F–J and final integration. Track A's separately flagged research-paper reproductions also remain unresolved. No public GitHub repository has been selected or published. See docs/COVERAGE.md for precise scope.

## Primary references

- Supplied Assignment 8, Track C/Section 5; Chapter 6 quantum lecture slides, acknowledged rather than redistributed.
- [QAOA](https://arxiv.org/abs/1411.4028), [VQE](https://arxiv.org/abs/1304.3061), [parameter-shift gradients](https://arxiv.org/abs/1811.11184), [QNG](https://arxiv.org/abs/1909.02108), [barren plateaus](https://arxiv.org/abs/1803.11173).
- [Spall's SPSA overview](https://www.jhuapl.edu/SPSA/PDF-SPSA/Spall_An_Overview.PDF), [depolarizing-channel convention](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html).
- References checked 2026-11-03. These citations support methods; all reported numbers come from this package's own experiments.
