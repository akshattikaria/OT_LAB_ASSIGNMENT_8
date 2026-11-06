# Local history and provenance

All commits in this Track G project are AI-assisted and use the [AI:ChatGPT] prefix. No manual student correction is attributed. No public GitHub remote is configured. The portable history.bundle contains the local commits; use `git clone history.bundle track-g-history` after extracting the package.

| Commit | Purpose |
| --- | --- |
| 31a3d9b8a32494a2b9dcb99ac5cb3c8f77fd3ff6 | Pin exact upstream MIT source and pristine comparison snapshot; verify all 82 blob hashes |
| bb501fb8adfaf52a2dd6cd604f3b227a9090be2d | Add kernel features/checks/instrumentation and preserve the incompatible copyout version plus real build failure |
| f7e43eb599c474f138fb1b4b3150d51a88ee4219 | Fix copyout by supplying the pinned API's process-size bound |
| 4adc2fae0483c106aa8c9eec6c3b98d864dd1766 | Freeze six native guest workloads and QEMU workflow; exact native source used for validation and measurement |
| f1a4399d4d383ef19e86845d4e0c24e747dd89dd | Preserve all four full guest suites, host checks, verified patch and AI-error evidence |

Subsequent AI-assisted evidence/report and final manifest commits are included in the bundle and are discoverable with `git log --oneline`. This index does not embed its own future commit hash or claim public commit URLs. The upstream MIT commit is independent of this local history and recorded in UPSTREAM.json.

The original/fixed source is directly reviewable with `git show HASH:xv6/kernel/sysproc.c`. The patch contains only the final native xv6 changes; the host scripts, reports and logs accompany it separately. The native source remained unchanged while full suites and measurements were running.
