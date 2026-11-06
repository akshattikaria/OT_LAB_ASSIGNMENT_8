// Physical page allocator: baseline global list or per-CPU lists with batch stealing.
#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
#include "labstats.h"

#if KMEM_PERCPU
#define NKMEM NCPU
#else
#define NKMEM 1
#endif
#define STEAL_BATCH 32
#define MAXPAGES ((PHYSTOP - KERNBASE) / PGSIZE)

extern char end[];
struct run { struct run *next; };
struct {
  struct spinlock lock;
  struct run *freelist;
  uint64 nfree, allocations, frees, steals, stolen;
} kmem[NKMEM];
static struct spinlock checklock;
static uchar seen[MAXPAGES / 8];

void
kinit(void)
{
  for (int i = 0; i < NKMEM; i++)
    initlock(&kmem[i].lock, "kmem");
  initlock(&checklock, "kmemcheck");
  for (char *p = (char *)PGROUNDUP((uint64)end);
       p + PGSIZE <= (char *)PHYSTOP; p += PGSIZE)
    kfree(p);
}

void
kfree(void *pa)
{
  if (((uint64)pa % PGSIZE) != 0 || (char *)pa < end ||
      (uint64)pa >= PHYSTOP)
    panic("kfree");
  memset(pa, 1, PGSIZE);
  push_off();
  int id = KMEM_PERCPU ? cpuid() : 0;
  struct run *r = (struct run *)pa;
  acquire(&kmem[id].lock);
  r->next = kmem[id].freelist;
  kmem[id].freelist = r;
  kmem[id].nfree++;
  kmem[id].frees++;
  release(&kmem[id].lock);
  pop_off();
}

void *
kalloc(void)
{
  push_off(); // Pin cpuid while choosing and updating the local list.
  int id = KMEM_PERCPU ? cpuid() : 0;
  struct run *r;
  acquire(&kmem[id].lock);
  kmem[id].allocations++;
  r = kmem[id].freelist;
  if (r) {
    kmem[id].freelist = r->next;
    kmem[id].nfree--;
  }
  release(&kmem[id].lock);
#if KMEM_PERCPU
  if (r == 0) {
    for (int offset = 1; offset < NKMEM; offset++) {
      int victim = (id + offset) % NKMEM;
      acquire(&kmem[victim].lock);
      struct run *head = kmem[victim].freelist;
      if (head == 0) {
        release(&kmem[victim].lock);
        continue;
      }
      struct run *tail = head;
      int count = 1;
      while (count < STEAL_BATCH && tail->next) {
        tail = tail->next;
        count++;
      }
      kmem[victim].freelist = tail->next;
      tail->next = 0;
      kmem[victim].nfree -= count;
      release(&kmem[victim].lock);
      // No two allocator locks are held at once on the allocation path.
      r = head;
      struct run *extra = head->next;
      acquire(&kmem[id].lock);
      if (extra) {
        tail->next = kmem[id].freelist;
        kmem[id].freelist = extra;
        kmem[id].nfree += count - 1;
      }
      kmem[id].steals++;
      kmem[id].stolen += count;
      release(&kmem[id].lock);
      break;
    }
  }
#endif
  pop_off();
  if (r)
    memset((char *)r, 5, PGSIZE);
  return (void *)r;
}

void
kallocstats(struct labstats *s)
{
  for (int i = 0; i < NKMEM; i++) {
    acquire(&kmem[i].lock);
    s->alloc_acquires += kmem[i].lock.acquisitions;
    s->alloc_spins += kmem[i].lock.failed;
    s->free_pages += kmem[i].nfree;
    s->alloc_calls += kmem[i].allocations;
    s->free_calls += kmem[i].frees;
    s->steals += kmem[i].steals;
    s->stolen_pages += kmem[i].stolen;
    release(&kmem[i].lock);
  }
}

// Full validation is outside timed workloads. The normal allocator never
// holds multiple list locks; this read-only check takes them in fixed order.
int
kalloccheck(void)
{
  int ok = 1;
  acquire(&checklock);
  memset(seen, 0, sizeof(seen));
  for (int i = 0; i < NKMEM; i++)
    acquire(&kmem[i].lock);
  for (int i = 0; i < NKMEM; i++) {
    uint64 count = 0;
    for (struct run *r = kmem[i].freelist; r; r = r->next) {
      uint64 address = (uint64)r;
      if (address < (uint64)end || address >= PHYSTOP ||
          address % PGSIZE || count >= MAXPAGES) {
        ok = 0;
        break;
      }
      uint64 bit = (address - KERNBASE) / PGSIZE;
      if (seen[bit / 8] & (1 << (bit % 8))) {
        ok = 0;
        break;
      }
      seen[bit / 8] |= 1 << (bit % 8);
      count++;
    }
    if (count != kmem[i].nfree)
      ok = 0;
  }
  for (int i = NKMEM - 1; i >= 0; i--)
    release(&kmem[i].lock);
  release(&checklock);
  return ok;
}
