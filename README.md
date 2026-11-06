# Track H: DBMS Index-Selection Optimization

Prepared for **Akshat Tikaria, roll 241070005**. Optimization Techniques, Assignment 8.

Open **results/report.html** after extraction. It is an offline report with three embedded figures, all seven physical portfolios, before/after query plans, every repetition and read/write/storage trade-offs. The exact synthetic SQLite database, source, query parameters, independent reference results, audits, viva notes and local history are included. Earlier track archives remain separate.

## What this implements

Six candidate composite, covering and partial indexes are selected under three measured storage budgets. Two Chapter 6 methods are compared: marginal-benefit-per-KiB **greedy** and a binary **ILP solved by SciPy/HiGHS**. Overlapping savings are counted using each query family's best selected single-index benefit. The ILP objective is independently checked against all 64 subsets at each budget.

The baseline uses the **normal SQLite optimizer**, primary keys, automatic_index=ON and full ANALYZE. Every selected design uses that same optimizer; no INDEXED BY or manual join-order hints are used. The external method chooses which persistent indexes are available, rather than replacing SQLite's planner. An unconstrained all-index reference is also measured and is not a feasible competitor at the smaller budgets.

The documented synthetic dataset contains **200,000 bookings, 20,000 customers and 600 stations**, generated with seed 241070005. Six query families cover customer history, station totals, confirmed revenue, status listings, daily aggregates and a city/station join. There are 12 training and 18 held-out parameter cases, with repeated slots, skewed keys/dates, NULL measures and deterministic ordering. This is not TPC-H, production customer data or an output of the main EV scheduler.

## Main measured results

| Physical design | Index MiB | Median mixed queries/s | Ratio vs baseline | Median insert rows/s |
| --- | --- | --- | --- | --- |
| Default SQLite planner | 0.000 | 99.3 | 1.00× | 103,371 |
| 20% budget: greedy | 4.234 | 173.4 | 1.75× | 62,087 |
| 20% budget: ILP | 3.902 | 190.0 | 1.91× | 71,579 |
| 40% budget: both methods | 7.613 | 529.8 | 5.33× | 33,026 |
| 60% budget: greedy | 11.516 | 1,250.6 | 12.59× | 19,847 |
| 60% budget: ILP | 12.777 | 3,289.0 | 33.11× | 18,727 |
| All six indexes, unconstrained | 22.289 | 3,389.6 | 34.12× | 10,133 |

At the 60% budget, ILP achieves about **33× the baseline read throughput**, while insert throughput falls to about **18% of baseline**. Greedy and ILP choose the same design at 40%; they differ at 20% and 60%. The ILP certificate covers the declared six-index coverage model, not minimum actual SQLite latency or arbitrary index definitions. Full-portfolio training costs are plotted against model predictions, including prediction errors.

These are **warm-cache, sequential single-client measurements on a shared cloud Linux host**, not a concurrent database-server, cold-disk or i3-laptop guarantee. Index/setup and ANALYZE costs are reported separately; the index/setup timer includes connection/PRAGMA setup, capability checking, CREATE INDEX and commit, but excludes copying the database. Timings include execute and fetching results, with hashes outside timing. Actual mixed-batch throughput is measured directly, rather than inferred from a median latency. All repetitions and min/max spreads are retained; no statistical-significance claim is made.

## Reproduce

Recorded setup: Python 3.12.14, SQLite 3.53.1, NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8, Linux x86-64. Reproduction currently targets **Linux/WSL2** and a Python-linked SQLite build with **dbstat** support. No external DB server, GPU, paid service or network access is needed after dependencies are installed. The recorded base database is about 6.5 MiB and the largest indexed copy about 29 MiB, so the experiment is practical on an 8 GB laptop. The offline report opens without installing anything.

From the extracted project directory:

```bash
python -m pip install -r requirements.txt
python -c "import sqlite3; c=sqlite3.connect(':memory:'); print(sqlite3.sqlite_version); print(c.execute('SELECT SUM(pgsize) FROM dbstat').fetchone())"
python -m unittest discover -s tests -v
python -m dblab audit results
```

The capability command should execute without a `no such table: dbstat` error. SQLite is supplied by Python, not installed by requirements.txt; use a compatible Python/SQLite build if that extension is missing. Versions and compile options are in results/environment.json. Different SQLite versions may select different plans and have different B-tree sizes.

Small functional workflow:

```bash
python -m dblab benchmark --out results-quick --rows 5000 --repeats 1 --profile-repeats 1 --write-rows 20 --write-repeats 1
python -m dblab audit results-quick
```

Full recorded protocol:

```bash
python -m dblab benchmark --out results-rerun --rows 200000 --repeats 5 --profile-repeats 3 --stream-size 100 --write-rows 2000 --write-repeats 3
python -m dblab audit results-rerun
```

Use a new output directory. Nonempty output directories and previously used isolated build workspaces are refused to preserve evidence. Work databases are generated under build/ and are not delivered. Each physical design starts from a byte-identical baseline copy; each insert trial starts from a fresh portfolio copy. A tiny run is functional evidence only, not suitable for performance conclusions.

Regenerate the report from retained data without remeasuring:

```bash
python -m dblab report results
```

The audit regenerates the logical dataset, verifies stored timings/checksums/model certificates and rebuilds all seven physical designs for **210 fresh SQL replays**. It does not replace timing samples. Storage equality on rebuilt files is checked when using the recorded SQLite version; cross-version replay still checks query semantics. An integrity check and foreign-key check validate the base and each write trial.

## Validation and corrected failures

**17 host tests passed**, including all **64 physical index combinations × 17 fixture query cases = 1,088 SQL/reference comparisons**, 25 random six-index ILP-versus-exhaustive instances, a greedy counterexample, NULL/empty/boundary/tie checks, actual constraints, deterministic generation and JSON persistence checks.

The final main audit passed **1,991 tracked checks/matches**, covering **252 training timings, 1,050 query-latency measurements, 35 actual mixed batches (3,500 requests), 21 insert trials and all 35 per-trial records**. All query results match an independent Python implementation. Shared method selections refer to the same measured portfolio, not separate independent samples.

Two genuine development issues are retained. An initial test reused cached statements across index/schema changes and produced a wrong result on this SQLite build; the final test uses fresh schemas/connections like the existing main workflow. The SQLite internal cause is unresolved, and no engine repair is claimed. Separately, an initial full run's saved aggregates lacked three trial blocks despite completion messages. The audit rejected it, and the **entire protocol was rerun** using atomic readback-verified JSON, separate trial records and strict completeness checks. The rejected data are clearly separated under validation/initial_incomplete_run and are excluded from all final numbers. No missing timings were reconstructed or selectively filled in.

## Files

| Path | Purpose |
| --- | --- |
| dblab/core.py | Schema, six candidate indexes, six SQL templates, deterministic generator and independent query oracles |
| dblab/select.py | Overlap-aware greedy, binary ILP and exhaustive model certificate |
| dblab/experiment.py | Real physical design creation, training, held-out timing, actual throughput, writes and per-trial persistence |
| dblab/audit.py, report.py | Independent retained-evidence audit/replay and offline report/figures |
| tests/test_dbms.py | 17 semantic, selection, constraint and persistence tests |
| results/data/charging.db, data_manifest.json | Exact primary-key-only database, logical/file identities and dataset facts |
| results/cases.json, queries.sql, reference_results.json | Every bound parameter, SQL template and independent expected row set |
| results/training_runs.json, training_plans.json | All single-index training timings and actual plans |
| results/model.json, selections.json, exhaustive_model.json | Cost model, two methods/three budgets and all 64-subset references per budget |
| results/plans.json, candidate_storage.json, portfolios.json | Actual before/after plans, B-tree/file bytes and construction measurements |
| results/latency_runs.json, throughput_runs.json, write_runs.json | All final actual measurements and output digests |
| results/trial_blocks/, throughput_traces.json | Every independent trial checkpoint and matched request stream |
| results/environment.json, protocol.json, evidence_sha256.json | Runtime/source identity, fairness assumptions, budgets and raw evidence hashes |
| results/report.html, REPORT.md, figures/, summary.json | Offline report, scientific plots and all seven summarized portfolios |
| docs/FORMULATION.md, COVERAGE.md, VIVA_GUIDE.md | Mathematics, assignment mapping and explanations |
| docs/AI_FAILURE_LOG.md, VALIDATION_RECORD.md | Actual defects/revisions and executed checks |
| prompts/H/, docs/COMMIT_INDEX.md, history.bundle | Actual prompt/response excerpts and local Git history |
| validation/initial_incomplete_run/ | Rejected initial raw evidence, clearly excluded from final analysis |
| validation/main_execution.log, audit_output.txt, cli_smoke/ | Final execution/audit evidence and separate tiny workflow replay |

FILE_SHA256.json checks delivered source, data, report and documentation, excluding itself and history.bundle to avoid recursion. Recover local history with `git clone history.bundle track-h-history`. Large working indexed databases are rebuilt rather than shipped; the exact baseline database is included.

## AI disclosure and next work

| Tool | Model identification | Date | Work |
| --- | --- | --- | --- |
| ChatGPT / Codex | GPT-6 family as identified by the environment; exact serving revision not exposed | 2026-11-04 | Formulation, SQL/generator, methods, debugging, testing, experiments, audit and documentation |

All substantial work here is AI-assisted. The exact model label should be confirmed from the session export before final publication rather than guessed. ChatGPT and Codex are not counted as two independent AI tools. No manual student correction is claimed. The excerpt log is not a full chat export; global failure-log requirements already have earlier A/B/D cases, with additional observations here and in F/G.

Track H's requested experiment scope is covered. Next is **Track I: quantum algorithms and QML comparison**, followed by J. Overall integration, outstanding research reproductions, full chat exports/model labels, an independent two-AI-tool comparison, the required public repository and live demonstration remain open. No public repository was configured or published here.

## Primary references

- Supplied Assignment 8 Track H and supplied Chapter 6 greedy/integer-programming material, acknowledged rather than redistributed.
- [SQLite EXPLAIN QUERY PLAN](https://sqlite.org/eqp.html), [query optimizer](https://sqlite.org/optoverview.html), [ANALYZE](https://sqlite.org/lang_analyze.html), [dbstat](https://sqlite.org/dbstat.html).
- [SciPy 1.17.0 MILP/HiGHS interface](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.milp.html).

References accessed 2026-11-04. External documentation supports the design; all numerical results are this project's own SQLite executions.
