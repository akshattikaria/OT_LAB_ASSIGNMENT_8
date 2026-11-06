# Track I requirement mapping

| Assignment requirement | Concrete evidence | Scope |
| --- | --- | --- |
| Every named quantum algorithm on a simulator | Deutsch, DJ, BV, Grover, QFT, QPE, toy Shor order finding, gate-based annealing; VQE/QAOA fresh SDK runs | Qiskit Statevector and Aer CPU simulation |
| At least two self-written circuits | Explicit gates/oracles/QFT in qstudy/circuits.py | No complete built-in algorithm constructors used |
| Real hardware or hardware noise model where possible | Historical FakeManila calibration snapshot, archived configuration/properties/license, generated NoiseModel and 24 Aer jobs | Hardware-derived noise model; no physical QPU |
| QML versus classical model on same data | Fidelity-kernel SVC versus RBF-kernel SVC, identical transforms/splits/C/learner | Two datasets, three seeds, 12 trained classifiers |
| Accuracy, training time, parameters, circuit evaluations | Raw qml_runs.json and matrices; explicit support coefficients/bias and exact overlap counts | Zero trained circuit weights; trained classical SVC coefficients are counted |
| Known complexity-advantage comparison | Grover oracle calls, actual classical scan checks, decomposed gate count and CPU wall-time components | Query scaling is separated from implementation time; observed early classical targets retained |
| Noise and data-loading limits | Paired Aer controls, synthetic kernel-shot sensitivity, explicit oracle/data-map construction | No claim of free input loading or current calibrated behavior |
| Barren plateaus and finite-shot training | Earlier Track C unchanged coverage, summary/audit/protocol with hashes | C empirical diagnostics are referenced, not silently counted as new I runs |
| Contrast quantum and parallel performance | Earlier D work-stealing steady/total metrics, original environment/protocol | Different cost models and startup costs explicitly distinguished |
| Correctness and traceability | Independent matrix/formula tests, QPY, raw objectives, matrices, seeded Aer replay, source/input hashes and Git history | Timings are retained rather than reconstructed |

The supplied 41-slide quantum deck explicitly covers Deutsch (13), Grover (14), parameterized circuits (18), VQA/VQE (20–24), QNN (25), QAOA/Max-Cut (27–30) and barren plateaus (32). Assignment Section 5 additionally names DJ/BV/QFT/QPE/Shor/annealing/quantum kernels, so those are included even where not explicit slide headings. Course source hashes and this mapping are recorded in inputs/chapter_coverage.json; source slides are acknowledged rather than redistributed.

Earlier C supplies QNG, SPSA, finite-shot VQE, generic noise, QNN and gradient-concentration experiments. Its preserved coverage document describes its historical state and is not a current overall progress checklist. Quantum annealing here means a declared closed-system Trotter simulation with dense reference; no D-Wave device, embedding or open-system annealer experiment was executed. Shor is a toy reversible order-finding demonstration, not a scalable factoring implementation.

Core Track I experiment scope is present. Track J, final combined checklist/report, unresolved research reproductions, exact serving-model/full-chat exports, independent two-tool comparison, public repository and live demonstration remain open. Instructor grading is not guaranteed by this checklist.
