# Track J requirement mapping

| Assignment requirement | Implemented demonstration | Verifiable evidence |
|---|---|---|
| Real software-engineering process | Regression-test selection/minimization for cachetools | README, original source/tests under vendor |
| Nontrivial/public codebase | Public MIT source release; 1,798 physical and 1,371 nonblank/noncomment Python source lines | UPSTREAM.json, archive SHA-256, six unmodified library files; no generated padding |
| Explicit variables/objective/constraints | 391 binary variables, positive duration costs, 1,005 source-line coverage constraints | docs/FORMULATION.md, results/costs.json, coverage/full/incidence.json |
| Named Chapter 6 method | Count greedy, weighted greedy and binary ILP | selci/selection.py; assignment Section 5 and supplied PPT1/PPT4 |
| Naive baseline | Run all 391 parent tests | Baseline coverage, profiles and seven full-suite timing trials |
| Profile baseline and identify bottleneck | Separate cProfile plus three untraced duration profiles; repeated test dispatch/compilation and costly autospec/threading tests | results/cprofile/baseline.pstats, profile_summary.json, profiles/, REPORT.md |
| Apply optimization and measure gain | Greedy/ILP selected suites, measured in shuffled serial fresh processes | results/methods.json, selections/, timings.json and all 28 raw process/run logs |
| Correctness checks | Pristine tests pass; selected suites retraced, saved SQLite reconstructed; source untouched | Ten host tests; validation/audit.json and fresh_replay/ |
| Quality/correctness cost | Reduced branch coverage, independently seeded mutant losses, common timeout | mutation_design.json, mutation_results.json; all 80 raw cases; three figures |
| Readability/maintenance cost | Vendor unchanged; recorder/selector/dependency/invalidation burden documented | REPORT.md and formulation |
| AI assistance and verification | Actual prompts/excerpts, traceable commits, two genuine development mistakes | prompts/J/, AI_FAILURE_LOG.md, COMMIT_INDEX.md, history.bundle |

This mapping is for Track J. It does not replace the final exact Chapter 6 checklist across A–J. An experiment on the student's own hardware, a two-AI-tool comparison, chat export, public repository and recorded demonstration are not claimed here.
