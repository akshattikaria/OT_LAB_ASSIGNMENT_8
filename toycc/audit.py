"""Audit saved IR, C source, disassembly, checksums and the finite search certificate."""
import hashlib
import json
from pathlib import Path
import re
from . import frontend,ir,search,native
from .experiment import VARIANTS,write_json


def audit(directory):
    root=Path(directory);read=lambda n:json.loads((root/n).read_text());comparisons=0;native_checks=0;ir_checks=0;order_checks=0;driver_checks=0
    def equal(a,b):
        nonlocal comparisons
        if a!=b:raise AssertionError(f'Audit mismatch: {a!r} != {b!r}')
        comparisons+=1
    for name,digest in read('input_sha256.json').items():equal(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
    compile_rows=read('compile_runs.json');stats=read('native_function_stats.json');searches=read('pass_search.json');validation=read('validation.json');protocol=read('protocol.json')
    project=Path(__file__).resolve().parents[1];build=project/'build'/'audit'/root.name;build.mkdir(parents=True,exist_ok=True)
    for entry in validation:
        name=entry['program'];program=frontend.parse((root/'sources'/f'{name}.toy').read_text());initial=ir.lower(program)
        vectors=read('validation_inputs/'+name+'.json');variants=[]
        for index,method in enumerate(VARIANTS):
            result=ir.from_json(read('ir/'+name+'_'+method+'.json'));variants.append(result)
            for row in (c for c in compile_rows if c['program']==name and c['variant']==method):
                equal(row['ir_instructions'],len(result.code));equal(row['weighted_ir_score'],sum(protocol['cost_model'][i.op] for i in result.code))
                equal(row['function_source_bytes'],len(native.function(result,index).encode()))
                if abs(row['python_compile_s']-(row['frontend_s']+row['optimization_s']+row['codegen_s']))>1e-9:raise AssertionError('Compile timing components mismatch')
            for vector in vectors:
                args=[int(x,16) for x in vector['args_hex']];expected=frontend.evaluate(program,args)
                equal(expected,int(vector['expected_hex'],16));equal(ir.execute(result,args),expected);ir_checks+=1
        equal((root/'generated'/f'{name}.c').read_text(),native.translation_unit(variants))
        enumeration=search.exhaustive(initial);saved=next(row for row in searches if row['program']==name)
        equal(enumeration,saved['oracle']);equal(ir.score(variants[VARIANTS.index('dp_order')]),enumeration['minimum_score']);order_checks+=24
        if ir.score(variants[-1])>ir.score(variants[-2]):raise AssertionError('DP worse than greedy in its declared search space')
        for level in ('O0','O2'):
            library,_=native.compile_library(root/'generated'/f'{name}.c',build/f'{name}_{level}.so',level)
            assembly=(root/'assembly'/f'{name}_{level}.txt').read_text();headers=list(re.finditer(r'^\s*[0-9a-fA-F]+ <toy_v([0-9]+)>:',assembly,re.M))
            counts={}
            for position,header in enumerate(headers):
                stop=headers[position+1].start() if position+1<len(headers) else len(assembly)
                counts[int(header.group(1))]=len(re.findall(r'^\s*[0-9a-fA-F]+:\s+\S',assembly[header.end():stop],re.M))
            for row in (s for s in stats if s['program']==name and s['level']==level):
                equal(row['static_disassembly_instructions'],counts[row['variant_index']])
                if row['machine_code_bytes']<1:raise AssertionError('Invalid machine code size')
            for index in range(len(variants)):
                for vector in vectors:
                    args=[int(x,16) for x in vector['args_hex']];equal(native.evaluate(library,index,args),int(vector['expected_hex'],16));native_checks+=1
                equal(int(library.benchmark_variant(index,123,64)),int(entry['driver_reference_checksum_hex'],16));driver_checks+=1
    runs=read('runtime_runs.json');groups={}
    for row in runs:
        equal(row['iterations'],protocol['iterations_per_timing'])
        if row['seconds']<=0:raise AssertionError('Nonpositive timing')
        groups.setdefault((row['program'],row['repeat']),set()).add(row['checksum_hex'])
    for values in groups.values():equal(len(values),1)
    result={'passed':True,'comparisons':comparisons,'ir_output_checks':ir_checks,'fresh_native_output_checks':native_checks,
        'fresh_native_driver_checks':driver_checks,'pass_orders_reenumerated':order_checks,'timing_records_checked':len(runs),
        'note':'Saved inputs, all compiled IR outputs, generated C, assembly instruction counts, cost-model certificates and same-seed timed checksums checked. C regenerated/recompiled under both levels to validate outputs, without repeating timed benchmark results. Saved native symbol sizes are host/compiler-specific.'}
    write_json(root/'audit.json',result);return result
