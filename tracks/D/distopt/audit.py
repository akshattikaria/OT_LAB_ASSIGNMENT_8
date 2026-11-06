"""Recompute saved candidates, learning predictions and resource-accounting identities."""
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from . import federated,multitask,scheduling
from .experiment import write_json


def audit(directory):
    root=Path(directory);read=lambda name:json.loads((root/name).read_text());checks=0
    def close(a,b,tol=1e-8):
        nonlocal checks
        np.testing.assert_allclose(a,b,atol=tol,rtol=0);checks+=1
    for name,sha in read('input_sha256.json').items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:raise AssertionError('Input hash mismatch')
        checks+=1
    coverage=read('coverage_runs.json');instances={}
    for row in coverage:instances.setdefault(row['instance'],[]).append(row)
    exact_cases=0
    for name,rows in instances.items():
        p=read('coverage_inputs/'+name+'.json')
        def value(indices):return sum(p['weights'][u] for u in set().union(*(set(p['sets'][i]) for i in indices)))
        for row in rows:
            selection=row['selected']
            if len(selection)>p['k'] or len(set(selection))!=len(selection):raise AssertionError('Invalid coverage cardinality')
            close(value(selection),row['value'])
        greedy=next(r for r in rows if r['method']=='greedy');lazy=next(r for r in rows if r['method']=='lazy_greedy')
        if greedy['selected']!=lazy['selected']:raise AssertionError('Lazy marginal result differs')
        exact=next((r for r in rows if r['method']=='exact'),None)
        if exact:
            optimum=max(value(S) for S in itertools.combinations(range(len(p['sets'])),p['k']));close(exact['value'],optimum);exact_cases+=1
            if greedy['value']+1e-9 < (1-(1-1/p['k'])**p['k'])*optimum:raise AssertionError('Greedy bound failed')
    fed=read('federated_runs.json');central=read('centralized_runs.json');partitions=read('client_partitions.json');refs={r['seed']:r for r in read('federated_reference.json')}
    learning_iterates=0;e1comparisons=0
    with threadpool_limits(limits=1):
        for row in fed+central:
            with np.load(root/'federated_data'/f'seed{row["seed"]}.npz') as dataset:
                for point in row['trace']:
                    metric=federated.metrics(np.array(point['theta']),dataset)
                    for key,value in metric.items():close(point[key],value)
                    if metric['train_objective']<refs[row['seed']]['objective']-1e-8:raise AssertionError('Below convex reference')
                    learning_iterates+=1
                for key,value in federated.metrics(np.array(row['theta']),dataset).items():close(row[key],value)
                total=row['steps'] if row['method']=='centralized' else row['rounds']*row['local_steps'];close(row['sample_visits'],512*total)
                if row['method']=='FedAvg':
                    close(row['logical_model_bytes'],2*4*7*8*row['rounds']);close(row['gradient_calls'],4*total)
                    if row['local_steps']==1:
                        match=next(r for r in central if r['seed']==row['seed'] and r['steps']==total);close(row['theta'],match['theta'],1e-12);e1comparisons+=1
        for part in partitions:
            indices=[i for group in part['clients'] for i in group]
            if sorted(indices)!=list(range(512)):raise AssertionError('Client split leaked or duplicated data')
            with np.load(root/'federated_data'/f'seed{part["seed"]}.npz') as d:
                close([np.mean(d['ytrain'][group]) for group in part['clients']],part['positive_rates'])
        mtl=read('multitask_runs.json');mtl_iterates=0
        for row in mtl:
            with np.load(root/'multitask_data'/f'{row["family"]}_s{row["seed"]}.npz') as d:
                for point in row['trace']:
                    metric=multitask.metrics(np.array(point['theta']),d)
                    close(metric['train_losses'],point['train_losses']);close(metric['test_mse'],point['test_mse']);close(sum(point['weights']),2)
                    _,gradients=multitask.losses_gradients(np.array(point['theta']),d['Xtrain'],d['Ytrain'],d['scales'])
                    close(np.linalg.norm(multitask.mgda_weights(gradients)@gradients/2),point['mgda_stationarity_norm']);mtl_iterates+=1
                metric=multitask.metrics(np.array(row['theta']),d)
                close(metric['train_losses'],row['train_losses']);close(metric['test_mse'],row['test_mse'])
    strong=read('scheduling_runs.json');weak=read('weak_scaling_runs.json');kernels={}
    for row in strong+weak:
        close(row['steady_s'],row['steady_finish_s']-row['steady_start_s']);close(row['end_to_end_s']-row['steady_s'],row['setup_cleanup_s'])
        if row['steady_start_s']<max(r['ready_s'] for r in row['worker_readiness']):raise AssertionError('Startup timer regression')
        ids=[j['job'] for j in row['jobs']]
        if len(ids)!=len(set(ids)):raise AssertionError('Duplicate scheduled job')
        if len(set(r['pid'] for r in row['worker_records']))!=row['workers']:raise AssertionError('Not distinct worker processes')
        for job in row['jobs']:
            key=(job['job'],job['units'],row['iterations_per_unit'])
            if key not in kernels:kernels[key]=scheduling.kernel(key[:2],key[2])
            if job['digest']!=kernels[key]:raise AssertionError('Kernel result changed')
            if not 0<=job['start']<=job['finish']<=row['steady_s']+1e-7:raise AssertionError('Event outside measurement')
            if job['stolen']!=(job['donor']!=job['worker']):raise AssertionError('Stealing metadata mismatch')
        active=[sum(j['finish']-j['start'] for j in row['jobs'] if j['worker']==rank) for rank in range(row['workers'])]
        close(active,row['active_compute_s']);close(sum(active)/(row['workers']*row['steady_s']),row['observed_utilization'])
        close(sum(j['stolen'] for j in row['jobs']),row['stolen_jobs']);close(sum(j['units'] for j in row['jobs']),row['predicted_total_units'])
    parallel=read('parallel_runs.json')
    for row in parallel['inference']+parallel['pipeline']:
        if row['max_abs_error']>1e-9:raise AssertionError('Parallel numeric mismatch')
        checks+=1
    for row in parallel['pipeline']:
        events={(e['stage'],e['microbatch']):e for e in row['events'] if 'microbatch' in e}
        if len(events)!=2*row['microbatches']:raise AssertionError('Missing pipeline event')
        for i in range(row['microbatches']):
            if events[1,i]['start']<events[0,i]['finish']:raise AssertionError('Pipeline dependency violated')
        close(row['ideal_balanced_stage_bubble_fraction'],1/(row['microbatches']+1))
    for row in read('synchronization_runs.json'):
        close(row['result'],row['total_increments'])
        if row['steady_start_s']<row['last_ready_s']:raise AssertionError('Counter timer includes startup')
    for row in read('communication_runs.json'):close(row['one_way_payload_bytes'],row['messages']*row['bytes_per_message'])
    for row in read('locality_runs.json')['rows']:close(row['result'],row['reference'],1e-7)
    summary={'passed':True,'numeric_comparisons':checks,'coverage_candidates':len(coverage),'exhaustive_coverage_cases':exact_cases,
        'federated_and_central_iterates':learning_iterates,'one_step_FedAvg_equalities':e1comparisons,'multitask_iterates':mtl_iterates,
        'strong_schedule_runs':len(strong),'weak_schedule_runs':len(weak),'distinct_kernel_inputs_recomputed':len(kernels),
        'note':'Every candidate and retained learning prediction recomputed; all task digests and timing boundaries checked. Parallel outputs were compared in full with serial results during measurement; small independent equivalence tests cover data/model/pipeline code. No wall times reconstructed or invented.'}
    write_json(root/'audit.json',summary);return summary
