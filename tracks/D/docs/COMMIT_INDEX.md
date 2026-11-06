# Local history

All commits were generated with ChatGPT assistance; none is represented as a manual student correction or independent second-tool contribution. No public remote is configured.

| Commit | Content |
| --- | --- |
| 1546c0f6c477e69b394cb08d421205b4e5a249b2 | Original algorithms, CPU kernels and initial timing boundary |
| 3e037b9d4513de8b27bc4dfdc07524270818f7b5 | Readiness handshake correcting the steady timer, with original/fixed observations |
| 92593d395b57358aa690084a6a8613b9703e2d3e | Shared-array work stealing, final tests, all recorded raw experiments, report and audit |
| Final documentation commit | README, formulation, coverage, validation, AI disclosure, viva notes and integrity manifest |

history.bundle contains the full reachable history, including the final documentation commit. Recover it using:

```bash
git clone history.bundle track-d-history
git -C track-d-history log --oneline
```

The original/fix pair preserves a genuine observed measurement defect. The Manager restriction and stdin launch issue are separately disclosed; no synthetic failure/fix pair was introduced to inflate the assignment count.

FILE_SHA256.json covers delivered source, results and documentation, excluding itself and history.bundle to avoid recursive identities. Compiled native output, bytecode, smoke outputs and temporary helper scripts are excluded from the archive.
