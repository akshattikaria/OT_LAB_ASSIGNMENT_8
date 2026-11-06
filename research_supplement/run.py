"""Run new source-linked studies without overwriting retained evidence."""
import argparse
import importlib
import platform
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from .common import save


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups',nargs='+',default=['curvature','submodular','tensorhyper','negative_learning','qmt','nom'])
    parser.add_argument('--out',type=Path,default=Path(__file__).parent/'results')
    a=parser.parse_args()
    with threadpool_limits(limits=1):
        for name in a.groups:
            start=time.perf_counter();print('Running',name,flush=True)
            if name in ['tensorhyper','negative_learning','qmt','nom']:
                value=getattr(importlib.import_module('research_supplement.quantum_studies'),name)()
            else:value=importlib.import_module('research_supplement.'+name).run()
            value['environment']={'python':platform.python_version(),'platform':platform.platform(),'scope':'Shared cloud CPU; not student laptop; one BLAS thread.'}
            save(a.out/(name+'.json'),value);print('Saved',name,'elapsed_s',round(time.perf_counter()-start,3),flush=True)


if __name__=='__main__':main()
