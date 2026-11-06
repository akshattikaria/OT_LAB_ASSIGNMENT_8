"""Budgeted maximum-coverage index selection; overlapping gains are not added."""
import itertools
import time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint


def validate(costs,gains,budget):
    costs=np.asarray(costs,dtype=float);gains=np.asarray(gains,dtype=float)
    if costs.ndim!=1 or gains.ndim!=2 or gains.shape[1]!=len(costs) or not len(costs):raise ValueError('Invalid model shape')
    if not np.all(np.isfinite(costs)) or not np.all(costs>0) or not np.all(np.isfinite(gains)) or np.any(gains<0) or not np.isfinite(budget) or budget<0:raise ValueError('Invalid model values')
    return costs,gains


def utility(selected,gains):
    gains=np.asarray(gains,dtype=float)
    return float(np.max(gains[:,list(selected)],axis=1).sum()) if selected else 0.0


def greedy(costs,gains,budget):
    costs,gains=validate(costs,gains,budget);start=time.perf_counter();selected=[];remaining=float(budget);trace=[]
    while True:
        current=utility(selected,gains);choices=[]
        for i,cost in enumerate(costs):
            if i not in selected and cost<=remaining+1e-9:
                gain=utility(selected+[i],gains)-current
                if gain>1e-9:choices.append((gain/cost,gain,-i,i))
        if not choices:break
        ratio,gain,_,i=max(choices);selected.append(i);remaining-=costs[i];trace.append({'index':i,'marginal_gain_ms':gain,'gain_per_kib':ratio})
    return {'selected':sorted(selected),'utility_ms':utility(selected,gains),'cost_kib':float(costs[selected].sum()),'seconds':time.perf_counter()-start,'trace':trace}


def ilp(costs,gains,budget):
    costs,gains=validate(costs,gains,budget);start=time.perf_counter();q,n=gains.shape;size=n+q*n
    # x_i: installed index. y_qi: this query receives this index's benefit.
    objective=np.r_[np.zeros(n),-gains.ravel()];matrix=[];upper=[]
    row=np.zeros(size);row[:n]=costs;matrix.append(row);upper.append(budget)
    for query in range(q):
        row=np.zeros(size);row[n+query*n:n+(query+1)*n]=1;matrix.append(row);upper.append(1)
        for i in range(n):
            row=np.zeros(size);row[n+query*n+i]=1;row[i]=-1;matrix.append(row);upper.append(0)
    result=milp(objective,integrality=np.ones(size),bounds=Bounds(0,1),constraints=LinearConstraint(np.array(matrix),-np.inf,np.array(upper)),options={'mip_rel_gap':0.0,'time_limit':30})
    if not result.success or result.status!=0:raise RuntimeError('MILP failed to prove model optimality: '+result.message)
    selected=[i for i in range(n) if result.x[i]>.5]
    for i in reversed(selected.copy()):
        alternate=[j for j in selected if j!=i]
        if abs(utility(alternate,gains)-utility(selected,gains))<1e-10:selected=alternate
    value=utility(selected,gains)
    if costs[selected].sum()>budget+1e-7 or abs(value+result.fun)>1e-6:raise AssertionError('MILP certificate inconsistent')
    return {'selected':selected,'utility_ms':value,'cost_kib':float(costs[selected].sum()),'seconds':time.perf_counter()-start,'status':int(result.status),'gap':float(result.mip_gap or 0),'nodes':int(result.mip_node_count or 0),'dual_bound':float(result.mip_dual_bound)}


def exhaustive(costs,gains,budget):
    costs,gains=validate(costs,gains,budget);best=None;records=[]
    for flags in itertools.product((0,1),repeat=len(costs)):
        selected=[i for i,flag in enumerate(flags) if flag];cost=float(costs[selected].sum());value=utility(selected,gains)
        row={'selected':selected,'cost_kib':cost,'utility_ms':value,'feasible':bool(cost<=budget+1e-9)};records.append(row)
        if row['feasible'] and (best is None or (value,-cost,tuple(-i for i in selected))>(best['utility_ms'],-best['cost_kib'],tuple(-i for i in best['selected']))):best=row
    return {'best':best,'portfolios':records}
