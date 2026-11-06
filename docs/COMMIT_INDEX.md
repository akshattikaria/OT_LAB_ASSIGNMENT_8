# Local provenance

All commits were made with ChatGPT assistance; none is claimed as a manual student correction or independent second-tool contribution. No public remote is configured.

| Commit | Content |
| --- | --- |
| 692a02f4653aa65d42e8bcb667c521471f118a7e | Original lexer/parser, SSA, four passes and DP/greedy search |
| 7bfdfdba4a729798ec0a4033b2560e3f04dbc6ae | Correct redundant greedy candidate transformation and work accounting, with observed evidence |
| cd071e5a0ad3a8879336617c052be55a08f91f10 | Verified semantics/tests, native C generation and benchmark controls |
| ea0774f1114f5eba21278a6b37788490e382fcf3 | Recorded native/IR measurements, audit and visual report |
| Final documentation commit | Formulation, coverage, validation, AI disclosure, viva notes and integrity manifest |

history.bundle preserves the complete reachable history, including final commits. Restore it using:

```bash
git clone history.bundle track-f-history
git -C track-f-history log --oneline
```

The original/fix pair concerns an actual observed redundant-work/accounting defect. No artificial failure/fix sequence was created. Earlier A/B/D already document three other corrected cases. The negative native runtime/code-size results are not presented as bugs.

FILE_SHA256.json covers delivered source, artifacts, measurements and documentation, excluding itself and history.bundle. Compiled shared libraries, bytecode, scratch CLI outputs and temporary transfer helpers are excluded from the archive; C source and disassembly remain available.
