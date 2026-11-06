import hashlib
import json
from pathlib import Path
import re
from .runtime import ROOT,VARIANTS,source_hash,write_json,parse_timebase
from .experiment import parse_result,expected_operations


def audit(directory):
    root=Path(directory);read=lambda name:json.loads((root/name).read_text());checks=0;rows=read('raw_runs.json');env=read('environment.json');protocol=read('protocol.json')
    if parse_timebase((root/'device_tree/virt.dtb').read_bytes())!=env['timebase_frequency_hz']:raise AssertionError('Timebase differs from QEMU device tree')
    for name,digest in read('uart_sha256.json').items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise AssertionError('UART integrity mismatch')
        checks+=1
    if env['source_sha256']!=source_hash(ROOT/'xv6'):raise AssertionError('Delivered kernel source differs from measured source')
    expected={(variant,repeat,kind) for variant in VARIANTS for repeat in range(protocol['repeats']) for kind in protocol['workload_iterations']}
    observed=[(row['variant'],row['repeat'],row['kind']) for row in rows]
    if len(set(observed))!=len(observed) or set(observed)!=expected:raise AssertionError('Missing or repeated benchmark cell')
    grouped={}
    for row in rows:
        grouped.setdefault(row['uart_log'],[]).append(row)
        if (row['percpu'],row['hash'])!=VARIANTS[row['variant']]:raise AssertionError('Kernel flag mismatch')
        if row['ops']!=expected_operations(row['kind'],row['iterations']):raise AssertionError('Incorrect workload units')
        if row['iterations']!=protocol['workload_iterations'][row['kind']]:raise AssertionError('Changed workload budget')
        seconds=row['dt']/env['timebase_frequency_hz']
        if abs(seconds-row['guest_seconds'])>1e-12 or abs(row['ops']/seconds-row['operations_per_guest_second'])>1e-6:raise AssertionError('Time conversion mismatch')
        if row['hits']+row['misses']!=row['lookups']:raise AssertionError('Cache accounting failure')
        checks+=6
    for log,samples in grouped.items():
        text=(root/log).read_text()
        if text.count('GCHECK PASS')!=2 or 'GBENCH FAIL' in text or 'panic:' in text:raise AssertionError('Benchmark invariants did not pass')
        emitted=[parse_result(line) for line in text.splitlines() if line.startswith('GRESULT ')]
        if len(emitted)!=len(samples):raise AssertionError('Unrecorded/duplicated guest output')
        for sample in samples:
            matches=[r for r in emitted if r['kind']==sample['kind']]
            if len(matches)!=1 or any(sample[key]!=value for key,value in matches[0].items()):raise AssertionError('Saved measurement differs from UART')
            checks+=1
    validation_path=ROOT/'validation'/'kernel_validation.json';validation=json.loads(validation_path.read_text())
    pristine=(ROOT/'validation'/'development'/'pristine_usertests.log').read_text();names=re.findall(r'(?m)^test ([^:\s]+):',pristine)
    if 'ALL TESTS PASSED' not in pristine:raise AssertionError('Pristine reference not validated')
    builds={row['variant']:row for row in read('builds.json')}
    for row in validation:
        text=(ROOT/'validation'/row['uart_log']).read_text()
        if not row['full_usertests_passed'] or 'ALL TESTS PASSED' not in text or text.count('GCHECK PASS')!=2:raise AssertionError('Kernel validation failed')
        emitted_names=re.findall(r'(?m)^test ([^:\s]+):',text)
        if sorted(row['test_names'])!=sorted(names) or emitted_names!=row['test_names']:raise AssertionError('Not the complete upstream test set')
        if row['source_sha256']!=env['source_sha256']:raise AssertionError('Validated and measured source snapshots differ')
        if builds[row['variant']]['kernel_sha256']!=row['kernel_sha256']:raise AssertionError('Measured kernel differs from validated kernel')
        checks+=4
    if set(r['variant'] for r in validation)!=set(VARIANTS):raise AssertionError('Missing kernel configuration validation')
    if len(rows)!=len(VARIANTS)*len(protocol['workload_iterations'])*protocol['repeats']:raise AssertionError('Missing benchmark cells')
    result={'passed':True,'checks':checks,'benchmark_runs':len(rows),'benchmark_boots':len(grouped),'full_validated_variants':len(validation),
        'upstream_named_tests_per_full_run':len(names),'pristine_full_test_pass':True,
        'note':'All numeric records matched to UART, work units/flags/time conversions checked, source and UART hashes verified. Complete real guest usertests sets and custom invariants verified for all four configurations. No workload timings rerun or reconstructed.'}
    write_json(root/'audit.json',result);return result
