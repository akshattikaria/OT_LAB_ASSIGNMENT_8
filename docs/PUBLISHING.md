# Publish only to the correct assignment repository

The assignment repository is [https://github.com/akshattikaria/OT_LAB_ASSIGNMENT_8](https://github.com/akshattikaria/OT_LAB_ASSIGNMENT_8). This source snapshot is published there; see `PUBLICATION.md`. The steps below are retained as instructions for future updates.

The integration history bundle records the added supplement/report/validation work. Original A-J local histories are preserved in their individual history bundles. The historical integration bundle kept imported tracks separate. The published root `.gitignore` now includes those tracks; the staging helper also verifies their exact imported hashes.

From the extracted package, after attaching the remaining sanitized platform export/screenshot evidence and reviewing the recorded comparison and files:

```bash
git init -b main
python tools/stage_for_publication.py --stage
git status
git diff --cached --stat
git commit -m "[AI:ChatGPT] Assemble verified Assignment 8 portfolio"
git remote add origin YOUR_CORRECT_ASSIGNMENT_REPOSITORY_URL
git push -u origin main
```

Replace the repository URL with the actual intended repository. Use your own configured Git identity when committing. The staging script verifies imported hashes and force-adds only the exact imported file list, not caches or arbitrary folders. It stages files but never pushes or publishes. Check that all ten tracks and required evidence are visible before submission.

To inspect the additional local history separately, use `git clone integration_history.bundle integration-history`. That bundle contains integration files; copy/use the tracks from the full package for experiments. The per-track bundles recover their own original repositories. Do not substitute an internal local commit hash for a public commit URL in the final submission; add public links after publication.

## Split history archive

`tracks/J/history.bundle` exceeds the upload interface's request limit after encoding. Its two binary parts and their exact sizes/hashes are recorded in `provenance/large_files.json`. Run `python tools/restore_large_files.py` to reconstruct the original archive. The audit, staging and packaging helpers do this automatically; the staging helper publishes the parts and keeps the reconstructed archive ignored. The original imported hash remains unchanged.
