# Exact classical models for Track C

Use the files under `results/quantum_baselines/`. Do not change the objective and still compare against these classical references.

| Model | Variables | Exact minimum | Interpretation |
|---|---:|---:|---|
| knapsack_6bit | 4 item bits + 2 slack bits | -6 | Feasible selected value 6, capacity 3, penalty 15 |
| maxcut_4bit | 4 node bits | -4 | Maximum cut weight 4 |

Each model JSON contains Q_upper, offset, named variables, Ising h/J_upper/offset and the original problem metadata. The corresponding classical JSON contains every state, its directly checked energy, every ground state and feasibility information. SHA-256 hashes are in `results/input_and_quantum_sha256.json`.

## Bit and spin order

- Model variable i is bit i of the integer basis index: index=sum(x_i*2^i).
- `bits` and `variable_order_bits` list variable zero first.
- `statevector_label` prints the integer's most significant bit first; it reverses `variable_order_bits`.
- Spins are s_i=1-2*x_i. For a Z-basis encoding this matches diagonal eigenvalue +1 for bit zero, -1 for bit one.
- Use the explicitly exported signs and offsets. Do not substitute another library's opposite spin convention without transforming coefficients.

For the knapsack optimum, the variable-order item bits are 0101 and both slack bits are zero. In the six-bit integer convention the optimal basis index is 10 and its statevector label is 001010. For Max-Cut, the ground basis indices are 5 and 10.

## Quantum comparison requirements

QAOA may use the cost Hamiltonian from the Ising coefficients. A constant shift affects reported energies but not which states minimize them. Positive energy rescaling preserves minimizers; record it and restore the scale/offset before energy comparisons. The full penalty model can have larger coefficient ranges than Max-Cut.

Report expected penalized energy, best observed feasible original objective, probability of original/encoded feasibility and probability of an optimal state separately. A sufficient penalty guarantees feasibility of exact ground states, not that a finite-depth/noisy/finite-shot sampler reaches them. For Max-Cut, interpret energy as negative cut value. These current files contain classical evidence only, not quantum speedup.
