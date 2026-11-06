# Track J viva preparation

1. **What are we optimizing?** Which tests to run to minimize an additive estimate of execution cost, while covering every library source line that the full suite exercised in a per-test context.
2. **What is x_i?** A binary variable: one if test i is selected, zero otherwise. There are 391 parent tests; nested subtests are not separately selectable.
3. **Why 1,005 lines rather than 1,798?** 1,798 is physical source size. The requirement universe is 1,005 lines exercised during test protocols. Standard coverage also counts import/collection execution and reports 1,179 covered executable statements out of 1,185. These are distinct definitions.
4. **How do you measure c_i?** Median setup+call+teardown time across three untraced full-suite runs; convert to positive integer microseconds with ceiling. Do not use coverage-traced durations as CI test costs.
5. **Show one coverage constraint.** If a line is exercised only by tests 2, 5 and 9, its constraint is x_2+x_5+x_9≥1.
6. **Explain greedy.** Repeatedly choose the test with the most uncovered lines per cost, then remove selected tests whose removal still preserves the universe. Count greedy ignores cost in the ranking.
7. **Why ILP?** Binary choices and linear coverage constraints fit directly. HiGHS reports zero gap and matching primal/dual bounds for this saved model. This does not certify real runtime or minimum test count.
8. **Give a tiny example.** Test A covers {1,2}, costs 10. B covers {1}, costs 2. C covers {2}, costs 2. Count greedy chooses A; weighted greedy and ILP choose B+C for cost 4.
9. **Why does the modeled optimum not have the lowest measured time?** Interpreter startup, imports, fixture sharing, garbage collection, test collection and host noise are not additive per-test costs. Seven wall-time trials show weighted greedy slightly faster at the median than ILP here; the ranges overlap.
10. **What is the naive baseline?** Every test in the official source distribution, unmodified. Every raw child asserts the cachetools module comes from the chosen subject source directory.
11. **How is coverage checked after removal?** Rerun only selected tests in a fresh process under coverage; compare its actual per-test line universe with the full baseline. Independently reconstruct matrices from the saved SQLite contexts.
12. **Does preserved line coverage mean correctness?** No. ILP preserves all required lines but loses six branch outcomes and misses three of the 16 faults killed by the full suite. Assertions can differ even when they execute the same line.
13. **How were mutants chosen?** A fixed-seed shuffle of eligible single AST comparison/arithmetic operators, independent of test selections or mutation outcomes; 20 distinct source lines. All are retained, including survivors and a common timeout.
14. **Why not count timeout as a kill?** A timeout alone does not establish an assertion failure; it is a separate outcome. M20 is an Add→Sub change at upstream line 510; excluding syntactic while descendants cannot prevent every indirect nontermination.
15. **How fair are the timings?** Same Python/dependencies/source/observer, serial shuffled order, seven fresh interpreters per method, no coverage or cProfile tracing. Parent wall clock includes startup, collection and evidence output. Warm caches and shared-host scheduling remain limitations.
16. **What did cProfile show?** Substantial pytest hook-dispatch, import/compilation and repeated protocol work. The highest median test cost was an autospec-call test, about 24% of the additive full-profile sum. Instrumented cProfile values are analyzed separately from speedup trials.
17. **What changed in the codebase?** No upstream code, tests or license changed. A separate selection/measurement system was added, bringing dependency and invalidation maintenance costs.
18. **When would you use this?** For quick feedback with the full regression suite retained for release checks. Refresh coverage/cost data when source, tests, fixtures or dependencies change.
19. **What would you modify live?** Add a must-run-test constraint x_i=1; introduce branch-based requirements with fresh measurement; change cost weights; or demonstrate the toy example. Explain why new quality requirements need independent evaluation rather than fitting to known mutant kills.
20. **Which AI errors were actually found?** Wrong working directory collected the wrong test folder, and verbose context JSON duplicated hundreds of MiB of evidence. Both fixes are traceable. Intentional mutants are not AI mistakes.

Practice explaining `selection.py`, changing a toy cost and predicting the chosen set without assistance. The supplied scripts and notes cannot substitute for the student's live understanding.
