# Track J validation record

Recorded 2026-11-04. Historical times are observations from this environment; this record does not simulate a fourteen-day activity diary.

| Check | Result | Evidence |
|---|---|---|
| Official source provenance | PyPI source archive SHA-256 verified; all 38 distribution file hashes match | UPSTREAM.json, inputs/, audit.json |
| Codebase scale | Six Python library files; 1,798 physical / 1,371 nonblank, noncomment lines | UPSTREAM.json source_counts |
| Baseline suite | 391 parent tests pass, with 24 passing subtests | validation/pristine_pytest.log; results/coverage/full/run.json |
| Host checks | Ten tests pass, including 25 ILP-vs-exhaustive toy instances | docs/unit_test_output.txt |
| Coverage recording | Four fresh SQLite context databases exactly reconstruct the saved matrices | audit.json and audit_final.json |
| Coverage constraints | Every selected suite freshly preserves all 1,005 required per-test lines | coverage/ and audit |
| Standard statement coverage | 1,179/1,185 for every method | Each coverage_report.json |
| Branch outcomes | Full 214; count greedy 210; weighted greedy 209; ILP 208 | Each coverage_report.json |
| Integer objective | Recomputed costs from three untraced profile runs; all sums match | costs.json, profiles/, audit |
| ILP certificate | Status optimal; gap zero; primal/dual 65.158 ms; one node | methods.json |
| Timing experiment | All 4×7=28 untraced fresh-process trials pass; complete shuffled grid retained | timings.json and per-round logs |
| Mutation challenge | All 20×4=80 cases retained; original sources untouched | mutation_design.json, mutation_results.json, raw mutations/ |
| Mutation classification | Full: 16 killed, 3 survived, 1 timeout. ILP: 13 killed, 6 survived, 1 timeout. No invalid runs | mutation_results.json; audit_final |
| Fresh replay | Full 391, count greedy 80, weighted greedy 79, ILP 74 all pass again | validation/fresh_replay/ and audit.json |
| Genuine failures | Wrong working directory; inefficient redundant context JSON | AI_FAILURE_LOG.md, initial logs, history.bundle |

The final audit additionally recalculates model objective, timing median/range/speedup, branch losses, full-suite fault-retention denominator, timeout/invalid counts and amortization values. A later no-replay audit validates the same historical measurements without overwriting the first replay record. Regenerating reports does not rerun or substitute timings.

Coverage traces and cProfile are separate from cost profiles and CI timing trials. The same lightweight outcome observer is present for every timed method. Parent wall time includes interpreter, import, collection and artifact-writing overhead. POSIX timeout enforcement uses a timer thread plus a blocking process wait, avoiding the polling granularity of `wait(timeout=...)` for short measurements.

Only original, deliberately seeded single-operator mutants are used; surviving mutants are not labeled equivalent. M20 changes an addition to subtraction at source line 510 and times out under every method. The 15-second cap is not counted as a fault kill. The observed reduced-suite fault losses are a quality limitation, even though all required lines remain covered.

The final archive is checked for CRC errors, manifest agreement and Git-bundle validity. The archive export check is retained beside the archive because an archive cannot include its own final checksum without a circular dependency. The previous A–I archives are checksum-verified separately and remain unchanged.
