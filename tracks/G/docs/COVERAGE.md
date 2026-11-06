# Track G coverage

Supplied Assignment 8, Section 6 Track G asks for one kernel feature over at least three workloads, a second feature for the full-credit scope, new user-level benchmarks under QEMU, boot/usertests preservation, OS explanation and a patch/diff. Marks remain the instructor's decision.

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Modify real xv6 kernel | Pinned MIT source in vendor/xv6; modified source in xv6 | UPSTREAM.json verifies all 82 original blob hashes |
| First kernel feature | Per-CPU physical-page free lists with bounded batch stealing | xv6/kernel/kalloc.c; pages, fork and pipes workloads |
| Second kernel feature | Hash index for buffer lookup under the existing cache lock and LRU | xv6/kernel/bio.c, buf.h; hotseq, hotrand and scan workloads |
| Explain OS concepts and objective | Synchronization, physical memory, process lifetime, file-system cache locality | docs/FORMULATION.md and VIVA_GUIDE.md |
| Before/after same workload | Baseline, allocator-only, hash-only, combined; identical budgets/check interfaces | results/protocol.json, raw_runs.json and build records |
| New guest programs | gbench and gcheck, not host-only simulations | xv6/user/gbench.c and gcheck.c; complete UART logs |
| Boots and full usertests | Pristine kernel plus all four instrumented configurations | validation/development/pristine_usertests.log; validation/uart/ |
| Correctness after changes | Full upstream tests, custom page/cache invariants, data/status checks | validation/kernel_validation.json and docs/VALIDATION_RECORD.md |
| Patch/diff | Patch applies to exact pinned pristine snapshot | patches/track_g.patch, verified across all 85 delivered modified-source files |
| Reproducibility | Source pin, tool versions, flags, FDT clock, seeds/order, raw measurements | oslab/, results/, requirements.txt and toolchain package manifest |
| AI traceability | Original incompatible copyout call, compiler failure, fix and regression | docs/AI_FAILURE_LOG.md, prompts/G/, history.bundle |

Track G is an OS experiment, not a replacement for the main EV charging case study or for the required A–D portfolio. No other algorithms are credited merely because their names appear in an explanation. H/I/J and overall assignment integration remain separate work.
