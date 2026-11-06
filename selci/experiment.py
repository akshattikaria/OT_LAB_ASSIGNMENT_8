"""Coverage-constrained CI test selection on the pinned cachetools distribution."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import pstats
import random
import statistics
import sys
import tempfile

from .common import ROOT, SUBJECT, dump, sha_file, source_digest
from .mutations import classify, design, materialize
from .process import run_subject
from .selection import greedy, integer_program, covered


def read(path):
    return json.loads(Path(path).read_text())


def pristine_check(directory, expected=None):
    result = read(Path(directory) / 'run.json')
    if result['exit_code'] or result['failed_reports']:
        raise AssertionError('Pristine suite failed: ' + str(directory))
    if expected is not None and result['collected'] != expected:
        raise AssertionError('Collected test order differs: ' + str(directory))
    return result


def checked_run(subject, directory, nodes=None, **kwargs):
    process = run_subject(subject, directory, nodes=nodes, **kwargs)
    if process['timed_out'] or process['exit_code']:
        raise AssertionError('Pristine child failed; inspect ' + str(directory))
    pristine_check(directory, nodes)
    return process


def profile_table(path):
    stats = pstats.Stats(str(path))
    rows = []
    for (filename, line, function), (primitive, calls, own, cumulative, callers) in stats.stats.items():
        label = str(filename)
        try:
            label = str(Path(filename).relative_to(ROOT))
        except ValueError:
            pass
        rows.append({'file': label, 'line': line, 'function': function,
                     'primitive_calls': primitive, 'calls': calls,
                     'own_s': own, 'cumulative_s': cumulative})
    return {'total_s': stats.total_tt, 'total_calls': stats.total_calls,
            'top_cumulative': sorted(rows, key=lambda r: -r['cumulative_s'])[:35],
            'top_self': sorted(rows, key=lambda r: -r['own_s'])[:35],
            'package_top_cumulative': sorted([r for r in rows if 'src/cachetools/' in r['file']], key=lambda r: -r['cumulative_s'])[:25],
            'caution': 'Nested cumulative times overlap. Instrumented cProfile times are not CI speedup measurements.'}


def summarize(out, methods, timing_rows, mutation_rows, baseline_u):
    by_method = {}
    base = [r['wall_ns'] / 1e9 for r in timing_rows if r['method'] == 'full']
    baseline = statistics.median(base)
    base_killed = {r['mutant'] for r in mutation_rows if r['method'] == 'full' and r['classification'] == 'killed'}
    full_report = read(out / 'coverage/full/coverage_report.json')['totals']
    for name, method in methods.items():
        rows = [r for r in timing_rows if r['method'] == name]
        walls = [r['wall_ns'] / 1e9 for r in rows]
        pytest_times = [r['pytest_elapsed_ns'] / 1e9 for r in rows]
        coverage = read(out / 'coverage' / name / 'coverage_report.json')['totals']
        incidence = read(out / 'coverage' / name / 'incidence.json')
        killed = {r['mutant'] for r in mutation_rows if r['method'] == name and r['classification'] == 'killed'}
        valid_pair = {r['mutant'] for r in mutation_rows if r['method'] == name and r['classification'] in ('killed', 'survived')}
        median = statistics.median(walls)
        saving = baseline - median
        by_method[name] = {'tests': len(method['selected']),
                           'modeled_cost_us': method['estimated_cost_us'],
                           'wall_median_s': median, 'wall_min_s': min(walls), 'wall_max_s': max(walls),
                           'pytest_median_s': statistics.median(pytest_times),
                           'wall_speedup': baseline / median, 'wall_reduction_pct': 100 * saving / baseline,
                           'line_universe': len(incidence['universe']),
                           'line_universe_preserved': set(baseline_u) <= set(incidence['universe']),
                           'statement_covered': coverage['covered_lines'],
                           'statement_total': coverage['num_statements'],
                           'branch_covered': coverage['covered_branches'],
                           'branch_total': coverage['num_branches'],
                           'branches_lost_vs_full': full_report['covered_branches'] - coverage['covered_branches'],
                           'mutants_killed': len(killed), 'full_killed_retained': len(killed & base_killed),
                           'full_killed_total': len(base_killed), 'paired_valid_full_killed': len(valid_pair & base_killed),
                           'missed_full_killed': sorted(base_killed - killed),
                           'timeouts': sum(r['classification'] == 'timeout' for r in mutation_rows if r['method'] == name),
                           'invalid': sum(r['classification'] == 'invalid' for r in mutation_rows if r['method'] == name),
                           'selection_s': method['selection_s'],
                           'selection_only_break_even_runs': math.ceil(method['selection_s'] / saving) if saving > 0 else None}
    return by_method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results')
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--profile-runs', type=int, default=3)
    parser.add_argument('--mutants', type=int, default=20)
    args = parser.parse_args()
    if args.repeats < 3 or args.profile_runs < 3 or args.mutants < 1:
        parser.error('Need at least three repetitions/profiles and one mutant')
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Use a new empty output directory to preserve evidence')
    out.mkdir(parents=True, exist_ok=True)
    versions = {name: importlib.metadata.version(name) for name in ['pytest', 'coverage', 'numpy', 'scipy', 'matplotlib']}
    metadata = {'started_utc': datetime.now(timezone.utc).isoformat(),
                'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                'machine': platform.machine(), 'cpu_count': os.cpu_count(), 'versions': versions,
                'source_digest': source_digest(), 'seed': 241070005,
                'repeats': args.repeats, 'profile_runs': args.profile_runs,
                'mutants': args.mutants, 'subject': str(SUBJECT),
                'timing_limit': 'Observed shared cloud host; not measured on the student i3 laptop. Fresh processes, warm OS file cache, serial randomized order; variability retained.'}
    dump(out / 'environment.json', metadata)
    print('1. Baseline per-test coverage', flush=True)
    baseline_process = checked_run(SUBJECT, out / 'coverage/full', trace=True)
    incidence = read(out / 'coverage/full/incidence.json')
    nodes, universe = incidence['test_nodes'], set(incidence['universe'])
    covers = [set(incidence['coverage'][n]) for n in nodes]
    print(f'   {len(nodes)} tests, {len(universe)} per-test source lines', flush=True)

    print('2. Uninstrumented cost profiles and independent cProfile', flush=True)
    profiles, profiling_processes = [], []
    for index in range(args.profile_runs):
        directory = out / 'profiles' / f'run_{index:02}'
        profiling_processes.append(checked_run(SUBJECT, directory))
        profile = pristine_check(directory, nodes)
        profiles.append({row['nodeid']: row['duration_s'] for row in profile['tests']})
    costs = [max(1, math.ceil(statistics.median(p[n] for p in profiles) * 1e6)) for n in nodes]
    dump(out / 'costs.json', {'unit': 'microseconds', 'rule': 'max(1, ceil(median of uninstrumented setup+call+teardown seconds across three profile runs * 1e6))',
                            'profile_runs': args.profile_runs, 'nodes': nodes, 'costs': costs})
    cprofile_process = checked_run(SUBJECT, out / 'cprofile', profile=True)
    dump(out / 'profile_summary.json', profile_table(out / 'cprofile/baseline.pstats'))

    print('3. Count greedy, weighted greedy and binary ILP', flush=True)
    methods = {'full': {'method': 'full', 'selected': list(range(len(nodes))),
                        'estimated_cost_us': sum(costs), 'selection_s': 0., 'optimal': False},
               'count_greedy': greedy(covers, costs, universe, weighted=False),
               'weighted_greedy': greedy(covers, costs, universe),
               'ilp': integer_program(covers, costs, universe)}
    for name, method in methods.items():
        if not universe <= covered(method['selected'], covers):
            raise AssertionError('Coverage constraint failed')
        dump(out / 'selections' / (name + '.json'), [nodes[i] for i in method['selected']])
        print(f"   {name}: {len(method['selected'])} tests, {method['estimated_cost_us']} us model cost", flush=True)
    dump(out / 'methods.json', methods)
    # Each reduced suite is retraced from a fresh process; the original matrix is
    # never accepted as evidence of coverage after dependencies/tests are removed.
    validation_processes = []
    for name, method in methods.items():
        if name == 'full':
            continue
        selected = [nodes[i] for i in method['selected']]
        validation_processes.append(checked_run(SUBJECT, out / 'coverage' / name, nodes=selected, trace=True))
        observed = set(read(out / 'coverage' / name / 'incidence.json')['universe'])
        if not universe <= observed:
            raise AssertionError('Fresh selected-suite coverage dropped; do not report an invalid selection')

    print('4. Interleaved fresh-process timings (no tracing)', flush=True)
    timing_rows, order = [], []
    rng = random.Random(241070005)
    for repetition in range(args.repeats):
        names = list(methods)
        rng.shuffle(names)
        for name in names:
            directory = out / 'timings' / f'round_{repetition:02}' / name
            selected = None if name == 'full' else [nodes[i] for i in methods[name]['selected']]
            process = checked_run(SUBJECT, directory, nodes=selected)
            run = pristine_check(directory, nodes if name == 'full' else selected)
            timing_rows.append({'repetition': repetition, 'method': name, 'wall_ns': process['wall_ns'],
                                'pytest_elapsed_ns': run['pytest_elapsed_ns'],
                                'phase_sum_s': sum(t['duration_s'] for t in run['tests']),
                                'path': str(directory.relative_to(out))})
            order.append([repetition, name])
    dump(out / 'timings.json', {'order': order, 'rows': timing_rows})

    print('5. Seeded mutation challenge (selection is already frozen)', flush=True)
    mutation_design = design(SUBJECT, args.mutants)
    dump(out / 'mutation_design.json', mutation_design)
    mutation_rows = []
    (ROOT / 'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mutants-', dir=ROOT / 'build') as temp:
        for descriptor in mutation_design['mutants']:
            mutant = materialize(SUBJECT, Path(temp) / descriptor['id'], descriptor)
            # Every generated mutant is tested, including full-suite survivors.
            for name, method in methods.items():
                selected = None if name == 'full' else [nodes[i] for i in method['selected']]
                directory = out / 'mutations' / descriptor['id'] / name
                process = run_subject(mutant, directory, nodes=selected, timeout=15)
                classification = classify(process)
                if classification in ('killed', 'survived'):
                    if not (directory / 'run.json').exists():
                        classification = 'invalid'
                    else:
                        observed = read(directory / 'run.json')
                        expected = nodes if selected is None else selected
                        if observed['collected'] != expected or (classification == 'killed' and not observed['failed_reports']):
                            classification = 'invalid'
                row = {'mutant': descriptor['id'], 'method': name, 'classification': classification,
                       'wall_ns': process['wall_ns'], 'exit_code': process['exit_code'],
                       'timed_out': process['timed_out'], 'path': str(directory.relative_to(out)),
                       'mutated_source_sha256': sha_file(mutant / descriptor['path'])}
                mutation_rows.append(row)
            dump(out / 'mutation_results.json', mutation_rows)
            print('   ' + descriptor['id'] + ': ' + ', '.join(r['method'] + '=' + r['classification'] for r in mutation_rows[-len(methods):]), flush=True)
    summary = summarize(out, methods, timing_rows, mutation_rows, universe)
    profile_overhead = baseline_process['wall_ns'] / 1e9 + sum(p['wall_ns'] / 1e9 for p in profiling_processes)
    for name, row in summary.items():
        saving = summary['full']['wall_median_s'] - row['wall_median_s']
        overhead = profile_overhead + row['selection_s']
        row['profiling_plus_selection_s'] = overhead
        row['profiling_plus_selection_break_even_runs'] = math.ceil(overhead / saving) if saving > 0 else None
        row['validated_setup_s'] = overhead + (0 if name == 'full' else read(out / 'coverage' / name / 'process.json')['wall_ns'] / 1e9)
        row['validated_setup_break_even_runs'] = math.ceil(row['validated_setup_s'] / saving) if saving > 0 else None
    dump(out / 'summary.json', summary)
    if source_digest() != metadata['source_digest']:
        raise AssertionError('Pristine subject was modified')
    dump(out / 'completion.json', {'finished_utc': datetime.now(timezone.utc).isoformat(),
                                   'source_unchanged': True, 'timing_trials': len(timing_rows),
                                   'mutation_trials': len(mutation_rows),
                                   'note': 'Complete measurement grid; raw failed/surviving/timeout/invalid mutants retained.'})
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
