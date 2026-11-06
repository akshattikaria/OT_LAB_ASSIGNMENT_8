# Chapter 6 evidence checklist

The root status supersedes historical per-track progress notes. Numerical models are not hardware experiments.

| Topic | Lecture | Status | Evidence | Scope |
|---|---|---|---|---|
| ML parameters and losses | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| MSE/cross-entropy/hinge | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| L0/L1/L2 regularization | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| Continuous/discrete variables | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| Convex/nonconvex landscapes | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| Local/global minima and saddle | PPT1 2-9,20,27 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/results/supplementary.json` |  |
| GD | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| SGD | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Mini-batch SGD | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Momentum | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Nesterov | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| AdaGrad | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| RMSProp | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Adam | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Newton | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Gauss-Newton | Assignment 5 / PPT1 10-21 | implemented | `tracks/A/contopt/optimizers.py`, `tracks/A/results/raw_runs.json` |  |
| Backpropagation distinct from optimizer | PPT1 11 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/tests/test_continuous.py` |  |
| Finite-difference gradient checks | PPT1 11 | implemented | `tracks/A/contopt/problems.py`, `tracks/A/tests/test_continuous.py` |  |
| Convex/strongly-convex bounds | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Nonconvex stationarity | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Step-size tuning | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Noisy gradient objectives | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Expected versus empirical Fisher | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Diagonal curvature | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Low-rank curvature | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Matrix-free HVP/CG | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| L-BFGS library demo | Assignment 5 / PPT1 20 / PPT4 4-6 | implemented | `tracks/A/contopt/supplement.py`, `tracks/A/results/supplementary.json` |  |
| Density greedy | Assignment 5 / PPT1 26 | implemented | `tracks/B/discopt/solvers.py`, `tracks/B/results/raw_runs.json` |  |
| Binary ILP | Assignment 5 / PPT1 26 | implemented | `tracks/B/discopt/solvers.py`, `tracks/B/results/raw_runs.json` |  |
| Branch-and-Bound | Assignment 5 / PPT1 26 | implemented | `tracks/B/discopt/solvers.py`, `tracks/B/results/raw_runs.json` |  |
| Dynamic programming | Assignment 5 / PPT1 26 | implemented | `tracks/B/discopt/solvers.py`, `tracks/B/results/raw_runs.json` |  |
| Forward feature selection | PPT1 23-27 / Assignment 5 | implemented | `tracks/B/discopt/supplement.py`, `tracks/B/discopt/qubo.py`, `tracks/B/results/supplementary.json` |  |
| Backward feature elimination | PPT1 23-27 / Assignment 5 | implemented | `tracks/B/discopt/supplement.py`, `tracks/B/discopt/qubo.py`, `tracks/B/results/supplementary.json` |  |
| Exhaustive feature reference | PPT1 23-27 / Assignment 5 | implemented | `tracks/B/discopt/supplement.py`, `tracks/B/discopt/qubo.py`, `tracks/B/results/supplementary.json` |  |
| QUBO constraint penalties | PPT1 23-27 / Assignment 5 | implemented | `tracks/B/discopt/supplement.py`, `tracks/B/discopt/qubo.py`, `tracks/B/results/supplementary.json` |  |
| Binary-to-spin Ising conversion | PPT1 23-27 / Assignment 5 | implemented | `tracks/B/discopt/supplement.py`, `tracks/B/discopt/qubo.py`, `tracks/B/results/supplementary.json` |  |
| Submodularity and diminishing returns | PPT1 29-34 | implemented | `tracks/D/distopt/coverage.py`, `tracks/D/results/coverage_controls.json` |  |
| Monotonicity/normalization | PPT1 29-34 | implemented | `tracks/D/distopt/coverage.py`, `tracks/D/results/coverage_controls.json` |  |
| Greedy cardinality guarantee assumptions | PPT1 29-34 | implemented | `tracks/D/distopt/coverage.py`, `tracks/D/results/coverage_controls.json` |  |
| Lazy greedy | PPT1 29-34 | implemented | `tracks/D/distopt/coverage.py`, `tracks/D/results/coverage_controls.json` |  |
| Failed-assumption control | PPT1 29-34 | implemented | `tracks/D/distopt/coverage.py`, `tracks/D/results/coverage_controls.json` |  |
| Static blocks | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| LPT scheduling | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Dynamic task pool | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Work stealing | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Makespan | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Strong/weak scaling | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Amdahl and Gustafson interpretation | PPT2 6-15 | implemented | `tracks/D/distopt/scheduling.py`, `tracks/D/results/summary.json` | Actual CPU processes; steady and total clocks are separate. |
| Storage-order traversal | PPT2 16-27 | implemented | `tracks/D/distopt/locality.py`, `tracks/D/results/locality_runs.json`, `tracks/D/results/synchronization_runs.json` | No hardware cache counters or network-cluster claim. |
| Tiled traversal | PPT2 16-27 | implemented | `tracks/D/distopt/locality.py`, `tracks/D/results/locality_runs.json`, `tracks/D/results/synchronization_runs.json` | No hardware cache counters or network-cluster claim. |
| Locks versus reduction | PPT2 16-27 | implemented | `tracks/D/distopt/locality.py`, `tracks/D/results/locality_runs.json`, `tracks/D/results/synchronization_runs.json` | No hardware cache counters or network-cluster claim. |
| Local IPC batching | PPT2 16-27 | implemented | `tracks/D/distopt/locality.py`, `tracks/D/results/locality_runs.json`, `tracks/D/results/synchronization_runs.json` | No hardware cache counters or network-cluster claim. |
| Data parallelism | PPT4 8-14 | implemented | `tracks/D/distopt/parallel.py`, `tracks/D/results/parallel_runs.json` | Actual shared-memory CPU forward inference, not multi-GPU training. |
| Model/tensor parallelism | PPT4 8-14 | implemented | `tracks/D/distopt/parallel.py`, `tracks/D/results/parallel_runs.json` | Actual shared-memory CPU forward inference, not multi-GPU training. |
| Pipeline microbatches | PPT4 8-14 | implemented | `tracks/D/distopt/parallel.py`, `tracks/D/results/parallel_runs.json` | Actual shared-memory CPU forward inference, not multi-GPU training. |
| FedAvg versus matched centralized GD | Assignment 5/D | implemented | `tracks/D/distopt/federated.py`, `tracks/D/distopt/multitask.py`, `tracks/D/results/multitask_runs.json` | Federated clients are serially emulated; no distributed wall-time claim. |
| MGDA | Assignment 5/D | implemented | `tracks/D/distopt/federated.py`, `tracks/D/distopt/multitask.py`, `tracks/D/results/multitask_runs.json` | Federated clients are serially emulated; no distributed wall-time claim. |
| GradNorm | Assignment 5/D | implemented | `tracks/D/distopt/federated.py`, `tracks/D/distopt/multitask.py`, `tracks/D/results/multitask_runs.json` | Federated clients are serially emulated; no distributed wall-time claim. |
| Grid search | PPT4 17-18,27 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/hpo.json` | Actual learning curves, policy replay; ASHA clock is offline event simulation. |
| Random search | PPT4 17-18,27 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/hpo.json` | Actual learning curves, policy replay; ASHA clock is offline event simulation. |
| Bayesian expected-improvement search | PPT4 17-18,27 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/hpo.json` | Actual learning curves, policy replay; ASHA clock is offline event simulation. |
| Successive halving | PPT4 17-18,27 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/hpo.json` | Actual learning curves, policy replay; ASHA clock is offline event simulation. |
| ASHA promotion scheduling | PPT4 17-18,27 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/hpo.json` | Actual learning curves, policy replay; ASHA clock is offline event simulation. |
| Top-k sparsification | PPT4 15 / PPT2 33 | implemented | `chapter_supplement/study.py`, `chapter_supplement/results/compression.json` | Toy optimization; logical payload only. Not OFLight/Subspace Networks. |
| Error feedback | PPT4 15 / PPT2 33 | implemented | `chapter_supplement/study.py`, `chapter_supplement/results/compression.json` | Toy optimization; logical payload only. Not OFLight/Subspace Networks. |
| Int8 gradient compression | PPT4 15 / PPT2 33 | implemented | `chapter_supplement/study.py`, `chapter_supplement/results/compression.json` | Toy optimization; logical payload only. Not OFLight/Subspace Networks. |
| Low-rank activation approximation | PPT4 15 / PPT2 33 | implemented | `chapter_supplement/study.py`, `chapter_supplement/results/compression.json` | Toy optimization; logical payload only. Not OFLight/Subspace Networks. |
| Hybrid-layout enumeration | PPT4 4-7,16 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/layouts.json` | Fictional layout model; separate bounded Rastrigin PSO. Not EAHP/Astra. |
| Genetic layout search | PPT4 4-7,16 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/layouts.json` | Fictional layout model; separate bounded Rastrigin PSO. Not EAHP/Astra. |
| PSO black-box control | PPT4 4-7,16 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/layouts.json` | Fictional layout model; separate bounded Rastrigin PSO. Not EAHP/Astra. |
| Cyclic scheduling | PPT2 12 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/scheduling.json` | Discrete-event scheduling, zero dispatch overhead. |
| Guided scheduling | PPT2 12 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/scheduling.json` | Discrete-event scheduling, zero dispatch overhead. |
| False sharing and padding | PPT2 20-24 | implemented | `chapter_supplement/false_sharing.c`, `chapter_supplement/results/false_sharing.json` | Two real OpenMP threads; no cache-coherence counters. |
| Atomic increments | PPT2 20-24 | implemented | `chapter_supplement/false_sharing.c`, `chapter_supplement/results/false_sharing.json` | Two real OpenMP threads; no cache-coherence counters. |
| NUMA/local placement | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Race interleavings | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Deadlock and ordered locks | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Broadcast/scatter/gather/reduce/allreduce semantics | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Stale-gradient effects | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Overlap arithmetic | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Weight quantization | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Magnitude pruning | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| Discrete architecture choices | PPT1 28 / PPT2 20-28 / PPT4 11-15 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/foundations.json` | Finite models/toy matrices; no actual MPI, NUMA hardware, trained NAS or asynchronous cluster timing. |
| VQE | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| QAOA with B QUBO | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| PQC | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| QNN/VQC | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| Parameter-shift | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| SPSA | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| Quantum natural gradient | Assignment 5/C / PPT3 18-30 | implemented | `tracks/C/qopt/models.py`, `tracks/C/qopt/optimizers.py`, `tracks/C/results/vqe_runs.json` | CPU simulator; QNG metric uses exact amplitudes. |
| Finite-shot measurement cost | PPT3 6-8,19,32 | implemented | `tracks/C/results/shot_study.json`, `tracks/C/results/noise_study.json`, `tracks/C/results/barren_plateaus.json` | Finite empirical diagnostics, not a universal asymptotic proof. |
| Generic hardware-noise effects | PPT3 6-8,19,32 | implemented | `tracks/C/results/shot_study.json`, `tracks/C/results/noise_study.json`, `tracks/C/results/barren_plateaus.json` | Finite empirical diagnostics, not a universal asymptotic proof. |
| Barren-plateau diagnostics | PPT3 6-8,19,32 | implemented | `tracks/C/results/shot_study.json`, `tracks/C/results/noise_study.json`, `tracks/C/results/barren_plateaus.json` | Finite empirical diagnostics, not a universal asymptotic proof. |
| Deutsch | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Deutsch-Jozsa | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Bernstein-Vazirani | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Grover | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| QFT | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| QPE | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Shor toy order finding | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Qubits/gates/entanglement | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Quantum annealing | Assignment 5/I / PPT3 3-18 | implemented | `tracks/I/qstudy/circuits.py`, `tracks/I/results/algorithm_runs.json`, `tracks/I/results/annealing_runs.json` | Explicit small circuits; dense toy arithmetic and gate-based annealing, not scalable factoring or physical annealer. |
| Quantum kernel versus matched RBF learner | Assignment I | implemented | `tracks/I/qstudy/learning.py`, `tracks/I/results/qml_runs.json`, `tracks/I/results/noise_provenance.json`, `tracks/I/results/grover_runs.json` |  |
| Hardware-calibrated noise | Assignment I | implemented | `tracks/I/qstudy/learning.py`, `tracks/I/results/qml_runs.json`, `tracks/I/results/noise_provenance.json`, `tracks/I/results/grover_runs.json` |  |
| Query/gate/wall-time accounting | Assignment I | implemented | `tracks/I/qstudy/learning.py`, `tracks/I/results/qml_runs.json`, `tracks/I/results/noise_provenance.json`, `tracks/I/results/grover_runs.json` |  |
| Minor embedding and chain penalties | Assignment 5 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/embedding.json` | Exact 16-state classical enumeration, no annealer hardware. |
| Coefficient rescaling and physical-qubit overhead | Assignment 5 | numerical_demo | `chapter_supplement/study.py`, `chapter_supplement/results/embedding.json` | Exact 16-state classical enumeration, no annealer hardware. |
| Main EV case: binary cost scheduling | Assignment Track E | implemented | `tracks/E/evcharge/solvers.py`, `tracks/E/results/summary.json` |  |
| Compiler: frontend/IR/backend, four passes and DP ordering | Assignment Track F | implemented | `tracks/F/toycc/search.py`, `tracks/F/results/summary.json` |  |
| Real xv6: page allocation and cache lookup | Assignment Track G | implemented | `tracks/G/patches/track_g.patch`, `tracks/G/results/summary.json` |  |
| Real SQLite: budgeted index portfolios | Assignment Track H | implemented | `tracks/H/dblab/select.py`, `tracks/H/results/summary.json` |  |
| Real software: test selection and fault trade-off | Assignment Track J | implemented | `tracks/J/selci/selection.py`, `tracks/J/results/summary.json` |  |

## Research boundary

The slides label these as research references/spotlights. Listing or bibliographic verification does not count as reproducing an algorithm. Related standard Fisher, greedy, stealing, SVD or GA demonstrations are not relabeled with paper names. If sir expects each paper-specific method as an experiment, the unreproduced rows remain additional work.

| Entry | Lecture | Verification | Experimental status |
|---|---|---|---|
| GRNG / RENG / RING | PPT1 35 | primary_checked_in_conversation | paper_not_reproduced |
| AdaFisher | PPT1 35,38 | primary_checked_in_conversation | paper_not_reproduced |
| Dynamic nonmonotone submodular methods | PPT1 36 | slide_citation_only | paper_not_reproduced |
| Differentially private submodular methods | PPT1 36 | slide_citation_only | paper_not_reproduced |
| OmniOpt taxonomy/benchmark | PPT1 38 | slide_citation_only | paper_not_reproduced |
| ResQue Greedy | PPT1 38 | primary_checked_in_conversation | paper_not_reproduced |
| PANA SpMV | PPT2 31 | primary_checked_in_conversation | paper_not_reproduced |
| PackStealLB | PPT2 31-32 | slide_citation_only | paper_not_reproduced |
| GSHetero | PPT2 31 | slide_citation_only | paper_not_reproduced |
| Architecture-aware currying | PPT2 33 | slide_citation_only | paper_not_reproduced |
| Subspace Networks | PPT2 33 | slide_citation_only | paper_not_reproduced |
| OFLight | PPT2 33 | slide_citation_only | paper_not_reproduced |
| EAHP | PPT4 22,24-25 | slide_citation_only | paper_not_reproduced |
| GAGS SVM | PPT4 22,24 | slide_citation_only | paper_not_reproduced |
| Astra | PPT4 22,24-25 | primary_checked_in_conversation | paper_not_reproduced |
| HPO tutorial/survey | PPT4 22,24,26 | slide_citation_only | paper_not_reproduced |
| ASHA systems paper | PPT4 27 | primary_checked_in_conversation | mechanism_replay_only |

Names explicitly marked not found/not cited in the slides are not fabricated: DiCTR, Mixer, RLDPSO, AutoHAAP, SSGS, OSCAR, LS-GT and AFS-GNN.
