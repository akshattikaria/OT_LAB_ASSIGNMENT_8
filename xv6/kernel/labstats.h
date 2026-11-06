#ifndef XV6_LABSTATS_H
#define XV6_LABSTATS_H
#ifndef KMEM_PERCPU
#define KMEM_PERCPU 0
#endif
#ifndef HASHBCACHE
#define HASHBCACHE 0
#endif
#define LAB_NHASH 13
struct labstats {
  uint64 version, percpu, hash, timestamp;
  uint64 alloc_acquires, alloc_spins, free_pages, alloc_calls, free_calls;
  uint64 steals, stolen_pages;
  uint64 cache_lookups, cache_hits, cache_misses;
  uint64 lookup_probes, recycle_probes, cache_acquires, cache_spins;
};
#endif
