"""Recalculate feasibility, coverage, timing and mutation claims from raw evidence."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

from coverage import CoverageData

from .common import ROOT, SUBJECT, dump, sha_file, source_digest
from .mutations import classify, design, mutated_text
from .process import run_subject


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def close(actual, expected, label):
    require(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), label)


def audit(out, replay=False):
    out = Path(out).resolve()
    upstream = read(ROOT / 'UPSTREAM.json')
    for name, digest in upstream['distribution_files_sha256'].items():
        require(sha_file(SUBJECT / name) == digest, 'Upstream changed: ' + name)
    require(sha_file(ROOT / 'inputs/cachetools-7.2.8.tar.gz') == upstream['archive_sha256'], 'sdist hash')
    env = read(out / 'environment.json')
    require(source_digest() == env['source_digest'], 'Production source digest')
    baseline = read(out / 'coverage/full/incidence.json')
    nodes, universe = baseline['test_nodes'], set(baseline['universe'])
    methods, cost = read(out / 'methods.json'), read(out / 'costs.json')
    require(len(nodes) == len(set(nodes)) == 391, 'Collected baseline tests')
    require(cost['nodes'] == nodes, 'Cost/model test order')
    profiles = [read(out / f'profiles/run_{i:02}/run.json') for i in range(env['profile_runs'])]
    samples = [{r['nodeid']: r['duration_s'] for r in profile['tests']} for profile in profiles]
    expected_cost = [max(1, math.ceil(statistics.median(p[n] for p in samples) * 1e6)) for n in nodes]
    require(cost['costs'] == expected_cost, 'Quantized uninstrumented median costs')
    line_counts = {}
    for name, method in methods.items():
        selection = method['selected']
        require(len(selection) == len(set(selection)) and all(isinstance(i, int) and 0 <= i < len(nodes) for i in selection), 'Selection indices')
        selected = [nodes[i] for i in selection]
        require(selected == read(out / f'selections/{name}.json'), 'Node list ' + name)
        covered = set().union(*(set(baseline['coverage'][n]) for n in selected))
        require(universe <= covered, 'Static coverage constraint ' + name)
        require(sum(expected_cost[i] for i in selection) == method['estimated_cost_us'], 'Objective ' + name)
        directory = out / 'coverage' / name
        run, incidence, report = (read(directory / f'{f}.json') for f in ['run', 'incidence', 'coverage_report'])
        require(run['collected'] == selected and run['exit_code'] == 0 and not run['failed_reports'], 'Fresh coverage correctness ' + name)
        data = CoverageData(basename=str(directory / 'contexts.sqlite'))
        data.read()
        reconstructed = {n: set() for n in selected}
        for relative, historical in incidence['measured_files'].items():
            for line, contexts in data.contexts_by_lineno(historical).items():
                for context in contexts:
                    if context in reconstructed:
                        reconstructed[context].add(relative + ':' + str(line))
        require({k: sorted(v) for k, v in reconstructed.items()} == incidence['coverage'], 'SQLite to matrix equality ' + name)
        observed = set().union(*reconstructed.values())
        require(observed == set(incidence['universe']) and universe <= observed, 'Fresh coverage preservation ' + name)
        require(sum(len(f['executed_lines']) for f in report['files'].values()) == report['totals']['covered_lines'], 'Statement totals')
        line_counts[name] = len(observed)
    ilp = methods['ilp']
    require(ilp['status'] in (0, 1) and ilp['gap'] >= 0, 'Solver status')
    if ilp['optimal']:
        require(ilp['status'] == 0 and ilp['gap'] <= 1e-8, 'ILP optimal status')
        close(ilp['dual_bound_ms'], ilp['estimated_cost_us'] / 1000, 'Matching primal/dual')

    timing = read(out / 'timings.json')
    rows = timing['rows']
    require(Counter((r['repetition'], r['method']) for r in rows) == Counter((r, m) for r in range(env['repeats']) for m in methods), 'Complete timing grid')
    require(timing['order'] == [[r['repetition'], r['method']] for r in rows], 'Timing execution order')
    for row in rows:
        directory = out / row['path']
        process, run = read(directory / 'process.json'), read(directory / 'run.json')
        require(not process['trace'] and not process['cprofile'] and not process['timed_out'], 'Uninstrumented timing')
        require(process['exit_code'] == 0 and run['exit_code'] == 0 and not run['failed_reports'], 'Timed suite passes')
        require(run['collected'] == [nodes[i] for i in methods[row['method']]['selected']], 'Timing selected tests')
        require(row['wall_ns'] == process['wall_ns'] >= row['pytest_elapsed_ns'] == run['pytest_elapsed_ns'] > 0, 'Raw timing equality')
        close(row['phase_sum_s'], sum(t['duration_s'] for t in run['tests']), 'Phase sum')

    mutation_design = read(out / 'mutation_design.json')
    require(design(SUBJECT, env['mutants'], env['seed']) == mutation_design, 'Seeded independent mutation design')
    mutations = read(out / 'mutation_results.json')
    require(Counter((r['mutant'], r['method']) for r in mutations) == Counter((m['id'], name) for m in mutation_design['mutants'] for name in methods), 'Complete mutation grid')
    mutant_hashes = {}
    import hashlib
    for descriptor in mutation_design['mutants']:
        text = mutated_text((SUBJECT / descriptor['path']).read_text(), descriptor)
        mutant_hashes[descriptor['id']] = hashlib.sha256(text.encode()).hexdigest()
    for row in mutations:
        directory = out / row['path']
        process = read(directory / 'process.json')
        classification = classify(process)
        if classification in ('killed', 'survived'):
            if not (directory / 'run.json').exists():
                classification = 'invalid'
            else:
                observed = read(directory / 'run.json')
                expected = [nodes[i] for i in methods[row['method']]['selected']]
                if observed['collected'] != expected or (classification == 'killed' and not observed['failed_reports']):
                    classification = 'invalid'
        require(classification == row['classification'], 'Mutation raw classification')
        require(row['mutated_source_sha256'] == mutant_hashes[row['mutant']], 'Mutant source reproducibility')
        require(row['wall_ns'] == process['wall_ns'] and row['exit_code'] == process['exit_code'], 'Mutation process values')

    summary = read(out / 'summary.json')
    base = statistics.median(r['wall_ns'] / 1e9 for r in rows if r['method'] == 'full')
    base_killed = {r['mutant'] for r in mutations if r['method'] == 'full' and r['classification'] == 'killed'}
    profiling_s = read(out / 'coverage/full/process.json')['wall_ns'] / 1e9 + sum(read(out / f'profiles/run_{i:02}/process.json')['wall_ns'] / 1e9 for i in range(env['profile_runs']))
    for name, result in summary.items():
        walls = [r['wall_ns'] / 1e9 for r in rows if r['method'] == name]
        pytest_times = [r['pytest_elapsed_ns'] / 1e9 for r in rows if r['method'] == name]
        median = statistics.median(walls)
        for key, expected in [('wall_median_s', median), ('wall_min_s', min(walls)), ('wall_max_s', max(walls)),
                              ('pytest_median_s', statistics.median(pytest_times)), ('wall_speedup', base / median),
                              ('wall_reduction_pct', 100 * (base - median) / base)]:
            close(result[key], expected, key + ' ' + name)
        require(result['tests'] == len(methods[name]['selected']) and result['modeled_cost_us'] == methods[name]['estimated_cost_us'], 'Summary model ' + name)
        require(result['line_universe'] == line_counts[name] and result['line_universe_preserved'], 'Summary coverage')
        coverage = read(out / 'coverage' / name / 'coverage_report.json')['totals']
        for key, source in [('statement_covered', 'covered_lines'), ('statement_total', 'num_statements'), ('branch_covered', 'covered_branches'), ('branch_total', 'num_branches')]:
            require(result[key] == coverage[source], 'Summary coverage total')
        kills = {r['mutant'] for r in mutations if r['method'] == name and r['classification'] == 'killed'}
        require(result['mutants_killed'] == len(kills) and result['full_killed_retained'] == len(kills & base_killed), 'Fault retention')
        valid = {r['mutant'] for r in mutations if r['method'] == name and r['classification'] in ('killed', 'survived')}
        require(result['full_killed_total'] == len(base_killed) and result['paired_valid_full_killed'] == len(base_killed & valid), 'Fault denominator')
        for state, key in [('timeout', 'timeouts'), ('invalid', 'invalid')]:
            require(result[key] == sum(r['classification'] == state for r in mutations if r['method'] == name), 'Exceptional outcome counts')
        require(result['missed_full_killed'] == sorted(base_killed - kills), 'Missed full-suite kills')
        full_branches = read(out / 'coverage/full/coverage_report.json')['totals']['covered_branches']
        require(result['branches_lost_vs_full'] == full_branches - coverage['covered_branches'], 'Lost branches')
        close(result['selection_s'], methods[name]['selection_s'], 'Selection time')
        close(result['profiling_plus_selection_s'], profiling_s + methods[name]['selection_s'], 'Setup overhead')
        saving = base - median
        expected_break_even = math.ceil(result['profiling_plus_selection_s'] / saving) if saving > 0 else None
        require(result['profiling_plus_selection_break_even_runs'] == expected_break_even, 'Setup amortization')
        selected_validation_s = 0 if name == 'full' else read(out / 'coverage' / name / 'process.json')['wall_ns'] / 1e9
        expected_setup = profiling_s + methods[name]['selection_s'] + selected_validation_s
        close(result['validated_setup_s'], expected_setup, 'Validated setup time')
        require(result['validated_setup_break_even_runs'] == (math.ceil(expected_setup / saving) if saving > 0 else None), 'Validated setup amortization')
        require(result['selection_only_break_even_runs'] == (math.ceil(methods[name]['selection_s'] / saving) if saving > 0 else None), 'Selection-only amortization')
    completion = read(out / 'completion.json')
    require(completion['timing_trials'] == len(rows) and completion['mutation_trials'] == len(mutations), 'Completion grid counts')
    replay_rows = {}
    if replay:
        for name, method in methods.items():
            directory = ROOT / 'validation/fresh_replay' / name
            if directory.exists():
                raise ValueError('Do not overwrite replay evidence')
            process = run_subject(SUBJECT, directory, nodes=[nodes[i] for i in method['selected']])
            run = read(directory / 'run.json')
            require(process['exit_code'] == 0 and not run['failed_reports'], 'Independent replay ' + name)
            replay_rows[name] = {'tests': len(run['collected']), 'passed': run['outcomes'].get('passed', 0)}
    result = {'passed': True, 'upstream_files_verified': len(upstream['distribution_files_sha256']),
              'baseline_tests': len(nodes), 'baseline_test_lines': len(universe),
              'coverage_sqlite_matrices_verified': len(methods), 'timing_trials': len(rows),
              'mutation_trials': len(mutations), 'ilp_optimal_for_static_model': ilp['optimal'],
              'fresh_replay': replay_rows,
              'scope': 'Saved evidence consistency and optional pristine-suite replay. No claim of universal correctness or independent reproduction of historical timings.'}
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results')
    parser.add_argument('--replay', action='store_true')
    parser.add_argument('--save')
    args = parser.parse_args()
    result = audit(args.out, args.replay)
    if args.save:
        dump(args.save, result)


if __name__ == '__main__':
    main()
