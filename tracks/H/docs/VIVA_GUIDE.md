# Track H viva guide

Start with: "I selected a set of SQLite indexes under a storage budget. I compared a greedy method with an ILP, then measured real query and insert performance while verifying identical results."

| Question | Short explanation |
| --- | --- |
| What does an index do? | It stores keys in an ordered search structure so a query can locate matching rows without scanning every table row. Building and updating it costs storage and work. |
| Why not add every index? | Space, insertion/update cost and construction time grow. Some indexes overlap, may be unused, or may change the optimizer's plan. |
| What are your variables? | x_i chooses whether index i is installed. y_qi assigns a query's modeled benefit to an installed index. |
| What is the constraint? | Sum of selected indexes' measured B-tree KiB must fit the budget. Fixed tables and primary keys are outside this discretionary budget. |
| What is the objective? | Maximize the weighted latency saving credited to the best selected single index for each query family. It is a model of benefits, not an exact CPU-time formula. |
| Why use maximum, not sum? | Two indexes may speed the same query. Adding both savings would count the same work twice. |
| What does greedy choose? | The fitting index with the highest additional benefit per KiB, recomputing the benefit after every choice. |
| Can greedy fail? | Yes. A high-ratio large item can block two smaller items with greater total value. The test costs 6,5,5; gains 12,9,9; budget 10 gives greedy 12 and optimum 18. This is a declared toy test, not an observed main-workload failure. |
| What does the ILP prove? | Its selected set is optimal for the six-index measured coverage model, checked against all 64 subsets. It does not prove minimum actual SQLite runtime. |
| Why are greedy and ILP sometimes identical? | Heuristics can find an exact optimum on a particular instance. That does not make the heuristic globally optimal or justify inventing an ILP advantage. |
| What is a composite index? | An index on several columns. Leading equality keys and following range/order columns influence which queries it can efficiently answer. |
| What is a covering index? | It contains the columns needed by a query, potentially avoiding separate table-row lookups. It is often larger and more costly to maintain. |
| What is your partial index? | confirmed_station includes only bookings with status='confirmed'. It cannot correctly answer arbitrary other-status requests by itself. |
| What does ANALYZE do? | It collects table/index statistics to help the normal SQLite cost planner choose plans. It is setup work, measured separately from SELECT execution. |
| What do SCAN and SEARCH mean? | SCAN traverses a table/index, while SEARCH uses conditions to visit a subset. A covering index can avoid visiting the base table. Full raw plan rows are retained. |
| Does EXPLAIN QUERY PLAN execute and time the query? | No. It describes a high-level plan. The benchmark separately times execute plus fetching all results. |
| Why include default optimizer? | The baseline uses normal SQLite planning with primary keys and automatic indexes enabled. Selected designs also use that same planner; the external method chooses which persistent indexes exist. |
| Why use training and held-out cases? | Training estimates benefits and chooses indexes. Different held-out identifiers/date ranges reveal some sensitivity to workload variation. One synthetic dataset does not prove universal generalization. |
| How did you measure throughput? | Execute a fixed mixed request stream, fetch every result, divide its actual request count by elapsed batch seconds, then verify outputs. It is not the reciprocal of a median. |
| How did you preserve correctness? | Compare with independent Python outputs, including NULL sums, empty ranges, duplicates and deterministic LIMIT ordering; run all 64 index combinations on a small fixture and replay selected full-data designs. |
| What is the write trade-off? | Every inserted booking may update each applicable index. Separate fresh-copy insert trials include transaction commit and check data/integrity afterward. |
| Why not claim disk-I/O reduction? | This run measures latency, throughput and bytes. It does not collect real disk-read counters or cold-cache server traces. |
| What failed during development? | A reused-connection fixture produced a parameter/schema-cache mismatch on this build, so tests were isolated like the real experiment. A final audit also rejected an incomplete saved record set; the whole protocol was rerun with atomic writes and per-trial persistence. |

For a live demonstration, open results/report.html, show the before/after plan for customer history, locate the storage constraint and overlap-aware objective, then run a small new-folder benchmark and its audit. Be able to change a request weight, explain why the chosen indexes might change, and rerun selection/measurements rather than editing a chart. Full chat exports, an independent second-tool comparison and a public repository are overall submission tasks, not already completed work.
