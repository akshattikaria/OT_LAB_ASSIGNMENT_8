"""Generate figures and a self-contained HTML report from saved observations."""
import argparse
import base64
from html import escape
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import numpy as np

from .common import ROOT


LABELS = {'full': 'Full suite', 'count_greedy': 'Count greedy',
          'weighted_greedy': 'Weighted greedy', 'ilp': 'Binary ILP'}
COLORS = ['#59697d', '#59a1c7', '#247a8a', '#1555a2']


def read(path):
    return json.loads(Path(path).read_text())


def make_figures(out, destination, summary, methods, timing, mutation):
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'savefig.facecolor': 'white', 'figure.facecolor': 'white'})
    names = list(summary)
    labels = [LABELS[n] for n in names]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), layout='constrained')
    y = np.arange(len(names))
    axes[0].barh(y, [summary[n]['tests'] for n in names], color=COLORS)
    for i, name in enumerate(names):
        axes[0].text(summary[name]['tests'] + 5, i, str(summary[name]['tests']), va='center')
    axes[0].set(yticks=y, yticklabels=labels, xlabel='Selected parent tests', xlim=(0, 445), title='Selection size')
    axes[0].invert_yaxis()
    for i, name in enumerate(names):
        values = [r['wall_ns'] / 1e9 for r in timing if r['method'] == name]
        offsets = np.linspace(-.12, .12, len(values))
        axes[1].scatter(values, i + offsets, s=26, alpha=.7, color=COLORS[i])
        axes[1].plot([summary[name]['wall_median_s']] * 2, [i - .25, i + .25], lw=3, color='#172333')
        axes[1].text(max(values) + .03, i, f"{summary[name]['wall_median_s']:.3f} s", va='center', fontsize=9)
    axes[1].set(yticks=y, yticklabels=labels, xlabel='Fresh-process wall time (seconds)',
                title='Seven real trials; dark marks are medians', xlim=(0, max(r['wall_ns'] / 1e9 for r in timing) + .35))
    axes[1].invert_yaxis()
    fig.savefig(destination / 'runtime_and_size.png', dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), layout='constrained')
    for i, name in enumerate(names):
        branch = summary[name]['branch_covered']
        total = summary[name]['branch_total']
        axes[0].barh(i, branch / total * 100, color=COLORS[i])
        axes[0].text(102, i, f'{branch}/{total}', va='center')
        killed, full = summary[name]['full_killed_retained'], summary[name]['full_killed_total']
        axes[1].barh(i, killed / full * 100 if full else 0, color=COLORS[i])
        axes[1].text(102, i, f'{killed}/{full}', va='center')
    for ax in axes:
        ax.set(yticks=y, yticklabels=labels, xlim=(0, 123), xticks=[0, 25, 50, 75, 100], xlabel='Percent')
        ax.invert_yaxis()
    axes[0].set_title('Branch coverage in fresh selected-suite runs')
    axes[1].set_title('Retention of faults killed by the full suite')
    fig.suptitle('All four suites preserve the same 1,005 per-test source lines', fontsize=12)
    fig.savefig(destination / 'coverage_and_faults.png', dpi=170)
    plt.close(fig)

    states = {'killed': 0, 'survived': 1, 'timeout': 2, 'invalid': 3}
    ids = sorted({r['mutant'] for r in mutation})
    outcomes = {(r['mutant'], r['method']): r['classification'] for r in mutation}
    matrix = np.array([[states[outcomes[mid, n]] for n in names] for mid in ids])
    palette = ['#247a8a', '#f2bc6c', '#b8bfca', '#c34d5a']
    fig, ax = plt.subplots(figsize=(8.4, 8), layout='constrained')
    ax.imshow(matrix, cmap=ListedColormap(palette), vmin=-.5, vmax=3.5, aspect='auto')
    for i, mid in enumerate(ids):
        for j, n in enumerate(names):
            state = outcomes[mid, n]
            ax.text(j, i, state, ha='center', va='center', fontsize=9,
                    color='white' if state in ('killed', 'invalid') else '#172333')
    ax.set(xticks=range(len(names)), xticklabels=labels, yticks=range(len(ids)), yticklabels=ids,
           title='Seeded mutation challenge: all 20 mutants retained')
    ax.tick_params(length=0)
    fig.savefig(destination / 'mutation_outcomes.png', dpi=170)
    plt.close(fig)


def generate(out):
    out = Path(out).resolve()
    summary, methods = read(out / 'summary.json'), read(out / 'methods.json')
    timing = read(out / 'timings.json')['rows']
    mutation = read(out / 'mutation_results.json')
    environment, profile = read(out / 'environment.json'), read(out / 'profile_summary.json')
    audit = read(ROOT / 'validation/audit.json')
    figures = ROOT / 'figures'
    make_figures(out, figures, summary, methods, timing, mutation)
    ilp, weighted = summary['ilp'], summary['weighted_greedy']
    rows = []
    for name, result in summary.items():
        rows.append(f"| {LABELS[name]} | {result['tests']} | {result['modeled_cost_us']/1000:.3f} | {result['wall_median_s']:.3f} ({result['wall_min_s']:.3f}–{result['wall_max_s']:.3f}) | {result['wall_speedup']:.2f}× | {result['branch_covered']}/{result['branch_total']} | {result['full_killed_retained']}/{result['full_killed_total']} |")
    table_header = '| Method | Tests | Modeled cost (ms) | Measured wall median (range), s | Wall speedup | Branches | Full-suite fault kills retained |'
    table_rule = '|---|---:|---:|---:|---:|---:|---:|'
    table = '\n'.join([table_header, table_rule] + rows)
    cost = read(out / 'costs.json')
    costly = sorted(zip(cost['costs'], cost['nodes']), reverse=True)[:8]
    top = '\n'.join(f'| `{n}` | {c/1000:.3f} |' for c, n in costly)
    descriptor = read(out / 'mutation_design.json')['mutants'][0]
    faults = '\n'.join(f"| {LABELS[n]} | {', '.join(r['missed_full_killed']) or 'None'} | {r['timeouts']} | {r['invalid']} |" for n, r in summary.items())
    overhead = '\n'.join(f"| {LABELS[n]} | {r['selection_s']:.4f} | {r['profiling_plus_selection_s']:.3f} | {r['profiling_plus_selection_break_even_runs'] or 'No saving'} | {r['validated_setup_break_even_runs'] or 'No saving'} |" for n, r in summary.items() if n != 'full')
    first = f"Binary ILP selects {ilp['tests']} of 391 parent tests, reducing median fresh-process wall time by {ilp['wall_reduction_pct']:.1f}% ({ilp['wall_speedup']:.2f}×). All 1,005 required per-test source lines are preserved, but it retains only {ilp['full_killed_retained']}/{ilp['full_killed_total']} faults caught by the full suite."
    fastest = min(summary, key=lambda n: summary[n]['wall_median_s'])
    text = f'''# Track J — Coverage-constrained regression-test selection

Akshat Tikaria · Roll 241070005 · Optimization Techniques, Assignment 8

{first}

## Case study and formulation

The subject is the complete MIT-licensed `cachetools 7.2.8` source distribution: 1,798 physical Python source lines (1,371 nonblank, noncomment) in six library files, with 391 collected parent tests and 24 passing subtests in the pristine baseline. The archive SHA-256 is pinned in `UPSTREAM.json`; every one of its 38 files remains unchanged. The local source distribution is the measured codebase; a repository commit identity is not asserted.

Choose a binary variable x_i for every test. Minimize Σ c_i x_i, where c_i is the positive, rounded-up median setup+call+teardown duration in microseconds from three uninstrumented full-suite profiles. For each of the 1,005 lines exercised in a per-test context, require Σ a_li x_i ≥ 1. All-suite execution is the naive baseline. Count greedy, cost-weighted greedy and binary ILP solve the same line-preservation task; count greedy ranks newly covered lines, weighted greedy ranks newly covered lines/cost, and both remove redundant chosen tests. The ILP uses HiGHS through SciPy. See `docs/FORMULATION.md` for the exact model and limits.

## Observed results

{table}

Seven trials per method ran serially in a seeded, shuffled order, each in a fresh Python process with third-party pytest plugin autoload disabled and no coverage/cProfile tracing. Every method uses the same lightweight observer to record outcomes and write JSON. The wall clock includes interpreter startup, imports, collection, tests and evidence output. Values are observed cloud-host results, not measurements on the student's i3 laptop. The ranges are observed minimum/maximum values, not confidence intervals. OS file caches were warm; host scheduling was uncontrolled.

The ILP status is {methods['ilp']['status']}, optimal={methods['ilp']['optimal']}, relative gap={methods['ilp']['gap']:.6g}; its primal cost and dual bound are both {methods['ilp']['estimated_cost_us']/1000:.3f} ms. That certificate concerns this frozen integer-cost matrix. It does not prove that {ilp['tests']} is the minimum number of tests, or that ILP has the lowest real wall time. The lowest observed wall median was {LABELS[fastest]}; timing noise and nonadditive startup/fixture costs can change the ranking. The full suite's modeled phase sum is {summary['full']['modeled_cost_us']/1000:.3f} ms, while its fresh-process median is {summary['full']['wall_median_s']:.3f} s.

![Selected tests and measured fresh-process times](figures/runtime_and_size.png)

## Baseline bottleneck

The separate cProfile run took {profile['total_s']:.3f} instrumented seconds. Its largest self-time entry is `{profile['top_self'][0]['function']}` in `{Path(profile['top_self'][0]['file']).name}` at {profile['top_self'][0]['own_s']:.3f} s, followed by `{profile['top_self'][1]['function']}` at {profile['top_self'][1]['own_s']:.3f} s. Pytest hook dispatch, compilation/import work and repeated test protocols account for material overhead; cache operations themselves are short. Cumulative call times overlap and must not be added. Profiling motivates reducing repeated tests but is not evidence that every remaining test is redundant as an assertion.

| Highest baseline test costs | Median phase sum (ms) |
|---|---:|
{top}

The top test contributes {costly[0][0]/sum(cost['costs'])*100:.1f}% of the additive profile cost. These short tests have noisy cost estimates; the fixed profile is a surrogate, not a prediction of all future CI runs.

## Coverage is not fault detection

Fresh instrumented runs verify all 1,005 required lines for every method. Standard statement coverage also includes collection/import execution and uses all 1,185 executable statements as its denominator; these are different quantities. The full suite covers 1,179/1,185 statements and all 214 branch outcomes. No 100% statement-coverage claim is made.

Twenty seeded, single-AST-operator mutants were generated independently of selection or kill outcomes. All 80 method/mutant combinations were executed. Each mutant changes one comparison boundary/equality or +/− operator inside a function, excluding while descendants. Mutants use isolated copies; AST unparsing changes formatting and removes comments in those disposable copies, so equivalence is checked structurally against exactly one intended operator edit. Surviving mutants are not assumed equivalent or harmless. A timeout or invalid execution is reported separately, never as a kill.

The full suite kills 16 mutants, survives three and times out on M20; all reduced suites also time out on M20. The 15-second cap applies per child. Excluding syntactic while descendants does not rule out indirect nontermination. The fault-retention denominator is the 16 full-suite kills, rather than all 20 generated mutants.

| Method | Faults killed by full suite but missed here | Timeouts | Invalid |
|---|---|---:|---:|
{faults}

For example, `{descriptor['id']}` changes `{descriptor['old']}` to `{descriptor['new']}` at `{descriptor['path']}:{descriptor['line']}`. The full suite fails on that mutant while ILP's selected suite passes. This is a concrete counterexample to treating line coverage as a guarantee of assertion strength. Deliberate mutants are validation faults, not AI coding mistakes.

![Branch coverage and retained fault detection](figures/coverage_and_faults.png)

![All mutation outcomes](figures/mutation_outcomes.png)

## Amortization and engineering costs

| Method | Selection time (s) | Baseline coverage + three profiles + selection (s) | Future runs to amortize | Runs including fresh coverage validation |
|---|---:|---:|---:|---:|
{overhead}

Break-even uses the observed median full-minus-selected wall time and assumes the source, costs and coverage matrix remain valid. These setup estimates exclude this research run's cProfile, seven timing repetitions, mutation challenge, report generation and audit; a complete evaluation costs more than deploying an already evaluated selector. Reprofile after code, tests, fixtures or dependencies change. Cheap test-count reduction does not remove interpreter startup or collection cost, and per-test costs are not fully additive.

The subject's code readability and maintainability are unchanged because production code is not refactored. Maintaining the selector, coverage-context recorder, SciPy/pytest/coverage dependencies, version pin and invalidation rules is an additional maintenance burden. POSIX process groups enforce timeouts; Windows users need Linux/WSL for the supplied driver. The mutation sample is small and operator-limited, and tests of concurrency/nondeterminism can vary between runs. This experiment supports a fast feedback stage with the full suite retained for complete regression checks; it does not justify replacing the full suite for releases.

## Validation and reproducibility

Ten host tests pass, including ILP versus exhaustive enumeration on 25 independently generated seven-variable models, invalid/uncoverable model rejection, actual child working-directory collection, pinned-source integrity, deterministic single-operator mutations and non-kill timeout classification. The evidence audit passed: {audit['upstream_files_verified']} upstream files, {audit['coverage_sqlite_matrices_verified']} SQLite-to-line matrices, {audit['timing_trials']} timing trials, {audit['mutation_trials']} mutation trials, objective/cost recomputation and primal/dual consistency. Four fresh suite replays passed. Raw logs, process times, selected node IDs, coverage databases, profiling data, mutation descriptors and classifications are included.

Run `python -m selci.audit --out results` to inspect saved evidence without overwriting it. Run `python -m selci.experiment --out results-rerun` for a new measurement grid, then `python -m selci.audit --out results-rerun`. New times and possibly selections can differ. `README.md` contains setup and commands; `docs/AI_FAILURE_LOG.md` records actual development mistakes and their fixes.

AI assistance: ChatGPT/Codex, GPT-6 family as identified by the environment; the exact serving revision is not independently exposed. The real continuation request and human-verifiable decisions are recorded in `prompts/J/001_continue.md`. This package is one track milestone, not the final integrated submission or an assertion that the fourteen-day diary, second-tool requirement, public repository or demonstration video is finished.

## Primary references

- User-supplied Assignment 8, Track J; PPT1 section on integer linear programming and PPT4 section on greedy strategy selection. The (1−1/e) cardinality-constrained maximization bound is not asserted for this weighted set-cover minimization problem.
- [Official pinned source release](https://pypi.org/project/cachetools/7.2.8/) and [upstream repository](https://github.com/tkem/cachetools).
- [Coverage measurement contexts](https://coverage.readthedocs.io/en/7.17.1/contexts.html).
- [CoverageData API](https://coverage.readthedocs.io/en/7.17.1/api_coveragedata.html).
- [SciPy mixed-integer programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html).
- [Pytest hook API](https://docs.pytest.org/en/stable/reference/reference.html).
'''
    (ROOT / 'REPORT.md').write_text(text)
    # This report is a single offline HTML file; embed images rather than needing
    # a running app, network connection or external font/chart assets.
    import re
    def inline(value):
        value = escape(value)
        value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
        return re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)', r'<a href="\2">\1</a>', value)
    sections = []
    for block in text.split('\n\n'):
        if block.startswith('# '):
            sections.append('<h1>' + escape(block[2:]) + '</h1>')
        elif block.startswith('## '):
            sections.append('<h2>' + escape(block[3:]) + '</h2>')
        elif block.startswith('!['):
            alt, path = re.match(r'!\[(.*?)\]\((.*?)\)', block).groups()
            data = base64.b64encode((ROOT / path).read_bytes()).decode()
            sections.append(f'<figure><img alt="{escape(alt)}" src="data:image/png;base64,{data}"><figcaption>{escape(alt)}</figcaption></figure>')
        elif block.startswith('|'):
            lines = [line for line in block.splitlines() if not re.fullmatch(r'[|:\- ]+', line)]
            cells = [[x.strip() for x in line.strip('|').split('|')] for line in lines]
            sections.append('<div class="table"><table><thead><tr>' + ''.join('<th>' + inline(x) + '</th>' for x in cells[0]) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + inline(x) + '</td>' for x in row) + '</tr>' for row in cells[1:]) + '</tbody></table></div>')
        elif block.startswith('- '):
            sections.append('<ul>' + ''.join('<li>' + inline(x.removeprefix('- ')) + '</li>' for x in block.splitlines()) + '</ul>')
        else:
            sections.append('<p>' + inline(block).replace('\n', ' ') + '</p>')
    body = '\n'.join(sections)
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Track J · Test selection</title><style>
    :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#eef3f7;color:#203045;font:16px/1.65 system-ui,sans-serif}main{max-width:1100px;margin:36px auto;background:white;padding:42px 48px;border-radius:18px;box-shadow:0 10px 40px #153a5b12}h1{font-size:34px;line-height:1.2;color:#163d64;border-top:7px solid #247a8a;padding-top:26px}h2{font-size:23px;color:#163d64;margin-top:40px}p{overflow-wrap:anywhere}p:nth-of-type(2){background:#fff3dc;padding:20px;border-left:5px solid #d79428;border-radius:5px}.table{overflow-x:auto}table{border-collapse:collapse;font-size:14px;width:100%;margin:12px 0}th{background:#163d64;color:white;text-align:left}th,td{padding:10px 12px;border-bottom:1px solid #d8e2eb}tr:nth-child(even){background:#f4f8fb}figure{margin:30px 0}img{display:block;width:100%;height:auto}figcaption{font-size:13px;color:#536477;text-align:center}li{margin:8px 0}@media(max-width:700px){main{margin:0;padding:20px;border-radius:0}h1{font-size:28px}}@media print{body{background:white}main{padding:0;box-shadow:none;margin:0}figure{break-inside:avoid}}
    </style></head><body><main>''' + body + '</main></body></html>'
    (ROOT / 'REPORT.html').write_text(html)
    print('Created REPORT.md, standalone REPORT.html and three figures.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results')
    args = parser.parse_args()
    generate(args.out)


if __name__ == '__main__':
    main()
