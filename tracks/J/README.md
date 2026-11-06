# Track J — Software-engineering optimization

**Akshat Tikaria · 241070005 · Optimization Techniques · Assignment 8**

This experiment minimizes regression-test cost on the real, public MIT-licensed **cachetools 7.2.8** codebase. The unmodified subject has **1,798 Python source lines** and **391 parent tests**. Weighted set cover is solved by greedy methods and binary ILP, compared with running every test.

The ILP selected **74 tests**. Its observed median fresh-process wall time fell from **1.196 s to 0.699 s**, a **41.5% reduction / 1.71× speedup**, over seven trials per method. Every selected suite preserves all **1,005 required per-test source lines** and **1,179/1,185 standard statement coverage**. The ILP loses **6 of 214 branch outcomes** and detects **13 of 16** faults detected by the full suite. One further mutant times out for all methods. These results demonstrate a real correctness trade-off; line coverage alone does not justify replacing the full suite.

| Method | Parent tests | Modeled phase cost, ms | Median wall time, s | Branches covered / 214 | Full-suite fault kills retained / 16 |
|---|---:|---:|---:|---:|---:|
| Full baseline | 391 | 425.695 | 1.196 | 214 | 16 |
| Count greedy | 80 | 74.171 | 0.673 | 210 | 14 |
| Weighted greedy | 79 | 66.322 | 0.664 | 209 | 13 |
| Binary ILP | 74 | 65.158 | 0.699 | 208 | 13 |

The ILP is optimal for the recorded additive, integer-cost coverage model (zero reported gap), not for actual wall time or number of tests. Weighted greedy has the lowest observed wall median. The measured host is a shared Linux cloud runtime, not the student's i3 laptop.

## Read and run

Open **REPORT.html** for the complete offline visual report; **REPORT.md** is the plain-text version. Start with `docs/FORMULATION.md` and `docs/VIVA_GUIDE.md` to understand the model and its limitations. No server or network connection is required to read the results.

Use **Python 3.12 on Linux/WSL**. The driver uses POSIX process groups for child timeouts. From the extracted project directory:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m selci.audit --out results
```

The audit reads historical evidence and verifies the unchanged vendor files, original archive, actual coverage SQLite databases, integer costs, coverage constraints, solver certificate, 28 timing runs and 80 mutation runs. It does not rerun or replace historical timings.

For new experiments, preserve `results/` and choose a new directory:

```bash
.venv/bin/python -m selci.experiment --out results-rerun
.venv/bin/python -m selci.audit --out results-rerun
```

Allow a few minutes; the 20-mutant challenge includes a 15-second timeout per child and can take longer for changes that hang. Different hosts and scheduling produce different costs, selections and times. The experiment refuses to overwrite a nonempty evidence directory. For an optional independent pristine-suite replay, `python -m selci.audit --out results --replay` writes `validation/fresh_replay/`; the packaged replay already exists, so use a clean copy of that directory if requesting another replay. Existing results must not be silently replaced.

To regenerate the packaged report after auditing its evidence:

```bash
.venv/bin/python -m selci.report --out results
```

The report labels the packaged seven-trial protocol. For customized repeat counts or a new source version, revise reporting and rerun validation rather than combining datasets. The included subject is imported from `vendor/`; do not install a separate `cachetools` release for these runs.

## What is included

| Location | Purpose |
|---|---|
| `selci/selection.py` | Count/weighted greedy and binary ILP |
| `selci/runner.py`, `process.py` | Fresh child processes, per-test contexts, precise wall timer and timeout handling |
| `selci/experiment.py` | Frozen profiles, fresh coverage validation, shuffled timing trials and mutation challenge |
| `selci/mutations.py` | Seeded, reproducible single-AST-operator mutation design |
| `selci/audit.py` | Recalculation of the recorded claims and optional fresh replay |
| `selci/report.py`, `figures/` | Standalone HTML, Markdown and exact-data figures |
| `tests/` | Ten host tests, including exhaustive small-model oracles |
| `vendor/cachetools-7.2.8/` | All 38 official distribution files, unmodified, including MIT license |
| `inputs/`, `UPSTREAM.json` | Original source archive and independently verified PyPI checksum |
| `results/` | Raw timings, selected tests, coverage SQLite files, profiles, logs, mutants and summary |
| `validation/` | Actual development failures, completed run log, audit and fresh replays |
| `docs/` | Formulation, requirement mapping, failure log, validation and viva material |
| `prompts/J/` | Actual continuation request, AI excerpts, implementation decisions and commit references |
| `history.bundle`, `FILE_SHA256.json` | Portable local Git history and final file checksums |

The mutation challenge uses disposable copies. Only mutation descriptors, resulting source hashes and execution evidence are retained; the original vendor source is unchanged. Coverage databases contain historical absolute paths; the audit uses their stored filename mappings, so the extracted project can live elsewhere.

## AI tools register

| Tool / model | Scope | Recorded date | Work |
|---|---|---|---|
| ChatGPT / Codex, GPT-6 family per environment; exact serving revision not independently exposed | Track J in this package; earlier tracks have their own logs | 2026-11-04 | Formulation, source provenance checks, code generation, debugging, tests, profiling, experiment execution, analysis and documentation |

The exact model version and full chat export must be confirmed from the user's tool interface/export before final submission. No second AI tool was run in this stage; the compulsory two-tool comparison remains open. Host tests and audits are verification executed by the same assistant, not evidence of a second tool or independent human review. Deliberately introduced mutants are not counted as AI mistakes. Actual mistakes are in `docs/AI_FAILURE_LOG.md`; commits use `[AI:ChatGPT]`.

## Milestone status

Track J's experiment, evidence and report are complete. Together with the earlier A–I packages, all ten experimental track packages now exist. The **final integrated report, exact Chapter 6 coverage audit, truthful activity diary, second-tool comparison, chat exports/model confirmation, public GitHub submission and short demonstration still require integration or completion**. A local Git bundle is supplied; no public repository was created for this stage. Do not submit this single-track ZIP as the whole assignment.

Primary sources and license details are linked in `REPORT.md` and recorded in `UPSTREAM.json`. This project does not modify the upstream code or imply endorsement by cachetools maintainers.
