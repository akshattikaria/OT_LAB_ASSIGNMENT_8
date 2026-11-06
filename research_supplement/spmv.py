"""Real two-thread CSR experiments for the micro-operation scheduling idea."""
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import numpy as np
from .common import array_digest


def run():
    root=Path(__file__).parent;rows=[]
    compiler=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0]
    with tempfile.TemporaryDirectory(prefix='research_spmv_') as temp:
        temp=Path(temp);binary=temp/'spmv'
        subprocess.run(['gcc','-O2','-fopenmp',str(root/'spmv.c'),'-lm','-o',str(binary)],check=True)
        for seed in range(5):
            for family in ['uniform','skewed','empty_rows']:
                rng=np.random.default_rng(8200+seed);n=1024;columns=2048
                counts=np.full(n,128,dtype=np.int64)
                if family=='skewed':counts[:]=4;counts[0]=200_000
                if family=='empty_rows':counts[::2]=0
                row=np.r_[0,np.cumsum(counts)].astype('<i8');col=rng.integers(0,columns,size=int(row[-1]),dtype=np.int32).astype('<i4');val=rng.normal(size=len(col)).astype('<f8');x=rng.normal(size=columns).astype('<f8')
                inputfile=temp/'input.bin'
                with inputfile.open('wb') as f:
                    np.array([n,columns,len(col)],dtype='<i8').tofile(f)
                    for a in [row,col,val,x]:a.tofile(f)
                result=subprocess.run([str(binary),str(inputfile)],capture_output=True,text=True,check=True,timeout=30);trials=[json.loads(line) for line in result.stdout.splitlines()]
                assert len(trials)==14
                summary={}
                for method,name in [(0,'row_static'),(1,'runtime_adaptive_nnz_tiles')]:
                    values=[r['seconds'] for r in trials if r['method']==method]
                    summary[name]={'median_s':statistics.median(values),'min_s':min(values),'max_s':max(values)}
                rows.append({'seed':seed,'family':family,'rows':n,'columns':columns,'nnz':len(col),'threads':2,'input_seed':8200+seed,'input_array_digest':array_digest(row,col,val,x),'summary':summary,'trials':trials})
    return {'runs':rows,'compiler':compiler,'scope':'Native OpenMP execution, 2 real threads, one warmup and 7 repetitions per method/case. Identical CSR inputs and serial reference, including duplicate columns/empty rows. Nonzero tiles split long rows, atomically accumulate boundary partials and adapt tile size to measured previous throughput. This is an original PANA-related mechanism control, not the unreleased PANA implementation (author repo contained README/LICENSE only) or its SIMD micro-operation design. No SuiteSparse/Intel/AMD paper speedup is claimed. Timer includes output reset, scheduling, atomics and synchronization, excluding compile/input creation.'}
