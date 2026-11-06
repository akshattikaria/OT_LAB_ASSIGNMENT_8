# Track I formulation and interpretation

The process is computation/learning with quantum circuits. Objectives and resource measures differ by task. A lower logical query count is not substituted for measured CPU time, accuracy or physical gate cost.

## Promise problems and explicit circuits

Deutsch/Deutsch-Jozsa decide constant versus balanced Boolean functions under that promise. The oracle maps |x,y> to |x,y XOR f(x)>. Phase kickback and interference determine the decision after one abstract query. The implemented small truth-table oracle explicitly enumerates marked inputs, so constructing it costs exponentially many table entries; it is not a free general-purpose data loader.

Bernstein-Vazirani assumes f_s(x)=s dot x modulo 2 and recovers hidden bits s. The CNOT oracle is explicit, with one query in the quantum model and n single-bit probes classically. QFT uses positive Fourier phases and is checked against F[j,k]=exp(2*pi*i*j*k/2^n)/sqrt(2^n), including relative phases. Inverse QFT follows controlled powers in QPE. Output integer conventions are little-endian; q0 is the least-significant bit.

Shor's toy example prepares four counting and four work qubits for N=15. Modular multiplication maps x<N to a*x modulo N and fixes unused basis state 15. This is a reversible permutation when gcd(a,N)=1. Controlled powers and inverse QFT produce order-related phases. Continued-fraction denominators are verified by modular exponentiation, and GCD(a^(r/2) +/- 1,N) supplies factors only when nontrivial. Zero, odd/invalid periods and the minus-one case are rejected. The circuit does not hardcode a period, but its dense modular matrix is an exponentially sized toy representation, not efficient scalable Shor arithmetic. No factoring wall-time advantage is claimed.

## Grover: logical complexity and implementation cost

For one marked element among N=2^n, theta=asin(1/sqrt(N)) and r is the nearest integer to pi/(4*theta)-1/2. The success probability after r rounds is sin^2((2r+1)*theta). The benchmark stores r oracle calls, one additional classical verification query, an actual sampled outcome, and a separately timed classical scan on the same marked element.

Uniform-target expected classical checks are (N+1)/2. Observed checks are marked_index+1 and can be much smaller for an early target. Both are shown. The known query-model difference is O(sqrt(N)) versus O(N), with a reversible oracle assumed available. Decomposed MCX gates, loading, routing, measurements, error correction and circuit construction are additional costs. The CPU total here includes circuit build, transpilation to u/cx, exact statevector simulation and output sampling/verification. It is not an estimate of QPU time.

## Hybrid optimization

VQE minimizes E(theta)=<0|U(theta) dagger H U(theta)|0>, with the explicit dimensionless Hamiltonian

H = 0.5 ZI - 0.4 IZ + 0.3 XX + 0.2 ZZ.

The ansatz has four RY parameters and one CX. Parameter-shift gives each derivative as [E(theta+pi/2 e_i)-E(theta-pi/2 e_i)]/2. Adam takes 60 updates at the fixed recorded step size. Each run makes one initial call and nine calls/update (eight shifts plus updated energy): 541 circuit evaluations. An exact eigensolver checks the variational lower bound. This is not a molecular-energy calculation.

QAOA minimizes expected negative cut on the five-edge four-node chapter graph. H_cost=-cut=(sum_edges ZiZj-5)/2, initial state |+>^4, cost gates RZZ(gamma) and mixer RX(2 beta). A depth-p circuit has 2p angles. Powell receives at most 300 objective calls per run; final distribution evaluation is counted separately. Exact enumeration gives cut optimum 4 and uniform expected cut 2.5. Local search/finite budgets do not certify a global optimum.

The annealing study uses H(s)=-(1-s)sum(X)+s*(-cut) and midpoint first-order Trotter steps. It is a gate-based closed-system approximation, checked against dense midpoint time evolution. T is dimensionless schedule time, not CPU seconds or device microseconds. Classical Metropolis simulated annealing is implemented separately. Neither this circuit nor its ground probability demonstrates an execution on quantum-annealing hardware or a tunneling advantage. Real embedding/chain/precision costs are discussed, not executed.

## Matched QML task

Two synthetic binary datasets, moons and circles, each use 120 examples and a stratified 60/60 split for each of three seeds. A StandardScaler fits training features only; both kernels receive the same bounded angles x=(pi/2)*tanh(scaled_features). No test labels select the feature map, C or RBF gamma.

The two-qubit map repeats U(x)=[D(x)(H tensor H)] twice. For z0,z1 in {-1,+1}, the diagonal phase is

exp[-i*(x0*z0+x1*z1+(pi-x0)*(pi-x1)*z0*z1)].

The fidelity kernel K(x,y)=|<phi(y)|phi(x)>|^2 equals the zero-state probability of U(y) dagger U(x). It is a PSD Hilbert-Schmidt kernel for pure states. Training executes n(n-1)/2 overlaps, mirrors the exact Gram matrix and fixes self-overlaps to one. Testing executes n*m overlaps. For n=m=60 that is 5,370 exact simulator circuit evaluations/model, each with 28 logical gates including eight CX gates. Hardware estimates would need shots per overlap; exact simulator calls are not physical measurement counts.

Both models solve the same precomputed-kernel SVC problem with C=1. With labels y in {-1,+1}, the dual maximizes sum(alpha)-1/2 sum(alpha_i alpha_j y_i y_j K_ij), subject to 0<=alpha<=C and sum(alpha_i*y_i)=0. The classical RBF uses gamma=1/(2*training_feature_variance). Learned parameter count reports support-vector dual coefficients plus bias. Common scaler parameters and stored training-point coordinates are excluded from this count.

There are zero trained quantum-circuit weights in this fixed kernel; it is still a trained classifier because SVC learns coefficients/bias. Track C's QNN is a separate variational model. A gradient barren plateau is not diagnosed by low accuracy in this fixed-kernel experiment. The kernel is tiny and analytically classically simulable; the audit reconstructs its four amplitudes directly. The measured SDK loop is not an optimal classical emulation or a hardware timing model.

Training time includes feature circuit creation/inversion, train kernel construction and SVC fitting; inference includes test encoders/kernel and prediction. Common data generation/scaling is outside both models' timers. Three seeds change datasets/splits, not merely repeat identical timing trials. Quantum/RBF execution order alternates by seed. No broad statistical or practical quantum-advantage claim follows from this small comparison.

## Noise and finite shots

The calibrated noise study uses the archived FakeManila properties dated 2024-05-27 and Aer NoiseModel.from_backend. It includes gate/depolarizing, thermal-relaxation and readout approximations. Ideal and noisy conditions use identical transpiled circuits/layouts; 4,096 shots/condition and three simulator seeds are recorded. This is historical emulation, not a current live device or physical execution. Calibration/model uncertainty is not represented by the plotted shot-sampling Wilson intervals.

The separate kernel-shot experiment samples binomial test-kernel estimates at fixed ideal-trained SVC coefficients. It is not calibrated noisy kernel training; it neither refits a noisy Gram matrix nor claims a PSD correction. All ideal model matrices, parameters, predictions and synthetic shot counts are retained for independent checking.
