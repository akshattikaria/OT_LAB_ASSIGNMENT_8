import ctypes
from pathlib import Path
import shutil
import subprocess
from time import perf_counter
import numpy as np


def library():
    root=Path(__file__).resolve().parents[1];build=root/'build';build.mkdir(exist_ok=True);target=build/'locality.so';source=root/'native'/'locality.c'
    compiler=shutil.which('cc')
    if compiler is None:raise RuntimeError('A C compiler is required for the explicit locality loops; install cc or use the supplied recorded results')
    command=[compiler,'-O3','-std=c11','-shared','-fPIC',str(source),'-o',str(target)]
    subprocess.run(command,check=True,capture_output=True)
    lib=ctypes.CDLL(str(target))
    for name in ('row_sum','column_sum','blocked_sum'):
        fn=getattr(lib,name);fn.argtypes=[np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS'),ctypes.c_size_t];fn.restype=ctypes.c_double
    return lib,command


def measure(repeats=3,sizes=(512,2048)):
    lib,command=library();rows=[]
    for n in sizes:
        array=np.random.default_rng(4500+n).uniform(-1,1,(n,n));expected=float(np.sum(array,dtype=np.longdouble))
        trials=[(name,r) for name in ('row_sum','column_sum','blocked_sum') for r in range(repeats)]
        for i in np.random.default_rng(4600+n).permutation(len(trials)):
            name,repeat=trials[i];fn=getattr(lib,name);fn(array,n);start=perf_counter();result=fn(array,n);seconds=perf_counter()-start
            if not np.isclose(result,expected,atol=1e-7,rtol=1e-10):raise AssertionError('Locality sum differs')
            rows.append({'n':n,'method':name,'repeat':repeat,'seconds':seconds,'result':result,'reference':expected,'abs_error':abs(result-expected)})
    return {'compiler_command':command,'rows':rows,'note':'Actual C loops over one C-order matrix; -O3 without fast-math. Loop order changes floating summation order. No measured cache-miss count or matrix-multiplication speedup is claimed.'}
