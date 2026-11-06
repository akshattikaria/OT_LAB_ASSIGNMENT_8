# Problems, update rules and interpretation

## Optimization problems

| Experiment | Decision variables | Objective | Constraints / reference |
|---|---|---|---|
| Ridge | Eight real weights w | ||Xw-y||^2/(2n) + lambda*||w||^2/2 | Unconstrained; augmented least-squares optimum |
| Neural network | 33 real weights/biases | Mean binary cross-entropy + 0.001*||theta||^2/2 | Unconstrained; global optimum unknown |
| Exponential fit | Real a,b | Mean (a*exp(b*x)-y)^2/2 | Same start/residuals for Newton, GN and independent local reference |
| Curvature study | Six logistic-regression weights | Mean logistic loss + 0.01*||w||^2/2 | Unconstrained; full, diagonal, low-rank and HVP approaches |
| Noisy oracle | Two real coordinates | ||w-[1,-2]||^2/2 | Known true optimum, additive gradient/value noise |

Inputs, initial weights, seeds, losses and units are explicit. These are synthetic experiments, not estimates of field/application performance.

## First-order methods

Let g be the mean batch loss gradient including the L2 derivative. GD uses all samples, SGD one shuffled sample, and the mini-batch family up to 32 samples per update.

- GD/SGD/mini-batch: w <- w - eta*g.
- Momentum: v <- beta*v + eta*g(w); w <- w-v.
- Nesterov: v <- beta*v + eta*g(w-beta*v); w <- w-v. The gradient is evaluated at the look-ahead point.
- AdaGrad: accumulate G <- G+g^2; w <- w-eta*g/(sqrt(G)+epsilon).
- RMSProp: G <- beta*G+(1-beta)*g^2; use its root in the denominator.
- Adam: maintain first/second exponential moments with beta1=0.9 and beta2=0.999, divide by 1-beta^k for bias correction, then update using m_hat/(sqrt(v_hat)+epsilon).

Momentum/NAG/RMSProp use beta=0.9; epsilon=1e-8. No hidden gradient clipping or weight-decay variant is used. L2 is part of the objective, including all neural biases.

## Backpropagation

Hidden activation h=tanh(XW+b); logit z=h*v+c. Stable binary cross-entropy is logaddexp(0,z)-y*z. Its mean logit derivative is (sigmoid(z)-y)/batch_size. Multiply backward through output weights and tanh derivative 1-h^2 to obtain each parameter derivative, then add lambda*theta.

Backpropagation computes derivatives. The separate optimizer state chooses how those derivatives change parameters. The same neural backprop implementation serves all eight first-order methods.

## Newton and Gauss-Newton

Newton uses g=gradient F and the exact Hessian H. Gauss-Newton represents the objective as ||r||^2/2 and uses g=J-transpose*r, B=J-transpose*J. Ridge regularization is encoded as additional residuals sqrt(lambda)*w with Jacobian sqrt(lambda)*I.

Both solve B*p=-g, symmetrizing/shifting curvature if its smallest eigenvalue is below 1e-8 and using Armijo backtracking with coefficient 1e-4. This globalization is explicitly disclosed. No claim is made that plain Newton always finds a minimum or the nearest stationary point.

For linear ridge residuals, GN curvature equals the exact Hessian, so a unit step solves the quadratic up to numerical precision. For a*exp(b*x), the exact Hessian additionally contains residual-weighted second derivatives. The nonlinear experiment makes that distinction visible.

## Curvature and Fisher

For logistic regression, conditional model Fisher F=X-transpose*diag(p*(1-p))*X/n is the unregularized cross-entropy Hessian. Observed-label per-example gradient outer products give an empirical Fisher that generally differs. L2 adds lambda*I separately.

Diagonal and rank-2 approximations drive actual optimization steps. The low-rank demonstration explicitly forms/eigendecomposes the small matrix; it does not claim an efficient large-model implementation. Matrix-free HVP uses X-transpose[(p*(1-p))*(Xv)]/n + lambda*v. Conjugate gradient solves a Newton system using these products, checked against dense multiplication and directional numerical differentiation.

## Strategy selection

| Criterion | Gradient family | Newton / Gauss-Newton | Curvature approximations |
|---|---|---|---|
| Suitable variables | Differentiable real parameters | Small smooth real problems; GN for residual losses | Smooth models with costly full curvature |
| Cost per update | One batch gradient plus O(d) state | Hessian/Jacobian construction and dense solve | Diagonal cheaper storage; HVP avoids a dense matrix |
| Memory structure | O(d) optimizer state plus model/data | O(d^2) Hessian storage, O(d^3) dense solve | O(d) diagonal; O(d*k) low rank plus floor |
| Guarantees | Depend on function class, noise and step assumptions | Local/regularity/globalization assumptions matter | Approximation and damping affect steps |
| Hardware in this study | CPU | CPU | CPU |

No single method is forced onto an unsuitable problem. Newton/GN are compared on ridge and a nonlinear least-squares task; the neural model uses the eight first-order methods, with its derivative checked independently.

## Fairness and limitations

Each first-order method gets four rates on an independent tuning problem and the same maximum per-problem epochs. The same evaluation data and initial weights are used across methods. A sample-gradient pass is a work proxy, not a FLOP measure: SGD performs many more parameter updates per epoch, and second-order methods need extra curvature work. Runtime includes diagnostics, and numerical-library thread counts are uncontrolled.

Early stopping uses a full-gradient norm at epoch boundaries. A stationary neural point is not declared globally optimal. Quality uses repeat 0 and timing uses all repeats. Means/SD in tables reflect differences across seeded datasets; plot convergence curves use medians/IQR. Finite grids and one tuning instance per family limit the generality of the conclusions.
