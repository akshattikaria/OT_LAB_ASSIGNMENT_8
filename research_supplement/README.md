# Source-linked research extension - 6 November 2026

> Current completion status: original AI evidence is included, Q-FLAIR is verified, and public archival source-revision links are mapped in docs/HISTORY_LINKS.md. The six exact-policy limitations remain. Earlier dated statements below describe their original stage.


This extension adds executable experiments or controls for all **22** Chapter 6 research entries. It preserves the original A-J packages and their measurements. It contains **10 scoped source ports, four algorithm variants, two survey demonstrations and six mechanism-only controls**. None claims an entire paper or its reported performance has been reproduced.

A **source port** implements the declared small specialization of a paper's equations or author architecture; its scale, data and any omissions remain explicit. An **algorithm variant** changes a source strategy or policy. A **survey demonstration** implements representative families discussed by a survey. A **mechanism-only control** is our original related example, whose detailed published algorithm was unavailable. These categories must not be merged into a claim of 22 exact implementations.

Read [METHOD_COVERAGE.md](METHOD_COVERAGE.md) for the complete mapping. Machine-readable identities and scope are in [SOURCE_REGISTRY.json](SOURCE_REGISTRY.json). Source-document hashes and unsuccessful public access are recorded in `provenance/research_source_documents.json`; papers themselves are not redistributed. Author dataset provenance and licenses are in `data/`.

## Run and verify

From the project root, using the root Python 3.12 requirements:

```bash
python -m unittest research_supplement.test_methods -v
python -m research_supplement.audit
python -m research_supplement.run --out research_supplement/results-rerun
```

The retained `results/` folder is intentionally immutable. Use a new output folder for every repetition. A complete run executes 14 result groups and can take several minutes; `liver` and statevector training dominate. GCC with OpenMP is required for `spmv`; its binary is compiled into a temporary directory. No physical QPU, GPU cluster, Hadoop, radio or MPI installation is needed. All original runs used shared cloud CPUs and one BLAS thread, not the student's laptop. Native SpMV uses two threads; live HPO uses four; SVM+ search uses two. Thread counts refer to actual execution only in these stated studies.

For selected groups:

```bash
python -m research_supplement.run --groups qmt privacy_certificate --out research_supplement/results-selected
```

The audit checks the **retained** results, source links, certificates and units. It does not remeasure historical performance. The 20 tests independently check analytic derivatives, parameter/input shifts, a TT chain rule, a unitary dilation/postselection branch, complete finite privacy distributions, constrained parameter-gradient equivalence, norm-oracle certificates, implicit differentiation, SVM+ primal/dual feasibility, training-only preprocessing and live-search invariants. A passing finite test is not a universal theorem.

## Evidence and comparison limits

All starts, seeds, input/split identities, candidate budgets, logical payload units and raw trials are retained. Synthetic or finite cost models are labelled. Three or five seeds are descriptive; no significance or general superiority claim follows. Simulator time is not QPU time. Logical byte counts exclude protocols, basis/model transfers where separately reported, and hardware effects. Native SpMV uses a fixed method order; short shared-host timings may include order and scheduling effects. Live HPO wall time includes thread scheduling and controller overhead, and completion order can affect asynchronous decisions.

Some budgets differ by design. Implicit hypergradients use 19 linear solves while each grid/random/Sobol search uses 20 including the selected refit. Halving changes total training work. The SVM+ GA and random control each use 16 unique fits per seed. The strategy catalog is fully evaluated for the reference, so GA query counts are not total workflow savings. QML-Liver uses validation early stopping, resulting in unequal epochs; the architecture comparison reports both quality and actual training time.

Negative results are retained: TT parameter generation is worse here; regularized natural-gradient controls do not beat the exact-reference NG run; the liver hybrid loses two of three splits to logistic; negative-rate branches have little effect; all five strategy GA runs miss the finite optimum; nested optimization retains positive energy gaps. Measurement-temperature gains are limited to the tested synthetic cases.

## Corrections observed during this work

1. The initial scalar-output AdaFisher factor collapsed under min-max normalization, reducing its intended curvature information. The primary experiment was changed to three-class softmax with both nontrivial factors. The initial diagnostic is retained in `diagnostics/curvature_scalar_initial.json` and the first implementation remains in Git history. Printed factor weighting is distinguished from the author's current source code.
2. A liver counter labelled state evaluations counted batched calls rather than per-example circuits. The corrected output separately records batched statevector calls and circuit instances, including validation/test work. Epochs, quality and measured timings are unchanged; the earlier diagnostic remains in `diagnostics/liver_initial_counter.json`.
3. SVM+ initially saved insufficient fields for independently recomputing its primal certificate. The complete correcting coefficients, intercept, slack and hyperparameters were added, then the six searches were rerun. The earlier result remains in `diagnostics/svmplus_before_full_certificate.json`.

## Remaining exact-method gaps

PANA, PackStealLB, GSHetero, architecture-aware currying, OFLight and EAHP have explicit mechanism-only experiments. Public searches reached abstracts, inaccessible full texts or incomplete author repositories. Exact source policies are still needed to implement these six faithfully. **Strict paper-method coverage is therefore incomplete.** The extension proceeds without requiring an instructor conversation; it does not pretend that source access or full reproduction occurred.
