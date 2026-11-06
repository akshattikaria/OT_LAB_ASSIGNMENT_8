# Track J mathematical model

The process is serial CI regression testing on the exact official cachetools 7.2.8 source distribution. The baseline runs all 391 parent tests (24 nested subtests are not independently selectable pytest items). The objective is to reduce repeated test execution cost while preserving the baseline's observed per-test source-line coverage.

Let T be the ordered set of 391 collected test node IDs. Let U contain the 1,005 library source lines exercised during any test's setup, call or teardown in a dedicated full-suite coverage run. A line identifier consists of the source path relative to the vendor root and its line number. Collection-only execution is recorded separately and is not added as a requirement to U.

For test i, C_i ⊆ U is its recorded set of exercised lines. Set a_li = 1 exactly when l ∈ C_i. Let c_i = max(1, ceil(10⁶ × median(d_i1, d_i2, d_i3))) microseconds, where d_ir sums pytest's setup, call and teardown durations in untraced full-suite profile r. Thus all integer costs are positive. Coverage tracing and cProfile times are excluded from these costs.

Decision variable:

\[
x_i\in\{0,1\},\qquad x_i=1\ \text{means run test }i.
\]

Objective and constraints:

\[
\min_x\sum_{i\in T}c_i x_i,
\qquad
\sum_{i\in T}a_{\ell i}x_i\ge1\quad\forall\ell\in U.
\]

This is weighted set-cover minimization. The additive objective is a surrogate: startup, import, fixture sharing, test order, Python compilation, concurrency and host noise are not captured by its sum. The model does not constrain branch coverage, assertion strength, mutation detection, a test-count budget, or memory. It does not establish that a selected set is a semantically complete replacement.

| Method | Rule | Why it fits | Limitation |
|---|---|---|---|
| Full baseline | x_i = 1 for all tests | Naive feasible reference, original regression checks | Highest observed wall median |
| Count greedy | Choose maximum newly covered lines, deterministic ties; prune redundant chosen tests | Simple discrete coverage heuristic | Ignores cost when ranking choices |
| Weighted greedy | Choose maximum newly covered lines / c_i, deterministic ties; prune redundancy | Cost-aware discrete heuristic | May miss the best feasible combination |
| Binary ILP | HiGHS via SciPy `milp`, bounds 0–1, integer variables; coverage matrix constraints | Exact formulation with solver certificate when optimal | Optimum is conditional on frozen matrix and surrogate costs |

Both greedy implementations return a feasible set or raise an error. Reverse pruning removes a selected test only when the remaining chosen tests still cover U, starting with expensive tests. The ILP is capped at 60 seconds; a time-limited feasible incumbent is labeled as such rather than called optimal. The recorded run solved in 0.0322 s, one branch-and-bound node, with zero reported gap and matching 65.158 ms primal/dual values. The implementation verifies binary-rounded choices against the original sets and integer costs.

The coverage function f(S) = |∪_{i∈S} C_i| is monotone and submodular: adding a test covers fewer new lines as S grows. This is a **min-cost cover constraint**, not maximization under |S|≤k. The course's (1−1/e) cardinality-maximization guarantee is therefore not asserted. No general approximation ratio is needed to interpret the measured comparison; the ILP provides a reference for this instance.

Every selection is validated by a new coverage run from a fresh process, with only selected node IDs, preserving their original relative order. The saved baseline matrix alone is insufficient because removing tests can remove initialization or fixture behavior. In this instance all four fresh runs preserve U, and standard statement coverage remains 1,179/1,185. Their branch coverage and mutation results differ.

The mutation design is frozen by a fixed seed and AST eligibility rules, without using either coverage gains or mutation outcomes to choose sites. All 20 generated mutants, including survivors and timeouts, are included. Fault-retention denominator = mutants that the full suite actually kills (16); an additional common timeout and three full-suite survivors are not treated as proven equivalent or as kills. This sample is a separate quality check, not part of the optimization model.

The practical use supported by the evidence is a limited fast-feedback stage while retaining the complete regression suite for release checks. Changing the required quality constraint would require a new, independently validated model and new measurements.
