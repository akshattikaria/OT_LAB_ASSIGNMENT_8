# Same-task comparison: ChatGPT/Codex and Google Gemini

> Current completion status: original AI evidence is included, Q-FLAIR is verified, and public archival source-revision links are mapped in docs/HISTORY_LINKS.md. The six exact-policy limitations remain. Earlier dated statements below describe their original stage.


Updated 6 November 2026 (Asia/Calcutta). Task: the same Python 3.12 0–1 knapsack function with maximum value, minimum weight and lexicographic index tie-breaking (TASK_PROMPT.txt). Gemini evidence is student-supplied. The screenshot shows the prompt beginning and selector; the complete supplied platform PDF is included.

| Measure | ChatGPT/Codex | Google Gemini |
|---|---|---|
| Model evidence | GPT-6 family; exact revision unavailable | Displayed selector: Argon High; underlying revision unverified |
| Shared test methods | 9/9 passed | 9/9 passed |
| Exhaustive small cases inside harness | 100/100 | 100/100 |
| Candidate versions to first pass | 1 retained | 1 supplied |
| Repair rounds | 0 recorded | 0 reported; no repair needed |
| AI generation latency | Not measured | Student estimate: approximately 60 ± 3 seconds |
| Unsupported external claims | None observed in code-only response | None observed in code-only response |

The nine methods cover invalid inputs including booleans/floats, item reuse, minimum-weight/lexicographic ties, empty inputs, zero capacity, no fitting items and input mutation. Finite tests are not a universal proof. The original ChatGPT baseline result is retained separately from the common-harness rerun.

## Function runtime on this host

Python 3.12.14; one warmup per candidate/case; seven paired repetitions with seeded randomized candidate order (56 timed calls). Inputs, imports, references and validation are outside the timed interval. Shared cloud host, not the student laptop. Medians and observed min–max ranges are milliseconds.

| Case (items; capacity) | ChatGPT median [range], ms | Gemini median [range], ms | ChatGPT/Gemini median time |
|---|---|---|---|
| small (12; 80) | 0.082542 [0.079988–0.132777] | 0.055312 [0.054861–0.059528] | 1.49 |
| medium_tight (35; 500) | 1.824198 [1.574790–1.939539] | 1.185343 [1.029273–1.332431] | 1.54 |
| large_tight (50; 5000) | 47.869222 [41.773612–64.901567] | 26.921525 [25.282559–34.270201] | 1.78 |
| large_loose (50; 10000) | 28.787809 [26.787729–29.293674] | 9.502221 [9.085928–10.607711] | 3.03 |

An independent capacity-at-most DP checks optimal value and minimum weight in runtime cases. Indices are checked for uniqueness, feasibility and matching sums; both functions return identical full results. Lexicographic ties are independently checked by exhaustive enumeration in the small-case harness. Pair agreement alone is not a proof.

## Explanation and limits

Both use exact-weight DP with descending updates to prevent item reuse. ChatGPT keeps value/index states together and makes final multi-key selection explicit. Gemini splits the arrays, skips overweight items and bounds sweeps by the sum of processed fitting weights capped at capacity. Its ascending final scan retains the lightest maximizer; lexicographic ties are handled within each weight. This reachable-weight bound plausibly contributes to the observed advantage, especially with loose capacity, but this benchmark does not isolate it from representation/interpreter overhead.

Both have O(nC) state visits in the worst case. Copying/comparing index tuples can cost O(n) per visit, giving a conservative Python-level bound of O(n²C) time and O(nC) storage including index tuples. Gemini changes practical work, not the worst-case state-count class. Integer capacity makes the algorithms pseudo-polynomial. The supplied benchmark limits are 50 items and capacity 10,000.

Readability is qualitative: ChatGPT expresses final ordering concisely; Gemini makes the loop bound explicit but has more update branches. No numerical style score is invented. Both validate the requested inputs, use only standard-library imports and leave input collections unchanged.

Both original candidates passed the common tests without repair. Gemini had lower median function runtime on all four retained cases (ChatGPT/Gemini median ratios 1.49–3.03). This supports a local implementation-runtime finding only. ChatGPT generation latency is unavailable, so there is no AI generation-speed winner.

Neither code-only response makes external claims to fact-check. No unsupported external claim was observed in this task; this is not a general hallucination-rate measurement. No repair was necessary, so repair quality cannot be compared.

## Evidence and reproduction

See comparison_record.json, gemini_evidence.md, both original candidate files, test-result JSON files and benchmark_results.json (full input arrays and every raw timed call). Harness elapsed time includes test/oracle work and is separate from function runtime and AI generation time.

```bash
python ai_tool_comparison/evaluate.py --candidate ai_tool_comparison/chatgpt_candidate.py --out ai_tool_comparison/chatgpt_result_rerun.json
python ai_tool_comparison/evaluate.py --candidate ai_tool_comparison/gemini_candidate_01.py --out ai_tool_comparison/gemini_result_rerun.json
python ai_tool_comparison/benchmark_pair.py --out ai_tool_comparison/benchmark_results_rerun.json
```

Use new output filenames to preserve evidence. New timings may differ. Original supplied chat exports and native selector screenshots are included; hidden backend revisions remain unverified; no general model ranking or generation-speed winner is justified.
