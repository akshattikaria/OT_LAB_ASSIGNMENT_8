# Assignment 8 - Integrated technical report

Akshat Tikaria | 241070005 | Updated 7 November 2026


## Overview: ten tracks, one optimization workflow


This portfolio identifies a process, formulates valid decisions, compares a baseline with optimization methods, verifies outputs and reports trade-offs. EV charging is the main case study. All 2,013 imported files from A-J are preserved unchanged; new supporting chapter experiments and this report connect the portfolio.


| Track | Measured finding | Meaning |

|---|---|---|

| A | Ridge exact references; varied neural optimizer outcomes | No universal optimizer ranking |

| B | Exact DP/ILP versus heuristic/bounded-search gaps | Quality and proof differ from speed |

| C | QNG lowers VQE gap with extra metric work | CPU simulation; not QPU advantage |

| D | 5.40x steady versus 1.026x total stealing speedup | Startup changes the conclusion |

| E | 49.44% flexible-case paired cost reduction | Synthetic data and fictional tariff |

| F | O0 gains; mixed O2 ratio 0.889 | Score optimum need not run faster |

| G | Zero page-allocation spins; 11.95x slower elapsed | Negative result retained |

| H | 33.11x mixed-read QPS at 60% ILP design | Storage and write trade-off |

| I | RBF beats tested quantum kernel on both datasets | Query count is not wall time |

| J | 74/391 tests; 41.5% less median wall time | Three detected faults missed |


Measurements use shared cloud CPU environments, not the student's i3 laptop. Quantum work is CPU simulation, including one historical hardware-derived noise model; no physical QPU was used. Each track has its own objective, data, timer scope and environment. Heterogeneous gains are not averaged into one project-wide percentage.


Per-track progress notes are original dated milestones. The root README and submission checklist give current overall status. Paper-specific research references and missing external evidence remain explicit.


## Track E: process, mathematics and strategy


Immediate charging can buy expensive energy despite cheaper later slots. Shared station capacity can let flexible arrivals crowd out urgent vehicles. Synthetic cases demonstrate these mechanisms; no field-station savings are claimed.


| Symbol | Meaning |

|---|---|

| x_it | Binary: vehicle i charges in slot t |

| a_i, d_i | Arrival and exclusive departure slots |

| r_i | Required number of charging slots |

| P_i, Δ | Fixed charging kW and slot duration in hours |

| c_t, C_t | Fictional rupees/kWh and station kW limit |


Minimize Σ_i Σ_t c_t P_i Δ x_it. Require Σ_t x_it = r_i for every EV; Σ_i P_i x_it ≤ C_t for every slot; x_it = 0 outside [a_i,d_i); x_it ∈ {0,1}. Exact energy equality prevents undercharging from appearing as a saving.


| Method | Rule | Suitability / limit |

|---|---|---|

| Baseline | Arrival priority, charge immediately | Simple reference; no guarantee |

| Greedy | Earlier deadlines, cheapest available slots | Fast discrete heuristic; interactions matter |

| Binary ILP | Joint vehicle-slot allocation | Linear objective and constraints; proof status retained |


Main workloads use 48 fifteen-minute slots, one assigned plug per EV and slot-aligned demand. Charging may pause at boundaries. Battery taper, losses, wear, demand charges, uncertainty and plug queues are outside scope. Identical powers allow a min-cost-flow interpretation; binary variables alone do not prove every restricted case hard.


Evidence: tracks/E/docs/FORMULATION.md; tracks/E/evcharge/solvers.py; results/protocol.json


## Track E: evidence of improvement and limits


Seventy-five main instances cover five scenario families, three fleet sizes and five seeds. Four diagnostic controls include a known feasible greedy failure and a provably infeasible station. Three repetitions/method/instance yield 711 recorded runs. Feasible input witnesses are audited and withheld from the solvers.


| Scenario | Baseline | Greedy | ILP | Certified paired saving |

|---|---|---|---|---|

| flexible | 15/15 | 15/15 | 15/15 | 49.44% (n=15) |

| flat prices | 15/15 | 15/15 | 15/15 | 0.00% (n=15) |

| tight deadlines | 13/15 | 12/15 | 15/15 | 8.36% (n=13) |

| limited power | 8/15 | 13/15 | 15/15 | 18.14% (n=8) |

| mixed power | 13/15 | 15/15 | 15/15 | 39.25% (n=8) |


![Pair counts require matched feasibility and an optimality certificate; they can be smaller than feasible counts.](reports/figures/ev_synthesis.png)


Main feasibility is 64/75 baseline, 70/75 greedy and 75/75 ILP. ILP proves 70 optimal; five time-limited candidates are independently feasible. Timeout is not infeasibility. Flexible-window savings average 49.44% on 15 pairs; flat-price saving is zero.


Independent checks recompute binary choices, availability, exact delivered slots, station load and cost. Twenty-nine retained host tests pass, including 80 random tiny ILP/exhaustive comparisons. Fictional tariffs, feasible-workload selection and excluded physical behavior limit generalization.


Evidence: tracks/E/results/raw_runs.json; instances/; witnesses/; input_sha256.json


## Track A: continuous optimization and verification


An eight-parameter ridge model minimizes half-MSE plus L2; augmented least squares provides its strongly convex optimum. A 2-8-1 tanh classifier has 33 regularized parameters and nonconvex cross-entropy. Five seeds and three repeats yield 270 main runs.


| Method | Mean ridge gap | Neural accuracy | Neural median ms |

|---|---|---|---|

| GD | 0.0443 | 91.95% | 10.11 |

| SGD | 0.000163 | 96.09% | 579.85 |

| MiniBatchSGD | 0.00187 | 94.69% | 27.69 |

| Momentum | 2.18e-05 | 95.86% | 28.20 |

| NAG | 6.07e-06 | 96.17% | 29.38 |

| AdaGrad | 0.000268 | 96.56% | 27.87 |

| RMSProp | 0.0107 | 96.56% | 30.86 |

| Adam | 0.000121 | 96.56% | 30.27 |

| Newton | 0 | n/a | n/a |

| GaussNewton | 0 | n/a | n/a |


Four candidate learning rates are tuned on a separate seed, with no test-label selection. GD, per-sample SGD and mini-batch methods use different update counts even at matched sample-gradient passes. Newton/Gauss-Newton add curvature/line-search work; this is not equal-FLOP comparison.


Backpropagation computes gradients; the optimizer chooses updates. All 33 neural derivatives are checked by finite differences. Model and empirical Fisher differ; diagonal/rank-2 curvature, matrix-free HVP/CG, L-BFGS and nonlinear Gauss-Newton controls are retained. Dense construction of the rank-2 approximation is not a memory-saving implementation.


Convex/strong-convex bounds, unequal local minima, a saddle and noisy objectives demonstrate limits. A zero gradient does not prove a minimum. The largest main gradient-check error is about 1.76e-11. Thirty retained host tests pass.


Evidence: tracks/A/contopt/; results/raw_runs.json; supplementary.json; tuning_*.json


## Track B: discrete decisions, QUBO and Ising


Binary item choices maximize Σv_i x_i under Σw_i x_i≤capacity. Input-order baseline, density greedy, DP, custom Branch-and-Bound and library ILP share inputs and are independently checked. Eighty main cases plus five controls, five methods and three repeats yield 1,275 runs.


| Family | Baseline gap | Greedy gap | B&B matches DP | ILP matches DP |

|---|---|---|---|---|

| uncorrelated | 32.72% | 0.97% | 20/20 | 20/20 |

| weakly correlated | 17.04% | 1.57% | 20/20 | 20/20 |

| strongly correlated | 12.81% | 3.18% | 17/20 | 20/20 |

| subset sum | 1.86% | 1.86% | 16/20 | 20/20 |


![Feature selection uses separate validation/test data; tiny QUBOs are checked state-by-state.](tracks/B/results/qubo_and_features.png)


DP certifies the bounded integer-capacity instances. Search limits and feasible incumbents remain distinct from proven optima. A feature study compares forward/backward selection with every three-feature subset.


Slack bits turn capacity into equality; the QUBO combines negative value with squared residual penalties. Direct/binary/spin energies and offsets agree for every tiny state. Weak penalties are deliberate controls. A real huge-coefficient cancellation defect is corrected by an explicit supported-range guard. Thirty retained host tests pass.


Evidence: tracks/B/discopt/solvers.py; qubo.py; results/supplementary.json; quantum_exports/


## Track C: hybrid quantum optimization in simulation


Explicit NumPy statevector/density simulators compare VQE parameter-shift GD/Adam, SPSA and QNG. QAOA consumes unchanged B exports for four-bit Max-Cut and six-bit knapsack. These CPU simulations do not establish quantum hardware speedup.


| VQE method | Mean gap | State preparations | Metric preparations | Mean s |

|---|---|---|---|---|

| ShiftGD | 0.000433 | 1297 | 0 | 0.222 |

| ShiftAdam | 0.000416 | 1297 | 0 | 0.228 |

| SPSA | 0.145 | 177 | 0 | 0.035 |

| QNG | 5.91e-10 | 2657 | 1360 | 0.404 |


![QNG improves this energy objective while paying additional exact state/metric work.](tracks/C/results/figures/vqe_cost.png)


Max-Cut mean ground probability increases from about 0.390 at depth 1 to 0.864 at depth 2 under C's budget. Penalized knapsack remains difficult; original feasibility and encoded feasibility are separately recorded. Local optimizer success is not a high-quality original solution certificate.


Finite-shot distributions, shot-trained VQE, generic gate/readout noise and 2-10-qubit gradient-concentration diagnostics retain all outcomes. These are finite experiments, not a universal barren-plateau theorem. QNN test accuracy averages 87.5% versus 90.625% logistic. Thirty-two retained host tests pass.


Evidence: tracks/C/results/vqe_runs.json; qaoa_runs.json; shot_study.json; barren_plateaus.json


## Track D: submodular, parallel and distributed work


Weighted coverage is normalized, monotone and submodular under nonnegative weights. Ordinary/lazy greedy have mean exact ratio 0.993 and worst 0.921 on small cases. The 1-1/e cardinality-maximization bound is not transferred to weighted set-cover minimization in J.


| Irregular work, p=8 | Steady s | Speedup | Efficiency | Total speedup |

|---|---|---|---|---|

| static_block | 0.2563 | 2.03x | 25.4% | 0.887x |

| static_lpt | 0.0934 | 5.16x | 64.4% | 0.828x |

| dynamic_pool | 0.0871 | 5.72x | 71.4% | 0.907x |

| work_stealing | 0.0975 | 5.40x | 67.5% | 1.026x |


![Actual PBKDF2 jobs return verified digests; readiness handshakes separate steady from total time.](tracks/D/results/figures/scheduling_scaling.png)


Ninety-six strong-scaling and 12 weak-scaling process runs compare static blocks, LPT, a central pool and deque stealing. At eight workers, stealing gives 5.40x steady but only 1.026x total speedup. Actual CPU data/model/pipeline forward inference preserves outputs; it is not multi-GPU pipeline training. Native locality, lock/reduction and local IPC controls retain their results.


FedAvg uses four unequal serially emulated clients. E=1 equals matched centralized GD; E=20 with fewer rounds cuts logical payload 20x at equal sample visits but increases drift under skew. MGDA and GradNorm select different compromises between two shared-model task losses. Neither universally improves both. Twenty-nine retained host tests pass.


Evidence: tracks/D/results/scheduling_runs.json; parallel_runs.json; federated_runs.json; multitask_runs.json


## Track F: compiler passes and DP ordering


The mini-compiler includes positioned lexer, precedence parser, immutable SSA, interpreter and unsigned C generation. Four passes perform fold/propagate, CSE, DCE and power-of-two strength reduction. Pure total uint64 wrap/shift semantics make the transformations well-defined.


Choose a four-pass permutation minimizing fixed weighted IR cost. DP state includes both used-pass mask and canonical transformed IR; a subset alone loses order effects. All 24 permutations verify each finite optimum. DP beats immediate greedy score on 10/20 programs; this is not native-runtime optimality.


| Family | IR reduction | Mean O0 ratio | Mean O2 ratio |

|---|---|---|---|

| constant_chain | 49.5% | 1.702x | 1.015x |

| redundant | 70.6% | 2.354x | 1.022x |

| dead_heavy | 86.3% | 3.701x | 1.009x |

| mixed | 77.3% | 3.314x | 0.889x |


![Ratios below one are regressions. O0 illustrates pass effects; O2 controls for host optimization.](tracks/F/results/figures/native_runtime.png)


Retained evidence includes 480 Python compiler timings, 40 native builds and 1,000 native timings on 20 programs. Independent AST/IR/native checks cover boundaries, wraparound and random inputs. Compile-time overhead, static disassembly counts and symbol sizes are reported separately. The mixed-family O2 ratio 0.889 is a negative result. Twenty-nine retained host tests pass.


Evidence: tracks/F/results/pass_search.json; runtime_runs.json; native_function_stats.json; validation.json


## Track G: real xv6 changes and an honest slowdown


Pinned MIT xv6 RISC-V commit e93dabeb98431235c6e1a101cb96c73c923fdbc4 is modified with per-CPU free lists/bounded stealing and a 13-bucket buffer-lookup hash index. The cache retains its original global lock, 30-buffer capacity and LRU policy.


Four configurations, six new guest workloads and three repeats yield 72 main measurements across 12 boots. QEMU guests have three vCPUs and 128 MiB RAM. Retained UART shows the pristine kernel and all four instrumented variants pass all 74 named upstream tests, with custom checks before/after.


| Objective / workload | Baseline | Changed | Conclusion |

|---|---|---|---|

| Page allocator failed exchanges | 182,069 | 0 | Less measured spinning |

| Page workload guest s | 0.3919 | 4.6821 | 11.95x slower |

| Hash hotseq probes/lookup | 8.132 | 2.270 | 72.09% fewer probes |

| Hash hotrand probes/lookup | 4.881 | 2.603 | 46.68% fewer probes |

| Hash scan probes/lookup | 15.148 | 2.182 | 85.60% fewer probes |


![Emulated guest times; all slow configurations and repetitions are preserved.](tracks/G/results/figures/elapsed.png)


Reduced contention/search work does not guarantee lower elapsed time; the allocator regression's cause is not isolated. Hashing does not reduce disk misses or remove the global lock. Page ownership/count, cache-key/reference and lock invariants are checked. The exact patch is supplied. Fourteen retained host tests pass; archived guest tests are not relabeled fresh integration runs.


Evidence: tracks/G/patches/track_g.patch; results/uart/; validation/kernel_validation.json


## Track H: real database portfolios and maintenance cost


SQLite holds 200,000 synthetic bookings, 20,000 customers and 600 stations. Binary index choices maximize measured training benefit under a B-tree storage budget. Greedy gain/KiB and ILP compare with the default planner and all-index reference. All 64 candidate subsets certify the finite surrogate model.


| Portfolio | Index MiB | Held-out ms | Mixed QPS | Insert rows/s |

|---|---|---|---|---|

| Default planner | 0.000 | 9.154 | 99 | 103371 |

| 20% GREEDY | 4.234 | 5.177 | 173 | 62087 |

| 20% ILP | 3.902 | 5.030 | 190 | 71579 |

| 40% G = ILP | 7.613 | 1.660 | 530 | 33026 |

| 60% GREEDY | 11.516 | 0.770 | 1251 | 19847 |

| 60% ILP | 12.777 | 0.237 | 3289 | 18727 |

| All six indexes | 22.289 | 0.251 | 3390 | 10133 |


![Same held-out SQL/parameters; throughput is independently timed from mixed batches.](tracks/H/results/figures/latency.png)


At 60% ILP, mixed-read QPS is 33.11x baseline, using 12.777 MiB indexes while insertion throughput falls from about 103,371 to 18,727 rows/s. This optimizes a read objective, not all operations.


Raw EXPLAIN QUERY PLAN records are high-level plans, not invented EXPLAIN ANALYZE counters. Independent references preserve integers, NULL behavior, ordering and LIMIT ties. The model certificate does not prove arbitrary-index or future-runtime optimality. Seventeen retained host tests pass.


Evidence: tracks/H/results/model.json; selections.json; plans.json; latency_runs.json; write_runs.json


## Track I: explicit algorithms and true cost accounting


Qiskit Statevector/Aer executes explicit Deutsch, DJ, BV, Grover, QFT, QPE, toy Shor, VQE/QAOA and gate annealing circuits. QFT is checked against the complete Fourier unitary; QPE against finite Fourier distributions; modular multiplication against reversible permutations.


| Algorithm | Verified example | Boundary |

|---|---|---|

| Deutsch / DJ | Constant/balanced promised oracles | Truth-table loading is not free |

| BV | Hidden three-bit strings | Explicit phase-kickback/CNOT oracle |

| QFT / QPE | 2-4 qubits, exact/off-grid phases | Full complex/distribution checks |

| Shor | N=15, multipliers 2/7/11/14 | Dense toy arithmetic, failure control |

| Annealing | Four-bit Trotter schedule | Closed system, dense reference |


![Logical queries, compiled physical gates and CPU simulation time are separate metrics.](tracks/I/results/figures/grover.png)


At N=256, Grover uses 12 oracle rounds plus verification versus 128.5 expected uniform-target classical checks. The observed sample mean is 35. The circuit has 4,080 compiled CX gates and about 206 ms median simulator time, versus microseconds for tiny classical scans. This is a query advantage, not practical wall-time advantage.


Oracles, data loading, compilation, routing, noise, shots and error correction all matter beyond a unit-query model. Complex unitarity uses U†U=I, not an ordinary transpose. No physical QPU was used.


Evidence: tracks/I/qstudy/circuits.py; results/algorithm_runs.json; grover_runs.json; annealing_runs.json


## Track I: matched QML and historical calibrated noise


| Data | Kernel | Test accuracy | Train s | Learned scalars | Circuits/model |

|---|---|---|---|---|---|

| moons | quantum | 64.44% | 1.7230 | 51.7 | 5370 |

| moons | rbf | 88.89% | 0.0015 | 28.7 | 0 |

| circles | quantum | 75.56% | 1.7588 | 43.3 | 5370 |

| circles | rbf | 97.22% | 0.0013 | 42.3 | 0 |


Both precomputed-kernel SVCs use the same stratified splits, training-fitted transforms, features and C=1. Averages use three seeds with 60 train/60 held-out records. The fixed two-qubit feature map has zero trained circuit weights, but the SVC learns coefficients/bias. The tested quantum kernel loses in accuracy and simulation training time on both datasets.


![Wilson bars describe shot sampling, not uncertainty in the calibration itself.](tracks/I/results/figures/noise.png)


Archived FakeManila calibration is dated 2024-05-27. Paired ideal/noisy jobs use identical compiled programs, layouts and mappings. Correct fractions under the historical noise model are 85.66% BV, 90.28% DJ, 46.67% Grover and 60.27% QPE. This approximates historical device errors, not current hardware behavior.


Kernel entries, predictions, Fourier formulas and circuit identities are independently checked. Twenty-three retained host tests pass. Simulator evaluations are not physical QPU shots; no computational-hardness or general QML superiority claim follows.


Evidence: tracks/I/results/qml_runs.json; noise_runs.json; noise_provenance.json; audit.json


## Track J: line preservation versus fault detection


The unchanged MIT cachetools 7.2.8 distribution contains 1,798 Python source lines and 391 parent tests with 24 subtests. Binary weighted set cover minimizes profiled duration while preserving 1,005 per-test source lines. Fresh selected-suite traces validate actual coverage rather than trusting only the baseline matrix.


| Method | Tests | Median wall s | Branches /214 | Full kills /16 |

|---|---|---|---|---|

| full | 391 | 1.196 | 214 | 16 |

| count greedy | 80 | 0.673 | 210 | 14 |

| weighted greedy | 79 | 0.664 | 209 | 13 |

| ilp | 74 | 0.699 | 208 | 13 |


![All suites preserve 1,179/1,185 statement coverage and the line universe; quality still differs.](tracks/J/figures/coverage_and_faults.png)


ILP selects 74 tests and reduces observed median wall time 41.5%; its zero-gap certificate covers the static additive model, not actual wall time or minimum test count. Weighted greedy has the lowest observed wall median. Seven trials/method give 28 timing records.


All 80 seeded mutation outcomes are retained. The full suite kills 16, survives three and times out on one. ILP retains 13/16 kills and loses six branch outcomes. The common timeout is not a kill or equivalence certificate. Use such a subset for limited fast feedback while retaining the full release suite. Ten retained host tests pass.


Evidence: tracks/J/results/methods.json; timings.json; mutation_results.json; coverage/


## Chapter supplement: search-policy experiments


All 27 fixed (learning rate,L2,momentum) configurations are trained for 27 epochs on five synthetic regression splits. Complete curves form an audit reference. Search policies reveal only authorized validation observations; held-out losses do not select a model.


| Policy | Mean epoch-units | Validation MSE | Held-out MSE |

|---|---|---|---|

| input_first | 27.0 | 2.1216 | 2.1431 |

| grid_all | 729.0 | 0.1150 | 0.1352 |

| random_9 | 243.0 | 0.1182 | 0.1333 |

| bayesian_9 | 243.0 | 0.1186 | 0.1382 |

| successive_halving | 81.0 | 0.1226 | 0.1369 |

| asha_replay | 233.4 | 0.1184 | 0.1343 |


Bayesian finite-pool search uses a Matérn Gaussian-process surrogate and expected improvement. Random/Bayesian methods each query nine full-budget models. Grid uses all 27. Successive halving keeps 27→9→3→1 at resources 1→3→9→27; checkpoint continuation costs 81 epoch-units, compared with 108 if each rung restarts.


ASHA is a four-worker promotion-rule trace replay, not measured parallel training. Rung results become available only at completion; eligible candidates are promoted using currently observed ranks. Event durations come from actual training segments. Reference-grid generation itself still incurs full compute; policy-accounting savings are not described as measured wall-time savings.


Unequal budgets are explicit. These small demonstrations do not reproduce the ASHA systems paper, a 500-worker deployment or every HPO framework. Seven supplemental tests check rank/resource/checkpoint behavior, test-label independence and other numerical invariants.


Evidence: chapter_supplement/study.py; results/hpo.json; validation/supplement_tests.log


## Chapter supplement: compression, strategy and embedding


| Gradient method | Mean final objective | Logical bytes /1000 updates |

|---|---|---|

| dense | 0.00609127 | 256000 |

| topk | 5.0498 | 24000 |

| topk_error_feedback | 0.00594657 | 24000 |

| int8_error_feedback | 0.00609129 | 40000 |


Five 32-coordinate SPD quadratics share starts, 1,000 updates and eta=.002. Top-2 without feedback converges more slowly in this control. With feedback, sum(sent)+residual=sum(uncompressed steps), checked numerically. Payload counts float64 values/uint32 indices or int8 codes/float64 scale; it excludes protocol and is not measured network traffic.


Additional records show SVD activation error/size, 28 ordered d·t·p=64 layouts under a fictional cost model, GA finite search and bounded 2D Rastrigin PSO against equal-call random search. These are mechanisms, not EAHP/Astra/Subspace Networks/OFLight reproductions.


| Chain C | Ground energy | Ground states | Broken chains | Rescaled logical coupling |

|---|---|---|---|---|

| 0 | -3 | 2 | 2 | 1.00 |

| 0.25 | -2.75 | 2 | 2 | 1.00 |

| 1 | -2 | 8 | 2 | 1.00 |

| 2 | -3 | 6 | 0 | 0.50 |

| 4 | -5 | 6 | 0 | 0.25 |


A logical triangle is embedded in a physical four-cycle using chain {0,1}. Exact 16-state enumeration shows weak-chain failures and coefficient rescaling as strength rises. This is classical verification, not annealer hardware/dynamics. Native OpenMP padding uses two real threads; cyclic/guided dispatch, NUMA placement, stale gradients, collectives and race/deadlock examples are explicitly finite models.


Evidence: chapter_supplement/results/compression.json; layouts.json; embedding.json; false_sharing.json; foundations.json


## Research extension: optimization and privacy


The 6 November extension adds experiments for all 23 research entries: 11 scoped equation/code ports, four algorithm variants, two survey demonstrations and six mechanism-only controls. A port means the stated small specialization is implemented; none reproduces an entire paper or its performance. Detailed sources, equation locators, changes and gaps are in METHOD_COVERAGE.md and SOURCE_REGISTRY.json.


| Binary logistic, 5 seeds | Mean reference gap | Training ms |

|---|---|---|

| gd | 0.00586 | 4.46 |

| natural_gradient | 0.00000 | 5.09 |

| ring | 0.00951 | 9.41 |

| reng | 0.00932 | 6.66 |


GRNG uses the RING/RENG regularizers with exact full-batch Fisher refresh; gradient-norm derivatives use the Hessian-vector expression. A separate regularized Kalman port checks covariance positivity. On the small logistic cases, ordinary natural gradient reaches the reference more closely than the regularized controls. This is no universal ranking.


AdaFisher follows the printed running-factor equation on a three-class single-layer model. Mean final cross-entropy is 1.0724 versus 1.0605 for Adam. An initial scalar-output factor normalized to zero; the informative multiclass correction and original diagnostic are retained. The authors' current factor update differs from the printed equation; code equivalence is not claimed.


ResQue implements the curvature trigger/step-back with a declared incumbent safeguard; both raw and guarded outcomes are saved. Guarded exact ratios range 0.944 to 1 over five cases. Dynamic nonmonotone selection uses disjoint level reservoirs and partial rebuilds, a finite threshold grid and an exact offline oracle: 90 insert/delete events, with no asymptotic guarantee claimed.


| Private greedy+ epsilon | Max |log(p/q)|, one neighbor pair |

|---|---|

| 0.2 | 0.051005 |

| 0.8 | 0.204718 |

| 2.0 | 0.514850 |


The paper-specific private density-greedy+ port uses generalized exponential noisy max and conservative pure composition, replacing the source's advanced composition. Fifteen sampled runs and an independent exponential-mechanism control retain utility and feasibility. The table integrates every output path on one three-item neighboring-dataset pair; it is a finite certificate, not a universal privacy proof or deployment claim.


Evidence: research_supplement/curvature.py; submodular.py; results/curvature.json; submodular.json; privacy_certificate.json


## Research extension: quantum training mechanisms


All quantum extensions use explicit CPU statevectors. Parameter-shift derivatives and the classical chain rule are checked against finite differences. Reported seconds measure simulator training, not QPU execution or quantum advantage.


![Left: each of five synthetic six-class temperature cases. Right: every held-out liver split; different data and tasks.](reports/figures/research_quantum_data.png)


| Study, 5 seeds | Retained result | Boundary |

|---|---|---|

| TensorHyper-VQC | Direct energy -2.129; TT -1.480 | 20 TT scalars generate 27 circuit angles; rank-one variant is worse |

| Negative-rate rule | Mean 0.4 ascent branches / 100 steps | Loss-triggered rule, 256-shot gradient; almost identical energy to descent |

| Measurement temperature | Mean accuracy 70.8% to 89.6% | Joint positive T and angles; synthetic six-class data only |

| Nested optimization | Mean energy gap 0.884 | Actual ancilla dilation/postselection; fixed ansatz replaces RL structure search |


TensorHyper uses a rank-one tensor-train parameter generator driven by Gaussian inputs. Direct optimization performs better here; parameter count alone does not imply a better solver. Negative learning is the source loss-triggered ascent branch, rather than an invented periodic schedule. Measurement temperature learns log T in softmax(z/T) from the same starts and training split as T=1.


Nested optimization specializes the Hermitian objective to p=1, constructs a dense unitary dilation, postselects its gradient-filter state and fits a parameterized circuit by fidelity. Unitarity error is 1e-15. Five runs retain every positive ground-state gap. Dense simulation, omitted sparse-oracle construction and fixed circuit structure rule out source-scale complexity claims.


Evidence: research_supplement/quantum.py; quantum_studies.py; results/{tensorhyper,negative_learning,qmt,nom}.json


## Research extension: QML-Liver on author data


The author repository provides the actual 583-row Indian Liver Patient Dataset CSV and a two-qubit notebook. This original NumPy port follows Dense(256)-dropout(.3)-Dense(128)-dropout(.3)-Dense(2), a two-qubit RX encoder with four BasicEntangler layers (eight circuit parameters), and a sigmoid output. The author code is MIT; the UCI dataset is CC BY 4.0, with attribution and hashes included.


| Model, 3 splits | Accuracy | Balanced acc. | Training s |

|---|---|---|---|

| hybrid quantum | 64.39% | 69.69% | 1.259 |

| matched classical | 63.82% | 69.58% | 0.159 |

| logistic reference | 66.95% | 72.08% | not timed |


| Split seed | Hybrid accuracy | Matched classical | Logistic |

|---|---|---|---|

| 31 | 70.94% | 65.81% | 71.79% |

| 41 | 62.39% | 62.39% | 62.39% |

| 51 | 59.83% | 63.25% | 66.67% |


Each split reserves 20% for testing, then 20% of the remainder for validation, stratified by label. Medians and standardization are fitted only on training rows. A maximum of 80 epochs and validation early stopping replace the source's 100-epoch setting. Test labels never choose an epoch. The matched classical model keeps the eight-parameter bottleneck and the same dense architecture; both use manual backpropagation, dropout and class-weighted focal loss.


The hybrid ties logistic on one split and loses on two; its mean accuracy is below logistic. Hybrid versus matched-classical mean accuracy differs by less than one percentage point, with only three splits. These outcomes do not establish a general quantum benefit or reproduce the paper's scores. This educational experiment is not a clinical validation.


Saved rows contain split indices, train-only preprocessing, all test probabilities, labels, confusion matrices, ROC AUC, chosen epoch and final parameters. Quantum counters distinguish batched statevector calls from per-example circuit instances, including parameter/input shifts, validation and testing. The initially ambiguous counter is retained as a diagnostic; the corrected counter is audited.


Evidence: research_supplement/liver.py; data/provenance.json; data/ATTRIBUTION.md; results/liver.json; validation/research_tests_final.log


## Research extension: native parallel and communication


![SpMV whiskers show the full range across five input-case medians, each based on seven timed repetitions. Right: actual search work.](reports/figures/research_native_search.png)


A native GCC/OpenMP SpMV control uses two real threads on identical CSR inputs and a serial reference. Uniform, skewed and empty-row families each use five seeds, two methods and seven timed repetitions: 210 trials. Long rows are split into nonzero tiles; partial sums use atomics and the tile size adapts to prior throughput. Maximum errors are within 1e-8. Method order is fixed, and these tiny shared-host timings are descriptive. This is PANA-related mechanism evidence; its unpublished-to-us SIMD policy is not claimed.


The Subspace Networks port uses two residual blocks, frozen high-rank embeddings and a shared width-32/rank-4 subspace. Dense and compressed executions of that same constrained model agree in all five 100-step parameter trajectories; maximum final parameter difference is 5.7e-16. Boundary payload is reduced by a factor of eight, excluding the one-time basis transfer. The raw dense backpropagated vector need not lie in the subspace; parameter-gradient equivalence is the checked property. A separate Grassmann step checks orthogonality and residual reduction.


| Related paper | What was actually run | Exact method status |

|---|---|---|

| OFLight | 20 low-rank FL projection/feedback controls; ideal summed uplink | Our SVD/refresh policies; detailed paper policy unavailable |

| GSHetero | Five MCL groupings, speed-aware placements and exact group references | Placement heuristic is original |

| Architecture-aware currying | 15 mesh partial-application/near-data controls; byte-hop counts | No source compiler port |

| PackStealLB | 10 task-pack/single-task transfer models with task invariants | No source packing-policy port |


All six remaining mechanism-only entries, including PANA and EAHP, are flagged in the registry. Their detailed full texts/code could not be retrieved from public sources. Logical bytes, byte-hops and scheduling models are not network, Hadoop, radio or multi-GPU measurements.


Evidence: research_supplement/spmv.c; spmv.py; communication.py; placement.py; results/{spmv,communication,placement}.json; SOURCE_REGISTRY.json


## Research extension: search and strategy decisions


| Live HPO, 3 seeds | Epoch units | Mean wall s | Validation MSE |

|---|---|---|---|

| full grid | 729.0 | 0.2044 | 0.24798 |

| synchronous halving | 81.0 | 0.0223 | 0.25072 |

| asynchronous stopping | 416.3 | 0.1366 | 0.24798 |


Four real worker threads train 27 ridge-learning configurations with checkpoint continuation and rungs 1/3/9/27. The asynchronous stopping variant sees only completed rung results and waits for three observations before stopping. Timings include scheduler overhead; synchronous halving uses much less work here. Completion order can alter later decisions. This is not the ASHA paper's 500-worker systems experiment.


The HPO survey demonstrations also compare exact implicit ridge hypergradients with grid/random/Sobol search: hypergradient descent uses 19 linear solves, versus 20 for each search including selected-model refit. OmniOpt motivates L1/L2/L-infinity/spectral linear minimization oracles, checked against dual-norm certificates. A survey is not presented as one newly invented algorithm.


| SVM+ search, 3 seeds | Mean test accuracy | Mean wall s | Candidate fits |

|---|---|---|---|

| random search | 69.44% | 0.304 | 16 per seed |

| grid island ga | 75.00% | 0.362 | 16 per seed |


The GAGS-inspired two-island GA and random search each evaluate 16 unique log-grid candidates using two threads. The convex RBF SVM+ solver retains feasible primal/dual certificates, independently recomputed gaps and inference without privileged input. All 96 candidate fits succeed. Narrow ranges, small population and the privileged-SVC tiebreak are declared adaptations; results use synthetic LUPI data, not the paper's datasets.


The Astra-related finite planner enumerates 1611 memory-feasible data/tensor/pipeline/device choices using explicit synthetic profiles and a GPipe DAG. Its exact model optimum is 0.6255 s/iteration on 4 modeled devices at $8.00/hour. The EAHP-related original GA misses that finite optimum in all five runs; the one-hot LP/exhaustive reference exposes the gaps. Profiles are fictional, not measured GPU costs; evaluating the catalog is included in the workflow and GA query counts are not total savings.


Twenty new tests check derivatives, unitary/postselection behavior, privacy distributions, exact SVM+ certificates, preprocessing and parallel/search invariants. The research audit verifies all 15 result files. All 2,013 original A-J imported files and their performance evidence remain unchanged.


Evidence: research_supplement/hpo.py; svmplus.py; strategies.py; test_methods.py; audit.py; results/{hpo,svmplus,strategies}.json


## Research extension: Q-FLAIR feature-map learning


Q-FLAIR (PPT3 slide 37) learns its quantum feature map gate by gate. This scoped QNN port grows a two-qubit circuit, reconstructs candidate outputs using shared zero and ±π/2 evaluations, then classically selects gate, feature and weight. Source: Jäger et al., arXiv:2510.03389v2, Sec. III / Algorithm 1 / Appendix A.1; author code commit 4f331783.


| Synthetic task | Features | Q-FLAIR accuracy | Logistic accuracy | Query ratio |

|---|---|---|---|---|

| linear | 4 | 97.9 ± 0.9% | 97.4 ± 1.8% | 121.3x |

| linear | 12 | 93.2 ± 2.4% | 95.3 ± 1.6% | 293.3x |

| xor | 4 | 58.9 ± 21.7% | 51.0 ± 5.5% | 116.0x |

| xor | 12 | 51.0 ± 12.1% | 50.5 ± 3.9% | 290.3x |


![Every seed is retained. The paired direct-grid QNN matches Q-FLAIR output; logistic is a separate classical reference.](reports/figures/qflair_comparison.png)


Twelve paired cases use 64 training/64 disjoint test rows, 41 weight values and an eight-generator pool. Train-only scaling and threshold selection prevent test leakage. Nine new tests compare author reconstruction, dense matrix exponentials, exhaustive candidates and Qiskit circuits. Independent replay agrees within 6e-16.


6/12 cases reach the 12-gate cap. XOR generalization is mixed; classical logistic wins on several splits. The query ratio counts logical black-box output evaluations, not measured QPU time or CPU speedup. Classical feature/weight scoring still grows with dimension. This is not the paper's QSVM, MNIST or IBM-hardware reproduction.


Evidence: research_supplement/qflair.py; test_qflair.py; QFLAIR.md; results/qflair.json; author_checks/; provenance/qflair_completion_20261106.json


## Chapter checklist and paper-specific research boundary


The checklist maps 112 core/supporting topics and 23 research entries to executable evidence, including Q-FLAIR. The extension adds 11 scoped equation/code ports, four algorithm variants, two survey demonstrations and six mechanism-only controls. A source port does not mean an entire paper or its reported performance has been reproduced.


| Evidence level | Count | Meaning |

|---|---|---|

| Scoped source port | 11 | Declared source equations/code specialized to small CPU experiments |

| Algorithm variant | 4 | Source strategy with explicit changes to policy, scale or model |

| Survey demonstration | 2 | Examples of surveyed families, not one invented survey algorithm |

| Mechanism only | 6 | Original controls; detailed published policies unavailable |


The remaining exact-method gaps are PANA, PackStealLB, GSHetero, architecture-aware currying, OFLight and EAHP. Public retrieval reached abstracts, unavailable manuscripts or incomplete author repositories. These experiments demonstrate the related mechanisms but are not relabeled exact paper implementations. Strict paper-method coverage therefore remains incomplete.


Six quantum spotlights have scoped experiments, including Q-FLAIR and the two-qubit author-data liver port. GRNG, AdaFisher, private density greedy+, ResQue and Subspace Networks also have source-linked numerical ports. All algorithms, adaptations, equation locators, datasets and result paths are listed in METHOD_COVERAGE.md; source-document hashes and access limitations are recorded separately.


Section 5 of the brief permits verifiable experimental demonstrations. The research spotlights use that route where full published policies could not be verified. Exact paper-policy fidelity remains separately limited; no instructor approval or source-scale hardware reproduction is asserted. Names explicitly marked absent from the slides are not fabricated.


Evidence: docs/CHAPTER6_CHECKLIST.json and .md; research_supplement/SOURCE_REGISTRY.json; METHOD_COVERAGE.md; provenance/research_source_documents.json


## Correctness, actual AI failures and disclosures


The 7 November final review again passes 243 original host tests: A30/B30/C32/D29/E29/F29/G14/H17/I23/J10. The fresh review also passes seven supplement tests and nine shared tests per AI candidate, with 100 exhaustive small cases each. Twenty-one research checks (including JSON sequence ordering) and nine Q-FLAIR checks verify numerical and mathematical references. Earlier logs and original performance measurements are retained. These counts do not include subject cachetools or archived xv6 guest suites. Imported source/result hashes are preserved.


| Track | Actual observed AI-code defect | Fix / retained check |

|---|---|---|

| A | Cancellation of tiny positive loss | Rationalized formula; limiting-case regression |

| B | Expanded float QUBO loses value difference | Declared coefficient-range guard |

| D | Steady timer included initialization | Readiness handshake; total time kept |

| F | Greedy repeated work but undercounted it | Reuse candidate; call-count regression |

| G | Incompatible pinned xv6 copyout call | Correct API; build/guest checks |

| H | Schema-changing test reused a cached connection | Isolate portfolios; context-limited reproducer |

| I | Rust EdgeList was not JSON serializable | Convert native lists; rerun/regression |

| J | Wrong test cwd and redundant huge JSON | Resolve/chdir; compact context evidence |


Each original/fix is documented in its track. The final audit also fixed ordered-tuple JSON export: strategy assignments, HPO configs and SVM+ grid labels are corrected from retained numeric records; original diagnostics remain. Numerical scores, fitted models and timings are unchanged. Intentional controls are not invented AI mistakes.


All substantial work is AI-assisted. Historical registers disclose gpt-6.1-sol for A/B/C/D/F/G and gpt-6-astra for E; H/I/J/integration retain GPT-6 family where serving revision is not exposed. Student evidence received 6 November adds Google Gemini with selector Argon High for the comparison function only; its underlying revision is unverified. Original ChatGPT/Gemini platform exports and native selector screenshots are now included; see docs/AI_EVIDENCE_INDEX.md. No manual student fixes or missing transcripts are invented.


Evidence: validation/submission-host-20261107/summary.json; final_submission_audit_20261107.json; docs/AI_TOOL_REGISTER.md


## Two-tool comparison: ChatGPT and Gemini


The fixed Python 3.12 task is a 0-1 knapsack function: maximize value, minimize weight, then select lexicographically smallest indices. The student supplied an unchanged Gemini answer and screenshot on 6 November. The screenshot shows selector Argon High and the prompt/code beginnings; the complete supplied prompt/response PDF is now included; the underlying backend revision remains unverified.


| Measure | ChatGPT / Codex | Google Gemini |

|---|---|---|

| Shared harness | 9/9 methods; 100 exhaustive small cases | 9/9 methods; 100 exhaustive small cases |

| Versions / repairs | First retained candidate passes; zero repairs | First supplied candidate passes; zero reported repairs |

| AI generation latency | Not measured | Student estimate: about 60 ± 3 seconds |


Function timing is separate: one warmup per candidate/case, seven paired repetitions with seeded randomized order, 56 timed calls. Inputs, imports, references and validation are excluded. Python 3.12.14 on a shared cloud host. Below: median [observed min, max] in milliseconds; ratio is ChatGPT/Gemini median time.


| Input case | ChatGPT ms | Gemini ms | Time ratio |

|---|---|---|---|

| small
(n=12, C=80) | 0.0825 [0.0800, 0.1328] | 0.0553 [0.0549, 0.0595] | 1.49 |

| medium tight
(n=35, C=500) | 1.8242 [1.5748, 1.9395] | 1.1853 [1.0293, 1.3324] | 1.54 |

| large tight
(n=50, C=5000) | 47.8692 [41.7736, 64.9016] | 26.9215 [25.2826, 34.2702] | 1.78 |

| large loose
(n=50, C=10000) | 28.7878 [26.7877, 29.2937] | 9.5022 [9.0859, 10.6077] | 3.03 |


Both use descending exact-weight DP to prevent item reuse. Gemini bounds sweeps by processed fitting weights and uses separate arrays; this plausibly contributes to its observed runtime advantage, but the benchmark does not isolate that mechanism. Both have O(nC) state visits; tuple copying/comparison can give O(n²C) time and O(nC) storage including indices.


Both passed without repair; Gemini had lower median function runtime on these four cases only. An independent DP checks optimal value/minimum weight in runtime cases; the small exhaustive tests check index ties. No generation-speed winner is possible without ChatGPT latency. No unsupported external claims were observed in either code-only answer; general hallucination or repair quality is not measured.


Evidence: ai_tool_comparison/COMPARISON.md; gemini_evidence.md; comparison_record.json; *_result*.json; benchmark_results.json


## Reproducibility, demonstration and final conclusions


Use Python 3.12 and root or per-track requirements. Native C/OpenMP and xv6 replay need documented Linux/WSL toolchains. Read retained reports without rerunning everything. New experiments use new output folders; seeds do not fix host scheduling, solver timeouts or numerical-library behavior.


| Task | Command / file |

|---|---|

| Integrated evidence audit | python tools/audit_project.py |

| EV demonstration | cd tracks/E; python -m evcharge demo |

| Supplement checks | python -m unittest chapter_supplement.test_study -v |

| Research audit / tests | python -m research_supplement.audit; python -m unittest research_supplement.test_methods research_supplement.test_qflair -v |

| New research run | python -m research_supplement.run --out research_supplement/results-rerun |

| New host validation | python tools/run_host_tests.py --out validation/host-rerun |

| Two-tool comparison | ai_tool_comparison/COMPARISON.md; evaluate.py; benchmark_pair.py |

| Short demonstration | reports/Assignment_8_Captioned_Demo.mp4 |


The captioned video shows actual command output and saved evidence; it is an edited guide, not physical station footage or an unscripted live recording. Explain the model and modify code yourself for the viva. The final-question answers and a live-demo guide are included.


Optimization improves a chosen objective under declared assumptions. E improves synthetic cost/feasibility; H buys reads with storage/writes; F/G show model-versus-time mismatch; J loses assertion strength despite line preservation. Quantum logical query gains and CPU parallel speedups use different cost models. No universal optimizer ranking or practical quantum advantage is claimed.


Actual activity is recorded on 31 October and 3/4/6/7 November 2026. No fourteen-day diary is invented. The supplied Gemini comparison is recorded, with estimated generation timing clearly attributed. AI platform evidence is included and the public repository is published. Q-FLAIR is verified and the historical source-revision mapping is published. All 23 research entries now have experiments or controls; six detailed published policies remain inaccessible and are explicitly mechanism-only. Those source-fidelity gaps remain visible without making an instructor conversation a prerequisite for this extension.


Evidence: README.md; docs/FINAL_QUESTIONS.md; docs/DEMONSTRATION_GUIDE.md; docs/SUBMISSION_CHECKLIST.md


## References and provenance


All numerical results are this project's recorded measurements/models. Supplied Assignment 8 and four Chapter 6 decks are acknowledged and hashed, not redistributed. Original public sources retain licenses and pinned identities. All source archives and 2,013 imported-file hashes are recorded under provenance/.


- SciPy mixed-integer programming: https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.milp.html


- FedAvg: https://proceedings.mlr.press/v54/mcmahan17a.html


- MGDA: https://arxiv.org/abs/1810.04650


- GradNorm: https://proceedings.mlr.press/v80/chen18a.html


- LLVM pass concepts: https://llvm.org/docs/Passes.html


- SQLite plans: https://sqlite.org/eqp.html


- IBM noise models: https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models


- Coverage contexts: https://coverage.readthedocs.io/en/7.17.1/contexts.html


- Error feedback: https://proceedings.mlr.press/v97/karimireddy19a.html


- ASHA systems paper: https://proceedings.mlsys.org/paper_files/paper/2020/file/a06f20b349c6cf09a6b171c71b88bbfc-Paper.pdf


- GRNG - scoped port: https://proceedings.mlr.press/v300/dash26a.html


- AdaFisher - scoped port: https://proceedings.iclr.cc/paper_files/paper/2025/hash/f88bec15cc4cb56b432ee040bb63f94f-Abstract-Conference.html


- ResQue Greedy - scoped port: https://arxiv.org/abs/2505.13670


- Astra - finite-model variant: https://arxiv.org/abs/2502.13480


- Q-FLAIR - scoped QNN port: https://arxiv.org/html/2510.03389v2


- Q-FLAIR author implementation: https://github.com/phels23/Q-FLAIR


External references support methods and research identification; they do not supply this project's measured gains. Historical calibration, CPU simulation, synthetic prices and modeled controls remain explicitly identified. Original local AI-assisted history bundles and the integration history are retained.
