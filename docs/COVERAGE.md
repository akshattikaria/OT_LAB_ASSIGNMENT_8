# Track H requirement mapping

| Assignment 8 Track H requirement | Concrete work | Evidence |
| --- | --- | --- |
| Real DBMS or student engine | Actual Python-linked SQLite database and ordinary SQL | Exact data/charging.db, source ID/compile options/pragmas in environment.json |
| Optimization beyond a single index | Storage-budgeted subset of six composite, covering and partial indexes | dblab/core.py and select.py; three budgets |
| Variables, objective and constraint | Binary index/assignment choices; maximum measured weighted coverage; B-tree KiB budget | docs/FORMULATION.md, model.json and selections.json |
| Two Chapter 6 methods and default optimizer | Marginal-gain-per-KiB greedy versus binary ILP; default SQLite planner baseline with automatic indexing enabled | Methods evaluated on identical training data; baseline and all-index reference |
| Documented dataset of stated size | 200,000 synthetic bookings, 20,000 customers, 600 stations; deterministic seed/skew/NULLs | Generator, actual database and data_manifest.json |
| EXPLAIN / EXPLAIN ANALYZE plans | Raw EXPLAIN QUERY PLAN for each case before/after and each single-index training design | plans.json, training_plans.json; plan table in report |
| Latency, throughput and storage | Execute/fetch timings, actual mixed batches, index/db bytes, build/ANALYZE and write maintenance | *_runs.json, candidate_storage.json, portfolios.json and figures |
| Identical results | Independent Python references; deterministic ordering; exact integer/NULL semantics | reference_results.json, all measurement digests, host tests and fresh SQL audit replay |
| Fair comparison and limitations | Matched query order/traces, same data/settings, held-out parameters and explicit warm-cache scope | protocol.json, environment.json, REPORT.md and audit.json |

This experiment uses SQLite EXPLAIN QUERY PLAN plus separately measured execution time; it does not label high-level plan output as EXPLAIN ANALYZE or invent runtime plan counters. Exhaustive enumeration certifies the finite cost model, while only the unique selected/baseline/all-index physical designs are benchmarked on the full dataset. Full-scale timing of all 64 designs is not claimed.

H is separate from the EV scheduling formulation in E. Tracks I/J and overall submission integration remain outstanding. Final grading is the instructor's decision.
