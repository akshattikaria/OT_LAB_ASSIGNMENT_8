"""All runs retained, independently audited, and compared with a DP reference."""
from datetime import datetime,timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
from time import perf_counter
import numpy as np
import scipy

from .data import FAMILIES,generate,controls,teaching
from .model import audit
from .solvers import SOLVERS,integer_programming,dynamic_programming


def write_json(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def environment():
    cpu='unknown';p=Path('/proc/cpuinfo')
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith('model name'):cpu=line.split(':',1)[1].strip();break
    quota=Path('/sys/fs/cgroup/cpu.max')
    return {"utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,"numpy":np.__version__,"scipy":scipy.__version__,
        "platform":platform.platform(),"cpu":cpu,"logical_cpus":os.cpu_count(),
        "affinity_cpus":len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
        "cpu_quota":quota.read_text().strip() if quota.exists() else None,
        "thread_env":{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        "note":"Sequential CPU runs; numerical-library/HiGHS threading not explicitly fixed. No GPU or quantum hardware used."}


def run_benchmark(directory,sizes=(10,20,40,80),seeds=(0,1,2,3,4),repeats=3,time_limit=2.0):
    if not sizes or not seeds or repeats<1:raise ValueError('Nonempty sizes/seeds and positive repeats required')
    if len(set(sizes))!=len(sizes) or len(set(seeds))!=len(seeds):raise ValueError('Sizes and seeds must be unique')
    if not np.isfinite(time_limit) or time_limit<=0:raise ValueError('Positive finite time limit required')
    output=Path(directory)
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output directory')
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'environment.json',environment())
    write_json(output/'protocol.json',{"sizes":list(sizes),"seeds":list(seeds),"families":list(FAMILIES),"repeats":repeats,
        "search_time_limit_s":time_limit,"branch_bound_node_limit":100000,"ilp_relative_gap_target":0.0,
        "canonical_quality_repeat":0,"dp_max_cells":10000000,
        "timing":"perf_counter includes input validation/model construction/solver execution; excludes generation, independent audit, references, plotting and imports",
        "quality":"Relative value gap = 100*(DP_optimum-candidate_value)/DP_optimum, or zero if optimum=0. Only feasible candidates enter quality means.",
        "repeat_note":"Algorithms/input fixed; method order deterministically shuffled. Quality uses repeat 0; runtime aggregates all repeats. No best-run selection.",
        "reference":"An untimed exact DP solution on each instance supplies a reference, verified independently on 100 small random cases and cross-checked against other exact solvers.",
        "warmup":"One untimed tiny ILP call before main measurements.","inputs":"All synthetic, positive integer costs and nonnegative integer values."})
    integer_programming(teaching(),time_limit=time_limit)
    cases=[generate(n,seed,family) for family in FAMILIES for n in sizes for seed in seeds]+controls()
    records=[]
    for index,p in enumerate(cases,1):
        p.save(output/'instances'/f'{p.name}.json')
        reference=dynamic_programming(p);ref=audit(p,reference.selection)
        if reference.status!='optimal' or not ref['feasible']:raise AssertionError('Main reference exceeds DP resource limits')
        for repeat in range(repeats):
            methods=list(SOLVERS);random.Random(f'{p.name}/{repeat}').shuffle(methods)
            for position,method in enumerate(methods):
                start=perf_counter();solution=SOLVERS[method](p,time_limit=time_limit);elapsed=perf_counter()-start
                checked=audit(p,solution.selection)
                if solution.status=='optimal' and (not checked['feasible'] or checked['value']!=ref['value']):
                    raise AssertionError(f'False optimum for {p.name}/{method}: {checked}')
                if checked['feasible'] and checked['value']>ref['value']:raise AssertionError('Candidate exceeds exact reference')
                reported=solution.details.get('objective')
                if checked['feasible'] and reported is not None and not np.isclose(reported,checked['value'],atol=1e-6,rtol=0):
                    raise AssertionError('Reported objective differs from independently evaluated selection')
                upper=solution.details.get('upper_bound')
                if upper is not None and upper+1e-6<ref['value']:raise AssertionError('Invalid claimed upper bound')
                gap=None if not checked['feasible'] else 0.0 if ref['value']==0 else 100*(ref['value']-checked['value'])/ref['value']
                records.append({"instance":p.name,"family":p.metadata.get('family'),"n":p.n,"seed":p.metadata.get('seed'),
                    "repeat":repeat,"method_order":position,"runtime_s":elapsed,"reference_value":ref['value'],
                    "value_gap_percent":gap,**solution.to_dict(),"audit":checked})
        print(f'[{index}/{len(cases)}] {p.name}',flush=True)
        write_json(output/'raw_runs.json',records)
    flat=[]
    for r in records:
        flat.append({**{k:r[k] for k in ('instance','family','n','seed','repeat','method_order','method','status','runtime_s','reference_value','value_gap_percent')},
            **{k:r['audit'][k] for k in ('feasible','value','weight')},"upper_bound":r['details'].get('upper_bound'),
            "nodes":r['details'].get('nodes'),"mip_gap":r['details'].get('mip_gap'),
            "dp_table_cells":r['details'].get('table_cells'),"dp_table_bytes":r['details'].get('table_bytes')})
    with (output/'runs.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    from .supplement import supplementary
    print('Running feature-selection, penalty-strength and DP-scaling experiments',flush=True)
    supplementary(output,write_json,seeds=seeds,repeats=repeats)
    paths=list((output/'instances').glob('*.json'))+list((output/'feature_datasets').glob('*.npz'))+list((output/'quantum_baselines').glob('*.json'))
    write_json(output/'input_and_quantum_sha256.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
    write_json(output/'summary.json',summarize(records))
    return records


def summarize(records):
    summary=[]
    for family in FAMILIES:
        for method in SOLVERS:
            all_rows=[r for r in records if r['family']==family and r['method']==method]
            canonical=[r for r in all_rows if r['repeat']==0]
            if not canonical:continue
            valid=[r for r in canonical if r['audit']['feasible']]
            medians=[statistics.median(q['runtime_s'] for q in all_rows if q['instance']==r['instance']) for r in canonical]
            gaps=[r['value_gap_percent'] for r in valid]
            summary.append({"family":family,"method":method,"instances":len(canonical),"feasible":len(valid),
                "certified_optimal":sum(r['status']=='optimal' for r in canonical),
                "matches_optimal_value":sum(r['audit']['value']==r['reference_value'] for r in valid),
                "mean_gap_percent":statistics.mean(gaps) if gaps else None,
                "sd_gap_percent":statistics.stdev(gaps) if len(gaps)>1 else 0.0 if gaps else None,
                "max_gap_percent":max(gaps) if gaps else None,"median_runtime_s":statistics.median(medians),
                "runtime_q1_s":float(np.percentile(medians,25)),"runtime_q3_s":float(np.percentile(medians,75))})
    return summary
