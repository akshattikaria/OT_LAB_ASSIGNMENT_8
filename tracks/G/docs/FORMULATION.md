# Track G formulation and OS concepts

The process is physical-page allocation/freeing and cached-block lookup in the real MIT xv6 RISC-V kernel. The problem is unnecessary shared-lock competition and linear buffer search, rather than an application-level scheduling simulation.

## Decisions and objectives

Let configuration x=(a,h), with binary a enabling per-CPU lists and binary h enabling hashed buffer lookup. The four measured choices are (0,0), (1,0), (0,1), (1,1). For each fixed workload w, measure elapsed guest seconds T_w(x), failed allocator atomic exchanges S_w(x), and buffer lookup probes P_w(x). Report all three separately: minimizing a probe count is not a proof of minimizing time.

The experimental comparison is T_w(0,0)/T_w(x), with each T the median of three repetitions. A ratio below one is a slowdown. Allocator contention is also normalized as 1000*S_w(x)/work_units. Buffer work is P_w(x)/lookups. Cache misses and recycle searches are separate counters. There is no weighted scalar objective whose optimum is claimed.

The allocator policy greedily takes a local page when available. If empty, it scans other lists cyclically and steals at most 32 pages from the first nonempty victim. This is a local-first resource policy with dynamic load balancing, related to Chapter 6's parallel workload distribution and synchronization overhead. The batch size 32, NCPU=8 metadata slots, 13 hash buckets and NBUF=30 are fixed design choices, not the outcome of a tuning search. Only three guest CPUs are active. No claim of globally optimal batching or hash size is made.

## Correctness constraints

1. A page returned by kalloc must be aligned, valid physical memory and absent from every free list. No free-list page may appear twice. Stored list counts must match traversal counts.
2. push_off/pop_off prevents migration while choosing a CPU-local list. Normal allocation/free paths hold at most one allocator-list lock. A steal detaches a private batch under the victim lock, releases it, then publishes extras under the local lock. Thus normal paths cannot form a two-list lock cycle.
3. The diagnostic checker serializes itself, acquires list locks in ascending order and releases in reverse order. Its 4 KiB seen bitmap is static rather than placed on xv6's small kernel stack. It checks list uniqueness/counts; it does not classify all allocated or temporarily detached pages. The benchmark calls it with its own workers quiescent.
4. Buffer keys, hash membership, LRU links and reference counts remain protected by the original global bcache.lock. There must be at most one assigned buffer per (device,block). On replacement, old hash membership is removed before changing the key and publishing new membership.
5. Only buffers with zero references can be recycled. The buffer sleep lock still serializes block use; logging pins remain intact. The global cache lock is released before sleeping on a buffer lock.
6. User-visible output/data must be correct, all upstream usertests must pass, and invalid labstats user pointers must return -1 through the pinned bounded copyout API.

## Buffer search and complexity

The original hit path scans an MRU/LRU list of at most 30 buffers. The added index searches bucket (dev XOR blockno) modulo 13. Expected search is shorter when keys spread across buckets; collisions retain a worst case linear in cached buffers. LRU replacement still scans unused buffers from the original list tail. The index adds pointers, assigned markers, bucket heads and update work. The baseline retains the same added buffer fields and statistics infrastructure, so it is an instrumented comparison kernel, distinct from the pristine upstream reference.

Hashing preserves capacity and eviction policy. It can reduce comparisons without reducing misses. bget miss counts include metadata accesses and do not directly certify a reduction in disk reads or physical storage latency. This implementation is not a striped-lock cache.

## Measurement boundaries

Three worker processes rendezvous before allocator timing begins. Their initial forks occur before the first snapshot; worker activity, exits and reaping occur within it. Consequently frees can exceed allocations by the pages used to create those initial workers. Barrier allocation and file setup are excluded; barrier release and ending counter collection are included. Each timestamp is read after collecting counters, so starting counter collection precedes the start timestamp. Counter deltas include observation-lock acquisitions; the per-CPU snapshot visits eight lists versus one in the baseline.

Cache workloads create, sync and warm files before timing. Reopening a stream at EOF is included; final close/unlink/sync is excluded. hotrand selects between two sequential eight-block streams using a fixed PRNG; it is not uniform random block access or an lseek benchmark. The scan spans 96 blocks and exceeds the 30-buffer cache.

Timing uses guest r_time. QEMU's saved flattened device tree reports 10,000,000 ticks/second. r_time is neither retired RISC-V instructions nor native host cycles. The experiment uses QEMU TCG on a shared cloud host, 3 vCPUs and 128 MiB RAM. Initial/full-suite host durations are correctness-run diagnostics, not optimization timings. Lock snapshots are individually protected, not a globally atomic view of all CPUs; observation work is retained consistently in every configuration.

All twelve benchmark boots run sequentially, with fresh filesystems, fixed iteration budgets and deterministically shuffled configuration/workload order. Three repeats and min/max spreads describe this experiment; they do not establish statistical significance or a guarantee for Akshat's i3 laptop.
