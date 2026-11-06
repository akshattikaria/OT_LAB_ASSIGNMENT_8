"""Weighted set cover over actual per-test source-line contexts."""
import time
import numpy as np
from scipy.optimize import Bounds,LinearConstraint,milp
from scipy.sparse import csc_matrix


def validate(covers,costs,universe):
    if len(covers)!=len(costs) or not covers or any(not isinstance(x,int) or x<=0 for x in costs):raise ValueError('Positive integer costs and matching test sets required')
    universe=set(universe)
    if not universe or not universe<=set().union(*map(set,covers)):raise ValueError('Universe must be nonempty and coverable')
    return [set(c)&universe for c in covers],universe


def covered(selected,covers):return set().union(*(covers[i] for i in selected)) if selected else set()


def greedy(covers,costs,universe,weighted=True):
    covers,universe=validate(covers,costs,universe);start=time.perf_counter();remaining=universe.copy();selected=[];trace=[]
    while remaining:
        choices=[(len(lines&remaining)/(costs[i] if weighted else 1),len(lines&remaining),-i,i) for i,lines in enumerate(covers) if i not in selected and lines&remaining]
        if not choices:raise AssertionError('Uncoverable residual')
        ratio,gain,_,index=max(choices);selected.append(index);remaining-=covers[index];trace.append({'test_index':index,'new_lines':gain,'ratio':ratio})
    for index in sorted(selected.copy(),key=lambda i:(-costs[i],i)):
        alternate=[i for i in selected if i!=index]
        if universe<=covered(alternate,covers):selected=alternate
    return {'selected':sorted(selected),'estimated_cost_us':sum(costs[i] for i in selected),'selection_s':time.perf_counter()-start,'trace':trace,'optimal':False,'method':'weighted_greedy' if weighted else 'count_greedy'}


def integer_program(covers,costs,universe,time_limit=60):
    covers,universe=validate(covers,costs,universe);start=time.perf_counter();elements=sorted(universe);position={x:i for i,x in enumerate(elements)};rows=[];cols=[]
    for test,lines in enumerate(covers):
        for line in lines:rows.append(position[line]);cols.append(test)
    matrix=csc_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(elements),len(covers)))
    result=milp(np.asarray(costs,dtype=float)/1000,integrality=np.ones(len(covers)),bounds=Bounds(0,1),constraints=LinearConstraint(matrix,1,np.inf),options={'mip_rel_gap':0.0,'time_limit':time_limit})
    if result.x is None or result.status not in (0,1):raise RuntimeError('ILP failed: '+str(result.message))
    selected=[i for i,value in enumerate(result.x) if value>.5];cost=sum(costs[i] for i in selected)
    if not universe<=covered(selected,covers) or abs(cost/1000-result.fun)>1e-6:raise AssertionError('Infeasible/inconsistent ILP solution')
    return {'selected':selected,'estimated_cost_us':cost,'selection_s':time.perf_counter()-start,'optimal':bool(result.status==0),'status':int(result.status),'gap':float(result.mip_gap),'dual_bound_ms':float(result.mip_dual_bound),'nodes':int(result.mip_node_count),'method':'ilp','certificate_scope':'Optimum only for the static per-test line matrix and quantized profile-duration sum when solver status is optimal; no runtime/fault-coverage guarantee.'}
