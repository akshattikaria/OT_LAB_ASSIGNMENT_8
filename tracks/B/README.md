# Track B: Discrete Optimization

Working Track B experiments for Assignment 8. Open **`results/report.html`** after extraction to read the self-contained report and charts offline. Earlier Track A and E packages remain separate.

## Implemented work

- Budgeted 0-1 selection: input-order baseline, value/cost greedy, dynamic programming, explicit Branch-and-Bound and a SciPy/HiGHS binary ILP.
- Independent feasibility/objective checks and exhaustive-search validation of small cases.
- Forward feature selection, backward elimination and exhaustive subset comparison with separate training/validation/test data.
- Constraint penalties, slack bits, upper-triangular QUBO and Ising conversion with offsets retained.
- Classical references for a **6-bit constrained knapsack** and **4-bit Max-Cut**, exported for Track C.
- Penalty-strength and DP integer-capacity scaling experiments.

All inputs are synthetic. This package does not claim quantum execution or completion of the full ten-track assignment.

## Run

Recorded environment: Python 3.12.14, with dependencies pinned in requirements.txt. Run from this extracted folder, preferably in a virtual environment:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m discopt demo
```

Demo: the input-order baseline gets value 5; greedy, DP, Branch-and-Bound and ILP get value 6 at capacity 3. The corresponding constrained QUBO minimum energy is -6, with all ground states satisfying the constraint.

Quick benchmark:

```bash
python -m discopt benchmark --out results-quick --sizes 10 20 --seeds 0 --repeats 1
```

Full protocol:

```bash
python -m discopt benchmark --out results-rerun --sizes 10 20 40 80 --seeds 0 1 2 3 4 --repeats 3 --time-limit 2
```

Regenerate the report without rerunning solvers:

```bash
python -m discopt report results
```

Choose a new output directory. Nonempty folders are refused to preserve evidence. Seeds reproduce inputs; runtimes and search-limit outcomes may vary across systems.

## Recorded evidence

- 80 generated main instances, four families and five diagnostic cases.
- Five methods, three repetitions: **1,275 method runs**.
- **30 tests passed**, including exact-method agreement with exhaustive enumeration on 100 random small instances and 20 random constrained QUBO checks.
- DP and ILP proved all 80 main optima. Branch-and-Bound proved 73 within its configured limits; the other seven returned feasible candidates at the node limit.
- Density greedy averaged a 1.8981% value gap on the 80 generated instances, with explicit counterexamples showing larger gaps can occur.
- Every one of the 64 knapsack and 16 Max-Cut bitstrings satisfies the direct/QUBO/Ising energy identity.
- One genuine AI-generated precision defect was detected and fixed with a regression check. See docs/AI_FAILURE_LOG.md.

The proof of the chosen QUBO penalty concerns global ground states. It does not guarantee that a heuristic or quantum sampler returns a feasible ground state. Track C should separately report feasibility probability, solution quality and measured energy.

## Files

| Path | Purpose |
|---|---|
| `discopt/model.py` | Problem schema and independent selection audit |
| `discopt/solvers.py` | Greedy, DP, Branch-and-Bound, ILP and exhaustive oracle |
| `discopt/qubo.py` | Penalty formulation, Ising conversion and exact energy checks |
| `discopt/data.py` | Synthetic families and designed controls |
| `discopt/supplement.py` | Feature selection, DP scaling and quantum export generation |
| `discopt/experiment.py` | Benchmark, timing and summaries |
| `discopt/report.py` | Static plots and HTML/Markdown report |
| `tests/test_discrete.py` | Correctness, numeric-range and data-isolation checks |
| `results/instances/` | Every exact benchmark input |
| `results/raw_runs.json`, `runs.csv` | All candidate selections, statuses, bounds and timings |
| `results/protocol.json`, `environment.json` | Evaluation rules and actual runtime conditions |
| `results/feature_datasets/` | Separate feature-selection data arrays |
| `results/supplementary.json` | Feature searches, penalty sweep and DP scaling results |
| `results/quantum_baselines/` | Coefficients, variable order, offsets, classical energies and minima |
| `results/input_and_quantum_sha256.json` | Input/export integrity hashes |
| `docs/FORMULATION.md`, `COVERAGE.md` | Mathematics, method selection and coverage |
| `docs/TRACK_C_HANDOFF.md` | Exact quantum model conventions |
| `docs/VIVA_GUIDE.md` | Short conceptual explanations |
| `prompts/B/001_continue.md` | Actual prompt and response excerpts |

## AI tools register

| Tool | Session-reported model | Date | Track | Use |
|---|---|---|---|---|
| ChatGPT | `gpt-6.1-sol` | 2026-11-03 | B | Formulation, code generation, debugging, tests, benchmarking, documentation |
| ChatGPT | `gpt-6.1-sol` | 2026-10-31 | A / chapter planning | Earlier continuous-optimization work and chapter reading |
| ChatGPT | `gpt-6-astra` | 2026-10-31 | E | Earlier EV scheduling case study |

Earlier ChatGPT overview turns with no exposed model version are not assigned an invented version. All code here is AI-assisted; no manual student corrections are claimed. NumPy, SciPy/HiGHS and Matplotlib are external libraries. The DP, Branch-and-Bound, greedy algorithms, mappings, checker and experiment code are explicit implementations; ILP uses a library solver. Google OR-Tools is a reference, not an installed dependency.

This track adds one genuine defect to the one documented earlier in Track A. The assignment-wide minimum of three is not yet satisfied. A comparison with a second independent AI tool and full chat exports/screenshots remain pending; this archive contains excerpts rather than a claimed full export.

## History and remaining work

`history.bundle` preserves original code, the numerical guard fix and final documentation. Recover it using `git clone history.bundle track-b-history`. See docs/COMMIT_INDEX.md. No public repository was selected or published in this milestone.

Next is Track C using the exact exported objectives. A/E packages remain preserved; C, D and F-J, final integration, broader outstanding research reproductions, demonstration and public GitHub publication remain.

## References

- Supplied Assignment 8, Track B/Section 5; Chapter 6 PPT1 and PPT3. Lecture files are acknowledged, not redistributed.
- [SciPy milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).
- [D-Wave QUBO/Ising conventions](https://docs.dwavequantum.com/en/latest/quantum_research/qubo_ising.html). Our spin sign convention is explicitly stated and numerically checked.
- [Google knapsack description](https://developers.google.com/optimization/pack/knapsack).
- Public references accessed 2026-11-03; measured installed versions are pinned and recorded.
