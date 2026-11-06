# Track J commit index

All listed commits are AI-assisted and use `[AI:ChatGPT]`. These are local Git identities, not public GitHub URLs. The final archive includes a portable history bundle; after extraction, inspect it with `git bundle list-heads history.bundle` or restore the tracked snapshot with `git clone history.bundle restored-track-j`.

| Commit | Work |
|---|---|
| `c4ed2abc155ff101baef27331cc8460c9fe70df9` | [AI:ChatGPT] Pin verified cachetools source and retain initial wrong-directory collection failure |
| `b80da3e99cbe3c24d61a3118752e7ae1f79916be` | [AI:ChatGPT] Fix child working directory and verify coverage with seven regression tests |
| `ba623ad329cf0ee597f46f75ea7c3e5000a748db` | [AI:ChatGPT] Add set-cover experiment with precise process timing and independent mutation checks |
| `2166f835f921362978d2d149f9d4f8abca7496a4` | [AI:ChatGPT] Complete Track J report, raw evidence, audits and genuine failure documentation |

`c4ed2ab` retains the actual wrong-directory failure, `b80da3e` fixes it, and `ba623ad` implements the experiment and removes redundant context expansion from future reports. `2166f83` completes the report/audit/evidence and removes remaining pilot serialization fragments from the final snapshot. Historical oversized JSON is retained only in compressed Git history.

A following packaging commit contains this index and validation metadata. The bundle captures the tracked project through the final packaging-source commit. The export manifest is generated afterward and is not tracked in that bundle: it hashes the final exported files, including `history.bundle`, while excluding itself. This avoids a circular bundle/manifest hash. When restoring only through `git clone`, copy `FILE_SHA256.json` from the archive if desired. No commit is claimed to embed its own hash.

Raw pytest failure logs retain their original trailing spaces; source and authored documentation whitespace checks are separate. No manual student edits, a second AI tool, public publication or fabricated user revisions are claimed.
