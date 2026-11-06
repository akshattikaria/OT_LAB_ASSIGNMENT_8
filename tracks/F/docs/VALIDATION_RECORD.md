# Track F validation

Date: 2026-11-04. Python 3.12.14, GCC 13.3.0 (Ubuntu), Linux x86-64. Actual toolchain, platform, CPU affinity and quota are in results/environment.json. Native measurements run serially in this shared cloud workspace, not on the student's laptop. No GPU, parallel or hardware-instruction-counter claim is made.

## Tests

Command: `python -m unittest discover -s tests -v`.

Final result: **29 tests passed**. Actual output is in unit_test_output.txt. The tests include:

- Syntax/precedence, lexical errors, immutable/defined names, literal/argument ranges and SSA validation.
- Independent AST versus register-IR execution, including modulo overflow and masked shift amounts.
- Constant chains, commutative-only CSE, chained aliases and transitive dead dependencies.
- Strength reduction for every power of two from 2^0 through 2^63, including overflow inputs.
- Full-state DP versus every 24-order oracle on all four families; subset-only merging is explicitly avoided.
- 50 random source programs × 24 orders × five vectors = **6,000 differential cases**, including high-bit, maximum and random inputs.
- Fresh native O0/O2 output comparisons for baseline and all 24 orders on an additional random program, wrapper validation, checksum equality and machine-code inspection.
- Instrumented greedy search requires ten actual candidate transformations, matching reported work.

## Main recorded benchmark

Main raw data was produced with:

```bash
python -u -c 'from toycc.experiment import run_benchmark; run_benchmark("results")'
python -m toycc report results
python -m toycc audit results
```

Default protocol: four families, seeds 0–4; eight compiler variants; three Python compiler repeats; five runtime repeats; 100,000 native calls/timing. All eight variants are timed at O0, baseline/DP additionally at O2. Warmup, varying inputs, checksums and within-comparison iteration counts are controlled. Trial order is shuffled with fixed seeds. No result was selected as a best run or replaced by theoretical timing.

| Retained main evidence | Count |
| --- | --- |
| Exact toy sources | 20 |
| Final compiled IR artifacts | 160 |
| Python compilation timing records | 480 |
| Native benchmark builds | 40 |
| Native symbol/disassembly records | 320 |
| Native runtime timing records | 1,000 |
| Complete pass-order oracle rows | 480 |
| Input/expected-output vectors | 660 |
| IR output comparisons during benchmark | 5,280 |
| Native output comparisons during benchmark | 10,560 |
| Native driver reference checks during benchmark | 320 |
| Source/vector files with input hashes | 40 |

The benchmark uses actual C execution, not sleep or an instruction-count-to-time conversion. IR cost weights are explicitly synthetic and are not used as runtime measurements. Static native instructions and symbol code bytes are separately measured from actual compiled artifacts.

## Retained-data audit

Result: **passed; 24,400 comparisons**, machine-readable in results/audit.json.

The audit verifies every input hash, reevaluates 5,280 IR outputs, regenerates saved C from each IR set, freshly compiles both levels and checks 10,560 native outputs and 320 native driver checks. It reenumerates all 480 pass orders and verifies every finite score optimum; saved disassembly instruction counts are independently parsed. It also checks all 1,000 timing record iteration counts and same-seed checksum equality across variants and native levels. Fresh builds validate outputs without replacing the original timing data. Saved symbol sizes remain explicitly host/compiler-specific.

DP beats greedy's modeled cost on ten programs and matches every oracle. This does not predict all native results: mixed programs average 0.889 O2 speedup and about 2.45 times baseline native function bytes. Those negative outcomes remain in all raw/report data. Strength-only and individual fixed-order slowdowns are retained as well.

## Public CLI and report

`python -m toycc demo` returned baseline 15 instructions/score 27, DP six instructions/score six, result 48 at (1,2,3). `python -m toycc compile examples/demo.toy --method dp_order` generated valid C at a separate output location.

A preliminary four-program protocol smoke run verified native inspection at both levels. The full public CLI was then run from a fresh output directory:

```bash
python -m toycc benchmark --out /workspace/scratch/f3cd84c5991c/tmp/trackf-cli-smoke --seeds 0 --repeats 1 --iterations 1000 --compile-repeats 1
```

It completed and generated its report. It did not overwrite main data. Main and smoke reports contain six embedded scientific charts with no external image dependencies. Key IR, native timing, pass-order and compile-time plots were inspected for readable labels and faithful presentation; O0/O2 panels intentionally retain distinct axis scales.

The genuine redundant greedy-transformation defect was reproduced and corrected before the benchmark, with observations/history/regression retained. No manual student correction or second independent AI-tool contribution is claimed. Prior A/B/C/D/E archives were hash-checked and unchanged. A final file manifest, archive integrity check and complete local history bundle accompany delivery.

## Limits

Straight-line immutable arithmetic is the supported language. Individual pass arguments rely on pure total uint64 semantics; no general compiler or branch/loop proof is claimed. A few generated programs and repeats on shared hardware do not establish universal performance or statistical significance. Native host optimization can dominate the pedagogical passes, and a finite score optimum can produce slower/larger target code. Outstanding assignment work is listed in COVERAGE.md.
