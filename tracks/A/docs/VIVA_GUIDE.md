# Track A viva: concise conceptual answers

**What did you compare?** Eight gradient optimizers on ridge regression and a small neural classifier, plus Newton/Gauss-Newton on suitable residual problems.

**What is being optimized?** Real model parameters that minimize a defined training loss with an L2 penalty. The neural loss uses cross-entropy; ridge uses half mean squared error.

**GD vs SGD vs mini-batch?** All data, one sample, or a small group for each gradient update. Smaller batches give more frequent but noisier updates. One epoch processes the training set once.

**Momentum vs Nesterov?** Momentum remembers a velocity. Nesterov computes its next gradient at a point predicted using that velocity, so it can correct the direction earlier.

**AdaGrad vs RMSProp?** AdaGrad accumulates every squared gradient; its denominator keeps growing. RMSProp uses a moving average and forgets older gradients.

**What does Adam add?** A first-moment estimate, a squared-gradient estimate, and bias correction for their zero initialization. It scales each coordinate's step.

**Is backpropagation an optimizer?** No. It applies the chain rule to compute gradients through the network. GD/Adam/etc. use the resulting gradients to update parameters.

**Newton vs Gauss-Newton?** Newton uses the exact Hessian. Gauss-Newton approximates a least-squares Hessian by J-transpose-J, omitting residual-weighted second derivatives. They coincide on linear ridge residuals.

**Why use damping and line search?** Indefinite curvature can produce an uphill step. Shifting the matrix and checking Armijo decrease safeguards the update. Those safeguards are disclosed as part of our methods.

**What is a Hessian-vector product?** H multiplied by a chosen direction, computed without first building every entry of H. Conjugate gradient can use these products to solve a Newton system.

**What is Fisher information here?** Expected score-gradient curvature under the model. For binary logistic cross-entropy it equals the unregularized Hessian. An empirical outer product of observed-label gradients is generally a different matrix.

**What does convexity guarantee?** Any local minimum of a convex function is global. Convergence rates also need assumptions such as smoothness and a suitable step. Strong convexity permits a geometric rate under the stated conditions.

**What is a saddle?** A stationary point with uphill and downhill directions. Our saddle has both positive and negative Hessian eigenvalues. Gradient zero does not establish a minimum.

**How was the comparison kept fair?** Same data, start and epoch limit per problem; four rates per first-order method on a separate tuning instance; test data unused for tuning; work counts and runtime reported alongside loss.

**Are epochs equal computation?** No. SGD makes many updates, Newton constructs curvature, and diagnostic costs matter. We report those differences rather than interpreting iteration count alone as speed.

**How did you check correctness?** Finite differences for gradients/Hessians, all neural parameters, explicit update values, independent least-squares references, adversarial result checks and a regression test for an actual numerical bug.

**What is not proved?** A neural global optimum, general optimizer superiority, real-data performance, or scalability to large models. All tested datasets are synthetic.
