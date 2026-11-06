# Track D: Submodular, Parallel and Distributed Optimization

Prepared for Akshat Tikaria, roll number **241070005**. Optimization Techniques, Assignment 8.

After extraction, open **results/report.html** for the offline report and seven embedded figures. This package includes source, exact inputs, raw measurements, tests, mathematical explanations, viva notes and local git history. E/A/B/C remain separate completed milestones; the full ten-track assignment is still in progress.

## What is implemented

- Nonnegative weighted coverage: input-order and singleton baselines, exact enumeration, ordinary marginal greedy and lazy greedy, with assumption checks and a genuine greedy counterexample.
- Actual spawned CPU processes: static blocks, greedy LPT load balancing, a central task pool and decentralized locked-deque work stealing.
- Fixed-problem strong scaling and growing-work weak scaling on 1, 2, 4 and 8 workers, with speedup, efficiency and overhead.
- Shared-memory CPU data parallelism, hidden-unit model/tensor parallelism, and two-stage forward inference pipelines with varying microbatches.
- C-loop locality, shared-counter synchronization and local-pipe batching controls.
- Full-participation FedAvg on four unequal IID or label-skewed clients, varying local steps and communication rounds, against matched centralized training.
- Equal weighting, exact two-task MGDA and GradNorm on three shared-parameter two-task regression settings.

## Run

Recorded environment: Python 3.12.14; NumPy/SciPy/Matplotlib/threadpoolctl versions are pinned. The locality experiment needs a C compiler (`cc`); Linux or WSL is recommended. No GPU, PyTorch, MPI service, network account or paid dependency is required.

From the extracted folder:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m distopt demo
```

Full protocol on a machine with at least eight available CPU equivalents:

```bash
python -m distopt benchmark --out results-rerun --seeds 0 1 2 3 4 --workers 1 2 4 8 --repeats 3 --iterations 30000 --mtl-steps 400
python -m distopt audit results-rerun
```

Use this smaller protocol on a low-spec laptop:

```bash
python -m distopt benchmark --out results-quick --seeds 0 --workers 1 2 --repeats 1 --iterations 500 --mtl-steps 40
```

The smaller protocol checks functionality; its tiny CPU tasks are unsuitable for substantive speedup conclusions. Omit --workers to select powers of two up to the detected quota/affinity, capped at eight. Nonempty output directories are refused. Run multiprocessing through these module commands or a guarded Python file, rather than pasting it into a stdin script/notebook cell. The recorded cloud results can be read without rerunning anything.

Regenerate the report without repeating timed experiments:

```bash
python -m distopt report results
```

## Main results

- **29 tests passed**; retained-data audit passed **25,253 numeric comparisons**.
- 45 coverage instances and 210 method runs; 30 small instances exhaustively checked. Greedy averaged **99.30% of optimum**, with a worst saved ratio of 92.06%; lazy greedy returned identical selections. These observations do not replace the worst-case theorem.
- 96 strong-scaling and 12 weak-scaling process runs. On irregular jobs at eight workers, the central task pool achieved **5.72× steady speedup**, versus 2.03× for static blocks; actual stealing moved a mean of six jobs/run. Startup erased most end-to-end gains for these short tasks.
- Data-parallel inference at batch 8,192 achieved **3.04×** at eight threads; model parallelism achieved 2.03×. Outputs agreed with the serial reference to at most 3.34e-15 absolute error in recorded model-partition runs.
- The two-stage pipeline reached **1.48×** at 16 microbatches; increasing to 64 reduced speedup to 1.32×.
- 90 FedAvg and 35 centralized runs. At equal sample visits, E=20/R=6 uses one twentieth the logical model payload of E=1/R=120, with larger objective error under label skew. Thirty E=1 final-model comparisons matched centralized training to 1e-12.
- 45 multi-task runs. For the conflicting 10×-scale family, mean unscaled task MSEs were Equal=(3.6356, 0.0473), MGDA=(0.8923, 1.4023), GradNorm=(1.1554, 1.1014). These are different trade-offs, not one universally best method.

All timing claims concern this cloud workspace: nine visible logical CPUs, affinity nine, cgroup quota eight CPU equivalents. Native BLAS uses one thread/kernel during inference. FedAvg clients are serially emulated; their logical model bytes are an accounting model, not actual network traffic. Pipeline experiments are forward inference, not multi-device training. No privacy, GPU, dedicated-core or multi-node claim is made.

## Evidence map

| Path | Purpose |
| --- | --- |
| distopt/coverage.py | Weighted-coverage objective, exact/greedy/lazy methods and assumption oracle |
| distopt/scheduling.py | Real process jobs, shared-array stealing deques, counters and local pipe echo |
| distopt/parallel.py | Equivalent data/model parallel inference and two-stage pipeline |
| native/locality.c, distopt/locality.py | Explicit row/column/tile loops and compiler wrapper |
| distopt/federated.py | Logistic loss, unequal-client weighted FedAvg and centralized GD |
| distopt/multitask.py | Two-task model, closed-form MGDA and frozen-target GradNorm |
| distopt/experiment.py | Protocol, workload generation and resource/learning experiments |
| distopt/report.py, distopt/audit.py | Offline report and saved-result verification |
| tests/test_track_d.py | 29 mathematical, integration and timing-boundary checks |
| results/*_runs.json | All selections, model coefficients, traces, measured timings and statuses |
| results/coverage_inputs/, federated_data/, multitask_data/ | Exact synthetic inputs and held-out arrays |
| results/protocol.json, environment.json, input_sha256.json | Settings, actual CPU allocation and input integrity |
| results/audit.json, summary.json | Verification counts and derived report tables |
| docs/FORMULATION.md, VIVA_GUIDE.md | Mathematics and short explanations |
| docs/AI_FAILURE_LOG.md | Actual timer defect, original/fix observations and commit references |
| docs/VALIDATION_RECORD.md, COVERAGE.md | Checks performed, limitations and assignment progress |
| prompts/D/001_continue.md | Actual visible prompt/response excerpts |
| history.bundle, docs/COMMIT_INDEX.md | Original code, correction and final implementation history |

Recover history using `git clone history.bundle track-d-history`. FILE_SHA256.json checks source, report, data and documentation; it excludes itself and the bundle to avoid recursive hashes. The compiled locality library is reproducible and excluded from delivery; its C source and exact build command are retained.

## AI disclosure

| Tool | Session-reported model | Date | Use |
| --- | --- | --- | --- |
| ChatGPT | gpt-6.1-sol | 2026-11-03 | Track D formulation, code, tests, diagnosis, benchmarks, audit and report |
| ChatGPT | gpt-6.1-sol | 2026-11-03 | Earlier B and C work |
| ChatGPT | gpt-6.1-sol | 2026-10-31 | Earlier A work and planning |
| ChatGPT | gpt-6-astra | 2026-10-31 | Earlier E case study |

All implementation is AI-assisted; no manual student corrections or second independent AI-tool use is claimed. NumPy supplies numerical kernels, SciPy supplies the convex logistic reference, threadpoolctl controls native threads, and Matplotlib renders figures. PBKDF2 is Python's standard cryptographic CPU workload, not a new cryptographic implementation. Gradients, selection methods, aggregation, MGDA, GradNorm, scheduling and checks are explicit implementations.

A genuine timer defect was found and fixed before recorded resource measurements. Together with the two numerical defects retained in A/B, **three genuine corrected AI error cases are now documented**. A blocked Manager transport and a failed stdin launch are separately disclosed execution issues. Neither is presented as an additional mathematical defect. Full conversation exports and a second independent AI-tool comparison are still pending.

Next is **Track F: compiler optimization**, since the main EV charging case study E was built first. F–J, the combined report, public repository, demonstration and outstanding research-paper reproductions remain. Lecture research spotlights are not claimed reproduced in this package.

## Primary references

- [Nemhauser, Wolsey & Fisher (1978)](https://thibaut.horel.org/submodularity/papers/nemhauser1978.pdf).
- [FedAvg](https://proceedings.mlr.press/v54/mcmahan17a.html), [MGDA/multi-objective learning](https://arxiv.org/abs/1810.04650), [GradNorm](https://proceedings.mlr.press/v80/chen18a.html).
- [GPipe](https://arxiv.org/abs/1811.06965), conceptual pipeline reference rather than a reproduced GPU-training benchmark.
- [Python multiprocessing](https://docs.python.org/3/library/multiprocessing.html), [threadpoolctl](https://github.com/joblib/threadpoolctl).
- Supplied Assignment 8 and Chapter 6 PPT1, PPT2, PPT4, acknowledged rather than redistributed. Public references checked 2026-11-03.
