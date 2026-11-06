"""C11 code generation, real native compilation, symbol sizes and disassembly."""
import ctypes
from pathlib import Path
import re
import shutil
import subprocess
from time import perf_counter
from .ir import validate

SYMBOL={ 'add':'+','sub':'-','mul':'*','xor':'^','and':'&','or':'|','shl':'<<','shr':'>>'}


def function(ir,index=0):
    validate(ir);lines=[f'__attribute__((noinline)) uint64_t toy_v{index}(const uint64_t *inputs) {{']
    for instruction in ir.code:
        op=instruction.op
        if op=='arg':expr=f'inputs[{instruction.value}]'
        elif op=='const':expr=f'UINT64_C({instruction.value})'
        elif op=='copy':expr=f'v{instruction.args[0]}'
        else:
            a,b=instruction.args;right=f'(v{b} & UINT64_C(63))' if op in ('shl','shr') else f'v{b}'
            expr=f'(v{a} {SYMBOL[op]} {right})'
        lines.append(f'    uint64_t v{instruction.dest} = {expr};')
    lines.extend((f'    return v{ir.result};','}'));return '\n'.join(lines)+'\n'


def translation_unit(irs):
    if not irs or any(ir.params!=irs[0].params for ir in irs):raise ValueError('Native variants must share the same parameters')
    parts=['#include <stdint.h>\n#include <stddef.h>\n']+[function(ir,i) for i,ir in enumerate(irs)]
    parts.append('typedef uint64_t (*toy_function)(const uint64_t *);\nstatic toy_function functions[] = {'+', '.join('toy_v'+str(i) for i in range(len(irs)))+'};\n')
    parts.append(f'unsigned parameter_count(void) {{ return {len(irs[0].params)}; }}\nunsigned variant_count(void) {{ return {len(irs)}; }}\n')
    parts.append(f'''uint64_t evaluate_variant(unsigned variant, const uint64_t *inputs) {{
    return functions[variant](inputs);
}}
uint64_t benchmark_variant(unsigned variant, uint64_t seed, size_t iterations) {{
    toy_function f = functions[variant];
    uint64_t state = seed, checksum = UINT64_C(0), inputs[8] = {{0}};
    for (size_t i=0; i<iterations; ++i) {{
        for (unsigned j=0; j<{len(irs[0].params)}; ++j) {{
            state = state * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
            inputs[j] = state;
        }}
        checksum += f(inputs);
    }}
    return checksum;
}}
''');return '\n'.join(parts)


def compile_library(source,output,optimization='O0'):
    if optimization not in ('O0','O2'):raise ValueError('Native level must be O0 or O2')
    compiler=shutil.which('cc')
    if compiler is None:raise RuntimeError('C compiler cc is required for native measurements')
    source=Path(source).resolve();output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    command=[compiler,'-'+optimization,'-std=c11','-shared','-fPIC',str(source),'-o',str(output)]
    clock=perf_counter();subprocess.run(command,check=True,capture_output=True,text=True);seconds=perf_counter()-clock
    library=ctypes.CDLL(str(output));library.evaluate_variant.argtypes=[ctypes.c_uint,ctypes.POINTER(ctypes.c_uint64)];library.evaluate_variant.restype=ctypes.c_uint64
    library.benchmark_variant.argtypes=[ctypes.c_uint,ctypes.c_uint64,ctypes.c_size_t];library.benchmark_variant.restype=ctypes.c_uint64
    library.parameter_count.restype=ctypes.c_uint;library.variant_count.restype=ctypes.c_uint
    library._toy_arity=library.parameter_count();library._toy_variants=library.variant_count()
    return library,{'command':command,'native_compile_s':seconds,'library_bytes':output.stat().st_size,'optimization':optimization}


def inspect_library(path,variants):
    nm=shutil.which('nm');objdump=shutil.which('objdump')
    if nm is None or objdump is None:raise RuntimeError('nm and objdump are required for symbol-size/instruction measurements')
    symbols=subprocess.run([nm,'-S','--defined-only',str(path)],check=True,capture_output=True,text=True).stdout
    sizes={match.group(3):int(match.group(2),16) for match in re.finditer(r'^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+[Tt]\s+(\S+)$',symbols,re.M)}
    rows=[];assemblies=[]
    for index in range(variants):
        name=f'toy_v{index}';disassembly=subprocess.run([objdump,'--no-show-raw-insn','-d','--disassemble='+name,str(path)],check=True,capture_output=True,text=True).stdout
        instructions=len(re.findall(r'^\s*[0-9a-fA-F]+:\s+\S',disassembly,re.M))
        if name not in sizes or instructions<1:raise AssertionError('Native function inspection failed')
        rows.append({'variant_index':index,'symbol':name,'machine_code_bytes':sizes[name],'static_disassembly_instructions':instructions});assemblies.append(disassembly)
    return rows,'\n'.join(assemblies)


def evaluate(library,index,arguments):
    if not isinstance(index,int) or not 0<=index<library._toy_variants or len(arguments)!=library._toy_arity or any(not isinstance(v,int) or not 0<=v<(1<<64) for v in arguments):raise ValueError('Invalid native variant or uint64 arguments')
    values=(ctypes.c_uint64*len(arguments))(*arguments);return int(library.evaluate_variant(index,values))
