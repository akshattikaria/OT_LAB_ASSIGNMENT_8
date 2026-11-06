#include "kernel/types.h"
#include "kernel/riscv.h"
#include "kernel/fcntl.h"
#include "kernel/labstats.h"
#include "user/user.h"

#define WORKERS 3
#define PAGE_BATCH 16
static char block[1024];

static void
fail(char *message)
{
  printf("GBENCH FAIL %s\n", message);
  exit(1);
}

static void
worker(char *kind, int iterations, int rank)
{
  for (int round = 0; round < iterations; round++) {
    if (strcmp(kind, "pages") == 0) {
      char *base = sbrk(PAGE_BATCH * PGSIZE);
      if (base == SBRK_ERROR)
        fail("sbrk");
      for (int page = 0; page < PAGE_BATCH; page++) {
        base[page * PGSIZE] = round + rank + page;
        base[page * PGSIZE + PGSIZE - 1] = round ^ rank ^ page;
      }
      for (int page = 0; page < PAGE_BATCH; page++)
        if ((uchar)base[page * PGSIZE] != (uchar)(round + rank + page) ||
            (uchar)base[page * PGSIZE + PGSIZE - 1] != (uchar)(round ^ rank ^ page))
          fail("page corruption");
      if (sbrk(-PAGE_BATCH * PGSIZE) == SBRK_ERROR)
        fail("shrink");
    } else if (strcmp(kind, "fork") == 0) {
      int pid = fork(), status = -1;
      if (pid < 0)
        fail("fork");
      if (pid == 0)
        exit(17);
      if (wait(&status) != pid || status != 17)
        fail("grandchild status");
    } else {
      int pipefd[2];
      char input[128], output[128];
      for (int j = 0; j < sizeof(input); j++)
        input[j] = round + rank + j;
      if (pipe(pipefd) < 0 || write(pipefd[1], input, sizeof(input)) != sizeof(input) ||
          read(pipefd[0], output, sizeof(output)) != sizeof(output) ||
          memcmp(input, output, sizeof(input)) != 0)
        fail("pipe data");
      close(pipefd[0]);
      close(pipefd[1]);
    }
  }
}

static void
name(int index, char *result)
{
  result[0] = 'g'; result[1] = 's';
  result[2] = '0' + index / 10; result[3] = '0' + index % 10;
  result[4] = 0;
}

static void
readblock(int fd, int file, int offset)
{
  if (fd < 0 || read(fd, block, sizeof(block)) != sizeof(block))
    fail("file read");
  for (int j = 0; j < sizeof(block); j++)
    if ((uchar)block[j] != (uchar)(file * 17 + offset * 31 + j))
      fail("file bytes");
}

static void
prepare(int files, int blocks)
{
  for (int i = 0; i < files; i++) {
    char path[5]; name(i, path); unlink(path);
    int fd = open(path, O_CREATE | O_TRUNC | O_WRONLY);
    if (fd < 0)
      fail("file create");
    for (int offset = 0; offset < blocks; offset++) {
      for (int j = 0; j < sizeof(block); j++)
        block[j] = i * 17 + offset * 31 + j;
      if (write(fd, block, sizeof(block)) != sizeof(block))
        fail("file write");
    }
    close(fd);
  }
  sync();
  for (int i = 0; i < files; i++) {
    char path[5]; name(i, path); int fd = open(path, O_RDONLY);
    for (int offset = 0; offset < blocks; offset++)
      readblock(fd, i, offset);
    close(fd);
  }
}

static void
report(char *kind, uint64 operations, struct labstats *a, struct labstats *b)
{
  printf("GRESULT kind=%s ops=%lu dt=%lu percpu=%lu hash=%lu",
         kind, operations, b->timestamp - a->timestamp, b->percpu, b->hash);
  printf(" alloc=%lu frees=%lu alocks=%lu aspins=%lu steals=%lu stolen=%lu",
         b->alloc_calls-a->alloc_calls, b->free_calls-a->free_calls,
         b->alloc_acquires-a->alloc_acquires, b->alloc_spins-a->alloc_spins,
         b->steals-a->steals, b->stolen_pages-a->stolen_pages);
  printf(" lookups=%lu hits=%lu misses=%lu probes=%lu recycle=%lu clocks=%lu cspins=%lu\n",
         b->cache_lookups-a->cache_lookups, b->cache_hits-a->cache_hits,
         b->cache_misses-a->cache_misses, b->lookup_probes-a->lookup_probes,
         b->recycle_probes-a->recycle_probes, b->cache_acquires-a->cache_acquires,
         b->cache_spins-a->cache_spins);
}

int
main(int argc, char **argv)
{
  if (argc != 3)
    fail("usage: gbench pages|fork|pipes|hotseq|hotrand|scan iterations");
  char *kind = argv[1]; int iterations = atoi(argv[2]);
  if (iterations < 1 || iterations > 100000)
    fail("iteration range");
  struct labstats a, b;
  if (labcheck() != 0)
    fail("initial invariants");
  uint64 operations;
  if (!strcmp(kind, "pages") || !strcmp(kind, "fork") || !strcmp(kind, "pipes")) {
    int ready[2], go[2];
    if (pipe(ready) < 0 || pipe(go) < 0)
      fail("barrier pipes");
    for (int rank = 0; rank < WORKERS; rank++) {
      int pid = fork();
      if (pid < 0)
        fail("worker fork");
      if (pid == 0) {
        close(ready[0]); close(go[1]); char token = 1;
        if (write(ready[1], &token, 1) != 1 || read(go[0], &token, 1) != 1)
          fail("barrier child");
        close(ready[1]); close(go[0]);
        worker(kind, iterations, rank); exit(0);
      }
    }
    close(ready[1]); close(go[0]);
    char token;
    for (int rank = 0; rank < WORKERS; rank++)
      if (read(ready[0], &token, 1) != 1)
        fail("barrier parent");
    if (labstats(&a) < 0)
      fail("stats before");
    for (int rank = 0; rank < WORKERS; rank++)
      if (write(go[1], "x", 1) != 1)
        fail("release workers");
    for (int rank = 0; rank < WORKERS; rank++) {
      int status = -1;
      if (wait(&status) < 0 || status != 0)
        fail("worker status");
    }
    if (labstats(&b) < 0)
      fail("stats after");
    close(ready[0]); close(go[1]);
    operations = (uint64)WORKERS * iterations * (!strcmp(kind,"pages") ? PAGE_BATCH : 1);
  } else if (!strcmp(kind, "hotseq") || !strcmp(kind, "hotrand") || !strcmp(kind, "scan")) {
    // One 16-block hot stream, two interleaved eight-block hot streams,
    // or one 96-block scan exceeding the 30-buffer cache.
    int files = !strcmp(kind, "hotrand") ? 2 : 1;
    int blocks = !strcmp(kind, "scan") ? 96 : (!strcmp(kind,"hotrand") ? 8 : 16);
    prepare(files, blocks);
    int descriptors[2], offsets[2] = {0, 0};
    for (int i = 0; i < files; i++) { char path[5]; name(i,path); descriptors[i]=open(path,O_RDONLY); }
    if (labcheck() < 0 || labstats(&a) < 0)
      fail("prepared invariants");
    uint random = 12345;
    for (int round = 0; round < iterations; round++) {
      int index;
      if (!strcmp(kind, "hotrand")) { random=random*1664525+1013904223; index=(random>>16)%files; }
      else index = 0;
      if (offsets[index] == blocks) {
        close(descriptors[index]); char path[5]; name(index,path);
        descriptors[index] = open(path,O_RDONLY); offsets[index] = 0;
      }
      readblock(descriptors[index], index, offsets[index]++);
    }
    if (labstats(&b) < 0)
      fail("stats after cache");
    operations = iterations;
    for (int i = 0; i < files; i++) close(descriptors[i]);
    for (int i = 0; i < files; i++) { char path[5]; name(i, path); unlink(path); }
    sync();
  } else fail("unknown workload");
  if (b.cache_hits + b.cache_misses != b.cache_lookups || labcheck() != 0)
    fail("final invariants");
  report(kind, operations, &a, &b);
  exit(0);
}
