# Track D coverage

| Required item | Implementation/evidence | Status |
| --- | --- | --- |
| Submodular objective and assumptions | Weighted coverage proof, exhaustive small checks and non-submodular control | Demonstrated |
| Greedy and approximation conditions | Ordinary/lazy greedy, exact small optima, cardinality guarantee | Implemented and measured |
| Load balancing and makespan | Static blocks, LPT and central queue, actual CPU jobs | Implemented and measured |
| Work stealing | Explicit per-worker shared-array deques with locks and stolen-job traces | Implemented and measured |
| Locality | Row/column/tile C loops over identical arrays | Measured; no cache-counter claim |
| Synchronization and communication | Per-increment lock vs reduction; exact pipe echo/batching | Measured on local processes |
| Data parallelism | Identical inference with row splits | Actual CPU threads |
| Model parallelism | Hidden-unit tensor split and partial-output reduction | Actual shared-memory CPU threads |
| Pipeline parallelism | Ordered two-stage forward pipeline, microbatch sweep | Actual inference, not training |
| Speedup/efficiency/overhead | 96 strong and 12 weak scaling runs, 1/2/4/8 workers | Measured and interpreted |
| Amdahl and Gustafson | Correct fixed/growing-work definitions and limitations | Explained |
| FedAvg vs centralized, local steps and rounds | 90 FedAvg + 35 matched centralized runs; IID/skew; E/R grid | Implemented and checked |
| MGDA and GradNorm vs equal weights | 45 runs on three fully shared two-task regression settings | Implemented and checked |
| Correctness and AI provenance | 29 tests, 25,253 audit comparisons, actual error/fix history | Included |

The core Track D requests are present. No GPU, physical network cluster, secure aggregation or multi-device pipeline training is implied. FedAvg uses serial client emulation; real concurrent CPU measurements occur in the scheduling/inference/control experiments.

Lecture research spotlights such as PANA, PackStealLB, GSHetero, architecture-aware currying, Subspace Networks and OFLight are not reproduced here. The chapter-wide checklist must resolve which research items the instructor expects. Earlier A research reproductions (GRNG/AdaFisher) remain flagged.

Overall: E was built first, followed by A/B/C/D. **Next is F (compiler optimization)**, then G/H/I/J. The combined report, complete chapter checklist, full chat exports, second independent AI-tool comparison, public repository and live demonstration remain pending. Three genuine corrected AI error cases are documented across A/B/D; this milestone does not finish the entire assignment.
