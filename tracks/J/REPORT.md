# Track J — Coverage-constrained regression-test selection

Akshat Tikaria · Roll 241070005 · Optimization Techniques, Assignment 8

Binary ILP selects 74 of 391 parent tests, reducing median fresh-process wall time by 41.5% (1.71×). All 1,005 required per-test source lines are preserved, but it retains only 13/16 faults caught by the full suite.

## Case study and formulation

The subject is the complete MIT-licensed `cachetools 7.2.8` source distribution: 1,798 physical Python source lines (1,371 nonblank, noncomment) in six library files, with 391 collected parent tests and 24 passing subtests in the pristine baseline. The archive SHA-256 is pinned in `UPSTREAM.json`; every one of its 38 files remains unchanged. The local source distribution is the measured codebase; a repository commit identity is not asserted.

Choose a binary variable x_i for every test. Minimize Σ c_i x_i, where c_i is the positive, rounded-up median setup+call+teardown duration in microseconds from three uninstrumented full-suite profiles. For each of the 1,005 lines exercised in a per-test context, require Σ a_li x_i ≥ 1. All-suite execution is the naive baseline. Count greedy, cost-weighted greedy and binary ILP solve the same line-preservation task; count greedy ranks newly covered lines, weighted greedy ranks newly covered lines/cost, and both remove redundant chosen tests. The ILP uses HiGHS through SciPy. See `docs/FORMULATION.md` for the exact model and limits.

## Observed results

| Method | Tests | Modeled cost (ms) | Measured wall median (range), s | Wall speedup | Branches | Full-suite fault kills retained |
|---|---:|---:|---:|---:|---:|---:|
| Full suite | 391 | 425.695 | 1.196 (1.006–1.614) | 1.00× | 214/214 | 16/16 |
| Count greedy | 80 | 74.171 | 0.673 (0.563–1.246) | 1.78× | 210/214 | 14/16 |
| Weighted greedy | 79 | 66.322 | 0.664 (0.575–0.737) | 1.80× | 209/214 | 13/16 |
| Binary ILP | 74 | 65.158 | 0.699 (0.584–0.781) | 1.71× | 208/214 | 13/16 |

Seven trials per method ran serially in a seeded, shuffled order, each in a fresh Python process with third-party pytest plugin autoload disabled and no coverage/cProfile tracing. Every method uses the same lightweight observer to record outcomes and write JSON. The wall clock includes interpreter startup, imports, collection, tests and evidence output. Values are observed cloud-host results, not measurements on the student's i3 laptop. The ranges are observed minimum/maximum values, not confidence intervals. OS file caches were warm; host scheduling was uncontrolled.

The ILP status is 0, optimal=True, relative gap=0; its primal cost and dual bound are both 65.158 ms. That certificate concerns this frozen integer-cost matrix. It does not prove that 74 is the minimum number of tests, or that ILP has the lowest real wall time. The lowest observed wall median was Weighted greedy; timing noise and nonadditive startup/fixture costs can change the ranking. The full suite's modeled phase sum is 425.695 ms, while its fresh-process median is 1.196 s.

![Selected tests and measured fresh-process times](figures/runtime_and_size.png)

## Baseline bottleneck

The separate cProfile run took 3.131 instrumented seconds. Its largest self-time entry is `__call__` in `_caller.py` at 0.363 s, followed by `<built-in method builtins.compile>` at 0.196 s. Pytest hook dispatch, compilation/import work and repeated test protocols account for material overhead; cache operations themselves are short. Cumulative call times overlap and must not be added. Profiling motivates reducing repeated tests but is not evidence that every remaining test is redundant as an assertion.

| Highest baseline test costs | Median phase sum (ms) |
|---|---:|
| `tests/test_cachedmethod.py::UnboundMethodTest::test_autospec_call` | 101.385 |
| `tests/test_cachedmethod.py::WeakRefMethodTest::test_weakref` | 25.750 |
| `tests/test_threading.py::ThreadingTest::test_cachedmethod_lock` | 22.862 |
| `tests/test_threading.py::ThreadingTest::test_cached_lock` | 19.762 |
| `tests/test_tlru.py::TLRUCacheTest::test_pickle_maxsize` | 16.221 |
| `tests/test_threading.py::ThreadingTest::test_cached_cond` | 14.216 |
| `tests/test_ttl.py::TTLCacheTest::test_pickle_maxsize` | 12.984 |
| `tests/test_threading.py::ThreadingTest::test_cachedmethod_cond` | 6.916 |

The top test contributes 23.8% of the additive profile cost. These short tests have noisy cost estimates; the fixed profile is a surrogate, not a prediction of all future CI runs.

## Coverage is not fault detection

Fresh instrumented runs verify all 1,005 required lines for every method. Standard statement coverage also includes collection/import execution and uses all 1,185 executable statements as its denominator; these are different quantities. The full suite covers 1,179/1,185 statements and all 214 branch outcomes. No 100% statement-coverage claim is made.

Twenty seeded, single-AST-operator mutants were generated independently of selection or kill outcomes. All 80 method/mutant combinations were executed. Each mutant changes one comparison boundary/equality or +/− operator inside a function, excluding while descendants. Mutants use isolated copies; AST unparsing changes formatting and removes comments in those disposable copies, so equivalence is checked structurally against exactly one intended operator edit. Surviving mutants are not assumed equivalent or harmless. A timeout or invalid execution is reported separately, never as a kill.

The full suite kills 16 mutants, survives three and times out on M20; all reduced suites also time out on M20. The 15-second cap applies per child. Excluding syntactic while descendants does not rule out indirect nontermination. The fault-retention denominator is the 16 full-suite kills, rather than all 20 generated mutants.

| Method | Faults killed by full suite but missed here | Timeouts | Invalid |
|---|---|---:|---:|
| Full suite | None | 1 | 0 |
| Count greedy | M08, M15 | 1 | 0 |
| Weighted greedy | M03, M08, M15 | 1 | 0 |
| Binary ILP | M01, M08, M15 | 1 | 0 |

For example, `M01` changes `Lt` to `LtE` at `src/cachetools/__init__.py:679`. The full suite fails on that mutant while ILP's selected suite passes. This is a concrete counterexample to treating line coverage as a guarantee of assertion strength. Deliberate mutants are validation faults, not AI coding mistakes.

![Branch coverage and retained fault detection](figures/coverage_and_faults.png)

![All mutation outcomes](figures/mutation_outcomes.png)

## Amortization and engineering costs

| Method | Selection time (s) | Baseline coverage + three profiles + selection (s) | Future runs to amortize | Runs including fresh coverage validation |
|---|---:|---:|---:|---:|
| Count greedy | 0.1177 | 8.381 | 17 | 21 |
| Weighted greedy | 0.1690 | 8.432 | 16 | 19 |
| Binary ILP | 0.0322 | 8.295 | 17 | 20 |

Break-even uses the observed median full-minus-selected wall time and assumes the source, costs and coverage matrix remain valid. These setup estimates exclude this research run's cProfile, seven timing repetitions, mutation challenge, report generation and audit; a complete evaluation costs more than deploying an already evaluated selector. Reprofile after code, tests, fixtures or dependencies change. Cheap test-count reduction does not remove interpreter startup or collection cost, and per-test costs are not fully additive.

The subject's code readability and maintainability are unchanged because production code is not refactored. Maintaining the selector, coverage-context recorder, SciPy/pytest/coverage dependencies, version pin and invalidation rules is an additional maintenance burden. POSIX process groups enforce timeouts; Windows users need Linux/WSL for the supplied driver. The mutation sample is small and operator-limited, and tests of concurrency/nondeterminism can vary between runs. This experiment supports a fast feedback stage with the full suite retained for complete regression checks; it does not justify replacing the full suite for releases.

## Validation and reproducibility

Ten host tests pass, including ILP versus exhaustive enumeration on 25 independently generated seven-variable models, invalid/uncoverable model rejection, actual child working-directory collection, pinned-source integrity, deterministic single-operator mutations and non-kill timeout classification. The evidence audit passed: 38 upstream files, 4 SQLite-to-line matrices, 28 timing trials, 80 mutation trials, objective/cost recomputation and primal/dual consistency. Four fresh suite replays passed. Raw logs, process times, selected node IDs, coverage databases, profiling data, mutation descriptors and classifications are included.

Run `python -m selci.audit --out results` to inspect saved evidence without overwriting it. Run `python -m selci.experiment --out results-rerun` for a new measurement grid, then `python -m selci.audit --out results-rerun`. New times and possibly selections can differ. `README.md` contains setup and commands; `docs/AI_FAILURE_LOG.md` records actual development mistakes and their fixes.

AI assistance: ChatGPT/Codex, GPT-6 family as identified by the environment; the exact serving revision is not independently exposed. The real continuation request and human-verifiable decisions are recorded in `prompts/J/001_continue.md`. This package is one track milestone, not the final integrated submission or an assertion that the fourteen-day diary, second-tool requirement, public repository or demonstration video is finished.

## Primary references

- User-supplied Assignment 8, Track J; PPT1 section on integer linear programming and PPT4 section on greedy strategy selection. The (1−1/e) cardinality-constrained maximization bound is not asserted for this weighted set-cover minimization problem.
- [Official pinned source release](https://pypi.org/project/cachetools/7.2.8/) and [upstream repository](https://github.com/tkem/cachetools).
- [Coverage measurement contexts](https://coverage.readthedocs.io/en/7.17.1/contexts.html).
- [CoverageData API](https://coverage.readthedocs.io/en/7.17.1/api_coveragedata.html).
- [SciPy mixed-integer programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).
- [Pytest hook API](https://docs.pytest.org/en/stable/reference/reference.html).
