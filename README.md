# Track I: Quantum Algorithms and QML Comparison

Prepared for **Akshat Tikaria, roll 241070005**. Optimization Techniques, Assignment 8.

Open **results/report.html** after extraction. The offline report contains four scientific plots, two handwritten-circuit diagrams, all algorithm outcomes, matched learning comparisons, calibrated-noise results and the contrast with Track D. Source, QPY circuits, raw measurements, matrices, tests, viva notes and local history are included.

## Implemented

- Explicit circuits for Deutsch, Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE and toy Shor order finding/factoring of 15; no complete built-in algorithm constructors replace the handwritten gates.
- New SDK VQE with parameter-shift Adam, finite-budget QAOA, and gate-based closed-system annealing with an independent dense reference and a separate classical simulated-annealing baseline.
- Quantum fidelity-kernel SVC versus classical RBF-kernel SVC on the same moons/circles data, split, transformed features, C=1 and learner, over three seeds.
- Qiskit Aer noise based on the **historical Manila calibration dated 27 May 2024**, with identical transpiled ideal controls. Exact calibration files, provider license, coupling map and noise-model data are preserved.
- Logical oracle/gate/circuit counts and actual CPU wall times, with explicit data-loading, sampling, trainability and simulation limits.

Track C already covers QNG, SPSA, finite-shot VQE, QNN and empirical gradient concentration. Earlier C/D summaries and provenance are copied unchanged and labeled as earlier measurements; they are not counted as fresh I runs. The original separate packages remain unchanged. Coverage matches the supplied quantum slides and the additional algorithm names in Assignment 8 Section 5.

## Main results

| Dataset | Mean quantum-kernel accuracy | Mean RBF accuracy | Quantum training seconds | RBF training seconds |
| --- | --- | --- | --- | --- |
| Moons | 64.44% | 88.89% | 1.72305 | 0.00155 |
| Circles | 75.56% | 97.22% | 1.75878 | 0.00125 |

Each dataset has 60 training and 60 held-out examples per seed. The quantum kernel is slower and less accurate for these fixed choices. The circuit has **zero trained quantum weights**, while the SVC learns support-vector coefficients and a bias; both kinds of parameter counts are disclosed. Every quantum model executes **5,370 exact overlap circuits**, totaling **32,220** across six datasets. Hardware estimates would require shots per overlap. The tiny two-qubit map is classically simulable; this is not evidence of a QML computational advantage.

Grover with N=256 uses **12 search-oracle calls plus one verification**, with ideal marked probability 0.999947. Uniform-target classical expectation is 128.5 checks; the three actual marks required 31, 72 and 2 checks. Some targets are found early classically. Median measured build/transpile/simulate/sample time was about 206 ms versus about 1.53 microseconds for the actual classical scan. The known quadratic statement concerns oracle-query scaling, not these CPU times or a physical QPU speedup.

| Program | Paired ideal correct fraction | Historical calibrated-noise fraction |
| --- | --- | --- |
| Bernstein-Vazirani | 100.00% | 85.66% |
| Deutsch-Jozsa balanced decision | 100.00% | 90.28% |
| Grover | 94.65% | 46.67% |
| QPE | 100.00% | 60.27% |

Each condition pools 12,288 emulated shots. The model approximates historical gate, relaxation and readout errors and omits drift/crosstalk and other effects. **No physical QPU, current live calibration, credentials or paid hardware job was used.** Three seeds do not establish broad statistical superiority. QAOA p=2 reaches its objective-call limit in all three main starts; the local results and failure statuses remain visible. Toy Shor rejects unhelpful phase samples rather than classically manufacturing an order.

## Setup and run

Recorded environment: Python 3.12.14; Qiskit 2.6.1, Aer 0.18.2, IBM Runtime 0.51.0, scikit-learn 1.8.0, NumPy 2.3.5 and SciPy 1.17.0. All direct experiment/report dependencies are pinned in requirements.txt. A fresh Python environment is recommended. Small circuits, at most eight qubits here, and one-thread numerical/Aer settings keep the experiment suitable for an 8 GB laptop. Runtime depends on the actual CPU. The offline report opens without installing anything.

From the extracted project folder:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m qstudy audit results --replay-noise
```

The audit reloads saved QPY circuits, checks mathematical references/matrices, recomputes retained hybrid objectives, verifies SVC predictions from coefficients and exactly replays the 24 seeded Aer jobs using pinned versions. It does not replace timings. Exact Aer replay and QPY compatibility depend on package versions; cross-version results/serialization can change.

Small functional run:

```bash
python -m qstudy benchmark --out results-quick --seeds 0 --shots 256 --train-size 12 --test-size 12 --steps 10 --maxfev 60 --quick
python -m qstudy audit results-quick --replay-noise
```

Full recorded protocol:

```bash
python -m qstudy benchmark --out results-rerun --seeds 0 1 2 --shots 4096 --train-size 60 --test-size 60 --steps 60 --maxfev 300
python -m qstudy audit results-rerun --replay-noise
```

Choose a new empty output folder. Tiny runs check functionality; their timings and accuracy are not main conclusions. Program output and matrices are written with completeness checks; JSON uses atomic replacement/readback. To regenerate figures/report without rerunning experiments:

```bash
python -m qstudy report results
```

No network or account is required after dependencies are installed. FrozenManila reads the delivered historical configuration/properties directly. Do not refresh that snapshot while attempting to reproduce the recorded noise study.

## Verification and scope

**23 tests passed.** They cover all four Deutsch functions, all eight promised two-bit DJ functions, all eight three-bit BV secrets, full Fourier matrices/inverses, grid/off-grid QPE, Grover formulas/marks, modular bijections and Shor peaks/postprocessing, VQE dense energy/finite differences, annealing products, analytical feature amplitudes/kernels, data leakage checks and the real backend's JSON metadata compatibility.

The final audit passed **1,803 tracked checks/matches**, including **1,401 retained hybrid expectations**, **86,400 kernel entries**, **720 held-out classifier predictions**, the classical annealing trajectories and exact replay of **all 24 Aer noise/control jobs**. Resource counters match the actual circuit loops. A separate final public-CLI smoke passed **335 checks**, with four tiny classifiers, 420 overlap evaluations and eight seeded Aer replays.

This is **CPU simulation**. Shor uses dense toy modular multiplication; annealing is a declared closed-system Trotter example, not a D-Wave run. Exact overlap probabilities are simulator quantities. Algorithm-suite count histograms are classical Born draws from SDK statevectors; only the calibrated study uses Aer shot jobs. Kernel-shot sensitivity is independent binomial test-kernel sampling with a fixed ideal-trained SVC, not calibrated noisy training. The report separates these evidence types.

A real initial integration error passed a Rust EdgeList directly to JSON and stopped the first pilot before QML. The fix converts edges to native lists; original/fix commits, actual diagnostics and a regression are retained. Partial/development pilots are explicitly excluded from the main analysis. Low quantum accuracy, simulator overhead and optimizer budget termination are results, not invented AI bugs.

## Files

| Path | Purpose |
| --- | --- |
| qstudy/circuits.py | Explicit oracles, algorithms, modular unitary, variational and annealing circuits |
| qstudy/learning.py | Quantum/RBF kernels, matched SVC training, analytical audit formula and shot sensitivity |
| qstudy/experiment.py | Actual SDK execution, source/runtime metadata, counters, preserved circuits and noise controls |
| qstudy/audit.py, report.py | Retained-evidence audit/replay and offline report/figures |
| tests/test_quantum.py | 23 independent semantic, mathematics and integration tests |
| results/algorithm_runs.json, circuits/ | 22 algorithm cases, complete probabilities/counts and QPY circuits |
| results/grover_runs.json | 21 marked-instance runs over 2–8 qubits; queries, gates and wall-time components |
| results/vqe_runs.json, qaoa_runs.json | Three VQE and six QAOA starts, parameters, histories and statuses |
| results/annealing_runs.json | Four quantum schedules/dense references and three separate classical annealing runs |
| results/noise_runs.json, calibrated_noise_model.json | 24 Aer jobs, raw counts, native gates/layouts and actual channel parameters |
| results/qml_runs.json, qml_data/ | Twelve classifiers, six complete datasets/Gram matrices/coefficients/predictions |
| results/kernel_shots.json | Eighteen synthetic fixed-model test-kernel shot controls |
| results/protocol.json, environment.json, evidence_sha256.json | Budgets, conventions, versions, measured source and raw evidence identities |
| inputs/fake_manila/, provenance.json | Exact archived device files/license and unchanged C/D evidence hashes |
| inputs/chapter_coverage.json | Teaching-source hash, slide mapping and additional assignment algorithms |
| docs/FORMULATION.md, COVERAGE.md, VIVA_GUIDE.md | Mathematics, requirement mapping and explanation practice |
| docs/AI_FAILURE_LOG.md, VALIDATION_RECORD.md | Genuine diagnostics/corrections and executed checks |
| prompts/I/, docs/COMMIT_INDEX.md, history.bundle | Actual prompt excerpts and portable local history |

FILE_SHA256.json covers delivered source/data/docs/report, excluding itself and history.bundle to avoid recursive identity. Recover history with `git clone history.bundle track-i-history`. Calibration/provider data retain their original license. Uploaded course slides are acknowledged rather than redistributed.

## AI disclosure and next work

| Tool | Model identification | Date | Use |
| --- | --- | --- | --- |
| ChatGPT / Codex | GPT-6 family as identified by the environment; exact serving revision not independently exposed | 2026-11-04 | Formulation, circuits, tests, debugging, experiments, audit, analysis and documentation |

All substantial work is AI-assisted; no manual student correction is claimed. Confirm the exact model from the full chat/session export before publication rather than guessing. ChatGPT and Codex are not counted as two independent tools. Prompt excerpts are not full conversation exports. Earlier A/B/D supply three genuine corrected cases, with further cases in F/G/H and this package; old C coverage is retained as a historical record rather than the latest global failure count.

Next is **Track J: software-engineering optimization**. Overall integration, unresolved research reproductions, complete exports/model labels, an independent two-AI-tool comparison, the public repository and live demonstration remain open. No public repository was configured or published here.

## Primary references

- Supplied Assignment 8 Section 5 / Track I and Chapter 6 quantum slides.
- [IBM Shor/order-finding learning](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/phase-estimation-and-factoring/shor-algorithm), [Grover operator concepts](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.GroverOperator), [noise-model guide](https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models).
- [Quantum feature-space inspiration](https://arxiv.org/abs/1804.11326), [scikit-learn 1.8 SVC](https://scikit-learn.org/1.8/modules/generated/sklearn.svm.SVC.html).

Sources checked 2026-11-04. Numerical results are this package's own CPU simulations; earlier C/D measurements are labeled separately. The kernel experiment is not a reproduction of the referenced hardware paper.
