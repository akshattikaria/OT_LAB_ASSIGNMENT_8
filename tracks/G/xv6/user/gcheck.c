#include "kernel/types.h"
#include "kernel/riscv.h"
#include "kernel/labstats.h"
#include "user/user.h"

static void
fail(char *message)
{
  printf("GCHECK FAIL %s\n", message);
  exit(1);
}

int
main(void)
{
  struct labstats before, after;
  if (labstats(&before) < 0 || before.version != 1 || before.free_pages == 0)
    fail("statistics ABI");
  if (labstats((struct labstats *)~(uint64)0) != -1)
    fail("invalid destination accepted");
  if (labcheck() != 0)
    fail("initial invariants");
  for (int round = 0; round < 8; round++) {
    char *base = sbrk(64 * PGSIZE);
    if (base == SBRK_ERROR)
      fail("allocation");
    for (int page = 0; page < 64; page++) {
      base[page * PGSIZE] = page + round;
      base[page * PGSIZE + PGSIZE - 1] = page ^ round;
    }
    for (int page = 0; page < 64; page++)
      if ((uchar)base[page * PGSIZE] != (uchar)(page + round) ||
          (uchar)base[page * PGSIZE + PGSIZE - 1] != (uchar)(page ^ round))
        fail("page isolation");
    if (sbrk(-64 * PGSIZE) == SBRK_ERROR || labcheck() != 0)
      fail("free-list consistency");
  }
  if (labstats(&after) < 0 || after.alloc_calls < before.alloc_calls + 512 ||
      after.free_calls < before.free_calls + 512)
    fail("allocation accounting");
  if (after.cache_hits + after.cache_misses != after.cache_lookups)
    fail("cache accounting");
  printf("GCHECK PASS percpu=%lu hash=%lu free=%lu\n",
         after.percpu, after.hash, after.free_pages);
  exit(0);
}
