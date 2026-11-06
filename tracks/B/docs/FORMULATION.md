# Formulation and method selection

## Primary problem

For each item i, choose x_i in {0,1}. Maximize sum(v_i*x_i), subject to sum(w_i*x_i) <= C. Values v_i are nonnegative integers; costs w_i are positive integers. This is a selection/allocation model with one shared resource budget, not a claim that real feature benefits are additive.

The baseline scans items in input order and accepts each fitting item. Density greedy scans by decreasing v_i/w_i. Comparisons use the same input, objective and constraint. Every candidate is checked independently for integrality, budget and objective value.

## Methods and strategy

| Method | Main decision / state | Guarantee / limitation | Resource cost |
|---|---|---|---|
| Input order | Take a fitting item immediately | Feasible, no optimality guarantee | O(n) scan |
| Density greedy | Sort by value/cost, then take fitting items | Feasible, can miss combinations with greater total value | O(n log n) sort |
| DP | Best value with first i items and budget c | Exact for positive integer costs within allocation limits | O(n*C) time/table space, pseudo-polynomial |
| Branch-and-Bound | Include/exclude tree with fractional upper bounds | Exact if frontier is closed; limit candidates retain a proof gap | Exponential worst case; explicit time/node limits |
| ILP | Binary variables, linear objective/capacity | Exact when library solver certifies; timeout is separate | Solver-dependent; explicit time limit |

The full DP table is retained for reconstruction. Its storage is measured from the allocated array, not inferred to be the whole process memory. DP is suitable here because capacities are small integers; larger binary-encoded capacities can make it inappropriate even at the same item count.

Branch-and-Bound uses a feasible density-greedy incumbent and best-bound search. Ratio sorting uses integer cross-products. Its upper bound fills remaining capacity fractionally; flooring that bound is safe because all attainable objective values are integers. Nodes whose bound cannot beat the incumbent are pruned. The reported maximum frontier bound remains an upper bound if the search is stopped.

ILP is supplied as minimization of -v-transpose*x with integer variables bounded by zero and one. Library matrices/status alone are not accepted as correctness evidence; returned selections and claimed optima are checked against independent data evaluation and DP.

## QUBO and slack

Let k = bit_length(C); introduce slack s=sum_(j=0..k-1) 2^j*b_j. This covers every integer from zero through C (and may include extra larger slack values). With all item/slack bits z and their coefficients a=(w_0,...,w_n-1,1,2,...), encode:

E(z) = -sum(v_i*x_i) + P*(a-transpose*z-C)^2.

For an upper-triangular Q with each pair counted once:

- Q_ii = P*(a_i^2-2*C*a_i) - reward_i, with zero reward for slack bits.
- Q_ij = 2*P*a_i*a_j for i<j.
- Offset = P*C^2.

Feasible original selections can achieve zero residual with nonnegative slack. Overweight selections cannot. If P > sum(values), any violating state has energy greater than zero, whereas a feasible empty item selection has energy zero. Thus all global minima are valid and minimize negative total reward. A weak penalty can create invalid minima or invalid ties. Checking only one argmin is insufficient.

The small teaching model uses four items, two slack bits and P=15. The inequality bound is sufficient, not necessary for each individual instance. The numeric encoder rejects total absolute coefficient magnitude above 2^45 after a reproducible cancellation defect was found. This protects the validated float range; it does not silently alter a large input or claim arbitrary-precision computation.

## Ising convention

Use spins s_i=1-2*z_i, so bit zero maps to spin +1. Write energy as c + sum(h_i*s_i) + sum_(i<j)(J_ij*s_i*s_j). Then:

- h_i = -Q_ii/2 - (sum of all pair coefficients incident on i)/4.
- J_ij = Q_ij/4.
- c = QUBO_offset + sum(Q_ii)/2 + sum_(i<j)(Q_ij)/4.

Some libraries use the opposite spin convention, which changes field signs. The explicit convention and every-state equivalence check avoid relying on an unstated sign assumption. Offsets do not change minimizers but are essential for matching reported energies.

The Max-Cut case minimizes -sum_edges weight*(x_u+x_v-2*x_u*x_v). It needs no constraint penalty itself; the constrained knapsack case supplies that required demonstration. The four-node graph's minimum is -4, equivalent to cut value 4.

## Separate feature-selection objective

Choose exactly three of eight candidate features to minimize validation MSE. Candidate linear models are trained on training data only. Test data never choose the subset. Forward and backward search are heuristics; exhaustive search over 56 subsets gives the validation optimum. The arbitrary validation objective is not assumed additive, monotone or submodular, and no approximation guarantee is borrowed from submodular maximization.

## Fairness and limitations

Use fixed seeded inputs, identical objectives and resource constraints, deterministic method order shuffling, three runtime repeats, quality from repeat zero and complete retention of candidates/limit statuses. DP supplies exact references here, with small-case independent exhaustive checks. Cross-instance SD is variability, not a confidence interval. Runtime includes construction and input validation, excludes independent audit/reference/plotting, and numerical-library thread counts are not controlled.

Synthetic families and small models do not establish real-world gains or general solver superiority. DP unit-scaling deliberately omits a GCD preprocessing step, which could remove that inflation. The QUBO references are classical enumeration; later quantum methods must report actual feasibility and sampling quality rather than assuming every sample is a ground state.
