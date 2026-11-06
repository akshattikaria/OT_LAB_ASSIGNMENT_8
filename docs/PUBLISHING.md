# Publish only to the correct assignment repository

No GitHub repository was selected, created or pushed in this stage. The unrelated VoltNest repository is not used.

The integration history bundle records the added supplement/report/validation work. Original A-J local histories are preserved in their individual history bundles. The integration Git ignore deliberately keeps imported tracks separate until publication; **a plain git add . alone will not stage them**.

From the extracted package, after completing the pending comparison/export evidence and reviewing the files:

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
