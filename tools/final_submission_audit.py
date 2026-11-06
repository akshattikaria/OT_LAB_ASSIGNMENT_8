"""Independent retained-data checks for the final submission; no timing reruns."""
import hashlib
import io
import json
import sys
from contextlib import redirect_stdout
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(name):
    return json.loads((ROOT / name).read_text())


def close(a, b, tolerance=1e-8):
    assert np.isclose(a, b, rtol=1e-9, atol=tolerance), (a, b)


def ev_replay():
    """Recompute every retained schedule without using the EV validator."""
    rows = read('tracks/E/results/raw_runs.json')
    checked = feasible_count = 0
    largest_binary_deviation = 0.
    for row in rows:
        assert row['runtime_s'] >= 0 and row['validation_s'] >= 0
        if row['schedule'] is None:
            assert not row['audit']['feasible']
            continue
        case = read('tracks/E/results/instances/' + row['instance'] + '.json')
        x = np.asarray(row['schedule'])
        vehicles = case['vehicles']
        assert x.shape == (len(vehicles), len(case['prices']))
        deviation = float(np.max(np.abs(x - np.rint(x))))
        largest_binary_deviation = max(largest_binary_deviation, deviation)
        assert deviation <= 1e-8 and np.all(x >= -1e-8) and np.all(x <= 1 + 1e-8)
        x = np.rint(x).astype(int)
        power = np.asarray([v['power_kw'] for v in vehicles])
        load = (x * power[:, None]).sum(0)
        outside = 0
        exact = True
        for i, vehicle in enumerate(vehicles):
            a, b = vehicle['arrival'], vehicle['departure']
            outside += int(x[i, :a].sum() + x[i, b:].sum())
            exact &= int(x[i, a:b].sum()) == vehicle['required_slots']
        audit = row['audit']
        close(audit['cost'], np.dot(load, case['prices']) * case['slot_minutes'] / 60)
        close(audit['energy_kwh'], load.sum() * case['slot_minutes'] / 60)
        np.testing.assert_allclose(audit['load_kw'], load, atol=1e-9)
        assert audit['outside_window_slots'] == outside
        valid = bool(exact and outside == 0 and np.all(load <= np.asarray(case['capacity_kw']) + 1e-8))
        assert audit['feasible'] == valid
        feasible_count += valid
        checked += 1
    return {'retained_rows': len(rows), 'schedules_recomputed': checked, 'feasible_schedules': feasible_count, 'largest_binary_solver_deviation': largest_binary_deviation, 'binary_replay_tolerance': 1e-8}


def research_controls():
    placement = read('research_supplement/results/placement.json')
    for row in placement['packing']:
        w = row['weights']
        nodes = [[i for i, n in enumerate(row['initial_mapping']) if n == node] for node in range(4)]
        moved = 0
        for event in row['trace']:
            close(event['before_makespan'], max(sum(w[i] for i in n) for n in nodes))
            donor, receiver = event['donor'], event['receiver']
            assert donor != receiver and len(event['pack']) == len(set(event['pack']))
            assert all(i in nodes[donor] for i in event['pack'])
            close(event['pack_load'], sum(w[i] for i in event['pack']))
            for i in event['pack']:
                nodes[donor].remove(i)
                nodes[receiver].append(i)
            moved += len(event['pack'])
            close(event['after_makespan'], max(sum(w[i] for i in n) for n in nodes))
            assert event['after_makespan'] <= event['before_makespan']
        assert nodes == row['final_nodes']
        assert row['migrated_tasks'] == moved
        assert row['logical_request_reply_messages'] == 2 * len(row['trace'])
        close(row['modeled_makespan'], max(sum(w[i] for i in n) for n in nodes))
    for row in placement['grouping']:
        a = np.asarray(row['affinity'])
        w, speeds = row['work'], row['speeds']
        groups = row['mcl_groups']
        def score(mapping):
            load = [sum(w[i] for i in range(len(w)) if mapping[i] == n) / speeds[n] for n in range(3)]
            remote = sum(a[i, j] * abs(mapping[i] - mapping[j]) for i in range(len(w)) for j in range(i + 1, len(w)))
            return max(load) + .02 * remote, max(load), remote
        for choice in row['assignments']:
            value, makespan, remote = score(choice['mapping'])
            close(choice['modeled_score'], value)
            close(choice['modeled_compute_makespan'], makespan)
            close(choice['remote_affinity_hops'], remote)
        opt = float('inf')
        for choices in product(range(3), repeat=len(groups)):
            mapping = [-1] * len(w)
            for group, node in zip(groups, choices):
                for i in group:
                    mapping[i] = node
            opt = min(opt, score(mapping)[0])
        close(row['exact_group_constrained_optimum'], opt)
    for row in placement['currying']:
        blocks = np.random.default_rng(5400 + row['seed']).normal(size=(9, 32))
        expected = float(np.sin(blocks + row['theta']).sum())
        close(row['direct_result'], expected)
        close(row['curried_result'], expected)
        close(sum(e['partial_value'] for e in row['trace']), expected)
        hops = sum(abs(i // 3) + abs(i % 3) for i in range(9))
        assert row['baseline_logical_byte_hops'] == hops * 32 * 8
        assert row['curried_logical_byte_hops'] == hops * 8
    communication = read('research_supplement/results/communication.json')
    fl_checks = 0
    for row in communication['low_rank_fl']:
        targets = np.random.default_rng(4500 + row['seed']).normal(size=(4, 12, 8))
        irreducible = float(np.mean(np.sum((targets - targets.mean(0)) ** 2, axis=(1, 2))) / 2)
        for point in row['trace']:
            close(point['global_objective'], irreducible + point['distance_to_exact_mean'] ** 2 / 2)
            assert point['feedback_conservation_error'] < 1e-9
            fl_checks += 1
        assert row['logical_uplink_bytes_per_client_round'] == (768 if row['method'] == 'dense' else 192)
        assert row['basis_downlink_bytes_per_round'] == (0 if row['method'] == 'dense' else 288)
        assert row['model_downlink_bytes_per_round'] == 768
    plans = read('research_supplement/results/strategies.json')
    devices = plans['devices']
    parameters = np.asarray(plans['layer_parameters'])
    for plan in plans['plans']:
        assert plan['gpu_count'] == plan['dp'] * plan['tp'] * plan['pipeline'] <= 8
        ends = [0] + plan['cuts'] + [len(parameters)]
        assert len(ends) - 1 == len(plan['device_types']) == plan['pipeline']
        for s, kind in enumerate(plan['device_types']):
            memory = 16 * parameters[ends[s]:ends[s+1]].sum() / plan['tp'] + plan['pipeline'] * 32 * 4096 * 4 / plan['tp']
            close(plan['stage_memory_bytes'][s], memory)
            assert memory <= devices[kind]['memory_bytes']
        close(plan['modeled_samples_s'], 128 * plan['dp'] / plan['modeled_iteration_s'])
        close(plan['modeled_cost_per_1000_samples'], plan['hourly_cost'] / 3600 / plan['modeled_samples_s'] * 1000)
    native = read('research_supplement/results/spmv.json')
    assert all(t['max_error'] <= 1e-8 for r in native['runs'] for t in r['trials'])
    return {'packing_trace_replays': len(placement['packing']), 'grouped_placement_exhaustive_rechecks': len(placement['grouping']), 'currying_numeric_replays': len(placement['currying']), 'low_rank_fl_objective_certificates': fl_checks, 'hybrid_layout_memory_and_cost_checks': len(plans['plans']), 'native_spmv_correctness_trials': sum(len(r['trials']) for r in native['runs']), 'exact_paper_policy_reproduction': False}


def main():
    from tools.audit_project import main as integrated_audit
    with redirect_stdout(io.StringIO()):
        prior = integrated_audit()
    core = read('validation/submission-host-20261107/summary.json')
    supporting = read('validation/submission_supporting_tests_20261107.json')
    assert len(core) == 10 and all(r['passed'] and r['exit_code'] == 0 for r in core)
    assert sum(r['tests'] for r in core) == 243
    assert supporting['passed'] and supporting['tests'] == 55
    for letter in 'ABCDEFGHIJ':
        assert list((ROOT / 'prompts' / letter).glob('*.md'))
    register = (ROOT / 'docs/AI_TOOL_REGISTER.md').read_text()
    table = '\n'.join(line for line in register.splitlines() if line.startswith('|'))
    assert table in (ROOT / 'README.md').read_text()
    assert 'Set the Drive folder access' not in (ROOT / 'docs/SUBMISSION_GUIDE.md').read_text()
    kernel = read('tracks/G/validation/kernel_validation.json')
    assert len(kernel) == 4 and all(r['full_usertests_passed'] and r['smoke_workloads'] >= 3 for r in kernel)
    for r in kernel:
        assert 'ALL TESTS PASSED' in (ROOT / 'tracks/G/validation' / r['uart_log']).read_text()
    return {'passed': True, 'audit_date_local': '2026-11-07', 'core_host_tests_fresh': 243, 'supporting_tests_fresh': 55, 'total_correctness_tests_fresh': 298, 'original_imports_verified': prior['imported_files_verified'], 'pdf_pages': prior['pdf_pages'], 'demo_seconds': prior['demo_seconds'], 'ai_register_in_readme': True, 'submission_route': 'public GitHub repository URL', 'separate_drive_upload_required': False, 'core_guest_validation_records_verified': 4, 'guest_campaign_rerun_now': False, 'ev': ev_replay(), 'research_mechanism_certificates': research_controls(), 'coverage_entries': prior['course_topic_entries'], 'research_entries': prior['research_reference_entries'], 'exact_paper_method_coverage_complete': False, 'scope': 'Fresh correctness and retained-data certificates. Original timings, raw results and guest logs unchanged. Six research spotlight demonstrations retain declared mechanism-only scope; no exact unpublished paper policies or instructor approval are asserted.'}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
