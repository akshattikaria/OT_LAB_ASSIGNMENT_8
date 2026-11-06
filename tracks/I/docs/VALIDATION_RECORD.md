# Track I executed verification

Executed 2026-11-04 on the shared cloud Linux host. Main implementation was frozen in commit 8c1d83da4fc9d357cebf04a23c4496a070766d38. Exact hashes for common.py, circuits.py, learning.py and experiment.py are in results/environment.json; subsequent audit/report/test/documentation changes do not alter measured code.

## Main experiment

| Evidence | Actual retained result |
| --- | --- |
| Algorithm cases | 22: four Deutsch, four DJ, four BV, three QFT, three QPE, four toy Shor |
| Saved QPY circuits | 26: 22 algorithm circuits and four transpiled device circuits |
| Grover runs | 21 = seven sizes (2–8 qubits) × three marked-instance seeds |
| VQE | Three starts, 60 parameter-shift Adam updates, 541 circuit calls/start |
| QAOA | Six starts, p=1/2 over three seeds; 1,218 objective calls total and six final distribution checks |
| Annealing | Four 128-step schedules with dense reference; three separate classical Metropolis runs |
| Calibrated/ideal Aer rows | 24 = four programs × three seeds × two conditions |
| Aer emulated shots | 98,304 = 24 × 4,096; not physical-device measurements |
| Classifiers | 12 = two families × three data/split seeds × two kernels |
| Quantum overlap evaluations | 32,220 exact Statevector calls, 5,370 per quantum model |
| Data records | 60 train + 60 held-out per dataset/seed; exact indices/transforms retained |
| Kernel-shot sensitivity | 18 synthetic fixed-model test-kernel controls, not noisy training |

Algorithm histograms are classical Born samples from exact SDK probabilities, distinct from the Aer noise-study shot jobs. All probabilities, criteria, bit conventions, model parameters, native gates, raw shot counts, complete hybrid histories and timing components are preserved. No live QPU, runtime account, credentials or paid job was used.

The archived FakeManila snapshot date is **2024-05-27T15:27:23-03:00**. Its exact JSON files, source package version, hashes, coupling map and license are retained. The model approximates historical gate/thermal/readout errors; it is not current calibration or a complete device model. Paired ideal/noisy conditions use the same transpiled circuit.

## Tests and audit

**23 tests passed**, with actual output in docs/unit_test_output.txt. Tests include all one-bit Boolean functions, all eight promised two-bit DJ functions, all eight three-bit BV secrets, full Fourier matrices through four qubits, exact/off-grid phase estimation, Grover formulas/marks, modular unitarity, Shor outcome rejection, dense VQE/finite-difference gradients, annealing products, analytical feature amplitudes/kernels, no-leakage generation and JSON metadata from the real pinned fake-backend API.

The final retained-data audit passed **1,803 tracked checks/matches**. It:

- verifies every raw-evidence hash, measured source hash and earlier C/D/calibration input identity;
- reloads QPY circuits and checks distributions against independent Fourier, phase, promise, amplification and modular-order mathematics;
- recomputes **1,401 retained hybrid expectations** and all final QAOA metrics, variational bounds and call budgets;
- recomputes dense annealing references/fidelities and the three seeded classical annealing trajectories;
- checks **86,400 kernel entries** against independent analytical state amplitudes and RBF formulas;
- manually reconstructs **720 held-out classifier predictions** from stored support vectors/dual coefficients/bias, with no refit;
- verifies resource counts, timing boundaries, synthetic shot predictions and all **24 seeded Aer noise/control runs by exact count replay** using pinned versions.

The expectation count covers saved objective histories, not every unsaved gradient-shift result; VQE's complete circuit-call count is independently checked against its update structure. Main query/accuracy/timing results are never replaced during auditing. Three data/split seeds are not described as repeated timing trials on an identical dataset. Shot-only confidence intervals do not account for calibration uncertainty.

## Public CLI smoke and development evidence

The final public CLI ran a separate one-seed protocol with 256 shots/condition, 12/12 classifier split, ten VQE updates, 60 QAOA objective calls and Grover sizes 2/4/6. Its audit passed **335 checks**, including 22 algorithm cases, three Grover runs, four classifiers, 420 overlaps, 1,152 kernel entries, 48 held-out predictions and all eight seeded Aer rows replayed. Full smoke outputs and actual logs are under validation/cli_smoke and validation/cli_smoke*; they are excluded from main conclusions.

The initial partial pilot stopped after eight Aer rows because a Rust EdgeList could not be serialized to JSON. Its actual diagnostic/minimal reproduction, original source and partial outputs remain explicitly labeled. The fix converts coupling edges to native lists and has an integration regression. An intermediate corrected pilot completed before the final resource metadata was frozen; its hashes are historical. No incomplete pilot contributes to the main report. See AI_FAILURE_LOG.md and bundled history.

## Report and package

All four scientific plots and two circuit diagrams were visually reviewed. The QML time legend was removed from the panel where it covered data; shared color meanings remain in the accuracy legend. The offline HTML contains **six embedded valid PNGs and ten tables**, with no external image/script requirement. Query counts versus measured CPU time, exact simulation versus emulated shots, and historical C/D evidence versus fresh I execution are distinguished.

Earlier A–H archive identities are rechecked before delivery and remain unchanged. Final packaging verifies the file manifest, complete Git bundle and ZIP integrity. No public repository, independent second-AI comparison or full chat export is claimed. Negative QML results, local optimizer limits and Shor failure controls remain visible.
