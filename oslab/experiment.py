from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import subprocess
import time
from .runtime import ROOT,VARIANTS,Guest,build,tool_environment,timebase,write_json,source_hash

WORKLOADS={'pages':800,'fork':200,'pipes':8000,'hotseq':8000,'hotrand':8000,'scan':8000}
NUMERIC=('ops','dt','percpu','hash','alloc','frees','alocks','aspins','steals','stolen','lookups','hits','misses','probes','recycle','clocks','cspins')


def parse_result(output):
    lines=[line for line in output.splitlines() if line.startswith('GRESULT ')]
    if len(lines)!=1 or 'GBENCH FAIL' in output or 'panic:' in output:raise ValueError('Missing/failed guest measurement')
    parts=lines[0].split()[1:];fields=dict(item.split('=',1) for item in parts)
    if len(fields)!=len(parts):raise ValueError('Duplicate counter field')
    if set(fields)!=set(NUMERIC)|{'kind'} or fields['kind'] not in WORKLOADS:raise ValueError('Unexpected measurement schema')
    result={'kind':fields['kind'],**{key:int(fields[key]) for key in NUMERIC}}
    if any(result[key]<0 for key in NUMERIC) or result['ops']<1 or result['dt']<1:raise ValueError('Invalid counter/timing values')
    if result['lookups']!=result['hits']+result['misses']:raise ValueError('Cache-accounting mismatch')
    if result['percpu'] not in (0,1) or result['hash'] not in (0,1):raise ValueError('Invalid kernel flags')
    return result


def expected_operations(kind,iterations):
    if kind not in WORKLOADS or not isinstance(iterations,int) or iterations<1:raise ValueError('Invalid operation budget')
    return iterations*(48 if kind=='pages' else 3 if kind in ('fork','pipes') else 1)


def validate_variant(variant,output,env,cpus=3):
    output=Path(output);directory,record=build(variant,env,output/'build_logs');start=time.monotonic();log=output/'uart'/f'validation_{variant}.log'
    with Guest(directory,env,log,cpus) as guest:
        before=guest.command('gcheck')
        if 'GCHECK PASS' not in before:raise AssertionError('Guest invariants failed')
        for kind in WORKLOADS:
            row=parse_result(guest.command('gbench '+kind+' 10'))
            if (row['percpu'],row['hash'])!=VARIANTS[variant]:raise AssertionError('Wrong kernel compiled')
        tests=guest.command('usertests',timeout=900)
        if 'ALL TESTS PASSED' not in tests:raise AssertionError('Full upstream usertests did not pass; see '+str(log))
        after=guest.command('gcheck')
        if 'GCHECK PASS' not in after:raise AssertionError('Post-usertests invariants failed')
    return {**record,'full_usertests_passed':True,'test_names':re.findall(r'(?m)^test ([^:\s]+):',tests),
        'invariants_before_after':True,'smoke_workloads':len(WORKLOADS),'elapsed_host_s':time.monotonic()-start,'uart_log':str(log.relative_to(output)),'guest_cpus':cpus}


def validate_all(directory,toolchain=None,cpus=3):
    output=Path(directory);output.mkdir(parents=True,exist_ok=True);env=tool_environment(toolchain);rows=[]
    for variant in VARIANTS:
        print('Validating '+variant+' kernel in QEMU',flush=True);rows.append(validate_variant(variant,output,env,cpus));write_json(output/'kernel_validation.json',rows)
        print(variant+' full usertests and invariants PASSED',flush=True)
    return rows


def run_benchmark(directory,toolchain=None,repeats=3,cpus=3,scale=1):
    output=Path(directory)
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output directory')
    if repeats<1 or scale<=0:raise ValueError('Positive repetitions/scale required')
    env=tool_environment(toolchain);output.mkdir(parents=True,exist_ok=True);frequency=timebase(env,output/'device_tree');versions={}
    for command in ('qemu-system-riscv64','riscv64-linux-gnu-gcc'):
        versions[command]=subprocess.run([command,'--version'],env=env,check=True,capture_output=True,text=True).stdout.splitlines()[0]
    write_json(output/'environment.json',{'utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'versions':versions,'timebase_frequency_hz':frequency,'guest_cpus':cpus,'guest_ram':'128 MiB','acceleration':'QEMU TCG full-system RISC-V emulation','source_sha256':source_hash(ROOT/'xv6')})
    budgets={name:max(1,int(iterations*scale)) for name,iterations in WORKLOADS.items()}
    write_json(output/'protocol.json',{'variants':VARIANTS,'repeats':repeats,'guest_cpus':cpus,'scale':scale,'workload_iterations':budgets,
        'allocator':'Three real guest worker processes use pipe readiness/start barriers. Initial forks occur before the snapshot; work and worker exit/reaping occur inside it. 16 pages/batch, nested fork/wait and pipe churn are distinct workloads.',
        'cache':'Sequential hot stream: 16 blocks; pseudo-random interleaving: two eight-block streams; scan: 96 blocks versus NBUF=30. Each read verifies all 1024 bytes. Setup, sync and warmup precede measurement; close/unlink cleanup follows it.',
        'baseline':'Both features disabled, with identical stats/check syscalls and spin instrumentation. Pristine MIT kernel validated separately.',
        'timing':'Elapsed guest r_time counter, frequency read from QEMU device tree. Snapshot/introspection overhead is included; counters include observation-lock acquisitions. Not native hardware cycles or host-laptop speedup.',
        'isolation':'A fresh disk image and boot per variant/repeat, fixed workload budgets, deterministically shuffled boot/workload order; guests run sequentially. Algorithmic probes and failed lock exchanges accompany elapsed time.',
        'correctness':'Full upstream usertests and gcheck per configuration recorded separately. Every benchmark verifies data/statuses and allocator/cache invariants. No simulated trace is substituted for QEMU execution.',
        'limits':'Hash lookup retains the global cache lock and LRU/replacement policy. Per-CPU lists may retain free pages unevenly until steal-on-empty. Measurement instrumentation perturbs lock paths in every variant.'})
    directories={};builds=[]
    for variant in VARIANTS:directories[variant],record=build(variant,env,output/'build_logs');builds.append(record)
    write_json(output/'builds.json',builds);trials=[(variant,repeat) for variant in VARIANTS for repeat in range(repeats)];random.Random(10000).shuffle(trials);rows=[]
    for variant,repeat in trials:
        log=output/'uart'/f'{variant}_r{repeat}.log';order=list(WORKLOADS);random.Random(11000+repeat).shuffle(order)
        with Guest(directories[variant],env,log,cpus) as guest:
            if 'GCHECK PASS' not in guest.command('gcheck'):raise AssertionError('Initial guest check failed')
            for kind in order:
                start=time.monotonic();response=guest.command(f'gbench {kind} {budgets[kind]}',timeout=300);host_seconds=time.monotonic()-start;row=parse_result(response)
                if (row['percpu'],row['hash'])!=VARIANTS[variant]:raise AssertionError('Variant flags mismatch')
                if row['kind']!=kind:raise AssertionError('Wrong workload result')
                rows.append({'variant':variant,'repeat':repeat,'iterations':budgets[kind],**row,'guest_seconds':row['dt']/frequency,'operations_per_guest_second':row['ops']*frequency/row['dt'],
                    'host_command_s':host_seconds,'uart_log':str(log.relative_to(output))})
                write_json(output/'raw_runs.json',rows)
            if 'GCHECK PASS' not in guest.command('gcheck'):raise AssertionError('Final guest check failed')
        print(f'{variant} repetition {repeat} complete',flush=True)
    write_json(output/'uart_sha256.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((output/'uart').glob('*.log'))});return rows
