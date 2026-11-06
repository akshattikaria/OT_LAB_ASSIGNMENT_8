# Track H executed validation

Executed 2026-11-04 in the shared cloud Linux workspace. The final experiment uses the core/generator, selection and experiment source revisions in commit cb844bcc7d66196faf468d92ec598f25e8d13bf9. Exact SHA256 identities for those three files are in results/environment.json; later report/audit/test/documentation changes do not alter the measured code.

## Final dataset and measurements

| Evidence | Actual result |
| --- | --- |
| Baseline SQLite database | 200,000 bookings, 20,000 customers, 600 stations; 6,811,648 bytes |
| Dataset seed | 241070005 |
| Booking NULL counts | total_cents: 3,907; energy_wh: 2,035 |
| Actual engine and libraries | SQLite 3.53.1; Python 3.12.14; SciPy 1.17.0; NumPy 2.3.5 |
| Training query timings | 252 = 7 single-index/baseline designs × 12 training cases × 3 repeats |
| Final measured physical portfolios | 7 unique designs; same 40% greedy/ILP set shares samples |
| Query-latency timings | 1,050 = 7 designs × 30 cases × 5 repeats |
| Actual mixed-batch trials | 35 batches, 100 requests each; 3,500 requests total |
| Insert trials | 21 = 7 designs × 3 trials; 2,000 inserted records each |
| Separate persisted trial blocks | 35; every saved block matched to aggregate records |
| Exhaustive model references | All 64 subsets at each of 3 budgets; all ILP objective certificates match |
| Fresh full-dataset SQL replay | 210 queries = 7 rebuilt designs × 30 cases; all match independent Python results |
| Final audit | PASS, 1,991 tracked checks/matches |

Every training and evaluation query verifies exact rows/order against an independent Python implementation. Every mixed stream verifies all outputs after timing. Insert trials verify inserted rows/counts, integrity and foreign keys after commit. The baseline database is unchanged; its SHA256 is 7e707a8de42c7b3c12ff9de9470ad38a2d86ab6d921c46b2bf14621ccfb730b8. Logical bookings SHA256 is e281e1d9c8633c705a6bcc65fc9f2659b94ddb476595257693f0f7900a2b353d.

The audit independently regenerates data/references, reconstructs the timing-derived model, checks completeness/duplicates/arithmetic/source/evidence identities, re-enumerates all model portfolios, verifies constraints, compares individual trial records to aggregates and rebuilds actual SQLite designs for semantic replay. Retained timings are not replaced during auditing.

## Semantic and selection tests

**17 tests passed**, recorded in docs/host_test_output.txt. The small fixture covers all **64 physical index combinations and 17 query cases**, totaling **1,088 exact SQL/Python comparisons**. Cases include empty ranges, all-NULL aggregates, missing customers, repeated slots, deterministic top-K ties and status changes with a confirmed-only partial index.

Other tests cover 25 random six-index ILP/exhaustive instances (64 subsets each), budget feasibility, a declared greedy counterexample, zero gains/budgets, invalid model input, actual SQL foreign-key/check constraints, generator reproducibility, result fingerprint semantics and persistence replacement/invalid-number handling. These are separate from full-dataset timing/output checks.

## Public CLI replay

A separate functional command ran 5,000 bookings with one training/evaluation/write repetition, 100 mixed requests per portfolio and 20 inserted rows per write. It produced 8 physical portfolios, 84 training timings, 240 latency timings, 8 mixed batches (800 requests), 8 write trials and 240 fresh SQL audit replays. Its audit passed **882 tracked checks/matches**. Metadata and actual logs are retained in validation/cli_smoke*; its tiny timings are excluded from the final performance report.

## Genuine rejected evidence and fixes

The initial reused-connection fixture failed on this SQLite build when status parameters changed after a schema/index change. Original output, executable reproducer and fresh-connection comparison are preserved. The test now matches the main experiment's isolation; SQLite internals are not claimed to be diagnosed or repaired.

An initial full run printed 25 completed trial messages but retained only 660/750 latency records and 22/25 batch records. The audit rejected it. That entire dataset/run is preserved under validation/initial_incomplete_run with an explicit REJECTION.json, and none of its timings contributes to final conclusions. Atomic readback-verified writes, individual trial records and final saved completeness checks were added, then the full protocol was rerun. The final two methods may choose different portfolios because their benefits derive from fresh training timings. No selective timing reconstruction was used.

The initial report's ILP-only ordering omitted unique greedy designs after the valid rerun. It now asserts and displays all seven physical portfolios. See AI_FAILURE_LOG.md for actual commit/revision details. The separate restart workspace guard correctly refused to overwrite an existing build directory; its diagnostic is retained in validation/restart_workspace_guard.log.

## Report and package checks

All three scientific figures were visually inspected. The latency legend was moved clear of the data. The offline HTML contains **three valid embedded PNGs, six tables and all seven physical portfolios**. No external image or script is required. Tables include actual spread; model predictions and full-portfolio training observations are distinguished. Main conclusions retain the insertion penalty and warm-cache/single-client scope.

Earlier A–G archive SHA256 identities were rechecked and remained unchanged. Final packaging checks the delivered file manifest, complete local Git bundle and ZIP integrity before saving. No external GitHub repository was published. No independent second-AI-tool evaluation or full chat export is claimed.
