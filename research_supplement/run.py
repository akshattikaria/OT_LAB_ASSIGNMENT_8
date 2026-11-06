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
    parser.add_argument('--groups',nargs='+',default=['curvature','submodular','tensorhyper','negative_learning','qmt','nom','communication','placement','hpo','svmplus','strategies','spmv','liver','privacy_certificate'])
    parser.add_argument('--out',type=Path,default=Path(__file__).parent/'results')
    a=parser.parse_args()
    with threadpool_limits(limits=1):
        for name in a.groups:
            start=time.perf_counter();print('Running',name,flush=True)
            if name in ['tensorhyper','negative_learning','qmt','nom']:
                value=getattr(importlib.import_module('research_supplement.quantum_studies'),name)()
            elif name=='privacy_certificate':
                from .submodular import exact_dp_distribution
                import numpy as np
                covers=[{0},{1},{0,1}];data=[{0},{1},{1}];neighbor={0};costs=[1,2,1];rows=[]
                def objective(dataset):
                    return lambda s:float(sum(bool(set(row)&set().union(*(covers[i] for i in s))) for row in dataset))
                for epsilon in [.2,.8,2.]:
                    p=exact_dp_distribution(objective(data),costs,2,epsilon)
                    q=exact_dp_distribution(objective(data+[neighbor]),costs,2,epsilon)
                    keys=sorted(p);pv=np.array([p[k] for k in keys]);qv=np.array([q[k] for k in keys])
                    rows.append({'epsilon':epsilon,'sets':keys,'p':pv,'q':qv,'maximum_absolute_log_ratio':float(np.max(np.abs(np.log(pv/qv))))})
                value={'dataset':data,'neighbor_added':neighbor,'coverage':covers,'costs':costs,'budget':2,'rows':rows,'scope':'Every greedy path and complete final noisy-max distribution integrated for this three-item neighboring-dataset control; not a universal privacy proof.'}
            else:value=importlib.import_module('research_supplement.'+name).run()
            value['environment']={'python':platform.python_version(),'platform':platform.platform(),'scope':'Shared cloud CPU; not student laptop; one BLAS thread.'}
            save(a.out/(name+'.json'),value);print('Saved',name,'elapsed_s',round(time.perf_counter()-start,3),flush=True)


if __name__=='__main__':main()
