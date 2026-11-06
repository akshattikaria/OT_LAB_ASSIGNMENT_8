# Track D formulations and interpretation

## Weighted coverage

Universe U has weights w_u>=0. Candidate i covers C_i. Select S subset of candidates, |S|<=k, maximizing

f(S)=sum_{u in union_{i in S} C_i} w_u.

f(empty)=0; adding a set cannot remove coverage. Its marginal is the weight in C_i not yet covered. If A subset B, fewer uncovered items remain under B, so Delta(i|A)>=Delta(i|B). This proves normalized monotone submodularity for all generated instances. The guarantee requires this objective class and a cardinality constraint; arbitrary feature accuracy, negative coverage weights or a different constraint do not inherit it.

Ordinary greedy evaluates all remaining marginals each iteration. Lazy greedy stores upper bounds from earlier, smaller sets; submodularity makes these safe. A candidate is accepted when its freshly computed gain dominates the heap, including the declared lowest-index tie break. Both have the same selection on the saved cases. Exact enumeration is restricted to n<=20; main exact cases have n=10 or 16. For k steps, greedy value is at least [1−(1−1/k)^k]OPT, hence at least (1−1/e)OPT. Large-case bounds are not exact optima.

The designed sets {0,1,3,4}, {0,1,2}, {3,4,5} with unit weights and k=2 yield greedy=5 and optimum=6. This demonstrates an algorithmic limit, not a code failure. The control f(S)=|S|² has gains 1 and 3 for empty versus singleton contexts and violates diminishing returns.

## Scheduling and CPU resources

For jobs j with predicted work d_j and assignment a_j in {0,...,p−1}, minimize makespan max_r sum_{j:a_j=r} d_j. The lower bound in work units is max(max_j d_j, sum_j d_j/p). Predicted units are not assumed to equal elapsed seconds exactly.

Static blocks preserve contiguous input order. LPT sorts descending by predicted work, then assigns the next job to the least-loaded worker. A shared central queue assigns the next pending job to an available worker. Decentralized work stealing gives each worker a locked shared-array deque; owners remove from the front, idle workers scan other deques and steal from the back. Only unstarted jobs move. No job runs while a deque lock is held. Fixed deque capacity suffices because this workload never appends new tasks.

Actual work is deterministic PBKDF2-HMAC-SHA256, iterations=30,000×units; every output digest is checked. Strong scaling uses 32 identical jobs at every p: uniform units=4, or eight initial jobs of 12 followed by 24 jobs of 1. Weak scaling uses 16p jobs of two units each. Different schedules change assignment, not work or results.

S(p)=T1/Tp, efficiency=S/p and aggregate parallel overhead=pTp−T1 for fixed work. Each scheduler uses its own one-worker median; compare absolute times when comparing schedulers. Weak efficiency=T1/Tp and scaled speedup=pT1/Tp refer to increasing total work. They are distinct from strong scaling. Amdahl assumes a fixed serial fraction and work size, S=1/[s+(1−s)/p]; Gustafson uses scaled work, S=p−s(p−1). These models explain trends, not an exact fitted performance law here.

Steady timing starts only after all workers signal readiness and the parent releases their barrier. It includes task dispatch, locks, imbalance and result collection. End-to-end time includes creation/setup and teardown. active_compute_s sums job wall intervals; observed_utilization is their fraction of worker wall capacity, not a hardware CPU-utilization counter. Separate process CPU times are retained. Shared cloud CPUs, frequency variability and three repeats limit timing precision.

## Equivalent parallel inference

Compute Y=tanh(XW1)W2 using the same double-precision matrices. Data parallelism partitions rows X_r and concatenates Y_r. Model/tensor parallelism partitions hidden indices H_r:

Y=sum_r tanh(X W1[:,H_r]) W2[H_r,:].

This identity holds because tanh acts separately on hidden units and the second multiplication sums those units. Reduction order introduces tiny roundoff. These are shared-memory CPU threads with native BLAS constrained to one thread/kernel. Slicing, reductions and output concatenation are timed; pool warmup is excluded from steady time.

Pipeline stage 1 computes tanh(X_m W1) for ordered microbatch m; stage 2 multiplies by W2. A bounded queue preserves dependencies and limits buffered activations. Outputs are reassembled in input order. For two balanced fixed-cost stages, total time=(m+1)t versus serial 2mt, giving ideal speedup 2m/(m+1) and bubble fraction 1/(m+1). Actual kernel costs change with m. This is forward inference with two CPU threads, not distributed neural-network training.

## Locality, synchronization and messages

The C loop experiment sums the same C-order matrix by row, column or 32x32 tiles. It checks against a long-double reference within declared roundoff tolerances and uses -O3 without fast-math. Cache-line behavior motivates the comparison; no cache misses are measured.

The counter control either locks a shared integer for every increment or accumulates privately and contributes once per worker. Both perform exactly 120,000 total increments. The local pipe echo checks exact bytes. Round-trip times include the response; the reported one-way payload byte count excludes its echo and protocol overhead. For a latency-plus-bandwidth model, T≈alpha+n/beta per message; aggregating messages can reduce repeated alpha. Local IPC numbers are not substituted for real FedAvg network times.

## FedAvg and equal-work comparisons

Binary logistic loss for n examples is mean[log(1+exp(Xw))−yXw]+0.01||w_nonbias||²/2. Features have six coordinates plus an intercept. Client sizes are 64/96/160/192. A seed creates the same global training/test data for IID and label-skewed partitions. The convex reference uses SciPy L-BFGS-B, with objective and convergence status retained.

Every client starts a round from w_t, takes E local full-batch GD steps of rate 0.2, and returns w_t^(k). The server sets w_{t+1}=sum_k (n_k/N)w_t^(k). Full participation and the same regularizer imply E=1 produces w−eta sum_k(n_k/N)grad L_k, exactly the centralized full-data GD update. Uniformly averaging unequal clients would change that objective; the weighted identity is tested to 1e-12.

E in {1,5,20}, R in {6,24,120}. Every E*R has a matching centralized run. The equal-work slice E*R=120 processes 120N=61,440 sample visits, while R and model payload vary. Fixed-R slices change work and are labeled separately. Logical full-model bytes are 2*K*d*8*R, with four clients, seven float64 coefficients, downlink plus uplink. Client execution is emulated serially; these are payload counts, not measured distributed performance or privacy guarantees. Test metrics do not select steps or settings.

## MGDA and GradNorm

Two tasks share all seven coefficients w, with fixed identity readouts Xw and distinct regression targets. L_i(w)=scale_i mean[(Xw−y_i)^2]/2. This fully shared linear model makes conflict observable; private heads are deliberately absent. Targets either conflict or nearly align, and scales are (1,1) or (1,10). Reported test MSE removes the scale factor. Two independent least-squares fits are references for a relaxed model, not simultaneously achievable under one shared vector.

Let task gradients be g1,g2 and d=g1−g2. Exact two-task MGDA chooses a=clip(−g2 dot d / ||d||²,0,1), with a=1/2 for identical gradients, minimizing ||a g1+(1−a)g2||². Weights (2a,2(1−a)) sum to two, matching equal weighting's step scale. A zero common minimum norm signals no strict common descent direction; it does not require both losses to vanish. These are convex quadratic task objectives, not a global-convergence claim for deep networks.

GradNorm keeps positive weights w_i (distinct from model coefficients), sum_i w_i=2. G_i=w_i||g_i||. Relative inverse learning rates r_i=[L_i(t)/L_i(0)] / mean_j[L_j(t)/L_j(0)]. Targets are mean(G)*r_i^1.5. In the weight objective sum_i|G_i−target_i|, targets are treated as stop-gradient constants, yielding sign(G_i−target_i)||g_i||. Weight rate is 0.01; projection at 1e-6 and renormalization keep weights positive. The model update uses the pre-update weights at rate 0.03. All methods share initialization and 400 updates. Finite differences verify task gradients and the frozen-target weight derivative.

Task-wise errors and weights expose the compromise. An aggregate scalar or one preferred task alone would hide it. No universal advantage, equal hyperparameter-tuning budget or reproduction of the original papers' neural benchmarks is claimed.
