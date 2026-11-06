# Optimization Techniques Lab - Assignment 8

Public repository: [https://github.com/akshattikaria/OT_LAB_ASSIGNMENT_8](https://github.com/akshattikaria/OT_LAB_ASSIGNMENT_8)

[Technical report](reports/Assignment_8_Integrated_Technical_Report.pdf) · [Captioned demo](reports/Assignment_8_Captioned_Demo.mp4) · [Submission checklist](docs/SUBMISSION_CHECKLIST.md)

**Akshat Tikaria | 241070005 | B.Tech Computer Science, third year**

The main case study is **EV charging scheduling**. All ten core experiment packages A-J are assembled under `tracks/`, with their original code, raw results, tests, source licenses and local histories unchanged. Start with `reports/Assignment_8_Integrated_Technical_Report.pdf` or the Markdown report. A captioned demonstration is included under `reports/`.

The EV experiment achieves 49.44% mean cost reduction on 15 matched, feasible, certified flexible-window cases, using synthetic sessions and fictional prices. Other results include useful negative findings: the xv6 allocator reduces measured spinning but slows elapsed time, some compiler improvements regress under O2, the tested quantum kernel loses to RBF SVC, and line-preserving test selection misses faults.

## Current status

The ten core tracks, integrated report, supporting chapter experiments, reproducibility checks and demonstration artifact are built. The 4 November integration run and 6 November final-review rerun each pass **243 track host tests** plus **7 supplement tests**. On 6 November, both original AI candidates passed the **same 9 comparison tests**, including 100 exhaustive small cases each. The supplied Gemini response and 56 paired function-runtime measurements are recorded in `ai_tool_comparison/COMPARISON.md`. The new research extension passes **29 mathematical tests** and audits **15 result files**, including **210 native SpMV timing trials**. These are separate from archived xv6 guest tests and the cachetools subject suite.

The four follow-ups are complete: original ChatGPT/Gemini platform evidence is included, Q-FLAIR is implemented and verified, public source-history revision links are available, and the report/package are refreshed. See the [AI evidence index](docs/AI_EVIDENCE_INDEX.md), [53-revision history map](docs/HISTORY_LINKS.md), and [current checklist](docs/SUBMISSION_CHECKLIST.md).

Q-FLAIR adds 12 paired cases and nine independent checks. The research inventory now has **23 entries**: 11 scoped source ports, four variants, two survey demonstrations and six mechanism-only controls. Those six detailed-policy limitations remain explicit; full paper reproductions and hardware performance are not claimed. Original track reports are dated milestones; root documentation states current status.

The included captioned video demonstrates actual EV CLI output and retained results. Rehearse it and explain/modify the code yourself for the viva. Add your own narration or live presentation if your instructor requires it.

The published repository includes the exact imported tracks and their original history bundles. `docs/PUBLISHING.md` explains how to stage future updates. The report PDF retains the status recorded at its review date; this README and the current checklist record the later GitHub publication.

The brief's suggested fourteen-day plan does not justify inventing daily work records. Actual dated work is recorded in `docs/ACTIVITY_RECORD.md`.

## Read and reproduce

One saved history archive, `tracks/J/history.bundle`, is published as two lossless parts because of the upload interface limit. The audit restores it automatically and checks its original SHA-256. To restore it directly, run `python tools/restore_large_files.py`. All source code, experiment data, reports and videos use their original paths.

Use Python 3.12 on Linux/WSL for the combined project. Each original track also has smaller requirements and detailed instructions. Native C/OpenMP and xv6 replays require their documented host toolchains; the large toolchain is excluded.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/audit_project.py
.venv/bin/python -m unittest chapter_supplement.test_study -v
```

Main demonstration:

```bash
cd tracks/E
python -m evcharge demo
```

The four-vehicle example prints fictional costs **406 -> 182 -> 182** for baseline, greedy and ILP, with all feasible. To repeat the additional chapter experiments, use a new output folder:

```bash
python -m chapter_supplement.study --out chapter_supplement/results-rerun
python tools/run_host_tests.py --out validation/host-rerun
python -m unittest research_supplement.test_methods -v
python -m research_supplement.audit
python -m unittest research_supplement.test_qflair -v
python -m research_supplement.run --out research_supplement/results-rerun
```

Historical timings are retained, not replaced by host-test elapsed times. Seeds do not fix host scheduling, solver tie choices or noisy shot outcomes. Read each track's timer scope and environment before quoting a speedup. The measurement host is a shared cloud environment, not Akshat's i3 laptop.

## Where to look

| Location | Content |
|---|---|
| `tracks/A` | Continuous optimizers, derivatives, curvature and convergence |
| `tracks/B` | Greedy/ILP/B&B/DP, feature selection and QUBO/Ising |
| `tracks/C` | VQE/QAOA/QNN, parameter-shift/SPSA/QNG, shots/noise |
| `tracks/D` | Submodular, real parallel CPU, FedAvg and multi-task studies |
| `tracks/E` | Main EV case, scheduling formulation and independently audited results |
| `tracks/F` | Mini-compiler, four passes, DP pass ordering and native checks |
| `tracks/G` | Real xv6 source/patch, guest programs and QEMU evidence |
| `tracks/H` | Real SQLite workload, plans and budgeted index portfolios |
| `tracks/I` | Explicit algorithms, calibrated-noise model and matched QML study |
| `tracks/J` | Real-codebase test selection, fresh coverage and mutation challenge |
| `chapter_supplement` | Search-policy replay, compression, layout/embedding/control experiments |
| `research_supplement` | 23 source-linked research experiments/controls; exact fidelity mapping and six gaps |
| `docs` | Exact course checklist, submission status, final answers and demo guide |
| `evidence/ai` | Four original ChatGPT/Gemini platform evidence files; page mapping in docs/AI_EVIDENCE_INDEX.md |
| `provenance` | Current source archive hashes and all 2,013 imported file hashes |
| `validation` | Dated test logs, audit and report/video checks |
| `ai_tool_comparison` | Supplied Gemini response, common tests and paired function-runtime comparison |

Per-track READMEs/reports are original dated milestones. Their earlier “next track” notes are historical. **This root README and `docs/SUBMISSION_CHECKLIST.md` describe current progress.** The imported originals are preserved for traceability.

## AI tools register

All implementation and documentation here are AI-assisted. Historical stage records disclose ChatGPT with session-reported `gpt-6.1-sol` for A/B/C/D/F/G and `gpt-6-astra` for E. H/I/J and integration identify the GPT-6 family where an exact serving revision is unavailable. Original exports now contain historical message labels; the native screenshot shows the current selector. No unexposed backend version is guessed. See `docs/AI_TOOL_REGISTER.md` and the original registers for dates/scope. Google Gemini supplied the second-tool function, with selector “Argon High” shown in student evidence received 6 November. Its approximately 60 ± 3 second generation time is a student estimate; ChatGPT generation latency is unavailable. No repair was needed. Original platform exports and native selector screenshots are included under evidence/ai/; no unexposed model revision or manual student correction is invented.

More than three genuine corrected AI-code defects are documented across the tracks. Intentional mutants, unstable controls and heuristic limitations are not counted as AI mistakes. Supplied course slides are acknowledged and hashed rather than redistributed; vendored public sources retain their licenses.
