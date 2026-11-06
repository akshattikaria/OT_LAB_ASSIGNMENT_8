# Track B coverage and assignment progress

| Requirement | Experiment / code | Status |
|---|---|---|
| Selection/allocation problem | Binary knapsack objective and capacity | Implemented |
| Baseline | Input-order fitting selection | Implemented and measured |
| Greedy | Exact density ordering and counterexample | Implemented and measured |
| Integer linear programming | Explicit binary formulation using SciPy/HiGHS | Implemented and checked |
| Branch-and-Bound | Own tree, relaxation bound, pruning and limit metadata | Implemented and checked |
| Dynamic programming | Own 0-1 recurrence and reconstruction | Implemented and checked |
| Exact/heuristic comparison | 80 generated cases plus five controls, repeated runs | Recorded |
| Feature selection | Forward, backward and all three-feature subsets | Implemented with separate validation/test data |
| QUBO with penalty terms | Slack-encoded knapsack and sufficient-P proof | Implemented; all 64 states checked |
| Ising conversion | Explicit spin signs/offsets and every-state identity | Implemented and checked |
| Classical baseline for C | Six-bit knapsack and four-bit Max-Cut | Exported with hashes and ground states |
| Incorrect-penalty behavior | Penalty sweep and all-minimizer feasibility counts | Demonstrated |
| Correctness | 30 tests, 100 random exact-method oracles, 20 random QUBOs | Passed |
| AI provenance | Prompt excerpts, original/fix commits, failure record | Included |

Overall: Track E working case study, Track A core experiments and Track B experiments have been built. Track A's flagged research-paper reproductions still need resolution in the final chapter-wide checklist. Track C is next, followed by D and F-J. The combined report, complete AI disclosure/export evidence, second-tool comparison, remaining genuine failure case, public GitHub publication and live demonstration remain pending.
