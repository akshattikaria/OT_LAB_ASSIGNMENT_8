# Track I viva guide

Start with: "I ran explicit quantum algorithms in Qiskit, compared a quantum-kernel SVM with a classical RBF SVM, and tested four circuits with an archived hardware-calibration noise model. I separated theoretical query savings from simulator time."

## A small Grover example

For four candidates, the uniform state has amplitude 1/2 on each. If 11 is marked, the oracle changes only its amplitude to -1/2. The mean amplitude becomes 1/4. The diffuser reflects every amplitude about the mean: a becomes 2*(1/4)-a. The three unmarked amplitudes become zero; the marked amplitude becomes one. Measuring then returns 11 with certainty in this ideal N=4 example. The main benchmark additionally charges an output-verification check.

| Term or question | Short explanation |
| --- | --- |
| Qubit | A state with two complex amplitudes. Their squared magnitudes give probabilities. It does not let us read both answers at once. |
| H / X / CX | H creates/interferes superpositions; X flips a bit; CX flips its target when the control is 1. |
| Oracle | A reversible implementation of a problem predicate. One abstract query can hide many gates and data-loading operations. |
| Phase kickback | Preparing the target in the minus state converts the function's output into a phase on the input states. |
| Interference | Amplitudes add or cancel; this changes the probability of the one output eventually measured. |
| What did Deutsch test? | Whether a one-bit function is constant or balanced, over all four possible functions. One oracle query suffices under the promise. |
| Deutsch-Jozsa versus BV | DJ asks constant/balanced; BV recovers a hidden linear bit string. Their circuits use a related interference pattern but solve different tasks. |
| Why is Grover quadratic? | It takes about pi/4 times sqrt(N) amplification rounds rather than linear expected classical checks. Oracle construction and physical gates are extra costs. |
| Why was classical search sometimes better? | An early marked item can be found in only a few checks. The (N+1)/2 comparator averages uniformly over all target positions. Raw sampled positions are retained. |
| Why no measured quantum speedup? | The computer classically simulates the state and many gates. Query complexity is a different measure from CPU wall time or device execution time. |
| What does QFT do? | It changes basis using complex phases. A probability histogram alone cannot verify it, so the full unitary was compared with the Fourier matrix. |
| What does QPE estimate? | The phase of an eigenvalue of a supplied unitary, given its eigenstate. Controlled powers and inverse QFT reveal an approximate binary phase. |
| What does little-endian mean here? | q0 is the least-significant bit. The printed bit string is q[n-1]...q0; 011 means integer 3. |
| Did Shor break real encryption? | No. It demonstrates factoring 15 through a dense toy modular permutation, order phases and classical postprocessing. Scalable reversible arithmetic and fault tolerance are not implemented. |
| Why can a Shor shot fail? | A zero phase, incomplete denominator or a^(r/2)=-1 modulo N may not yield nontrivial factors. The program rejects these outcomes. |
| What is a shot? | One emulated measurement outcome. Exact statevector probabilities need no shots in the simulator; physical estimation would require repeated preparations/measurements. |
| Was a real QPU used? | No. Aer uses archived Manila calibration parameters from 27 May 2024, including gate, relaxation and readout approximations. |
| Why paired ideal controls? | To compare noise on exactly the same transpiled circuit, routing and measurement mapping. Logical and physical gate counts can differ. |
| What is a density matrix? | A representation that supports mixed states and noisy channels. It costs more classical storage than a statevector. |
| T1 / T2 | Relaxation and coherence time scales used in the approximate noise model. The snapshot is historical and omits many device effects. |
| What is a quantum kernel? | The squared overlap between two encoded quantum states. Here it is the all-zero probability of a compute-uncompute circuit. |
| What is a Gram matrix? | A table of similarities between every pair of training examples. The SVM uses it to learn a decision rule. |
| Why is it PSD? | The ideal fidelity kernel can be written as an inner product between density-matrix features. Tiny numerical negatives are tolerated; no noisy training projection is claimed. |
| What was trained with zero circuit parameters? | The quantum feature map is fixed. The classical SVM still learns support-vector dual coefficients and a bias. |
| Why is the comparison fair? | Same raw split, transformed features, C=1 and SVC solver; no test-fitted scaler. The kernels have different inductive biases, so universal equivalence is not claimed. |
| Why report kernel-construction time? | Reporting only the final SVC fit would hide most of the quantum simulator work. Encoder/inverse construction and overlap simulations are included. |
| How many overlaps per quantum model? | 60*59/2 training overlaps plus 60*60 test overlaps = 5,370. Self-overlaps are known to be one and the training matrix is mirrored. |
| What are the learned parameter counts? | Number of support-vector dual coefficients plus one bias. Common scaler values and stored training data are reported separately from this count. |
| Why was quantum accuracy lower? | This fixed tiny embedding is not well suited to every dataset. That result is not proof of a barren plateau or a statement about all QML. |
| Parameter-shift | For each of these single-use rotation parameters, derivative = [E(theta+pi/2)-E(theta-pi/2)]/2. The tests compare it with finite differences. |
| VQE versus QAOA | VQE seeks a low expected Hamiltonian energy with a chosen ansatz; QAOA alternates problem and mixer layers for a combinatorial objective. |
| What if an optimizer reports failure? | It may hit its finite evaluation budget. The returned local result and status remain visible; it is not described as global convergence. |
| Quantum versus simulated annealing | This quantum example evolves a state under a changing Hamiltonian. Classical simulated annealing uses stochastic Metropolis moves; they are implemented separately. |
| What is a barren plateau? | A setting in which gradients can become extremely small across parameter space, making variational learning expensive. Earlier C studies empirical concentration; this fixed kernel has no trained circuit gradient. |
| How does D differ? | D measures CPU workers and startup/communication costs. Grover's theoretical advantage counts oracle calls. Neither number can be substituted for the other. |
| What AI error was caught? | The SDK returned a Rust EdgeList, which JSON could not serialize. Explicit native lists fixed metadata output; the original error and a real-backend metadata regression are retained. |

For a live demonstration, open results/report.html, show the handwritten BV/Grover diagrams, then the query/time chart and the lower quantum-kernel accuracy. Locate the feature map, support-vector coefficients and calibrated-noise provenance. Run the tiny new-folder benchmark and audit. Be able to change a hidden string or target and predict its output without an AI tool.
