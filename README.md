# Track G: xv6 Operating-System Optimization

Prepared for **Akshat Tikaria, roll 241070005**. Optimization Techniques, Assignment 8.

Open **results/report.html** after extracting this package. The offline report includes three figures, all four configurations, every repetition, correctness evidence and limitations. Source, the applicable xv6 patch, raw QEMU UART logs, tests, viva notes and local Git history are included. Earlier E/A/B/C/D/F packages remain separate and unchanged.

## Implemented and measured

1. Per-CPU physical-page free lists with local-first allocation and stealing of at most 32 pages on an empty list. This targets allocator lock contention.
2. A 13-bucket buffer-lookup hash index. It retains the global cache lock, the original 30-buffer capacity, LRU replacement, buffer sleep locks and logging pins. This targets lookup comparisons rather than changing cache capacity or claiming a lock-free design.

New guest programs gbench and gcheck run inside the real xv6 RISC-V kernel under QEMU. The baseline disables both features but keeps the same instrumentation/check interfaces. Allocator-only, hash-only and combined variants isolate their effects. A pristine MIT kernel is separately validated for provenance and correctness.

All **72 main measurements** were executed: four configurations × six workloads × three repetitions, using **12 fresh boots**. The pristine kernel and all four instrumented configurations each passed the full **74-test upstream usertests suite**, including slow tests. Custom checks passed before and after each configuration's suite and each benchmark boot. Every workload verifies data/status and allocator/cache invariants. There are **14 additional host tests**; these are distinct from guest usertests.

## Results and limits

The per-CPU allocator's page workload reduced median failed allocator exchanges from **182,069 to zero**, but median elapsed guest time increased from **0.39190 to 4.68213 seconds: 11.95× slower**. Fork and pipe workloads also slowed. Reducing a contention counter did not improve elapsed performance here; the cause of the large regression is not isolated. The report retains these results.

| Cache workload | Baseline probes/lookup | Hash-only probes/lookup | Probe reduction | Hash-only elapsed ratio |
| --- | --- | --- | --- | --- |
| Hot sequential stream | 8.132 | 2.270 | 72.09% | 1.036× |
| Two interleaved hot streams | 4.881 | 2.603 | 46.68% | 0.985× |
| Over-capacity scan | 15.148 | 2.182 | 85.60% | 1.111× |

Elapsed ratio is baseline median seconds divided by variant median seconds; below one is slower. The miss fractions were identical across configurations: zero for the two hot cases and about 47.16% for the scan, which also includes metadata lookups. Fewer probes do not imply fewer disk reads. All raw repetitions and min/max time spreads are retained; three repeats do not establish statistical significance.

These are **QEMU TCG emulated guest measurements on a shared cloud host**, not timings on Akshat's i3 laptop. Each guest used 3 vCPUs and 128 MiB RAM. Guest r_time deltas are divided by the saved QEMU device tree's 10,000,000 Hz frequency; they are not retired instructions or native hardware cycles. Instrumentation and observation overhead remain included. Full usertests host durations are validation diagnostics and are not performance comparisons.

## Setup and commands

Recorded environment: Linux x86-64, Python 3.12.14, QEMU 8.2.2, RISC-V GCC 13.3.0, binutils 2.42, NumPy 2.3.5 and Matplotlib 3.10.8. Linux or WSL2 is recommended. No GPU or paid service is needed. The guest RAM is small enough for an 8 GB laptop; full suites may take several minutes per configuration.

Typical Ubuntu/WSL setup:

```bash
sudo apt-get update
sudo apt-get install build-essential git qemu-system-misc gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu
python -m pip install -r requirements.txt
```

Run these from the extracted project directory:

```bash
python -m unittest discover -s tests -v
python -m oslab audit results
```

The audit requires only Python for retained evidence. It passed **532 checked assertions/matches**, verifying every measurement against raw UART, work units, flags, clock conversion, source/UART hashes, validated kernel hashes and complete test sets. It does not rerun or replace timings.

Execute a small functional trial:

```bash
python -m oslab benchmark --out results-quick --repeats 1 --cpus 3 --scale 0.0025
python -m oslab audit results-quick
```

Tiny timings are not performance evidence. The retained CLI smoke under validation/cli_smoke contains 24 such measurements across four boots and a separate audit.

Reproduce the full kernel validation and recorded benchmark protocol:

```bash
python -m oslab validate --out validation-rerun --cpus 3
python -m oslab benchmark --out results-rerun --repeats 3 --cpus 3
python -m oslab audit results-rerun
```

The benchmark refuses nonempty output directories. The validator writes/replaces its chosen output logs; use a new folder to preserve evidence. Builds are made in isolated build/ copies; vendor/xv6 and xv6 remain source-only. Each boot copies a fresh filesystem image. Do not build directly in the delivered source directories if you want source hashes to keep matching the saved experiment.

The audit compares against delivered validation/ records for the same source, not automatically against a newly named validation-rerun folder. If modifying native source, retain the original package and run validate with a new project's empty validation/ directory before generating its new results. The report similarly uses that project's validation/ records. Changing just host reports does not change kernel source identity.

On this managed host, packages were downloaded from the configured signed Ubuntu snapshot and unpacked into an isolated prefix without a global upgrade. docs/toolchain_packages.json lists the exact 42 package archives and hashes. The large toolchain is excluded from delivery. A compatible toolchain on PATH is enough; optionally pass `--toolchain /absolute/prefix` when a prefix contains usr/bin and usr/lib/x86_64-linux-gnu. Cross-version results may differ.

Regenerate the offline report without rerunning measurements:

```bash
python -m oslab report results
```

## Patch and interactive guest

Upstream: MIT xv6-riscv, branch riscv, pinned commit **e93dabeb98431235c6e1a101cb96c73c923fdbc4**. UPSTREAM.json contains the exact tree and all 82 verified Git blob hashes. Both snapshots retain the MIT LICENSE. The patch adds/changes 15 files and reconstructs the 85-file modified source tree; it has been applied to a clean pristine copy and compared byte-for-byte.

To apply it to a separate clean checkout of that exact upstream commit, run from that checkout:

```bash
git apply /absolute/path/to/patches/track_g.patch
make TOOLPREFIX=riscv64-linux-gnu- KMEM_PERCPU=1 HASHBCACHE=1 CPUS=3 qemu
```

Alternatively copy the supplied xv6 directory to a separate working directory and run the same make command there. To change flags in a reused working tree, run `make clean` first: make does not automatically rebuild every object solely because a command-line macro changed. The host workflow already uses separate directories for every variant. Exit make qemu with Ctrl-A then X.

At the guest shell:

```text
gcheck
gbench pages 800
gbench fork 200
gbench pipes 8000
gbench hotseq 8000
gbench hotrand 8000
gbench scan 8000
usertests
```

The host workflow uses a headless, network-free guest and records all UART output automatically. Intentional bad-memory tests can print traps; diskfull/outofinodes print expected allocation failures. Read the complete test result rather than mistaking expected negative-test output for a successful or failed suite.

## Files and evidence

| Path | Purpose |
| --- | --- |
| vendor/xv6/, UPSTREAM.json | Exact pristine MIT source and provenance |
| xv6/kernel/kalloc.c | Per-CPU allocation, batch stealing and free-list checker |
| xv6/kernel/bio.c, buf.h | Hash lookup with original global locking/LRU and cache checker |
| xv6/kernel/spinlock.*, labstats.h, sysproc.c | Consistent counters, statistics/check interfaces and bounded copyout |
| xv6/user/gbench.c, gcheck.c | Six real guest workloads and custom correctness checks |
| patches/track_g.patch | Applicable diff against the pinned pristine tree |
| oslab/runtime.py, experiment.py | Isolated real builds, QEMU control, FDT clock, deterministic protocol |
| oslab/report.py, audit.py | Offline report/figures and retained-evidence audit |
| results/raw_runs.json, uart/ | All 72 main measurements and full serial output |
| results/builds.json, build_logs/ | Build flags, kernel/filesystem hashes and make output |
| results/protocol.json, environment.json, device_tree/ | Budgets, seeds, configuration, host/tool versions and clock evidence |
| validation/kernel_validation.json, uart/ | Four full guest test suites, six smoke workloads each, before/after gcheck |
| validation/development/ | Actual pristine full suite, initial boot/builds and earlier baseline development logs |
| validation/cli_smoke/ | Separate public-CLI functional replay, excluded from main timing analysis |
| docs/FORMULATION.md, VIVA_GUIDE.md | Objectives, invariants, trade-offs and explanation practice |
| docs/COVERAGE.md, VALIDATION_RECORD.md | Requirement mapping and checks actually run |
| docs/AI_FAILURE_LOG.md, initial_copyout_build_failure.log | Actual rejected AI code, fix and regression evidence |
| prompts/G/, docs/COMMIT_INDEX.md, history.bundle | Actual excerpts and complete local code history |

FILE_SHA256.json covers delivered source, data, documentation and report files, excluding itself and history.bundle to avoid recursive identity. Executables, filesystem images and large toolchain packages are rebuilt from saved sources rather than shipped. Recover local history with `git clone history.bundle track-g-history`.

## AI disclosure and remaining assignment work

| Tool | Session-reported model | Date | Use |
| --- | --- | --- | --- |
| ChatGPT / Codex | gpt-6.1-sol | 2026-11-04 | G formulation, kernel features, debugging, toolchain setup, guest/host checks, experiments and documentation |

All substantial implementation and documentation here are AI-assisted; no manual student correction is claimed. ChatGPT and Codex are not counted as two independent AI tools. The original code assumed an outdated four-argument copyout signature; the actual pinned API needs five arguments including process size. Compilation caught it, the fix uses p->sz, and gcheck tests an invalid user destination. Original/fix commits and the real failure log are retained. Earlier A/B/D already document three corrected cases; F adds another. Prompt excerpts are not full conversation exports.

The two kernel features and six workloads cover Track G's requested experiment scope. Formal race proof, KCSAN and an official MIT lock-lab grading run were not performed. Next is **Track H: DBMS optimization**, followed by I/J. Overall integration, unresolved research reproductions, full chat exports, an independent two-AI-tool comparison, the required public repository and the live demonstration remain pending. No public repository was configured or published here.

## Primary references

- Supplied Assignment 8, Track G, and the supplied Chapter 6 parallelism/strategy material; acknowledged rather than redistributed.
- [Official MIT xv6 source and license](https://github.com/mit-pdos/xv6-riscv), [pinned revision](https://github.com/mit-pdos/xv6-riscv/commit/e93dabeb98431235c6e1a101cb96c73c923fdbc4).
- [MIT tool setup](https://pdos.csail.mit.edu/6.1810/2025/tools.html) and [MIT lock lab concepts](https://pdos.csail.mit.edu/6.1810/2025/labs/lock.html).

Public references accessed 2026-11-04. The numerical results are this project's own QEMU measurements, not reused MIT example results.
