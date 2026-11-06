# Track F: Compiler Optimization

Prepared for Akshat Tikaria, roll number **241070005**. Optimization Techniques, Assignment 8.

Open **results/report.html** after extraction for the offline report and six embedded charts. Source, inputs, generated IR/C, disassembly, measurements, tests, mathematical explanations, viva notes and local history are included. Earlier E/A/B/C/D packages remain separate.

## Implemented

- Own lexer, precedence parser and immutable three-address SSA intermediate representation for a small unsigned arithmetic language.
- Four passes: constant folding/propagation, common-subexpression elimination, dead-code elimination and strength reduction.
- A compiler decision formulated as minimizing weighted IR cost over the four-pass order, solved by stateful dynamic programming and compared with greedy, a fixed order and all 24 permutations.
- Register-IR execution, independent AST evaluation and C generation; real GCC native builds at O0 and O2.
- Measured IR/native instruction counts, function source/native code sizes, native runtime and Python/native compile time.

This is a pure straight-line arithmetic compiler, not a production C compiler, LLVM/GCC plugin or loop optimizer. uint64 operations wrap modulo 2^64 and shifts mask their count to 0–63. These declared semantics avoid signed-overflow and floating-point reassociation issues.

## Run

Recorded environment: Python 3.12.14, GCC 13.3.0, Linux x86-64. Install NumPy/Matplotlib for reports. Native tests/experiments require a GCC- or Clang-compatible `cc`, plus `nm` and `objdump`; Linux or WSL is recommended. No GPU or paid service is required.

From the extracted folder:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m toycc demo
```

Compile the supplied example to a new C translation-unit file:

```bash
python -m toycc compile examples/demo.toy --method dp_order --out generated_demo.c
```

The generated C defines callable functions and its benchmark driver; it is a library translation unit rather than a standalone executable with main. The benchmark command compiles and runs it automatically.

Full recorded protocol:

```bash
python -m toycc benchmark --out results-rerun --seeds 0 1 2 3 4 --repeats 5 --iterations 100000 --compile-repeats 3
python -m toycc audit results-rerun
```

Small functional run, suitable for checking the workflow on a low-spec laptop:

```bash
python -m toycc benchmark --out results-quick --seeds 0 --repeats 1 --iterations 1000 --compile-repeats 1
```

Tiny smoke timings are not suitable for performance conclusions. Nonempty benchmark output folders and existing compile-output files are refused. To regenerate the report without remeasuring:

```bash
python -m toycc report results
```

The audit recompiles C to check outputs; it does not replace the retained timing results. Native code sizes/times depend on the actual compiler and host. Recorded reports remain readable without any compiler installed.

## Results and verification

- **29 tests passed**, including 6,000 all-pass-order differential cases across 50 random programs and boundary/random inputs, plus native O0/O2 comparisons.
- Audit passed **24,400 comparisons**, including 5,280 saved IR output checks, 10,560 fresh native output checks, 320 driver checks and all 480 pass-order references.
- 20 synthetic programs in four families; eight compiler variants; 480 Python compilation timings, 40 native builds, 320 native function metric records and 1,000 native runtime timings.
- DP matched the exhaustive optimum for the declared weighted IR cost on all 20 programs; it strictly improved on greedy's score on ten. The certificate covers four passes used once, not native-runtime or general compiler optimality.

| Family | Mean DP IR-count reduction | Mean native O0 speedup | Mean native O2 speedup |
| --- | --- | --- | --- |
| Constant chain | 49.49% | 1.70× | 1.015× |
| Redundant expressions | 70.63% | 2.35× | 1.022× |
| Dead-code-heavy | 86.27% | 3.70× | 1.009× |
| Mixed | 77.28% | 3.31× | 0.889× |

Each speedup is an arithmetic mean of within-program median-time ratios; all repeats/seeds are retained. O0 isolates teaching-pass effects and does not establish an advantage over an optimizing host compiler. At O2, gains are small or negative; mixed-program DP functions also averaged about **2.45× the baseline native code bytes**. The IR cost model is not a CPU-cycle oracle. Strength reduction alone averaged below 1× at O0, demonstrating why pass interactions and measurement matter.

For examples/demo.toy, the demo reduces the IR body from 15 instructions/score 27 to six instructions/score six. Both evaluate to 48 at inputs (1,2,3). The IR body count excludes the final return/driver, and straight-line code executes every retained instruction once. Static disassembly counts are not retired hardware-instruction counts.

## Files

| Path | Purpose |
| --- | --- |
| toycc/frontend.py | Lexer, AST, parser and independent source interpreter |
| toycc/ir.py | SSA validation/lowering, register interpreter and declared cost model |
| toycc/passes.py | Four explicit transformations and deterministic canonicalization |
| toycc/search.py | Fixed order, greedy, full-state memoized DP and exhaustive reference |
| toycc/native.py | C generation, real builds, symbol sizes and saved disassembly |
| toycc/programs.py | Synthetic families, boundary vectors and random-program generator |
| toycc/experiment.py | Reproducible protocol, checksums, timing and all variants |
| toycc/report.py, toycc/audit.py | Report and retained-result audit |
| examples/demo.toy | Small inspectable compiler example |
| tests/test_compiler.py | 29 semantic, optimization, search and native checks |
| results/sources/, validation_inputs/ | Exact toy sources and hex-encoded uint64 vectors/results |
| results/ir/, generated/, assembly/ | Every compiled IR, combined C unit and native disassembly |
| results/*_runs.json | All compile/runtime measurements and checksums |
| results/pass_search.json | Every 24-order oracle and search work count |
| results/native_builds.json, native_function_stats.json | Actual compiler flags/times, symbol sizes and instruction counts |
| results/protocol.json, environment.json, input_sha256.json | Settings, host and input integrity |
| docs/FORMULATION.md, VIVA_GUIDE.md | Mathematics, soundness assumptions and explanations |
| docs/COVERAGE.md, VALIDATION_RECORD.md | Requirement mapping and actual checks |
| docs/AI_FAILURE_LOG.md | Observed redundant greedy work, fix and regression |
| prompts/F/001_continue.md | Actual prompt/response excerpts |
| history.bundle, docs/COMMIT_INDEX.md | Original/fixed code and complete local history |

Compiled shared libraries are excluded from delivery and rebuilt from saved C. FILE_SHA256.json checks delivered source/data/report/documentation; it excludes itself and history.bundle to avoid recursion. Recover history using `git clone history.bundle track-f-history`.

## AI disclosure and next work

| Tool | Session-reported model | Date | Use |
| --- | --- | --- | --- |
| ChatGPT | gpt-6.1-sol | 2026-11-04 | F formulation, compiler, tests, debugging, native experiments, audit and report |
| ChatGPT | gpt-6.1-sol | 2026-11-03 | Earlier B/C/D work |
| ChatGPT | gpt-6.1-sol | 2026-10-31 | Earlier A work and planning |
| ChatGPT | gpt-6-astra | 2026-10-31 | Earlier E case study |

All implementation is AI-assisted; no manual student correction or second independent AI-tool comparison is claimed. GCC supplies native code compilation, nm/objdump supply binary inspection, NumPy supplies report statistics and Matplotlib draws plots. The lexer/parser, SSA, passes, cost model, search and checker are explicit code here; LLVM is a conceptual reference rather than a dependency.

A genuine pre-benchmark implementation defect made greedy compute each candidate transformation twice while reporting ten transitions. Instrumentation measured twenty actual calls; reuse fixed it, with original/fix commits and a regression. Earlier A/B/D already contain three other documented corrected cases. None of the negative runtime/code-size results is mislabeled as a code bug.

Next is **Track G: xv6 OS optimization**, followed by H/I/J. Full assignment integration, unresolved research-paper reproductions, full chat exports, second-tool comparison, public repository and live demonstration remain pending. No public repository was configured or published here.

## Primary references

- Supplied Assignment 8 Track F and Chapter 6 DP/strategy-selection material, acknowledged rather than redistributed.
- [LLVM transformations](https://llvm.org/docs/Passes.html), [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html), [GCC function attributes](https://gcc.gnu.org/onlinedocs/gcc/Common-Function-Attributes.html).
- Public sources checked 2026-11-04. All numeric results come from this package's experiments.
