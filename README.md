# Track A: Continuous Optimization

Working core experiments for Assignment 8, Track A. Open **`results/report.html`** after extraction to read the report and charts without installing anything. The report is self-contained and works offline.

This package covers continuous optimization. The earlier Track E EV scheduler remains a separate preserved package. This is not the combined ten-track submission.

## Implemented methods and experiments

- GD, single-sample SGD, mini-batch SGD, Momentum, Nesterov, AdaGrad, RMSProp and Adam.
- Safeguarded Newton and Gauss-Newton, including a nonlinear exponential-fit comparison.
- Manual backpropagation in a 2-8-1 neural network, independently checked by finite differences.
- Full Fisher, diagonal and low-rank curvature, and matrix-free Hessian-vector products with conjugate gradient.
- Convex, strongly convex, local-minimum and saddle controls, with applicable convergence bounds checked.
- Independent learning-rate tuning, unstable-rate controls and repeated noisy-oracle experiments.
- Loss/regularization examples and a separate SciPy L-BFGS-B demonstration.

Research-paper spotlights such as GRNG and AdaFisher are explicitly marked as pending reproduction in `docs/COVERAGE.md`; they are not mislabelled as implemented algorithms.

## Run

The measured run used Python 3.12.14. Use Python 3.12, preferably in a virtual environment, and run from this extracted folder:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m contopt demo
```

Small smoke benchmark:

```bash
python -m contopt benchmark --out results-quick --seeds 0 --repeats 1 --ridge-epochs 8 --mlp-epochs 12 --n 64
```

Full recorded protocol:

```bash
python -m contopt benchmark --out results-rerun --seeds 0 1 2 3 4 --repeats 3 --ridge-epochs 35 --mlp-epochs 80 --n 256
```

Regenerate figures/report from stored measurements:

```bash
python -m contopt report results
```

Choose new output directories; nonempty folders are refused. Seeds reproduce arrays and sampling sequences with the pinned environment. Runtime, floating-point rounding and library stopping details can vary by system.

## Recorded results and checks

- **270 main training runs:** ten ridge methods and eight neural methods, five data seeds and three timing repeats.
- **64 tuning runs:** four rates for each of eight first-order methods on two independent tuning instances, seed 999.
- **120 noisy-oracle trajectories:** four methods, three noise levels, ten seeds, 800 gradient queries each.
- **30 tests passed**, including all 33 neural derivatives, explicit update values, closed-form references and numerical-stability regression checks.
- Newton and Gauss-Newton reach the ridge optimum in one update on each evaluation instance; this is expected for this quadratic residual model.
- The largest normalized final-gradient check error across all main runs is approximately **1.76e-11**.
- A genuine numerical cancellation defect was found, fixed, tested and recorded in `docs/AI_FAILURE_LOG.md` with original and corrected commits.

All data are synthetic. Neural accuracy comparisons are limited to this small XOR task; they do not establish a general optimizer ranking. The report states work, timing and memory-accounting limitations.

## File map

| Path | Purpose |
|---|---|
| `contopt/problems.py` | Losses, models, analytic gradients, Hessians and data generation |
| `contopt/optimizers.py` | Explicit update rules, safeguards, stopping and work counters |
| `contopt/checks.py` | Numerical derivative checks and independent final-state audit |
| `contopt/experiment.py` | Independent tuning, repeated benchmark and summaries |
| `contopt/supplement.py` | Landscapes, noise, Fisher/HVP, nonlinear fit and L-BFGS |
| `contopt/report.py` | Figures and self-contained HTML/Markdown reports |
| `tests/test_continuous.py` | Correctness and adversarial checks |
| `results/datasets/` | Exact input arrays and metadata, including initial parameters |
| `results/raw_runs.json` | Main training traces, counters, audits and timing repeats |
| `results/tuning_*.json` | Every tuning candidate and selected setting |
| `results/supplementary.json` | Complete supplementary experimental evidence |
| `results/runs.csv` | Flat main results table |
| `results/dataset_sha256.json` | Dataset integrity hashes |
| `results/protocol.json`, `environment.json` | Conditions and actual runtime environment |
| `docs/FORMULATION.md`, `COVERAGE.md` | Mathematics and assignment mapping |
| `docs/VIVA_GUIDE.md` | Concise conceptual explanation |
| `prompts/A/001_move_to_next.md` | Actual user request, response excerpts and verification |

## AI tools register

| Tool | Session-reported model | Date | Tracks | Work |
|---|---|---|---|---|
| ChatGPT | `gpt-6.1-sol` | 2026-10-31 | A | Planning, code generation, derivative checks, benchmarking, debugging, report and documentation |
| ChatGPT | `gpt-6-astra` | 2026-10-31 | E, prior context | Earlier EV case-study implementation; no claim that it produced the Track A code |
| ChatGPT | `gpt-6.1-sol` | 2026-10-31 | A-J planning | Earlier Chapter 6 reading and coverage mapping |

Earlier assignment-overview assistance also used ChatGPT; exact versions not exposed in those turns are not guessed. All code here is AI-assisted; no manual student edits are claimed. NumPy, SciPy and Matplotlib are acknowledged external libraries. The main first-order updates and Newton/Gauss-Newton loops are explicit implementations; reference least-squares and L-BFGS experiments use SciPy.

One genuine AI-generated numerical defect has been documented in this track. Two further genuine cases are still needed for the assignment-wide minimum of three. The second independent AI-tool comparison, full conversation exports/screenshots, remaining tracks and public GitHub publication are still outstanding.

## History

`history.bundle` preserves the local AI-assisted commits, including the original numerical defect and its correction. Recover a repository with `git clone history.bundle track-a-history`. See `docs/COMMIT_INDEX.md`. No remote repository was selected or published in this milestone.

## Sources

- Supplied Assignment 8, Track A and Section 5; Chapter 6 PPT1 and PPT4. Lecture files are acknowledged, not redistributed.
- Kingma and Ba, [Adam: A Method for Stochastic Optimization](https://arxiv.org/abs/1412.6980).
- Goodfellow, Bengio and Courville, [Deep Feedforward Networks](https://www.deeplearningbook.org/contents/mlp.html), including backpropagation.
- SciPy [least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html) and [L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html) documentation, accessed 2026-10-31. Installed versions are pinned and recorded.
