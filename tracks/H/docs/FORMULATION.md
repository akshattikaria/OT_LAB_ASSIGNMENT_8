# Storage-constrained index selection

The process is repeated read queries over SQLite bookings, with insert maintenance measured as a trade-off. The six fixed candidate index definitions are in dblab/core.py. Index selection is a physical-design problem: SQLite's normal optimizer still selects each execution plan after the candidate subset is installed.

## Data and workload

The final experiment has 200,000 bookings, 20,000 customers and 600 stations. Generation uses seed 241070005, integer amounts/energy, 8,760 possible hourly slots, ten synthetic cities, four statuses, repeated slots, nullable measures, hot/cold identifiers and recent-date skew. It is a documented synthetic benchmark, not TPC-H or real customer data. The synthetic bookings are analytics records, not an output of the main EV charging scheduler.

Six query families cover customer history, station-window totals, confirmed-station revenue, status-window listings, daily totals and a station-city join. The request weights are respectively 40%, 15%, 15%, 10%, 10%, 10%. Each family has two training parameter cases and three held-out cases. Selection uses training measurements only; the same held-out SQL/parameters/traces are sent to every physical portfolio. ORDER BY includes an id tie-breaker for limited listings, preserving deterministic outputs across plans.

## Model

Let x_i be 1 if index i is installed, and s_i its B-tree storage in KiB. dbstat counts actual index pages; page size is 4096 bytes, so sizes are exact multiples of 4 KiB. The constraint is

$$\sum_i s_i x_i \le B,\qquad x_i\in\{0,1\}.$$

Fixed data tables, primary keys and statistics are outside this discretionary index budget. Whole-file size is reported separately. B is 20%, 40% or 60% of the total size of all six candidates, rounded down to a page. Candidate definitions, weights, fractions and the 5% benefit threshold are fixed choices, not claimed to be optimized.

For family q, t_q0 is the mean of the two training-case median latencies without optional indexes; t_qi is the corresponding value with only index i available. Latencies time execute plus fetchall; row hashing is outside timing. Define

$$g_{qi}=w_q\max(0,t_{q0}-t_{qi}),$$

setting g_qi to zero when the measured gain is below 5% of t_q0. The weighted coverage model maximizes

$$F(S)=\sum_q\max(\{g_{qi}:i\in S\}\cup\{0\}).$$

This avoids adding two indexes' benefits for the same query. It is a nonnegative monotone submodular coverage objective under a knapsack constraint, but the implemented simple ratio greedy is not given a general approximation certificate. It can be suboptimal, as a unit test demonstrates.

Greedy repeatedly installs the feasible index maximizing [F(S union {i}) - F(S)] / s_i. Zero remaining gain ends the search. ILP introduces binary y_qi meaning query q receives index i's modeled benefit:

$$\max \sum_{q,i}g_{qi}y_{qi},\quad y_{qi}\le x_i,\quad\sum_i y_{qi}\le1,$$

plus the storage constraint. SciPy/HiGHS solves this binary program. The implementation checks solver status, rounded installed choices, feasibility and recomputed objective. Exhaustive enumeration of all 64 subsets at each budget independently verifies the optimum of this finite cost model. Redundant installed indexes may be pruned without changing its objective; no globally minimum-storage tie-breaking claim is made.

The experiment compares greedy, ILP, primary-key-only default planning with automatic indexes enabled, and an unconstrained all-six-index reference. Default query planning does not automatically solve this persistent-index budget problem. The all-index design may violate a budget and need not be fastest.

## Limits of the model and measurements

Only the best single-index benefit is credited per family. Joint-index complementarity, automatic-index interactions, changed join plans, data-page locality and planner regressions are not predicted exactly. Measured full-portfolio training costs are displayed separately from model predictions. An ILP optimum therefore does not certify minimum actual SQLite latency, arbitrary index definitions or future workload quality.

Index construction, ANALYZE and insert cost are measured but not included in this read-latency objective. A workload dominated by writes or a short deployment lifetime would need a different objective, for example adding a weighted write/build cost and a query horizon. No such unmeasured benefit is claimed.

SQLite uses its standard planner, bound parameters, automatic_index=ON and full ANALYZE for each design. No INDEXED BY or forced join order is used. Schema construction completes before query connections open. Queries are warmed once per portfolio/repeat, with an 8 MiB pager cache, mmap disabled and temporary structures in memory. These are warm OS-cache, sequential single-client tests; cold disk, concurrent clients and production durability under power failure are not tested.

Five latency repetitions cover all 30 cases. Five actual mixed-request batches per portfolio measure throughput directly, rather than deriving it from a median latency. Three separate insert trials use fresh copies and include BEGIN IMMEDIATE, inserts and COMMIT, with DELETE journaling and synchronous FULL. All result checks follow the timing boundary. All data and negative outcomes remain retained; tiny functional runs are excluded from performance conclusions.
