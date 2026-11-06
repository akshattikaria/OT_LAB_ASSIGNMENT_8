# Track H: SQLite Index Selection

Prepared for Akshat Tikaria, roll 241070005. Optimization Techniques, Assignment 8.

This experiment uses real SQLite, a documented synthetic EV-booking dataset, six candidate B-tree indexes and a storage budget. Greedy marginal-benefit selection is compared with a binary ILP, the default SQLite planner on a primary-key-only schema, and an unconstrained all-index reference. SQLite chooses every query plan in every configuration; no index or join-order hints force a preferred outcome.

# Main findings

Greedy and ILP selected the same portfolio at 1 of the three stated budgets. Exhaustive enumeration of all 64 model portfolios per budget verifies ILP objective optimality for that finite model; this is not a proof of the fastest possible SQLite design. At the 60% budget, ILP-selected indexes occupy 12.777 MiB. Median actual mixed-stream throughput changes from 99.3 to 3289.0 queries/s (33.11 times baseline), while insert throughput changes from 103,371 to 18,727 rows/s (0.181 of baseline). Index maintenance is a substantial cost.

These are warm-cache, single-client, shared-cloud measurements over this synthetic dataset. They do not establish a concurrent-server, cold-disk or native-laptop speed guarantee. All repetitions and observed spread remain in the data; no statistically significant improvement or general ILP advantage over greedy is claimed.

# Dataset and reproducible setup

| Item | Recorded value |
| --- | --- |
| Bookings | 200000 |
| Customers / stations | 20000 / 600 |
| Baseline DB bytes | 6811648 |
| Data seed | 241070005 |
| NULL total_cents / energy_wh | [3907, 2035] |
| SQLite | 3.53.1 |
| Python | 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ] |
| NumPy / SciPy | 2.3.5 / 1.17.0 |
| Page / cache configuration | 4096-byte pages; 8 MiB pager cache; mmap disabled; temp storage in memory |

The generator deliberately includes hot/cold customers/stations, recent-date skew, repeated slots, four statuses and nullable amounts/energy. All identifiers are synthetic and contain no personal information. This is not TPC-H or production EV data. Bookings are analytics records, not a claim that each simulated reservation satisfies the main scheduler’s constraints. The seed, generator, exact baseline database, schema, status counts and logical/file SHA256 identities are delivered.

There are two training parameter cases and three held-out cases per query family, 30 cases total. Training determines the design; held-out cases are not fed into index selection. SQLite receives automatic_index=ON, full ANALYZE after each physical design, bound parameters and its ordinary planner. The baseline has the same primary keys, data and statistics protocol. The planner chooses among available indexes but does not solve a global persistent-index storage budget.

# Optimization formulation and methods

Choose binary x_i indicating whether candidate index i is installed, subject to sum_i s_i*x_i <= B, where s_i is measured B-tree KiB from dbstat. The budget excludes fixed tables/primary keys and statistics; full database size is reported separately. Budgets are fixed at 20%, 40% and 60% of all candidate index bytes, rounded down to a 4 KiB page.

For query family q, baseline time t_q0 and single-index time t_qi come from the mean of its two training-case median latencies. A benefit smaller than 5% of baseline is set to zero. Weighted benefit g_qi = weight_q*max(0,t_q0-t_qi); weights sum to one. The model maximizes sum_q max over selected i of g_qi. Taking a maximum avoids double-counting overlapping indexes. The ILP introduces binary assignment y_qi, y_qi <= x_i and sum_i y_qi <= 1, maximizing sum_qi g_qi*y_qi.

Greedy repeatedly chooses the feasible index with highest remaining marginal gain per KiB, stopping when no positive gain fits. The ILP is solved by SciPy/HiGHS, checked for success, feasibility and objective value against all 64 subsets. Neither method is claimed to be a general physical-design optimizer. The model omits joint-index complementarity, planner changes, construction/write cost and cache interactions; some estimated gains may be timing noise.

# Candidate indexes and choices

| Index | Definition | B-tree KiB |
| --- | --- | --- |
| customer_time | (customer_id,slot,id) | 3460 |
| station_time | (station_id,slot) | 2584 |
| status_time | (status,slot) | 3996 |
| station_cover | (station_id,slot,status,total_cents,energy_wh) | 5744 |
| time_cover | (slot,status,total_cents,energy_wh) | 5288 |
| confirmed_station | (station_id,slot,total_cents) WHERE status='confirmed' | 1752 |

| Budget KiB | Method | Chosen indexes | Used KiB | Modeled gain (ms/request) | Selection time (ms) |
| --- | --- | --- | --- | --- | --- |
| 4564 | greedy | station_time, confirmed_station | 4336 | 9.5060 | 0.094 |
| 4564 | ilp | status_time | 3996 | 10.3844 | 14.101 |
| 9128 | greedy | customer_time, station_time, confirmed_station | 7796 | 13.5240 | 0.157 |
| 9128 | ilp | customer_time, station_time, confirmed_station | 7796 | 13.5240 | 14.450 |
| 13692 | greedy | customer_time, station_time, status_time, confirmed_station | 11792 | 14.3814 | 0.655 |
| 13692 | ilp | customer_time, station_time, time_cover, confirmed_station | 13084 | 14.5835 | 4.576 |

The two methods’ labels refer to 7 unique physical portfolios including baseline and all-index reference. Identical selected sets share one measured portfolio rather than being presented as independent repeated experiments. All-index reference may exceed the stated budgets and is not a feasible budgeted competitor or a guaranteed runtime upper bound.

# Held-out plans and latency

![Each bar is the mean of three held-out parameter-case median latencies, with 5 timing repetitions per case. The log scale makes both scan and indexed latencies visible.](figures/latency.png)

Each bar is the mean of three held-out parameter-case median latencies, with 5 timing repetitions per case. The log scale makes both scan and indexed latencies visible.
| Portfolio | Weighted held-out ms/request | Median mixed QPS | Min–max mixed QPS | QPS ratio |
| --- | --- | --- | --- | --- |
| Default planner | 9.1535 | 99.3 | 85.5–106.9 | 1.000 |
| 20% GREEDY | 5.1771 | 173.4 | 164.6–201.2 | 1.745 |
| 20% ILP | 5.0295 | 190.0 | 181.4–205.4 | 1.913 |
| 40% G = ILP | 1.6602 | 529.8 | 448.0–580.8 | 5.333 |
| 60% GREEDY | 0.7700 | 1250.6 | 923.8–1457.9 | 12.589 |
| 60% ILP | 0.2369 | 3289.0 | 2658.0–4051.9 | 33.108 |
| All six indexes | 0.2514 | 3389.6 | 2838.2–4312.3 | 34.121 |

Weighted latency averages family metrics with the declared 40/15/15/10/10/10 request mix. Throughput is separately timed from actual deterministic mixed streams, not calculated as a reciprocal of a median. A batch includes execute/fetch/Python loop overhead, with output hashes checked afterward. Different parameters can return different row counts, but each portfolio receives identical SQL, parameters, request traces and output checks.

# EXPLAIN QUERY PLAN evidence

| Query family | Baseline plan | 60% selected plan |
| --- | --- | --- |
| customer | SCAN bookings; USE TEMP B-TREE FOR ORDER BY | SEARCH bookings USING INDEX customer_time (customer_id=?) |
| station | SCAN bookings | SEARCH bookings USING INDEX station_time (station_id=? AND slot>? AND slot<?) |
| confirmed | SCAN bookings | SEARCH bookings USING COVERING INDEX confirmed_station (station_id=? AND slot>? AND slot<?) |
| status | SCAN bookings; USE TEMP B-TREE FOR ORDER BY | SEARCH bookings USING INDEX time_cover (slot>? AND slot<?); USE TEMP B-TREE FOR LAST TERM OF ORDER BY |
| daily | SCAN bookings; USE TEMP B-TREE FOR GROUP BY | SEARCH bookings USING COVERING INDEX time_cover (slot>? AND slot<?); USE TEMP B-TREE FOR GROUP BY |
| city | SCAN b; BLOOM FILTER ON s (id=?); SEARCH s USING INTEGER PRIMARY KEY (rowid=?); USE TEMP B-TREE FOR GROUP BY | SCAN s; SEARCH b USING COVERING INDEX confirmed_station (station_id=? AND slot>? AND slot<?) |

Full four-column raw EXPLAIN QUERY PLAN rows for all cases are retained, alongside training plans. SCAN, SEARCH, covering indexes and temporary sort trees describe the actual chosen strategies. This command is high-level plan inspection, not an EXPLAIN ANALYZE execution-time or disk-read counter. Latencies are measured separately with perf_counter_ns. Plan text can change between SQLite versions; replay checks result semantics rather than requiring identical wording.

# Storage, construction and writes

![Selected index pages consume storage and require maintenance on every insert. The write trials include BEGIN, insertion and COMMIT with DELETE journaling and synchronous FULL.](figures/tradeoffs.png)

Selected index pages consume storage and require maintenance on every insert. The write trials include BEGIN, insertion and COMMIT with DELETE journaling and synchronous FULL.
| Portfolio | Index MiB | Total DB MiB | Index/setup + ANALYZE seconds | Median insert rows/s | Min–max insert rows/s |
| --- | --- | --- | --- | --- | --- |
| Default planner | 0.000 | 6.496 | 0.0062 + 0.0051 | 103371 | 83129–141734 |
| 20% GREEDY | 4.234 | 10.730 | 0.2970 + 0.0250 | 62087 | 55926–67280 |
| 20% ILP | 3.902 | 10.398 | 0.3255 + 0.0293 | 71579 | 55664–77650 |
| 40% G = ILP | 7.613 | 14.109 | 0.6218 + 0.0531 | 33026 | 32553–36791 |
| 60% GREEDY | 11.516 | 18.012 | 0.8563 + 0.0629 | 19847 | 17519–19902 |
| 60% ILP | 12.777 | 19.273 | 0.8240 + 0.0754 | 18727 | 2912–20275 |
| All six indexes | 22.289 | 28.785 | 1.5836 + 0.1239 | 10133 | 7011–11995 |

Each write trial inserts 2000 generated records into a fresh copy of the same portfolio, with 3 trials. Data, counts, integrity and foreign keys are checked after commit. Read batches are sequential rather than concurrent transactions. The build timer includes connection/PRAGMA setup, the dbstat capability check, CREATE INDEX and commit; database copying is outside it, and ANALYZE is timed separately. Construction and write costs are reported, not optimized by this read-only cost objective. dbstat reports B-tree pages, whereas whole-file size also contains fixed/system space; both are retained.

# Cost-model limits

![Predicted training cost is baseline training latency minus maximum-coverage benefit. The separate measured training bars execute complete portfolios. Prediction error is not hidden or treated as an SQL failure.](figures/model.png)

Predicted training cost is baseline training latency minus maximum-coverage benefit. The separate measured training bars execute complete portfolios. Prediction error is not hidden or treated as an SQL failure.
The finite ILP/exhaustive certificate concerns the measured single-index coverage model only. It does not certify global optimality over arbitrary SQL rewrites, index definitions, actual multi-index runtime or future workloads. The warmup, data skew, two training parameters, shared-host scheduling and small repeat count affect generalization. The fixed candidate set and storage fractions were not tuned using held-out performance.

# Correctness and observed development failure

Every training and evaluation query is compared with an independent Python reference, preserving exact integers, NULL SUM semantics, row order, duplicates and LIMIT tie-breaks. The main raw data also retains every output digest. Host tests exercise all 64 physical index combinations on a small fixture, including empty/all-NULL aggregates and boundaries. The audit regenerates the complete dataset, verifies all raw timing arithmetic/model certificates/checksums, rebuilds selected physical portfolios and reruns SQL without replacing timings.

An initial test harness reused one connection and its cached statements across index/schema changes. On this SQLite build, the retained reproducer returned no pending row after first querying confirmed rows, while a fresh portfolio returned the correct pending row. The final fixture test uses a fresh schema/connection per portfolio, matching the main experiment’s existing isolation. Original failing code/output, a reproducer and corrected tests are retained. The internal cause is not established; this observation is not generalized to all SQLite versions or claimed as an engine repair. The reproducer launcher’s local import path was also corrected for direct execution.

All implementation is AI-assisted ChatGPT/Codex work; no manual student correction, independent second-AI comparison or full chat export is claimed. H completes this experiment stage; I/J, assignment integration, research reproductions, full exports, second-tool comparison, public repository and live demonstration remain open.

# Primary references

SQLite EXPLAIN QUERY PLAN: https://sqlite.org/eqp.html

SQLite index/optimizer concepts: https://sqlite.org/optoverview.html

SQLite ANALYZE: https://sqlite.org/lang_analyze.html

SQLite dbstat: https://sqlite.org/dbstat.html

SciPy 1.17.0 MILP API and HiGHS solver: https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.milp.html

Supplied Assignment 8 Track H and Chapter 6 greedy/integer-programming material. Accessed 2026-11-04. External documentation supports the methods; all numerical results are this project’s own measurements.
