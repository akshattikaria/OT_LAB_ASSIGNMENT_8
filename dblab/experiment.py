from contextlib import closing
from datetime import datetime,timezone
import hashlib
import os
from pathlib import Path
import platform
import random
import shutil
import sqlite3
import statistics
import sys
import time
import numpy as np
import scipy
from .core import ROOT,INDEXES,QUERIES,WEIGHTS,cases,connect,dump,fingerprint,generate_rows,populate,reference,sha_file
from .select import greedy,ilp,exhaustive,utility


def install(base,target,selected):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise FileExistsError(target)
    shutil.copyfile(base,target);start=time.perf_counter()
    with closing(connect(target)) as c:
        c.execute('BEGIN')
        for name in selected:c.execute(INDEXES[name])
        c.execute('COMMIT');index_seconds=time.perf_counter()-start
        analyze_start=time.perf_counter();c.execute('ANALYZE');analyze_seconds=time.perf_counter()-analyze_start
        sizes=dict(c.execute('SELECT name,SUM(pgsize) FROM dbstat GROUP BY name').fetchall())
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    return {'selected':list(selected),'index_bytes':sum(sizes.get(name,0) for name in selected),'object_bytes':sizes,'file_bytes':target.stat().st_size,
            'index_build_s':index_seconds,'analyze_s':analyze_seconds}


def execute(c,case):return c.execute(QUERIES[case['kind']],case['params']).fetchall()


def checked(c,case,truth):
    start=time.perf_counter_ns();rows=execute(c,case);elapsed=time.perf_counter_ns()-start;digest=fingerprint(rows)
    if digest!=truth[case['id']]['sha256']:raise AssertionError('Query output differs: '+case['id'])
    return {'case':case['id'],'kind':case['kind'],'split':case['split'],'elapsed_ns':elapsed,'rows':len(rows),'sha256':digest}


def plans(path,query_cases):
    with closing(connect(path,readonly=True)) as c:
        return [{'case':case['id'],'kind':case['kind'],'params':case['params'],'plan':[list(row) for row in c.execute('EXPLAIN QUERY PLAN '+QUERIES[case['kind']],case['params']).fetchall()]} for case in query_cases]


def build_model(samples,catalog,profile_repeats):
    names=list(INDEXES);kind_order=list(WEIGHTS);times={};base=[];benefits=[]
    for kind in kind_order:
        row=[]
        for profile in ['none']+names:
            case_ids=sorted({r['case'] for r in samples if r['profile']==profile and r['kind']==kind})
            values=[statistics.median(r['elapsed_ns']/1e6 for r in samples if r['profile']==profile and r['case']==case_id) for case_id in case_ids]
            if len(case_ids)!=2 or any(sum(r['case']==case_id and r['profile']==profile for r in samples)!=profile_repeats for case_id in case_ids):raise AssertionError('Incomplete training samples')
            row.append(statistics.mean(values))
        times[kind]=dict(zip(['none']+names,row));base.append(row[0]);benefits.append([WEIGHTS[kind]/100*max(0,row[0]-value) if row[0]-value>=.05*row[0] else 0 for value in row[1:]])
    return {'indexes':names,'kinds':kind_order,'weights':WEIGHTS,'training_median_mean_ms':times,'baseline_weighted_ms':sum(WEIGHTS[k]/100*times[k]['none'] for k in kind_order),
            'weighted_gains_ms':benefits,'costs_kib':[catalog[name]['index_bytes']/1024 for name in names],
            'benefit_noise_threshold':.05,'note':'Per-family mean of two parameter-case median latencies. Benefit below 5% of baseline latency is set to zero. Portfolio gain is the sum across query families of their best selected single-index weighted gain; overlaps are not additive. Joint-index complementarity and planner regressions are not modeled.'}


def run(directory,rows=200000,repeats=5,profile_repeats=3,stream_size=100,write_rows=2000,write_repeats=3,seed=241070005):
    output=Path(directory).resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty result folder')
    if min(rows,repeats,profile_repeats,stream_size,write_rows,write_repeats)<1 or stream_size%100:raise ValueError('Positive budgets; stream size must be a multiple of 100')
    output.mkdir(parents=True,exist_ok=True);work=ROOT/'build'/hashlib.sha256(str(output).encode()).hexdigest()[:12]
    if work.exists():raise FileExistsError('Build workspace already exists; choose a fresh output path')
    work.mkdir(parents=True);base=output/'data'/'charging.db';bookings,facts=populate(base,rows,seed);query_cases=cases();train=[c for c in query_cases if c['split']=='train'];heldout=[c for c in query_cases if c['split']=='heldout']
    truth={c['id']:{'rows':[list(r) for r in reference(bookings,c)],'sha256':fingerprint(reference(bookings,c))} for c in query_cases}
    dump(output/'data_manifest.json',facts);dump(output/'cases.json',query_cases);dump(output/'reference_results.json',truth)
    source_files=['core.py','select.py','experiment.py']
    with closing(connect(base,readonly=True)) as c:
        options=[r[0] for r in c.execute('PRAGMA compile_options')];source_id=c.execute('SELECT sqlite_source_id()').fetchone()[0]
        pragmas={name:c.execute('PRAGMA '+name).fetchone()[0] for name in ('automatic_index','foreign_keys','cache_size','temp_store','mmap_size','threads','journal_mode','synchronous','page_size')}
    quota=Path('/sys/fs/cgroup/cpu.max')
    dump(output/'environment.json',{'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'sqlite':sqlite3.sqlite_version,'sqlite_source_id':source_id,'compile_options':options,'numpy':np.__version__,'scipy':scipy.__version__,'pragmas':pragmas,'host_logical_cpus':os.cpu_count(),'host_affinity':sorted(os.sched_getaffinity(0)),'host_cpu_max':quota.read_text().strip() if quota.exists() else None,'source_sha256':{name:sha_file(ROOT/'dblab'/name) for name in source_files}})
    protocol={'rows':rows,'seed':seed,'repeats':repeats,'profile_repeats':profile_repeats,'stream_size':stream_size,'write_rows':write_rows,'write_repeats':write_repeats,
              'weights':WEIGHTS,'budget_fractions':[.20,.40,.60],'indexes':INDEXES,'queries':QUERIES,'timing':'perf_counter_ns around execute+fetchall only for per-query latencies; hashes outside timing. Batch throughput includes the sequential execute/fetch/Python loop, checks after timing. Warmup excludes initial runs; no cold disk/cache claim.',
              'planner':'SQLite default cost planner with automatic_index=ON and full ANALYZE for every portfolio; no INDEXED BY hints or manual join-order forcing.',
              'storage':'Budget limits selected index B-tree bytes from dbstat, in exact KiB units; total DB bytes and build/analyze costs reported separately. Data/primary keys/statistics are not charged to the discretionary index budget.',
              'evaluation':'Two training parameter sets per family select indexes. Three held-out sets per family evaluate generalization. Matched deterministic query orders per repeat; fresh connection per portfolio/repeat; OS caches warm, pager cache 8 MiB. Unique portfolios timed once and shared by method labels.'}
    dump(output/'protocol.json',protocol);(output/'queries.sql').write_text('\n\n'.join('-- '+name+'\n'+sql+';' for name,sql in QUERIES.items())+'\n')
    profiles={};catalog={}
    for name in ['none']+list(INDEXES):
        path=work/('profile_'+name+'.db');record=install(base,path,[] if name=='none' else [name]);profiles[name]=path;catalog[name]=record
    dump(output/'candidate_storage.json',catalog);dump(output/'training_plans.json',{name:plans(path,train) for name,path in profiles.items()})
    samples=[];trials=[(name,repeat) for name in profiles for repeat in range(profile_repeats)];random.Random(501).shuffle(trials)
    for name,repeat in trials:
        order=train.copy();random.Random(502+repeat).shuffle(order)
        with closing(connect(profiles[name],readonly=True)) as c:
            for case in order:checked(c,case,truth)
            for case in order:samples.append({'profile':name,'repeat':repeat,**checked(c,case,truth)})
        dump(output/'training_runs.json',samples)
    model=build_model(samples,catalog,profile_repeats);dump(output/'model.json',model);selections=[];oracles=[];total=sum(model['costs_kib'])
    for fraction in protocol['budget_fractions']:
        budget=int(total*fraction//4)*4;oracle=exhaustive(model['costs_kib'],model['weighted_gains_ms'],budget);oracles.append({'fraction':fraction,'budget_kib':budget,**oracle})
        for method,solver in [('greedy',greedy),('ilp',ilp)]:
            result=solver(model['costs_kib'],model['weighted_gains_ms'],budget)
            if result['cost_kib']>budget+1e-7 or (method=='ilp' and abs(result['utility_ms']-oracle['best']['utility_ms'])>1e-6):raise AssertionError('Selection failed exhaustive model certificate')
            selections.append({'method':method,'fraction':fraction,'budget_kib':budget,**result})
    dump(output/'selections.json',selections);dump(output/'exhaustive_model.json',oracles);print('Training complete; greedy and ILP certified against all 64 model portfolios',flush=True)
    unique={():None,tuple(range(len(INDEXES))):None}
    for selection in selections:unique[tuple(selection['selected'])]=None
    portfolios={};metadata={};names=list(INDEXES)
    for selected in unique:
        identifier='none' if not selected else 'p_'+'_'.join(map(str,selected));path=work/(identifier+'.db');metadata[identifier]={'positions':list(selected),**install(base,path,[names[i] for i in selected])};portfolios[identifier]=path;unique[selected]=identifier
    for selection in selections:selection['portfolio']=unique[tuple(selection['selected'])]
    dump(output/'selections.json',selections);dump(output/'portfolios.json',metadata);dump(output/'plans.json',{name:plans(path,query_cases) for name,path in portfolios.items()})
    mixed=[]
    for repeat in range(repeats):
        r=random.Random(800+repeat);trace=[]
        for kind,weight in WEIGHTS.items():trace.extend(r.choice([c for c in heldout if c['kind']==kind])['id'] for _ in range(weight*stream_size//100))
        r.shuffle(trace);mixed.append(trace)
    dump(output/'throughput_traces.json',mixed);case_by_id={c['id']:c for c in query_cases};latencies=[];throughput=[]
    trials=[(name,repeat) for name in portfolios for repeat in range(repeats)];random.Random(700).shuffle(trials)
    for name,repeat in trials:
        order=query_cases.copy();random.Random(701+repeat).shuffle(order)
        with closing(connect(portfolios[name],readonly=True)) as c:
            for case in order:checked(c,case,truth)
            for case in order:latencies.append({'portfolio':name,'repeat':repeat,**checked(c,case,truth)})
            trace=mixed[repeat];start=time.perf_counter_ns();outputs=[execute(c,case_by_id[identifier]) for identifier in trace];elapsed=time.perf_counter_ns()-start
            for identifier,result in zip(trace,outputs):
                if fingerprint(result)!=truth[identifier]['sha256']:raise AssertionError('Throughput query result differs')
            throughput.append({'portfolio':name,'repeat':repeat,'requests':len(trace),'elapsed_ns':elapsed,'queries_per_second':len(trace)*1e9/elapsed,'trace_sha256':fingerprint(trace),'output_sha256':fingerprint(outputs)})
        dump(output/'latency_runs.json',latencies);dump(output/'throughput_runs.json',throughput);print(f'{name}, repetition {repeat}: checked 30 query cases and {stream_size} mixed requests',flush=True)
    writes=[]
    for name,path in portfolios.items():
        for repeat in range(write_repeats):
            trial=work/(f'write_{name}_{repeat}.db');shutil.copyfile(path,trial);inserted=generate_rows(write_rows,seed+1000+repeat,rows+1)
            with closing(connect(trial)) as c:
                start=time.perf_counter_ns();c.execute('BEGIN IMMEDIATE');c.executemany('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',inserted);c.execute('COMMIT');elapsed=time.perf_counter_ns()-start
                if c.execute('SELECT * FROM bookings WHERE id>? ORDER BY id',(rows,)).fetchall()!=inserted:raise AssertionError('Insert data mismatch')
                if c.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]!=rows+write_rows or c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():raise AssertionError('Write correctness failed')
            writes.append({'portfolio':name,'repeat':repeat,'inserted':write_rows,'elapsed_ns':elapsed,'rows_per_second':write_rows*1e9/elapsed,'inserted_sha256':fingerprint(inserted),'file_bytes_after':trial.stat().st_size})
        print(name+' write-cost trials complete',flush=True)
    dump(output/'write_runs.json',writes)
    if sha_file(base)!=facts['file_sha256']:raise AssertionError('Baseline data changed')
    dump(output/'evidence_sha256.json',{str(path.relative_to(output)):sha_file(path) for path in sorted(output.rglob('*')) if path.is_file()});return output
