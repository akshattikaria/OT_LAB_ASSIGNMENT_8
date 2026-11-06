# Track G validation record

Executed 2026-11-04 in the shared Linux cloud workspace. These are actual build/QEMU results, not planned checks. Native source was frozen at commit 4adc2fae0483c106aa8c9eec6c3b98d864dd1766 and has SHA256 ec069d60d2808f53d2c17f2ee9fc04e9c9a2a87d8491162ba4e93cd2055847e4. Later revisions affect host checking/reporting and documentation only.

## Real kernel runs

| Configuration | Guest CPUs | Full upstream named tests | Before/after gcheck | Six workload smoke tests |
| --- | --- | --- | --- | --- |
| Pristine MIT kernel | 3 | 74, PASS | Not added to pristine source | Not added to pristine source |
| Instrumented baseline | 3 | 74, PASS | PASS | PASS |
| Per-CPU allocator only | 3 | 74, PASS | PASS | PASS |
| Hash lookup only | 3 | 74, PASS | PASS | PASS |
| Combined features | 3 | 74, PASS | PASS | PASS |

The five cited full suites comprise **370 named guest-test executions**. Each includes slowtests, rather than only the quick suite. validation/kernel_validation.json lists the exact test names, source/kernel identity, commands and UART paths for the four configurations. validation/development/pristine_usertests.log is the pristine full run. An older development baseline full run is also retained, but is not added to the cited 370 count or performance dataset.

All test names in each instrumented run match the pristine set. Tests intentionally trigger invalid-memory traps and disk/inode exhaustion; the final ALL TESTS PASSED plus the full named-test set establish suite success. These finite runs are not a formal race proof, KCSAN run or official MIT lock-lab grade.

gcheck verifies valid statistics ABI/version, nonzero free pages, invalid user destination returning -1, repeated 64-page allocation/touch/verification/free, accounting, free-list uniqueness/counts and cache invariants. Every gbench run verifies its own page bytes, child exit status or pipe/file contents and invokes allocator/cache invariant checking outside timing. Byte counts and operation budgets are checked again by the host audit.

## Performance evidence

- Main protocol: **72 measurements**, four variants × six workloads × three repetitions, across **12 fresh boots**. Six workload budgets are recorded in results/protocol.json. All runs and all repeat spreads remain in results/raw_runs.json.
- QEMU: 8.2.2, RISC-V full-system TCG, 3 vCPUs, 128 MiB RAM, no network device or KVM. Host: 9 visible logical CPUs, affinity 0–8, cgroup quota 800000/100000 (8 CPU equivalents), shared scheduling. Toolchain: RISC-V GCC 13.3.0/binutils 2.42.
- Timing: saved QEMU FDT gives **10,000,000 Hz**, parsed by both the experiment and audit. Guest r_time is not a native hardware-cycle counter. Counter collection/observation overhead is disclosed in FORMULATION.md.
- Main audit: **PASS, 532 tracked checks/matches**. It matches every numeric record to raw UART, rejects absent/duplicate experiment cells, verifies work units/flags/budgets/time conversion/cache identities, checks UART/source hashes, matches measured kernel hashes to validated ones, and reparses all full-suite test names.
- Public CLI smoke: a separate scale-0.0025 run with one repetition completed **24 tiny measurements across four boots**. Its audit passed **188 tracked checks/matches**. Raw data/logs are in validation/cli_smoke and do not enter the main report.

The allocator-only pages case has zero median failed exchanges but runs 11.95 times slower than baseline in this experiment. This regression is retained and its cause is unresolved. Hash lookup reduces comparisons by 46.68–85.60%, with unchanged misses and mixed/smaller elapsed effects. None of these observations is recast as a native laptop speed guarantee.

## Host, patch and delivery checks

**14 host tests passed**, covering parser schema/numeric validation, duplicate records/fields, explicit guest failure rejection, cache accounting, work-unit calculations, guest CPU bounds/headless flags, source hash sensitivity, all 82 pristine Git blobs and the saved device-tree clock. The executed output is docs/host_test_output.txt. These host tests are additional to the actual guest suites.

Patch verification passed using a fresh pristine copy, git apply --check, actual git apply, then comparison of every file path and byte with the delivered modified source: **85 files**, **15 changed/added paths**. Record: validation/patch_check.json. The patch SHA256 is 7b09d84b8af29852954c4dc1e5f898209334daf45dbcdc9d6082fe5559dd83d8.

All three scientific figures were visually inspected for readable labels/legends and correct data trends. The self-contained HTML was parsed and verified to contain **three valid embedded PNGs and seven tables** without external image dependencies. Negative results are stated near the beginning and in the full timing table.

The SHA256 identities of the earlier A–F archives were rechecked and remained unchanged. Delivery packaging also verifies the file manifest, ZIP integrity and the local Git bundle before saving. The package includes code/data/logs rather than large toolchain downloads or build products. Source/report tests were not substituted for actual QEMU execution.

## Genuine corrected failure

The initial four-argument copyout failed compilation against the pinned five-argument API. Actual diagnostics and original/fix commits are preserved. The fixed syscall includes p->sz and is exercised by gcheck's invalid destination plus the upstream copyout and related memory tests. See AI_FAILURE_LOG.md. No second independent AI tool, manual student correction or full chat export is claimed.
