# Track G viva guide

Be able to find and explain these functions without an AI tool. Read the actual code and practice a small change before the viva.

| Question | Explanation to give |
| --- | --- |
| What bottlenecks did you target? | One shared physical-page free-list lock and a linear buffer lookup while holding a cache lock. The measured objectives are contention, probes and elapsed time. |
| What does per-CPU mean? | Each CPU gets a separate free list and lock. kfree returns to the current CPU; kalloc first tries that list, then steals a batch if empty. It does not mean a process owns that memory forever. |
| Why disable interrupts while reading cpuid? | The current process must not migrate between selecting its CPU index and using that CPU's list. push_off nests safely with acquire's own interrupt handling. |
| Why steal a batch? | It amortizes victim-lock acquisition across later allocations. A large batch can concentrate free memory; a small batch requires more transfers. 32 is a fixed policy here, not a proven optimum. |
| Why no normal two-list lock acquisition? | Detach the batch while holding the victim lock, release it, then attach extras while holding the local lock. This avoids cross-list cycles. |
| Is the diagnostic checker an exception? | Yes. It freezes all lists in one fixed order and releases them in reverse. Allocation paths do not hold one list while requesting another, so they cannot form a cycle with it. |
| Why is the seen bitmap static? | It needs 4096 bytes for 32768 possible physical pages, too much for safe placement on xv6's small kernel stack. A separate checker lock serializes use. |
| What is page poisoning? | Free and allocated pages are filled with characteristic bytes to help reveal stale references/uninitialized uses. It is retained and its memory-write cost can dominate timing. |
| What did hashing change? | The lookup search chooses one of 13 buckets. The 30-buffer capacity, global cache lock, per-buffer sleep locks, LRU and logging pins remain. |
| Why keep both hash and LRU links? | Hash links answer key lookup; the LRU list selects an unused replacement. These are different operations. |
| What prevents duplicate blocks? | Lookup, old-key removal, new-key assignment, insertion and reference updates happen under the same global cache lock. |
| Why release bcache.lock before acquiresleep? | A spinlock must not be held while sleeping. The reference increment prevents recycling while the caller waits for the buffer sleep lock. |
| Is a cache miss a disk I/O count? | No. The measured counter describes bget lookup misses; reads, metadata, validity and storage service are distinct. No direct disk-read improvement is claimed. |
| How are failed exchanges different from lock acquisitions? | Every successful lock entry increments acquisitions. Failed test-and-set exchanges count competition while waiting, not lock hold time or CPU utilization. Zero is a valid observed value. |
| Why can frees exceed allocations? | Initial worker forks happen before the timing snapshot, but worker exit/reaping frees those pages during timing. It is an intentional interval boundary, not by itself a leak. |
| What is hotrand? | A deterministic choice between two sequential eight-block streams. xv6 has no lseek here; it is not uniform random access to a 16-block array. |
| What do 10 MHz and speedup mean? | Divide the guest r_time delta by the QEMU FDT's 10,000,000 Hz frequency. Compare medians of the same workload. It is an emulated guest elapsed ratio, not native hardware-cycle speedup. |
| Why run four configurations? | The allocator-only and hash-only runs separate effects; combined shows interaction. The pristine kernel is a correctness/provenance reference, not the instrumented performance baseline. |
| What was the AI error? | It assumed an old four-argument copyout. This pinned API needs five arguments, including p->sz. Compilation caught it; invalid-pointer gcheck and full guest tests cover the fixed path. |

## Short demonstration

1. Open results/report.html and compare lookup probes with elapsed ratios and misses; mention negative results and repeat spread.
2. Show kalloc's detach/release/publish sequence and bget's old-hash-removal/new-insertion sequence.
3. Show the complete ALL TESTS PASSED UART evidence, then the bounded copyout correction and gcheck invalid destination.
4. Run the small benchmark command in README and explain why its tiny durations are functional evidence only.

For a live modification, change the steal batch or bucket count in a separate copy, rebuild, run gcheck, all six smoke workloads and full usertests before comparing measurements in a new result folder. Do not claim a tuning improvement without rerunning the same protocol. No KCSAN or formal race-freedom proof was performed.
