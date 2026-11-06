# Validation record

Date: 2026-10-31.

- Final test suite: 30 tests passed after the numerical-stability correction.
- All 270 main final states and every stored trace objective/gradient norm were re-evaluated against the exact saved input.
- All 64 tuning candidates were re-audited and the selected learning rates checked against the declared criterion.
- All 24 dataset hashes were checked. Test metrics and ridge reference solutions were independently recomputed.
- Every one of 90 method/problem/seed groups has exactly three timing repeats.
- Every stored true objective in 120 noisy trajectories was recomputed from its parameters.
- Summary values match a fresh summary of raw_runs.json.
- The final comparison/noise plots and the landscape/curvature figures were visually inspected.
- The earlier Track E ZIP hash remains unchanged.

The two-stage git history retains the original numerical defect and correction. These checks support specific properties; they do not prove absence of all bugs or a neural global optimum.

The demo CLI and an end-to-end reduced benchmark (two problems, one seed, one repeat, reduced budgets) completed successfully in separate temporary output directories. The main experiment evidence was preserved.
