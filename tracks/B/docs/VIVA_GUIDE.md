# Track B: short viva explanations

**What is the optimization problem?** Choose items with maximum total value while staying within one budget. Each item is either selected once or not selected.

**What does binary mean?** Each decision is 0 or 1. This is different from fractional knapsack, which allows taking part of an item.

**Why can density greedy fail?** A locally attractive item can block a better combination. With values 60,100,120, costs 10,20,30 and capacity 50, greedy gets 160 but the best pair gets 220.

**How does DP work?** Store the best value using the first i items and each remaining capacity. Compare excluding item i with including it once using a solution from the previous row.

**What is pseudo-polynomial?** O(n*C) depends on the numeric capacity C, not just the number of bits needed to write C. A huge integer capacity can make the table impractical.

**What is Branch-and-Bound?** Explore include/exclude choices while maintaining a feasible best solution. A fractional relaxation gives an optimistic bound; branches unable to improve the incumbent are discarded.

**Why is a fractional bound valid for a binary problem?** Allowing fractions enlarges the feasible set, so its maximum is at least the binary maximum. Integer total values permit flooring that upper bound without excluding a better integer value.

**What happens at the search limit?** A feasible incumbent is retained with an upper bound. Unless the gap closes, it is not called a proved optimum. Seven main cases hit the configured node limit in the canonical run.

**What did ILP do?** It solved the same binary linear objective and capacity constraint through an acknowledged library solver. We wrote the formulation, not HiGHS itself.

**What is QUBO?** A quadratic objective over binary variables with constraints incorporated into its energy. Here a squared penalty encodes capacity using nonnegative slack bits.

**Why slack?** It turns weight <= capacity into weight + slack = capacity. Binary powers represent the nonnegative integer unused capacity.

**How large should the penalty be?** For this nonnegative integer model, P greater than the sum of all values is sufficient to make every exact energy minimum feasible. It is conservative, and too-small penalties can allow invalid minima or ties.

**Does that make every quantum sample feasible?** No. The proof concerns global minima. A sampler can produce excited or noisy states, so feasibility probability must be measured separately.

**What changes in the Ising model?** Binary bits become spins +/-1. Our convention is spin=1-2*bit. Coefficients and the constant offset are transformed so every state's energy is preserved.

**Why keep the offset?** It does not change which state minimizes energy, but omitting it changes the reported energy and breaks a fair classical/quantum comparison.

**How were feature subsets selected?** Train candidate linear models using training data and choose subsets by validation error. Held-out test error is evaluated afterward, not used for selection.

**Is feature-selection validation error submodular?** We do not assume that. Greedy has no borrowed 1-1/e guarantee for this arbitrary objective.

**How was correctness checked?** Independent selection audits, exhaustive enumeration on 100 small cases, 20 tiny constrained QUBOs, energy equality for all exported states and tests of bit ordering, bounds and data isolation.
