// Mutual exclusion lock.
struct spinlock {
  uint locked; // Is the lock held?
  uint64 acquisitions;
  uint64 failed;

  // For debugging:
  char *name;      // Name of lock.
  struct cpu *cpu; // The cpu holding the lock.
};
