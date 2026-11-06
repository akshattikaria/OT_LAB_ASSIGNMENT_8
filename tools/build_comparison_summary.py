"""Render the comparison from retained evidence; never regenerate timings."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'ai_tool_comparison'
    record = json.loads((folder / 'comparison_record.json').read_text())
    benchmark = json.loads((folder / 'benchmark_results.json').read_text())
    lines = [
        '# Same-task comparison: ChatGPT/Codex and Google Gemini',
        '',
        'Updated 6 November 2026 (Asia/Calcutta). Task: the same Python 3.12 0–1 knapsack function with maximum value, minimum weight and lexicographic index tie-breaking (TASK_PROMPT.txt). Gemini evidence is student-supplied. The screenshot shows the prompt beginning and selector; a complete platform export remains pending.',
        '',
        '| Measure | ChatGPT/Codex | Google Gemini |',
        '|---|---|---|',
        '| Model evidence | GPT-6 family; exact revision unavailable | Displayed selector: Argon High; underlying revision unverified |',
        '| Shared test methods | 9/9 passed | 9/9 passed |',
        '| Exhaustive small cases inside harness | 100/100 | 100/100 |',
        '| Candidate versions to first pass | 1 retained | 1 supplied |',
        '| Repair rounds | 0 recorded | 0 reported; no repair needed |',
        '| AI generation latency | Not measured | Student estimate: approximately 60 ± 3 seconds |',
        '| Unsupported external claims | None observed in code-only response | None observed in code-only response |',
        '',
        'The nine methods cover invalid inputs including booleans/floats, item reuse, minimum-weight/lexicographic ties, empty inputs, zero capacity, no fitting items and input mutation. Finite tests are not a universal proof. The original ChatGPT baseline result is retained separately from the common-harness rerun.',
        '',
        '## Function runtime on this host',
        '',
        f"Python {benchmark['python']}; one warmup per candidate/case; seven paired repetitions with seeded randomized candidate order (56 timed calls). Inputs, imports, references and validation are outside the timed interval. Shared cloud host, not the student laptop. Medians and observed min–max ranges are milliseconds.",
        '',
        '| Case (items; capacity) | ChatGPT median [range], ms | Gemini median [range], ms | ChatGPT/Gemini median time |',
        '|---|---|---|---|',
    ]
    cases = {c['name']: c for c in benchmark['cases']}
    for row in benchmark['summary']:
        case = cases[row['case']]
        a, b = row['chatgpt'], row['gemini']
        lines.append(f"| {row['case']} ({len(case['weights'])}; {case['capacity']}) | {a['median_ms']:.6f} [{a['min_ms']:.6f}–{a['max_ms']:.6f}] | {b['median_ms']:.6f} [{b['min_ms']:.6f}–{b['max_ms']:.6f}] | {row['chatgpt_over_gemini_time_ratio']:.2f} |")
    lines += [
        '',
        'An independent capacity-at-most DP checks optimal value and minimum weight in runtime cases. Indices are checked for uniqueness, feasibility and matching sums; both functions return identical full results. Lexicographic ties are independently checked by exhaustive enumeration in the small-case harness. Pair agreement alone is not a proof.',
        '',
        '## Explanation and limits',
        '',
        'Both use exact-weight DP with descending updates to prevent item reuse. ChatGPT keeps value/index states together and makes final multi-key selection explicit. Gemini splits the arrays, skips overweight items and bounds sweeps by the sum of processed fitting weights capped at capacity. Its ascending final scan retains the lightest maximizer; lexicographic ties are handled within each weight. This reachable-weight bound plausibly contributes to the observed advantage, especially with loose capacity, but this benchmark does not isolate it from representation/interpreter overhead.',
        '',
        'Both have O(nC) state visits in the worst case. Copying/comparing index tuples can cost O(n) per visit, giving a conservative Python-level bound of O(n²C) time and O(nC) storage including index tuples. Gemini changes practical work, not the worst-case state-count class. Integer capacity makes the algorithms pseudo-polynomial. The supplied benchmark limits are 50 items and capacity 10,000.',
        '',
        'Readability is qualitative: ChatGPT expresses final ordering concisely; Gemini makes the loop bound explicit but has more update branches. No numerical style score is invented. Both validate the requested inputs, use only standard-library imports and leave input collections unchanged.',
        '',
        record['conclusion'],
        '',
        'Neither code-only response makes external claims to fact-check. No unsupported external claim was observed in this task; this is not a general hallucination-rate measurement. No repair was necessary, so repair quality cannot be compared.',
        '',
        '## Evidence and reproduction',
        '',
        'See comparison_record.json, gemini_evidence.md, both original candidate files, test-result JSON files and benchmark_results.json (full input arrays and every raw timed call). Harness elapsed time includes test/oracle work and is separate from function runtime and AI generation time.',
        '',
        '```bash',
        'python ai_tool_comparison/evaluate.py --candidate ai_tool_comparison/chatgpt_candidate.py --out ai_tool_comparison/chatgpt_result_rerun.json',
        'python ai_tool_comparison/evaluate.py --candidate ai_tool_comparison/gemini_candidate_01.py --out ai_tool_comparison/gemini_result_rerun.json',
        'python ai_tool_comparison/benchmark_pair.py --out ai_tool_comparison/benchmark_results_rerun.json',
        '```',
        '',
        'Use new output filenames to preserve evidence. New timings may differ. Full sanitized chat exports and stronger model/prompt authentication remain evidence to attach; no general model ranking or generation-speed winner is justified.',
    ]
    (folder / 'COMPARISON.md').write_text('\n'.join(lines) + '\n')
    print(folder / 'COMPARISON.md')


if __name__ == '__main__':
    main()
