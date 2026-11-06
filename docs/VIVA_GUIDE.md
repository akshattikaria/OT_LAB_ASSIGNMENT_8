# Short viva answers

1. **What is submodularity?** Diminishing returns: adding the same candidate helps less once we already have a larger selected set. Coverage is a direct example because overlapping items count once.
2. **What is the objective here?** Cover the greatest total nonnegative item weight using at most k candidate sets.
3. **When does greedy have the guarantee?** A normalized, nonnegative monotone submodular objective under a cardinality budget, with true marginal-gain selection. The bound is at least 1−1/e, not a promise of exact optimality.
4. **Can greedy fail to be optimal?** Yes. Our designed coverage case gives 5 while exact enumeration gives 6. That is an algorithmic limit, not an implementation bug.
5. **What does lazy greedy save?** It reuses older marginal gains as upper bounds, recomputing only candidates that might win. Submodularity justifies those upper bounds.
6. **What is makespan?** The time until the slowest worker finishes. Average load alone does not determine completion time.
7. **What is LPT?** Sort jobs from largest predicted work to smallest, repeatedly assign the next job to the currently least-loaded worker.
8. **Task pool versus stealing?** A task pool has one central pending queue. Stealing gives each worker its own deque; an idle worker takes a pending job from another worker.
9. **How do you prevent duplicate stolen jobs?** Hold that deque's lock while changing its head/tail. Execute the selected job after releasing the lock.
10. **What is speedup and efficiency?** Speedup=T1/Tp. Efficiency=speedup/p. State which baseline and whether setup is included.
11. **Why can eight workers be slower overall?** Process creation, coordination and cleanup may cost more than they save on short tasks. Our strong steady gains largely disappear in end-to-end timing.
12. **Strong versus weak scaling?** Strong keeps the same total problem and adds workers. Weak increases total work with workers, keeping work per worker fixed.
13. **Amdahl versus Gustafson?** Amdahl emphasizes the serial bottleneck for fixed work. Gustafson considers growing work with more processors. Both still require realistic overhead assumptions.
14. **What was the actual hardware?** Cloud workspace: nine visible logical CPUs and eight CPU-equivalent quota. It is not a benchmark of my laptop or eight dedicated physical cores.
15. **Data/model/pipeline parallelism?** Data splits examples; model splits hidden units/weights; pipeline assigns consecutive stages to workers and streams microbatches between them.
16. **Did you train a model in the pipeline?** No. It is a verified two-stage forward inference demonstration on CPU threads. The reported speedup includes queue and output assembly costs.
17. **Why not keep increasing microbatches?** Smaller kernels and queue overhead can outweigh reduced idle bubbles. The best recorded setting was 16, not 64.
18. **Why does locality matter?** Adjacent C-order elements use nearby memory. Column traversal jumps through rows; tiles can improve reuse. We measured loop times, not cache misses.
19. **Why use reductions?** Most additions stay private, with one shared update per worker rather than a contended lock per addition.
20. **What is FedAvg?** Clients start from one global model, do local learning, and send models back. The server averages using sample-count weights.
21. **Why not average four clients equally?** Client sizes differ; equal averaging would give small clients too much influence relative to the full-data objective.
22. **Why does E=1 match centralized GD here?** Full participation and weighted full-batch gradients make their aggregate exactly the full-data gradient, with the same regularizer and rate.
23. **What happens when E grows?** Fewer communication rounds are needed for equal work, but clients drift further, especially on non-IID data. Communication and accuracy trade off.
24. **Did FedAvg run on four network machines?** No. Client learning was emulated serially. Its logical byte count is not a network-time measurement or privacy guarantee.
25. **What does MGDA do?** Finds the minimum-norm convex combination of task gradients, giving a common descent direction when one exists. We solve the two-task case in closed form.
26. **What does GradNorm do?** Adjusts task weights using gradient sizes and relative learning progress. Its target is treated as constant during the weight-gradient calculation.
27. **Why show two separate task errors?** A method can improve one task by sacrificing another. A single weighted number would hide that compromise.
28. **What model is shared?** A seven-coefficient linear predictor with fixed identity task readouts and two regression targets. It deliberately exposes conflict; it is not a deep multi-head network reproduction.
29. **How was correctness verified?** 29 tests plus a retained-data audit of selections, learning predictions, digests, counts and timing boundaries; parallel outputs match the serial model.
30. **What AI mistake was found?** The steady timer started before workers were ready. Readiness messages fixed the boundary, and end-to-end costs remain visible. Actual observations and original/fix commits are retained.

Live demo: run tests, run `python -m distopt demo`, show the greedy counterexample, open the Gantt plot, explain the end-to-end timing table, then show FedAvg's E=1 equality and the two-task trade-off plot.
