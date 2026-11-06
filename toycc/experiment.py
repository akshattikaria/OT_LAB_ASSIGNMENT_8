from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
from time import perf_counter
from . import frontend,ir,passes,search,native,programs

VARIANTS=('baseline','fold_only','cse_only','dce_only','strength_only','fixed','greedy_order','dp_order')


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def compile_variant(source,variant):
    if variant not in VARIANTS:raise ValueError('Unknown compiler variant')
    start=perf_counter();program=frontend.parse(source);initial=ir.lower(program);front_done=perf_counter();info={'order':[]}
    if variant.endswith('_only'):
        name=variant[:-5];result=passes.PASSES[name](initial);info={'order':[name]}
    elif variant=='fixed':result=passes.apply_order(initial,search.FIXED);info={'order':list(search.FIXED)}
    elif variant=='greedy_order':result,info=search.greedy(initial)
    elif variant=='dp_order':result,info=search.dynamic_programming(initial)
    else:result=initial
    optimize_done=perf_counter();code=native.function(result,VARIANTS.index(variant));finish=perf_counter()
    return result,{'variant':variant,'frontend_s':front_done-start,'optimization_s':optimize_done-front_done,'codegen_s':finish-optimize_done,
        'python_compile_s':finish-start,'ir_instructions':len(result.code),'weighted_ir_score':ir.score(result),'function_source_bytes':len(code.encode()),'search':info}


def environment():
    compiler=shutil.which('cc');version=subprocess.run([compiler,'--version'],check=True,capture_output=True,text=True).stdout.splitlines()[0] if compiler else None
    path=Path('/sys/fs/cgroup/cpu.max')
    return {'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'compiler':compiler,'compiler_version':version,
        'logical_cpus':os.cpu_count(),'affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'cpu_max':path.read_text().strip() if path.exists() else None,
        'timing_note':'Serial CPU wall-clock timings on a shared cloud workspace, not the student laptop; native workload loop runs entirely in C.'}


def driver_reference(program,seed,iterations):
    state=seed;checksum=0
    for _ in range(iterations):
        args=[]
        for _ in program.params:
            state=(state*6364136223846793005+1442695040888963407)&frontend.MASK;args.append(state)
        checksum=(checksum+frontend.evaluate(program,args))&frontend.MASK
    return checksum


def run_benchmark(directory,seeds=(0,1,2,3,4),repeats=5,iterations=100000,compile_repeats=3):
    output=Path(directory)
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output folder')
    if not seeds or len(set(seeds))!=len(seeds) or repeats<1 or iterations<1 or compile_repeats<1:raise ValueError('Invalid benchmark protocol')
    if shutil.which('cc') is None or shutil.which('nm') is None or shutil.which('objdump') is None:raise RuntimeError('cc, nm and objdump are required')
    output.mkdir(parents=True,exist_ok=True);write_json(output/'environment.json',environment())
    write_json(output/'protocol.json',{'seeds':list(seeds),'runtime_repeats':repeats,'iterations_per_timing':iterations,'compile_repeats':compile_repeats,
        'variants':list(VARIANTS),'families':list(programs.FAMILIES),'native_levels':['O0','O2'],
        'language':'Own lexer/precedence parser; immutable lets, one return, up to eight uint64 arguments; pure straight-line +,-,*,bitwise and masked shifts; no loops, memory, division or I/O.',
        'semantics':'Each result wraps modulo 2**64; shift counts mask with 63. No signed-overflow assumptions or floating-point reassociation.',
        'cost_model':ir.COST,'score_note':'Synthetic target-model cost, not measured CPU cycles; all instructions weight 1 except multiplication weight 4.',
        'search':'Exactly one use of each of four passes. DP state includes used subset and canonical transformed SSA, verified against all 24 permutations. Optimality concerns this score only.',
        'fairness':'Same source, varying-input native driver, number of iterations, seed and compiler flags for each within-level comparison. Runtime trial order is predeclared and shuffled. No best timing selection.',
        'native_controls':'All eight variants timed at -O0; baseline and DP timed at -O2. -O0 isolates pedagogical pass effects; -O2 exposes overlap with host optimizations. Functions use GCC/Clang noinline attribute, no LTO.',
        'counts':'IR count excludes final return and benchmark driver; straight-line IR executes each retained instruction once/invocation. Disassembly count is static native instructions, including padding, not retired hardware counters.',
        'compile_time':'Python frontend+optimization+C generation measured per variant/repetition. Native compile time is per combined eight-variant translation unit and cannot be assigned to one variant.',
        'validation':'33 edge/random input vectors per program; AST, IR and both native levels must agree for every variant. 64-iteration native driver check against AST, plus same-seed checksums for each timed run.',
        'scale':'20 synthetic teaching programs in the main protocol. No production-C compiler, LLVM/GCC pass plugin, branch/loop optimization or whole-program optimality claim.'})
    compiled=[];runtime=[];search_rows=[];native_builds=[];native_stats=[];validation=[];input_hashes={}
    project=Path(__file__).resolve().parents[1];build=project/'build'/output.name;build.mkdir(parents=True,exist_ok=True)
    for family in programs.FAMILIES:
        for seed in seeds:
            identity=f'{family}_s{seed}';source=programs.generate(family,seed);folder=output/'sources';folder.mkdir(exist_ok=True);source_path=folder/(identity+'.toy');source_path.write_text(source)
            input_hashes[str(source_path.relative_to(output))]=hashlib.sha256(source_path.read_bytes()).hexdigest();program=frontend.parse(source);baseline=ir.lower(program)
            vectors=programs.vectors(seed);reference=[frontend.evaluate(program,args) for args in vectors]
            write_json(output/'validation_inputs'/f'{identity}.json',[{'args_hex':[hex(x) for x in args],'expected_hex':hex(expected)} for args,expected in zip(vectors,reference)])
            variants=[];records=[]
            for variant in VARIANTS:
                first=None
                for repeat in range(compile_repeats):
                    candidate,row=compile_variant(source,variant);compiled.append({'program':identity,'family':family,'seed':seed,'repeat':repeat,**row})
                    if first is None:first=candidate;records.append(row)
                    elif candidate!=first:raise AssertionError('Nondeterministic compiled IR')
                variants.append(first);write_json(output/'ir'/f'{identity}_{variant}.json',first.json())
                for args,expected in zip(vectors,reference):
                    if ir.execute(first,args)!=expected:raise AssertionError('Compiler changed source semantics')
            oracle=search.exhaustive(baseline);dp=records[VARIANTS.index('dp_order')]
            if dp['weighted_ir_score']!=oracle['minimum_score']:raise AssertionError('DP disagrees with independent 24-order oracle')
            search_rows.append({'program':identity,'family':family,'seed':seed,'oracle':oracle,'dp':dp['search'],'greedy':records[VARIANTS.index('greedy_order')]['search']})
            c=output/'generated'/f'{identity}.c';c.parent.mkdir(exist_ok=True);c.write_text(native.translation_unit(variants));levels=('O0','O2') if seed%2==0 else ('O2','O0')
            driver_expected=driver_reference(program,123,64)
            for level in levels:
                library_path=build/f'{identity}_{level}.so';library,info=native.compile_library(c,library_path,level);native_builds.append({'program':identity,'family':family,**info})
                stats,assembly=native.inspect_library(library_path,len(variants))
                for stat in stats:native_stats.append({'program':identity,'family':family,'level':level,'variant':VARIANTS[stat['variant_index']],**stat})
                disassembly=output/'assembly'/f'{identity}_{level}.txt';disassembly.parent.mkdir(exist_ok=True);disassembly.write_text(assembly)
                for index in range(len(variants)):
                    for args,expected in zip(vectors,reference):
                        if native.evaluate(library,index,args)!=expected:raise AssertionError('Native output differs from AST')
                    if library.benchmark_variant(index,123,64)!=driver_expected:raise AssertionError('Native harness differs from independent AST loop')
                    library.benchmark_variant(index,123,2000) # Same explicit warmup for every variant.
                indices=list(range(len(VARIANTS))) if level=='O0' else [0,VARIANTS.index('dp_order')]
                checksums={}
                for repeat in range(repeats):
                    run_seed=((seed+1)*0x9e3779b97f4a7c15+repeat)&frontend.MASK
                    checksums[repeat]=int(library.benchmark_variant(0,run_seed,iterations))
                trials=[(index,repeat) for index in indices for repeat in range(repeats)];random.Random(9000+seed+(0 if level=='O0' else 100)).shuffle(trials)
                for index,repeat in trials:
                    run_seed=((seed+1)*0x9e3779b97f4a7c15+repeat)&frontend.MASK;clock=perf_counter();checksum=int(library.benchmark_variant(index,run_seed,iterations));seconds=perf_counter()-clock
                    if checksum!=checksums[repeat]:raise AssertionError('Timed native checksum mismatch')
                    runtime.append({'program':identity,'family':family,'seed':seed,'variant':VARIANTS[index],'level':level,'repeat':repeat,'iterations':iterations,'seconds':seconds,
                        'driver_seed_hex':hex(run_seed),'checksum_hex':hex(checksum)})
            validation.append({'program':identity,'vectors':len(vectors),'variants':len(variants),'ir_comparisons':len(vectors)*len(variants),
                'native_comparisons':len(vectors)*len(variants)*2,'driver_reference_iterations':64,'driver_checks':len(variants)*2,'driver_reference_checksum_hex':hex(driver_expected)})
            print(f'Compiled and measured {identity}',flush=True)
    write_json(output/'compile_runs.json',compiled);write_json(output/'runtime_runs.json',runtime);write_json(output/'pass_search.json',search_rows)
    write_json(output/'native_builds.json',native_builds);write_json(output/'native_function_stats.json',native_stats);write_json(output/'validation.json',validation)
    for file in sorted((output/'validation_inputs').glob('*.json')):input_hashes[str(file.relative_to(output))]=hashlib.sha256(file.read_bytes()).hexdigest()
    write_json(output/'input_sha256.json',input_hashes);print('All Track F experiments complete',flush=True)
