// Buffer cache.
//
// The buffer cache is a linked list of buf structures holding
// cached copies of disk block contents.  Caching disk blocks
// in memory reduces the number of disk reads and also provides
// a synchronization point for disk blocks used by multiple processes.
//
// Interface:
// * To get a buffer for a particular disk block, call bread.
// * After changing buffer data, call bwrite to write it to disk.
// * When done with the buffer, call brelse.
// * Do not use the buffer after calling brelse.
// * Only one process at a time can use a buffer,
//     so do not keep them longer than necessary.

#include "types.h"
#include "param.h"
#include "spinlock.h"
#include "sleeplock.h"
#include "riscv.h"
#include "defs.h"
#include "fs.h"
#include "buf.h"
#include "labstats.h"

struct {
  struct spinlock lock;
  struct buf buf[NBUF];

  // Linked list of all buffers, through prev/next.
  // Sorted by how recently the buffer was used.
  // head.next is most recent, head.prev is least.
  struct buf head;
  struct buf *buckets[LAB_NHASH];
  uint64 lookups, hits, misses, probes, recycle;
} bcache;

#if HASHBCACHE
static uint
hashkey(uint dev, uint blockno)
{
  return (dev ^ blockno) % LAB_NHASH;
}

// Caller holds bcache.lock: assignment and hash membership change atomically.
static void
hashremove(struct buf *b)
{
  if (!b->assigned)
    return;
  struct buf **link = &bcache.buckets[hashkey(b->dev, b->blockno)];
  while (*link && *link != b)
    link = &(*link)->hash_next;
  if (*link != b)
    panic("hashremove");
  *link = b->hash_next;
  b->hash_next = 0;
}
#endif

void
binit(void)
{
  struct buf *b;

  initlock(&bcache.lock, "bcache");

  // Create linked list of buffers
  bcache.head.prev = &bcache.head;
  bcache.head.next = &bcache.head;
  for (b = bcache.buf; b < bcache.buf + NBUF; b++) {
    b->next = bcache.head.next;
    b->prev = &bcache.head;
    initsleeplock(&b->lock, "buffer");
    bcache.head.next->prev = b;
    bcache.head.next = b;
  }
}

// Look through buffer cache for block on device dev.
// If not found, allocate a buffer.
// In either case, return locked buffer.
static struct buf *
bget(uint dev, uint blockno)
{
  struct buf *b;

  acquire(&bcache.lock);
  bcache.lookups++;

  // Is the block already cached?
#if HASHBCACHE
  for (b = bcache.buckets[hashkey(dev, blockno)]; b; b = b->hash_next) {
#else
  for (b = bcache.head.next; b != &bcache.head; b = b->next) {
#endif
    bcache.probes++;
    if (b->dev == dev && b->blockno == blockno) {
      bcache.hits++;
      b->refcnt++;
      release(&bcache.lock);
      acquiresleep(&b->lock);
      return b;
    }
  }

  // Not cached.
  bcache.misses++;
  // Recycle the least recently used (LRU) unused buffer.
  for (b = bcache.head.prev; b != &bcache.head; b = b->prev) {
    bcache.recycle++;
    if (b->refcnt == 0) {
#if HASHBCACHE
      hashremove(b);
#endif
      b->dev = dev;
      b->blockno = blockno;
      b->assigned = 1;
#if HASHBCACHE
      uint key = hashkey(dev, blockno);
      b->hash_next = bcache.buckets[key];
      bcache.buckets[key] = b;
#endif
      b->valid = 0;
      b->refcnt = 1;
      release(&bcache.lock);
      acquiresleep(&b->lock);
      return b;
    }
  }
  panic("bget: no buffers");
}

// Return a locked buf with the contents of the indicated block.
struct buf *
bread(uint dev, uint blockno)
{
  struct buf *b;

  b = bget(dev, blockno);
  if (!b->valid) {
    virtio_disk_rw(b, 0);
    b->valid = 1;
  }
  return b;
}

// Write b's contents to disk.  Must be locked.
// Only the log calls bwrite.
void
bwrite(struct buf *b)
{
  if (!holdingsleep(&b->lock))
    panic("bwrite");
  virtio_disk_rw(b, 1);
}

// Release a locked buffer.
// Move to the head of the most-recently-used list.
void
brelse(struct buf *b)
{
  if (!holdingsleep(&b->lock))
    panic("brelse");

  releasesleep(&b->lock);

  acquire(&bcache.lock);
  b->refcnt--;
  if (b->refcnt == 0) {
    // no one is waiting for it.
    b->next->prev = b->prev;
    b->prev->next = b->next;
    b->next = bcache.head.next;
    b->prev = &bcache.head;
    bcache.head.next->prev = b;
    bcache.head.next = b;
  }

  release(&bcache.lock);
}

void
bpin(struct buf *b)
{
  acquire(&bcache.lock);
  b->refcnt++;
  release(&bcache.lock);
}

void
bunpin(struct buf *b)
{
  acquire(&bcache.lock);
  b->refcnt--;
  release(&bcache.lock);
}

void
bcachestats(struct labstats *s)
{
  acquire(&bcache.lock);
  s->cache_lookups = bcache.lookups;
  s->cache_hits = bcache.hits;
  s->cache_misses = bcache.misses;
  s->lookup_probes = bcache.probes;
  s->recycle_probes = bcache.recycle;
  s->cache_acquires = bcache.lock.acquisitions;
  s->cache_spins = bcache.lock.failed;
  release(&bcache.lock);
}

int
bcachecheck(void)
{
  int ok = 1, count = 0;
  acquire(&bcache.lock);
  for (struct buf *b = bcache.head.next; b != &bcache.head; b = b->next) {
    if (++count > NBUF || b->next->prev != b || b->prev->next != b) {
      ok = 0;
      break;
    }
  }
  if (count != NBUF)
    ok = 0;
  for (int i = 0; i < NBUF; i++) {
    struct buf *b = &bcache.buf[i];
    for (int j = i + 1; j < NBUF; j++)
      if (b->assigned && bcache.buf[j].assigned &&
          b->dev == bcache.buf[j].dev && b->blockno == bcache.buf[j].blockno)
        ok = 0;
#if HASHBCACHE
    int occurrences = 0;
    for (int key = 0; key < LAB_NHASH; key++) {
      int steps = 0;
      for (struct buf *p = bcache.buckets[key]; p; p = p->hash_next) {
        if (++steps > NBUF) { ok = 0; break; }
        if (!p->assigned || hashkey(p->dev, p->blockno) != key)
          ok = 0;
        if (p == b)
          occurrences++;
      }
    }
    if (occurrences != (b->assigned ? 1 : 0))
      ok = 0;
#endif
  }
  release(&bcache.lock);
  return ok;
}
