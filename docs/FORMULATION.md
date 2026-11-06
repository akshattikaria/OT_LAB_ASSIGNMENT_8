# Mathematical formulation

## Conventions

Qubit 0 is the least significant bit. Basis index is sum_q x_q 2^q; a printed conventional state label is reversed relative to a list [x0,x1,...]. Track B supplies upper-triangular Q: E(x)=offset+x^TQx, with off-diagonal coefficients counted once. Spin s_q=1−2x_q. Every QUBO energy is checked against the supplied Ising expression and classical state list. Constants remain in all reported energies.

For Max-Cut, E=-cut and min E=-4 over 16 strings. For knapsack, four item bits and two slack bits represent

E = −(5x0+4x1+3x2+2x3) + 15(3x0+2x1+2x2+x3+s0+2s1−3)^2.

P=15 exceeds total positive value 14, so a global minimum satisfies the encoded equality. The capacity constraint weight<=3 is original feasibility; weight+slack=3 is encoded feasibility. They differ for non-ground samples. The exact minimum is -6 at index 10, with bits [0,1,0,1,0,0]. A penalty proof is not a guarantee that QAOA samples that state.

## VQE, gradients and quantum geometry

H=0.7Z0+0.3Z1+0.6X0X1−0.2Z0Z1. Minimize E(theta)=<psi(theta)|H|psi(theta)> using two Ry/Rz layers with a 0→1 CNOT after each. Eight angles each occur once. The exact 4x4 eigensolver gives ground energy -1.36619037896906. All energies are dimensionless.

For a parameter in one R_P(theta)=exp(−i theta P/2),

dE/dtheta_j = [E(theta+pi e_j/2)−E(theta−pi e_j/2)]/2.

This costs 2d objectives per gradient. Shared parameters, general generators and nonlinear losses need additional analysis; the single-gate formula is not applied indiscriminately.

The Fubini–Study metric is g_ij=Re(<d_i psi|d_j psi>−<d_i psi|psi><psi|d_j psi>). Exact amplitude derivatives use [psi(theta+pi e_i/2)−psi(theta−pi e_i/2)]/(2sqrt(2)); this differs from the expectation derivative's factor 1/2. Projecting out global phase is essential. With d=8 in a four-dimensional complex pure state, g has rank at most 6.

QNG update is −0.08(g+0.001I)^−1 grad E; the update norm is capped at 1. Full metric construction uses 1+2d=17 extra state preparations/update. It uses simulator state access, not finite-shot hardware metric measurement. ShiftGD rate is 0.15; ShiftAdam rate is 0.08 with beta1=0.9, beta2=0.999. All use the same initial angles per seed.

SPSA samples independent Delta_j in {-1,+1}, approximating gradient_j by [E(theta+c_k Delta)−E(theta−c_k Delta)]Delta_j/(2c_k). Here c_k=0.1/k^0.101 and a_k=0.5/(k+10)^0.602. Two objectives/update are independent of parameter dimension. Less work/update does not guarantee better accuracy at equal updates.

## QAOA

Start in |+>^n. Each layer applies exp(−i gamma_l H_C), followed by exp(−i beta_l sum_q X_q). Theta stores all gammas, then all betas. A diagonal cost is simulated by elementwise complex phases; mixers are Rx(2 beta). For gate/noise analysis, h_i Z_i uses Rz(2 gamma h_i); J_ij Z_iZ_j uses CNOT–Rz(2 gamma J_ij)–CNOT. The constant offset contributes only global phase to the state and is omitted only in that gate list.

Classical Powell search uses gamma in [0,2pi], beta in [0,pi], at most 600 objective calls, 150 iterations and documented tolerances. All seeds and cost traces are kept, without selecting the best run for the main table. These are bounded local searches. Convergence or success status certifies no global minimum. Scaling/penalty makes the knapsack angle landscape highly oscillatory; the unchanged raw Hamiltonian was retained for an honest Track B comparison. A future normalized-angle or multistart study would be a separate protocol, not a replacement for these results.

## Measurements and noise

Born probabilities are |psi_x|^2 or diag(rho). QAOA uses computational-basis multinomial counts. A Pauli term rotates X by H, Y by S-dagger then H, and Z needs no rotation; parity of observed bits estimates its +/-1 expectation. VQE uses four separately sampled terms, without grouping. Each logged objective uses four times the stated per-term shot count.

Depolarization D_p on one qubit equals (1−3p/4)rho+(p/4)(XrhoX+YrhoY+ZrhoZ), with other qubits left implicit. It acts after each primitive gate on all involved qubits; this is two independent channels after a CNOT. Final readout flips each classical bit independently with probability r. Measurement basis changes are ideal. This synthetic model excludes device-specific calibration, routing, correlated noise and T1/T2 effects.

Finite shots are virtual Born samples. State-preparation counters describe simulator calls; physical circuit repetitions would scale with the separately recorded shot totals. Exact objectives have zero measurement shots. Metric calls are included in state_preparations; diagnostic_preparations is a separate counter for ideal validation of shot-trained iterates. CPU simulation wall time cannot establish quantum speedup.

## PQC classifier and barren-plateau diagnostic

Feature x_q is encoded by Ry(pi*x_q/2). Two trainable layers follow. Let z=<Z0>, p=0.02+0.96(1−z)/2. Mean binary cross-entropy has derivative mean[(p−y)/(p(1−p)) * (−0.48) * dz/dtheta]. Parameter shift computes dz/dtheta, then the classical chain rule supplies the loss derivative. Directly shifting cross-entropy would be incorrect. This is tested against central finite differences. Adam trains 60 minibatches of size 8 from 24 training examples; 64 independent test examples are used once. Labels x0+0.5x1>0 deliberately admit a simple logistic baseline.

For gradient concentration, angles are uniform in [-pi,pi], n in {2,4,6,8,10}, depth either 2 or n. The tested derivative is the first Ry angle. Global cost is product_q Z_q and local cost Z0, each with operator norm 1. Each configuration has 64 random parameter vectors. Variance uses ddof=1. Each shifted expectation is additionally estimated with 128 or 1,024 shots, 20 times. Raw samples support error calculations. This finite circuit-family experiment illustrates concentration and measurement difficulty; it does not prove an asymptotic exponential law.
