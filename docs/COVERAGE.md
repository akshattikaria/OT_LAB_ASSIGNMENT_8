# Track A coverage and remaining work

| Required topic / technique | Code / evidence | Status |
|---|---|---|
| ML parameters, loss and L2 regularization | problems.py; supplementary foundations; report | Implemented |
| MSE, cross-entropy and hinge examples | supplement.foundations | Numerically demonstrated |
| L0/L1/L2 distinction and soft-threshold | supplement.foundations | Small numerical foundation example; full discrete selection belongs in B |
| GD, SGD, mini-batch SGD | FirstOrder and main benchmark | Implemented and compared |
| Momentum, Nesterov | FirstOrder; one/two-step regression tests | Implemented and compared |
| AdaGrad, RMSProp, Adam | FirstOrder; moment/bias-correction tests | Implemented and compared |
| Newton | optimizers.train; ridge and exponential fit | Implemented and compared |
| Gauss-Newton | residual/Jacobian formulation; two fit experiments | Implemented and compared |
| Backpropagation distinct from optimizer | MLP.grad; all-parameter finite differences | Implemented and checked |
| Fisher and empirical/expected distinction | Logistic.fisher / empirical_fisher; curvature experiment | Implemented and checked |
| Diagonal and low-rank curvature | curvature_experiment | Actual optimization demonstrations; small dense construction disclosed |
| Hessian-vector products | Logistic.hvp; HVP_CG | Matrix-free products and independent checks |
| Convex/strongly convex convergence | landscapes; analytic upper bounds | Experimentally checked under stated assumptions |
| Non-convex minima and saddle | double well and bounded-below saddle controls | Demonstrated; no global neural guarantee |
| Step size and optimizer tuning | independent seed 999 grids and rate sensitivity | All candidates retained |
| Noisy objectives / gradients | 120 seeded noisy-oracle trajectories | Implemented; variability recorded |
| L-BFGS, mentioned in PPT4 | SciPy L-BFGS-B ridge demonstration | Additional library experiment |
| GRNG / AdaFisher research spotlights | PPT1 slides 35 and 38 mention these | Pending source verification/reproduction; not claimed as implemented |
| Other research-only optimizer names | PPT1 research-reference slides | Literature/extension entries, not silently substituted for implemented methods |

The main experiment covers the explicit Track A core requirements. The broader assignment says every taught technique must be accounted for; this table preserves research reproduction gaps so the combined submission can resolve them accurately. It does not declare all Chapter 6 content complete.

Overall progress: Track E working prototype preserved; Track A core experiment implemented here. B-D and F-J remain. Public repository publication, full chat exports, a second AI-tool comparison and the rest of the genuine AI-failure log remain outstanding.
