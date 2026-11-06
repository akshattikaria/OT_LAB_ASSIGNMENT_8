from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
from time import perf_counter
import numpy as np
import scipy
from threadpoolctl import threadpool_info,threadpool_limits
from . import coverage,federated,multitask,scheduling,parallel,locality


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def environment():
    affinity=sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else list(range(os.cpu_count() or 1))
    quota_path=Path('/sys/fs/cgroup/cpu.max');quota=quota_path.read_text().split() if quota_path.exists() else None
    capacity=float(quota[0])/float(quota[1]) if quota and quota[0]!='max' else len(affinity)
    return {'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,
        'platform':platform.platform(),'logical_cpus':os.cpu_count(),'affinity':affinity,'cpu_max':quota,
        'effective_cpu_capacity':min(len(affinity),capacity),'blas_libraries':threadpool_info(),
        'note':'Measured on this cloud workspace. No user-laptop, GPU, network-cluster, or multi-device performance claim.'}


def run_coverage(root,seeds):
    rows=[];folder=root/'coverage_inputs';folder.mkdir()
    for n in (10,16,80):
        for family in ('independent','clustered','redundant'):
            for seed in seeds:
                p=coverage.generate(n,seed,family);identity=f'{family}_n{n}_s{seed}';write_json(folder/f'{identity}.json',p.json())
                for method in ('input_order','singleton','greedy','lazy_greedy')+ (('exact',) if n<=20 else ()):
                    start=perf_counter();run=coverage.solve(p,method);rows.append({'instance':identity,'family':family,'n':n,'seed':seed,'k':p.k,
                        'runtime_s':perf_counter()-start,'cardinality_upper_bound':min(float(sum(p.weights)),sum(sorted((p.value([i]) for i in range(n)),reverse=True)[:p.k])),**run})
    counter=coverage.Coverage([{0,1,3,4},{0,1,2},{3,4,5}],[1]*6,2)
    assumption=coverage.Coverage(coverage.generate(10,999,'independent').sets[:8],[1]*20,3)
    controls={'greedy_counterexample':{'input':counter.json(),'runs':[coverage.solve(counter,m) for m in ('greedy','lazy_greedy','exact')]},
        'exhaustive_assumptions':coverage.exhaustive_assumptions(assumption),
        'non_submodular_control':{'function':'|S|^2','A':[],'B':[0],'e':1,'gain_A':1,'gain_B':3,'diminishing_returns':False,
            'note':'The cardinality-greedy theorem is not claimed for arbitrary non-submodular objectives.'}}
    write_json(root/'coverage_runs.json',rows);write_json(root/'coverage_controls.json',controls)


def run_federated(root,seeds):
    folder=root/'federated_data';folder.mkdir();fed=[];central=[];refs=[];partitions=[]
    totals=sorted(set(E*R for E in (1,5,20) for R in (6,24,120)))
    with threadpool_limits(limits=1):
        for seed in seeds:
            d=federated.data(seed);np.savez_compressed(folder/f'seed{seed}.npz',**d);refs.append({'seed':seed,**federated.reference(d)})
            for steps in totals:central.append({'seed':seed,**federated.centralized(d,steps)})
            for kind in ('iid','label_skew'):
                clients=federated.partition(d['ytrain'],kind,seed)
                partitions.append({'seed':seed,'partition':kind,'clients':[c.tolist() for c in clients],
                    'sizes':[len(c) for c in clients],'positive_rates':[float(np.mean(d['ytrain'][c])) for c in clients]})
                for E in (1,5,20):
                    for R in (6,24,120):fed.append({'seed':seed,'partition':kind,**federated.fedavg(d,clients,E,R)})
            print(f'FedAvg seed {seed} complete',flush=True)
    write_json(root/'federated_runs.json',fed);write_json(root/'centralized_runs.json',central)
    write_json(root/'federated_reference.json',refs);write_json(root/'client_partitions.json',partitions)


def run_multitask(root,seeds,steps):
    folder=root/'multitask_data';folder.mkdir();rows=[]
    with threadpool_limits(limits=1):
        for family in ('conflict_equal','conflict_10x','aligned_10x'):
            for seed in seeds:
                d=multitask.data(seed,family);np.savez_compressed(folder/f'{family}_s{seed}.npz',**d)
                for method in ('Equal','MGDA','GradNorm'):rows.append({'family':family,'seed':seed,**multitask.train(d,method,steps)})
            print(f'Multi-task {family} complete',flush=True)
    write_json(root/'multitask_runs.json',rows)


def run_scheduling(root,workers,repeats,iterations):
    rows=[];workloads={'uniform':[(i,4) for i in range(32)],'irregular':[(i,12 if i<8 else 1) for i in range(32)]}
    methods=('static_block','static_lpt','dynamic_pool','work_stealing')
    references={family:{i:scheduling.kernel(job,iterations) for i,job in enumerate(jobs)} for family,jobs in workloads.items()}
    trials=[(family,method,p,r) for family in workloads for method in methods for p in workers for r in range(repeats)]
    order=np.random.default_rng(5100).permutation(len(trials))
    for count,index in enumerate(order):
        family,method,p,repeat=trials[index];run=scheduling.schedule(workloads[family],p,method,iterations)
        if any(row['digest']!=references[family][row['job']] for row in run['jobs']):raise AssertionError('Scheduled computation changed')
        rows.append({'family':family,'repeat':repeat,**run})
        if (count+1)%12==0:print(f'Strong-scaling schedule trials {count+1}/{len(trials)} complete',flush=True)
    write_json(root/'scheduling_runs.json',rows)
    weak=[]
    for p in workers:
        jobs=[(i,2) for i in range(16*p)];ref={job[0]:scheduling.kernel(job,iterations) for job in jobs}
        for repeat in range(repeats):
            run=scheduling.schedule(jobs,p,'static_lpt',iterations)
            if any(row['digest']!=ref[row['job']] for row in run['jobs']):raise AssertionError('Weak-scaling computation changed')
            weak.append({'repeat':repeat,'scaling':'weak','jobs_per_worker':16,**run})
    write_json(root/'weak_scaling_runs.json',weak)


def run_system_controls(root,workers,repeats):
    sync=[]
    for p in workers:
        for method in ('locked_each','private_reduce'):
            for repeat in range(repeats):sync.append({'repeat':repeat,**scheduling.synchronization(p,method)})
    write_json(root/'synchronization_runs.json',sync)
    comm=[]
    for messages,size in ((100,1024),(100,65536),(100,1048576),(1000,100),(10,10000)):
        for repeat in range(repeats):comm.append({'repeat':repeat,**scheduling.communication(messages,size)})
    write_json(root/'communication_runs.json',comm);write_json(root/'locality_runs.json',locality.measure(repeats))


def run_benchmark(directory,seeds=(0,1,2,3,4),workers=None,repeats=3,iterations=30000,mtl_steps=400):
    root=Path(directory)
    if root.exists() and any(root.iterdir()):raise ValueError('Choose a new empty output folder')
    if not seeds or len(seeds)!=len(set(seeds)) or repeats<1 or iterations<1 or mtl_steps<10:raise ValueError('Invalid protocol')
    env=environment();capacity=max(1,math.floor(env['effective_cpu_capacity']))
    if workers is None:workers=tuple(p for p in (1,2,4,8) if p<=capacity)
    if not workers or 1 not in workers or len(set(workers))!=len(workers) or any(p<1 or p>capacity for p in workers):raise ValueError('Workers must be unique, include 1, and fit the detected CPU quota/affinity')
    root.mkdir(parents=True,exist_ok=True);write_json(root/'environment.json',env)
    write_json(root/'protocol.json',{'seeds':list(seeds),'workers':list(workers),'repeats':repeats,'iterations_per_unit':iterations,'mtl_steps':mtl_steps,
        'coverage':'Three weighted-coverage families; n=10,16,80; exact enumeration only n<=20. Cardinality budget, nonnegative weights, f(empty)=0.',
        'scheduling':'32 fixed jobs/family; PBKDF2 CPU kernel; actual spawned processes; predeclared shuffled trial order. Ready handshake excludes startup from steady timers; end-to-end retains setup and cleanup.',
        'work_stealing':'Each worker owns a shared-array deque protected by a lock; idle workers take unstarted jobs from another deque. Lock/scan overhead is included. Dynamic central task pool is separately named.',
        'parallel_inference':'Data and hidden-unit tensor parallelism via shared-memory threads; native BLAS one thread/kernel; identical weights/inputs/output. Two-stage pipeline is inference, not backpropagation.',
        'federated':'Serial client emulation: four unequal clients, full participation, full-batch local GD, E=1/5/20, R=6/24/120. Train/test data retained. No real network or privacy guarantee.',
        'federated_fairness':'Compute-matched E*R=120 comparisons and fixed-round comparisons shown separately. Centralized runs match every distinct E*R. Logical model bytes exclude protocol/security overhead.',
        'multitask':'Two regression tasks sharing all seven coefficients with fixed identity readouts. Equal, exact two-task shared-gradient MGDA, GradNorm; same initialization and steps. Raw losses and unscaled per-task test MSE reported.',
        'multitask_settings':'Model learning rate 0.03; weights sum 2 for all methods. GradNorm alpha=1.5, weight rate=0.01, positive projection 1e-6; targets stop-gradient. No test-based tuning.',
        'timing':'Cloud CPU wall times only. Fixed-size strong scaling and fixed-work-per-worker weak scaling are distinct. No GPU/multi-node results or simulated timing claims.',
        'fairness_limits':'Few repeats on shared cloud hardware; scheduling methods have different control structures and setup costs. Pipeline partitioning changes BLAS sizes; interpret all overheads, not only compute.'})
    run_coverage(root,seeds);run_federated(root,seeds);run_multitask(root,seeds,mtl_steps)
    run_scheduling(root,workers,repeats,iterations)
    write_json(root/'parallel_runs.json',parallel.measure_inference(workers,repeats))
    run_system_controls(root,workers,repeats)
    sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('coverage_inputs','federated_data','multitask_data') for p in sorted((root/folder).glob('*'))}
    write_json(root/'input_sha256.json',sources);print('All Track D raw experiments complete',flush=True)
