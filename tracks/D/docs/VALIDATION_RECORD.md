# Validation record

Date: 2026-11-03. CPU workspace: nine visible logical CPUs, affinity nine, cgroup cpu.max=800000/100000 (eight CPU equivalents). This is not a measurement of the student's laptop or a dedicated eight-core machine. Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8 and threadpoolctl 3.6.0 were used. Native BLAS was limited to one thread/kernel during numerical parallelism and learning comparisons. Actual library/backend and platform metadata are retained in results/environment.json.

## Tests

Command: `python -m unittest discover -s tests -v`.

Final result: **29 tests passed**, actual output in unit_test_output.txt. The earlier environment-dependent failure is retained in initial_test_failure.txt. Socket Manager queues were replaced with shared-array deques and locks before final measurement. No final test is skipped.

Tests cover weighted union values, monotonicity/submodularity, the finite-k greedy bound on random exact oracles, lazy equivalence on 45 random cases, tie breaks, unequal-client aggregation, finite-difference gradients, E=1 centralized equivalence, exact MGDA simplex minimization, the frozen-target GradNorm derivative, equivalent data/model/pipeline outputs, scheduler exact-once completion, timer readiness, synchronization count, pipe bytes and partial native tiles.

## Recorded experiment and recovery

The first attempt called `run_benchmark("results")` using the full default five seeds and budgets. Coverage and learning stages completed. The resource stage encountered the blocked Manager transport before retaining parallel measurements. Those completed learning records were preserved, and their SHA-256 hashes are recorded in resume_record.json.

After the shared-array fix and passing tests, the resource portion was resumed through:

```bash
python -u -m distopt.resume_resources results
python -m distopt report results
python -m distopt audit results
```

An earlier stdin-based resume launch was interrupted because portable spawn cannot import a stdin script. It generated no retained resource timings. The supplied guarded module CLI works from a normal terminal; the public full benchmark command was additionally tested from an empty output folder using the reduced protocol below.

Main protocol: seeds 0–4; timing repeats=3; workers=1/2/4/8; 30,000 PBKDF2 iterations per work unit; 400 multi-task updates; FedAvg E=1/5/20 and R=6/24/120. Main data/model measurements use three forwards per timing, batch sizes 2,048 and 8,192, dimensions 256→512→256; pipeline measurements time one forward with two stages and m=1/4/16/64.

| Evidence | Count |
| --- | --- |
| Weighted-coverage input instances | 45 |
| Coverage method runs | 210 |
| Exhaustive small-instance optima | 30 |
| Strong-scaling process timings | 96 |
| Weak-scaling process timings | 12 |
| Data/model/serial timings | 54 |
| Two-stage pipeline timings | 12 |
| Shared-counter synchronization timings | 24 |
| Local pipe timings | 15 |
| C-loop locality timings | 18 |
| FedAvg runs | 90 |
| Matched centralized runs | 35 |
| Multi-task runs | 45 |
| Saved input files with SHA-256 hashes | 65 |

CPU jobs compute deterministic digests rather than sleep. Every scheduler returns every job exactly once, and outputs match references. Measured strong-scaling worker trials and data/model configurations use predeclared shuffled order. Repeats, seeds and raw outcomes are retained; no best-seed replacement or artificial timing is used.

## Retained-data audit

Result: **passed; 25,253 numerical comparisons**. See results/audit.json.

- All 210 coverage selections independently reevaluated from weighted unions; all 30 tiny optima independently enumerated. Lazy and ordinary greedy selections agree.
- 5,325 retained federated/centralized iterates reevaluated on saved arrays, with convex-reference lower-bound checks and sample/communication accounting.
- All 30 E=1 FedAvg final models equal the matched centralized result within 1e-12.
- 1,845 retained multi-task iterates reevaluated for both task errors, weighting normalization and MGDA stationarity.
- All 108 strong/weak scheduler runs checked for distinct worker PIDs, exact task digests, timing/readiness boundaries, work totals, job intervals and stealing metadata. Digests were freshly recomputed for 192 distinct kernel inputs and reused for repeated comparisons.
- Full inference/pipeline output arrays were compared with serial results during measurement; all saved errors are below 1e-9. Small independent tests use irregular partition sizes. Pipeline dependencies and event counts are checked by the audit.
- Every shared-counter result equals 120,000; all message payload counts and native sum references agree.

## CLI and presentation checks

`python -m distopt demo` completed: coverage greedy/lazy=5, exact=6; five one-step FedAvg rounds versus centralized GD differ by about 6.94e-17 in the largest coefficient.

The full public CLI completed a fresh reduced protocol in a separate output directory:

```bash
python -m distopt benchmark --out /workspace/scratch/f3cd84c5991c/tmp/trackd-cli-smoke --seeds 0 --workers 1 2 --repeats 1 --iterations 500 --mtl-steps 40
```

That smoke run did not replace main data. Both reports contain seven embedded PNG charts and seven tables with no external image dependencies. Gantt traces, data/model/pipeline scaling, FedAvg and multi-task plots were visually inspected for readable labels, clipping and faithful interpretation.

Previous A/B/C/E archives were hash-checked and unchanged. The final source/data manifest, archive integrity check and complete local history bundle accompany delivery. No public repository is configured or published.

## Practical limits

Three repeats on shared hardware support small demonstrations, not universal timing rankings. Steady and end-to-end speeds differ materially. Model/pipeline implementations use CPU shared memory and forward inference; FedAvg uses serial client emulation and logical bytes. The fully shared linear two-task model is deliberately small. Research-paper benchmark reproductions, the remaining tracks and final assignment integration remain open as declared in COVERAGE.md.
