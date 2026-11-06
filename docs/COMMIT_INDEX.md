# Track H local history

All commits are AI-assisted and marked [AI:ChatGPT]. No manual student correction is attributed. No public remote is configured. Recover the complete local history using `git clone history.bundle track-h-history` after extracting the package.

| Commit | Concrete change |
| --- | --- |
| eb7589881b4489f133c06e7f0c950ebf3b9d6cdf | Initial schema/data/oracles, overlap-aware greedy/ILP, real experiment and tests; original failing fixture output retained |
| d4eea40495ff1f04ec559b546828e4760ccd38d3 | Fresh-schema fixture isolation and partial-index parameter regression; initial passing 15-test output |
| cb844bcc7d66196faf468d92ec598f25e8d13bf9 | Atomic readback, separate trial-block persistence and final completeness checks after incomplete saved evidence was rejected; final measured core source frozen |
| f0270c446a4849b3d1563bf251ca6c0f535e39ad | Complete final measurements/audit, rejected initial evidence, all-seven-portfolio report, CLI replay, documentation and viva notes |

Subsequent evidence/report and final manifest commits are included in the bundle and discoverable with `git log --oneline`. This index does not embed its own future hash or invent public commit URLs. Prompt excerpts map to these real revisions; there was no invented revised user prompt for debugging within the continuation request.

Use `git show HASH:dblab/experiment.py` to compare the original checkpoint-only workflow with the final persisted-block checks. Original/rejected data are retained separately and are not used in final charts. The exact model-serving revision is not independently exposed by the environment; confirm it from the full chat header/export before final publication rather than inventing a label.
