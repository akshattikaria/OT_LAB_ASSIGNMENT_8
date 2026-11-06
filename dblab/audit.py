"""Verify retained measurements and replay SQL without replacing timing data."""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from .core import ROOT,INDEXES,QUERIES,WEIGHTS,connect,fingerprint,generate_rows,reference,sha_file,dump
from .experiment import build_model,install,execute
from .select import exhaustive,utility


def audit(directory):
    root=Path(directory);read=lambda name:json.loads((root/name).read_text());protocol=read('protocol.json');env=read('environment.json');facts=read('data_manifest.json');truth=read('reference_results.json');query_cases=read('cases.json');by_id={c['id']:c for c in query_cases};checks=0
    for name,digest in read('evidence_sha256.json').items():
        if sha_file(root/name)!=digest:raise AssertionError('Evidence checksum mismatch: '+name)
        checks+=1
    for name,digest in env['source_sha256'].items():
        if sha_file(ROOT/'dblab'/name)!=digest:raise AssertionError('Measured implementation changed: '+name)
        checks+=1
    base=root/'data/charging.db'
    if sha_file(base)!=facts['file_sha256']:raise AssertionError('Dataset file identity changed')
    generated=generate_rows(protocol['rows'],protocol['seed'])
    if fingerprint(generated)!=facts['logical_rows_sha256']:raise AssertionError('Generator identity changed')
    for case in query_cases:
        expected=reference(generated,case)
        if fingerprint(expected)!=truth[case['id']]['sha256'] or fingerprint(truth[case['id']]['rows'])!=fingerprint(expected):raise AssertionError('Independent reference mismatch')
        checks+=1
    with closing(connect(base,readonly=True)) as c:
        if fingerprint(c.execute('SELECT * FROM bookings ORDER BY id').fetchall())!=facts['logical_rows_sha256']:raise AssertionError('Database differs from generated rows')
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():raise AssertionError('Baseline integrity failed')
    train=read('training_runs.json');catalog=read('candidate_storage.json');model=read('model.json')
    if build_model(train,catalog,protocol['profile_repeats'])!=model:raise AssertionError('Training model differs from raw timings')
    expected_train={(profile,repeat,c['id']) for profile in ['none']+list(INDEXES) for repeat in range(protocol['profile_repeats']) for c in query_cases if c['split']=='train'}
    observed=[(r['profile'],r['repeat'],r['case']) for r in train]
    if len(set(observed))!=len(observed) or set(observed)!=expected_train:raise AssertionError('Training sample cells missing/duplicated')
    for row in train:
        if row['elapsed_ns']<=0 or row['sha256']!=truth[row['case']]['sha256'] or row['rows']!=len(truth[row['case']]['rows']):raise AssertionError('Invalid training measurement')
        checks+=1
    selections=read('selections.json');oracles=read('exhaustive_model.json');portfolios=read('portfolios.json');names=list(INDEXES)
    for record in oracles:
        if exhaustive(model['costs_kib'],model['weighted_gains_ms'],record['budget_kib'])!={k:v for k,v in record.items() if k not in ('fraction','budget_kib')}:raise AssertionError('Exhaustive certificate differs')
        checks+=64
    for row in selections:
        selected=row['selected'];value=utility(selected,model['weighted_gains_ms']);cost=sum(model['costs_kib'][i] for i in selected);certificate=next(r for r in oracles if r['fraction']==row['fraction'])
        if abs(value-row['utility_ms'])>1e-9 or cost!=row['cost_kib'] or cost>row['budget_kib']:raise AssertionError('Selection violates objective/budget')
        if row['method']=='ilp' and abs(value-certificate['best']['utility_ms'])>1e-6:raise AssertionError('ILP not model-optimal')
        if portfolios[row['portfolio']]['positions']!=selected:raise AssertionError('Selection/physical portfolio mismatch')
        checks+=3
    latency=read('latency_runs.json');expected={(p,r,c['id']) for p in portfolios for r in range(protocol['repeats']) for c in query_cases};observed=[(r['portfolio'],r['repeat'],r['case']) for r in latency]
    if len(set(observed))!=len(observed) or set(observed)!=expected:raise AssertionError('Latency cells missing/duplicated')
    for row in latency:
        if row['elapsed_ns']<=0 or row['sha256']!=truth[row['case']]['sha256'] or row['rows']!=len(truth[row['case']]['rows']) or row['kind']!=by_id[row['case']]['kind'] or row['split']!=by_id[row['case']]['split']:raise AssertionError('Invalid latency/result record')
        checks+=1
    traces=read('throughput_traces.json');batch=read('throughput_runs.json');writes=read('write_runs.json')
    if {(r['portfolio'],r['repeat']) for r in batch}!={(p,r) for p in portfolios for r in range(protocol['repeats'])} or len(batch)!=len(portfolios)*protocol['repeats']:raise AssertionError('Missing throughput trial')
    for row in batch:
        trace=traces[row['repeat']];frequencies=Counter(by_id[i]['kind'] for i in trace)
        if frequencies!={k:v*protocol['stream_size']//100 for k,v in WEIGHTS.items()} or any(by_id[i]['split']!='heldout' for i in trace):raise AssertionError('Mixed trace differs from held-out workload')
        if row['requests']!=len(trace) or row['trace_sha256']!=fingerprint(trace) or row['output_sha256']!=fingerprint([truth[i]['rows'] for i in trace]):raise AssertionError('Throughput output/trace mismatch')
        if row['elapsed_ns']<=0 or abs(row['queries_per_second']-len(trace)*1e9/row['elapsed_ns'])>1e-6:raise AssertionError('Throughput arithmetic mismatch')
        checks+=3
    if {(r['portfolio'],r['repeat']) for r in writes}!={(p,r) for p in portfolios for r in range(protocol['write_repeats'])} or len(writes)!=len(portfolios)*protocol['write_repeats']:raise AssertionError('Missing write trial')
    for row in writes:
        inserted=generate_rows(protocol['write_rows'],protocol['seed']+1000+row['repeat'],protocol['rows']+1)
        if row['inserted_sha256']!=fingerprint(inserted) or row['inserted']!=len(inserted) or row['elapsed_ns']<=0 or abs(row['rows_per_second']-len(inserted)*1e9/row['elapsed_ns'])>1e-6:raise AssertionError('Write arithmetic/data mismatch')
        checks+=2
    replayed=0
    with tempfile.TemporaryDirectory(prefix='trackh-audit-') as temporary:
        for name,record in portfolios.items():
            path=Path(temporary)/(name+'.db');rebuilt=install(base,path,record['selected'])
            if record['selected']!=[names[i] for i in record['positions']] or record['index_bytes']!=sum(record['object_bytes'][n] for n in record['selected']):raise AssertionError('Incorrect storage accounting')
            if env['sqlite']==sqlite3.sqlite_version and rebuilt['index_bytes']!=record['index_bytes']:raise AssertionError('Rebuilt index storage differs')
            with closing(connect(path,readonly=True)) as c:
                for case in query_cases:
                    if fingerprint(execute(c,case))!=truth[case['id']]['sha256']:raise AssertionError('Fresh SQL replay differs')
                    replayed+=1;checks+=1
    result={'passed':True,'tracked_checks':checks,'training_measurements':len(train),'latency_measurements':len(latency),'throughput_batches':len(batch),'throughput_requests':sum(r['requests'] for r in batch),'write_trials':len(writes),'unique_portfolios':len(portfolios),'fresh_sql_replays':replayed,'query_cases':len(query_cases),'exhaustive_model_portfolios_per_budget':64,'budgets':len(oracles),'baseline_database_sha256':sha_file(base),
            'note':'Retained timing data are not replaced. Query/reference results, raw timing arithmetic, exhaustive model certificates, storage accounting and source/data checksums passed; physical portfolios rebuilt for fresh SQL replay. Cross-version storage equality is checked only for the recorded SQLite version.'}
    dump(root/'audit.json',result);return result
