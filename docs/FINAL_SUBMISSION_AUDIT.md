# Final submission audit — 7 November 2026

The public repository is the submission destination, following the instructor's link-only instruction as reported by the student. No separate Drive upload is required. All written submission artifacts are present and the fresh correctness campaign passes 298 checks: 243 A–J host checks, seven chapter checks, 30 research checks and nine checks per AI candidate. Source/result integrity and the report/video are verified separately.

## Written requirements and evidence

| Brief requirement | Final evidence |
|---|---|
| Public repository, clear README and setup | Root README, requirements.txt, per-track setup and explicit reproduction commands |
| Main process and mathematical formulation | EV charging Track E; objective, binary decisions, energy/window/capacity constraints and strategy comparison |
| Complete taught-topic inventory | CHAPTER6_CHECKLIST.md: 112 core/supporting topics and 23 research entries, each mapped to executable evidence |
| Code and correctness for all ten tracks | Source, raw results and tests under tracks/A–J; 243 fresh host checks pass |
| Baseline and optimized comparisons | Retained tables/plots/raw runs with units, seeds, budgets, timer scopes and negative results |
| AI tools register in README | The complete tools/model/dates/scope table is included directly in the root README |
| Per-track prompts, code revisions and platform evidence | Root prompts/A–J contain original excerpts plus verified source-revision, correction, test and original-chat links; Integration holds subsequent requests |
| At least three genuine AI-code corrections | Original track failure logs and public before/after source snapshots; exporter correction is also retained |
| At least two AI tools on one task | Unchanged ChatGPT/Gemini knapsack candidates, common correctness cases and 56 retained paired function timings; unavailable generation latency is explicitly unmeasured |
| Technical report and short demonstration | 28-page PDF, Markdown equivalent and 100-second captioned video |
| Compiler, xv6, database and QML details | Four compiler passes/native checks; two kernel features and four retained full guest validations; SQLite portfolios/plans; algorithms/QML and calibrated-noise model |
| Final questions | FINAL_QUESTIONS.md answers all ten; DEMONSTRATION_GUIDE.md supports the live explanation |

## Research scope assessed against the supplied material

Section 5 of the written brief explicitly permits an implementation, a library experiment or another verifiable experimental demonstration. The six entries at issue appear as research spotlights: PPT2 slides 31–33 and PPT4 slides 22,24–25. PPT4 slide 22 expressly separates authors' reported results from illustrative numbers. These are the basis for the scoped demonstration route used here. This assessment is not an instructor approval, and no minimum mark or future grading decision is guaranteed.

| Research spotlight | Actual demonstration and independent final check | Fidelity retained |
|---|---|---|
| PANA-related scheduling | Native nonzero-tile adaptive scheduling; all 210 retained trials agree with the serial reference | Original mechanism control; no claimed published SIMD policy or SuiteSparse reproduction |
| PackStealLB-related packing | Replay all ten transfer traces, task ownership, pack loads, makespans, migrations and message counts | Finite modeled work stealing; no Charm++/published epsilon-Nash algorithm claim |
| GSHetero-related placement | Recompute five grouped-placement scores and exhaustive group-constrained optima | MCL plus declared placement heuristic; no Hadoop or unavailable exact placement policy claim |
| Architecture-aware currying | Recompute all 15 numeric reductions and geometry-based byte-hop counts | Near-data/partial-work illustration; no complete compiler transformation claim |
| OFLight-related compression | Check 2,000 quadratic-objective certificates, feedback conservation and both uplink/downlink payloads | Declared projection controls and ideal superposition; no RF execution or unavailable full policy claim |
| EAHP-related strategy search | Recheck all 1,611 device-memory constraints/cost records and retained GA/exact comparisons | Explicit synthetic GA/finite-model experiment; no source-scale LLM training or full-paper policy claim |

All six remain visibly labelled mechanism controls. Strict full-paper policy reproduction remains false, separately from whether the required demonstration artifacts exist. The submission is ready as the declared experimental portfolio; exact paper reproduction is not silently substituted or claimed.

## Export correction found by the deep audit

The shared research exporter sorted tuples as though they were unordered sets. Source calculations were correct, but exported strategy device types, HPO configurations and SVM+ grid indices could lose order. The exporter now preserves tuples while retaining deterministic set order, with a nested-order regression.

A fresh deterministic strategy run corrected 1,033 device-label sequences. HPO metadata were recovered from the original configuration product and stored trial IDs; SVM+ indices were uniquely recovered from unchanged stored numerical hyperparameters. Independent comparisons confirm that all numerical scores, training timings, selected fitted models, GA traces, optimum values and reported conclusions are unchanged. Original exports are retained under research_supplement/diagnostics/. The correction proof is validation/strategy_export_correction_20261107.json.

## Final check scope

The audit independently recomputes 708 stored EV schedules in 711 retained rows (three rows return no schedule), including costs, energy, windows, exact demands and station capacity. Solver values are binary within 1.29e-10 before rounding, tighter than the independent replay tolerance of 1e-8. Deliberately infeasible/control outcomes remain visible. All 2,013 imported files retain their hashes. Host checks are fresh; historical performance and QEMU guest campaigns are retained and verified rather than falsely described as rerun.

The instructor still needs the repository link, and the student remains responsible for explaining/modifying the code during the viva. These are submission/presentation actions; no unfinished file-edit task is left by this audit.
