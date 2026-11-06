# Two-tool comparison recorded

> Current completion status: original AI evidence is included, Q-FLAIR is verified, and public archival source-revision links are mapped in docs/HISTORY_LINKS.md. The six exact-policy limitations remain. Earlier dated statements below describe their original stage.


Read **COMPARISON.md** for the measured comparison. Both original candidates pass the same nine tests, including 100 exhaustive small cases. Neither required a repair. Gemini's function has lower median runtime on the four retained cases; this is a local function benchmark.

The student supplied Gemini's original code and screenshot on 6 November 2026. The selector shown is **Argon High**; an underlying numbered model revision is not established. The student estimates generation took approximately **60 ± 3 seconds**. ChatGPT's original generation time was not measured, so AI generation speed cannot be compared. See `gemini_evidence.md` for provenance and limits.

TASK_PROMPT.txt is the fixed task. The screenshot corroborates its visible beginning; the complete student-supplied platform PDF is now included. `chatgpt_candidate.py` is the original internally generated ChatGPT/Codex baseline, not a separate human-authored exchange. `gemini_candidate_01.py` preserves the supplied answer unchanged. No repair response or missing transcript has been fabricated.

Run the shared `evaluate.py` harness and `benchmark_pair.py` with the commands in COMPARISON.md. The original baseline result, new per-candidate results, exact input arrays, raw paired timings and source digests are retained. Use new output paths when rerunning. Test execution time is separate from function runtime and AI generation time.
