# Track E: Smart EV Charging Scheduling

**Status: working synthetic-data experiment for Track E of Assignment 8.**
This package does not claim completion of the other nine tracks or the full assignment.

Open **`results/report.html`** in a browser to read the measured results without installing anything. It contains the charts and is self-contained. The Markdown version is `results/REPORT.md`.

## What this does

Given vehicles' connection windows, fixed charging rates, slot-aligned energy requirements, a tariff and a station power limit, choose when each vehicle charges. We compare:

1. **Baseline:** arrival-order priority, charge as soon as possible.
2. **Greedy:** earlier departure first, reserve each vehicle's cheapest available slots.
3. **Binary integer optimization:** optimize all vehicle-slot choices jointly using SciPy's HiGHS-backed `milp` solver.

Every output is independently checked. An undercharged vehicle makes the schedule infeasible, even if its electricity bill is low. Solver timeouts are kept distinct from infeasibility and proven optimality.

## Run locally

The recorded run used Python 3.12.14. Use Python 3.12 and, preferably, an isolated virtual environment. Commands below run from this folder after extraction.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m evcharge demo
```

The four-vehicle demonstration should print baseline cost **406**, greedy **182**, ILP **182**, with all three schedules feasible. Its prices are fictional rupees/kWh.

Quick benchmark (smaller suite):

```bash
python -m evcharge benchmark --out results-quick --sizes 10 --seeds 0 1 --repeats 1
```

Reproduce the full protocol:

```bash
python -m evcharge benchmark --out results-rerun --sizes 10 20 30 --seeds 0 1 2 3 4 --repeats 3 --time-limit 3
```

Existing nonempty output folders are refused so the submitted evidence is not silently overwritten. Runtime and solver tie choices can differ across machines. A three-second cutoff can also change whether a difficult instance gets an optimality certificate.

Solve a saved instance:

```bash
python -m evcharge solve results/instances/flexible_n20_s0.json --method ilp --out solution.json
```

Regenerate the report from stored results without rerunning the solvers:

```bash
python -m evcharge report results
```

## Recorded evidence

- 75 generated main instances: 5 scenario families, 3 fleet sizes and 5 seeds.
- 4 diagnostic controls, including a known feasible greedy failure and a provably infeasible station.
- 3 repetitions per method and instance: 711 recorded method runs.
- 29 tests passed, including 80 small random ILP-versus-exhaustive-search comparisons.
- Main-case feasibility: baseline 64/75, greedy 70/75, ILP 75/75.
- ILP proved 70/75 main cases optimal. Five hit the time limit with independently validated candidate schedules.
- Flexible-window cases: mean 49.44% lower cost than baseline across 15 matched feasible cases. Flat-price cases: 0% cost reduction.

These are results for **synthetic sessions and fictional prices**, not measured savings at a real charging station. Read the report's pair counts and limitations before citing a percentage.

## Files

| Path | Purpose |
|---|---|
| `evcharge/model.py` | Data definitions and validation |
| `evcharge/data.py` | Seeded generators, feasibility witnesses and diagnostic cases |
| `evcharge/solvers.py` | Baseline, greedy, integer model and exhaustive oracle |
| `evcharge/verify.py` | Independent schedule audit |
| `evcharge/experiment.py` | Timing, recording and paired summaries |
| `evcharge/reporting.py` | Reproducible charts and report |
| `tests/test_core.py` | Correctness and adversarial checks |
| `docs/FORMULATION.md` | Mathematics, assumptions and strategy-selection table |
| `docs/ASSIGNMENT_STATUS.md` | What this milestone covers and what remains |
| `docs/AI_FAILURE_LOG.md` | Honest disclosure of observed AI errors and pending requirements |
| `docs/COMMIT_INDEX.md` | Recorded AI-assisted commit trace |
| `prompts/E/001_start.md` | Original user request, response excerpt and verification record |
| `results/instances/` | Exact experiment inputs |
| `results/witnesses/` | Audited feasibility witnesses, not solver hints |
| `results/raw_runs.json` | Every candidate schedule, audit, status and timing |
| `results/runs.csv` | Flat machine-readable result table |
| `results/input_sha256.json` | Integrity hashes of all instance files |
| `results/environment.json` | Actual environment and CPU limits |
| `results/protocol.json` | Seeds, sizes, repeats and comparison rules |
| `results/summary.json` | Summary values and paired observations |
| `results/report.html` | Self-contained report with embedded plots |

## AI tools register

| Tool | Model version as exposed by this session | Date | Tracks | Use |
|---|---|---|---|---|
| ChatGPT | `gpt-6-astra` | 2026-10-31 | E | Case-study planning, code generation, checking, benchmarking, report and documentation |
| ChatGPT | `gpt-6.1-sol` | 2026-10-31 | A-J planning only | Earlier reading of the supplied Chapter 6 slides and coverage mapping; no A-D/F-J implementation in this package |

Earlier assignment-overview assistance in this conversation also used ChatGPT; its exact model version was not exposed and is not guessed here. All implementation in this package is AI-assisted; there are no claimed manual student corrections. AI-generated commit subjects use `[AI:ChatGPT]`. A second independent AI tool has **not** been used or compared yet.

The supplied brief/slides are acknowledged but not redistributed. NumPy, SciPy/HiGHS and Matplotlib are external libraries, not student-written optimizers. The binary formulation, heuristic implementations, validation, experiment runner and tests were generated with ChatGPT and executed in this session. The student must review and understand them before submission and viva.

## Git history and publication

The archive includes `history.bundle` with the local AI-assisted commits. To recover the repository with its history, run `git clone history.bundle ev-charging-history` from the extracted folder. `docs/COMMIT_INDEX.md` describes the commits. No remote repository has been selected or published by this milestone.

## Sources

- User-supplied Assignment 8 brief, Track E and Sections 4, 8-10.
- User-supplied Chapter 6 PPT1 (greedy/ILP) and PPT4 (strategy selection).
- [SciPy milp documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html), accessed 2026-10-31. Installed versions are pinned and recorded.
- [Caltech ACN-Data](https://ev.caltech.edu/dataset), a possible future source of real sessions; it was not used to generate these results.
