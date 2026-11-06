# Observed failures and corrections

All revisions are AI-assisted ChatGPT/Codex work. No student manual correction or independent second-tool review is claimed. These are actual observations, not invented negative examples. Earlier A/B/D already provide three documented corrected cases for the overall assignment.

## 1. Reused-connection fixture mismatch

Original commit eb75898 reused one in-memory connection across 64 sets of CREATE INDEX / ANALYZE / DROP INDEX operations and parameterized queries. The real test failed: a pending booking expected as `(4,24,600,0)` was missing when the confirmed-only partial index was present. Original test output is initial_test_failure.txt.

The narrowed reproducer queries the old schema, adds the partial index and ANALYZE, then switches status parameters on that same connection. On recorded SQLite 3.53.1, the pending row is absent in that sequence but present with schema construction before a fresh portfolio's queries. schema_cache_reproducer.py and schema_cache_observation.txt preserve the executable diagnostic and actual output. The internal cause is not isolated; this is not a general SQLite finding, an engine fix, or a claim that ordinary documented schema changes should require reconnecting.

Commit d4eea40 changes the fixture to a new schema/connection for each portfolio, matching the already isolated main experiment, and adds a confirmed/pending switching regression. The final fixture verifies every row against a Python oracle over all 64 portfolios. The reproducer launcher also initially lacked the project import path; that direct-execution path was corrected. No invalid main query result is accepted merely because a test was isolated.

## 2. Incomplete saved aggregate records

The initial full run printed completion for 25 trial blocks, but its saved aggregates had only 660/750 latency records and 22/25 mixed batches. The audit raised `Latency cells missing/duplicated`. The exact rejected data and REJECTION.json are retained under validation/initial_incomplete_run. The persistence cause is unresolved; no infrastructure or SQLite root cause is asserted.

The initial generated measurement workflow did not perform a final readback/completeness assertion. Commit cb844bc adds atomic temporary-file replacement, flush/fsync/readback, a separate immutable-named record per completed trial, comparison of saved blocks to in-memory measurements and final saved-count checks. The whole protocol was rerun, including data creation, training, method selection and all evaluation/write trials. No missing records were filled with fabricated or selectively rerun timings.

The final run has all 35 trial blocks, 1,050 latency samples, 35 mixed batches, 21 write trials and 252 training samples across seven physical portfolios. The audit matches all block content to aggregate content and rejects missing/duplicate cells. JSON replacement and invalid-number preservation regressions are in tests/test_dbms.py. The initial and final designs can differ because they come from separate timing-derived models; only the complete final run supplies submitted conclusions.

## 3. Report coverage corrected

The first reporter listed only ILP-selected designs, baseline and all-index reference. That was sufficient when both methods happened to select the same sets in the rejected initial run. In the valid rerun, greedy and ILP differed at two budgets, exposing omitted greedy portfolios in the presentation. The reporter now includes every unique measured portfolio and asserts set equality with the portfolio manifest. All seven designs appear in tables and figures; identical 40% selections share measurements and are not counted twice.

Lesson: validate results, saved evidence and reporting coverage independently. A successful completion message, a proven model optimum or a visually convincing chart is insufficient without complete raw data and semantic checks. Performance regressions and estimation errors are retained as outcomes, not counted as code defects merely because they are inconvenient.
