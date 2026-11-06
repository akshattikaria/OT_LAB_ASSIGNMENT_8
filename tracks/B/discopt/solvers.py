"""Explicit greedy, DP and Branch-and-Bound; library ILP and small exact oracle."""
from dataclasses import dataclass,field
from functools import cmp_to_key
import heapq
import math
from time import perf_counter
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint

from .model import audit


@dataclass
class Solution:
    method:str
    status:str
    selection:object
    details:dict=field(default_factory=dict)

    def to_dict(self):
        return {"method":self.method,"status":self.status,
                "selection":None if self.selection is None else np.asarray(self.selection).tolist(),"details":self.details}


def density_order(p):
    # Integer cross-products avoid rounding ratios before sorting or bounding.
    def compare(i,j):
        difference=p.values[i]*p.weights[j]-p.values[j]*p.weights[i]
        return -1 if difference>0 else 1 if difference<0 else (i>j)-(i<j)
    return sorted(range(p.n),key=cmp_to_key(compare))


def _pack(p,order):
    bits=np.zeros(p.n,dtype=int);used=0
    for i in order:
        if used+p.weights[i]<=p.capacity:
            bits[i]=1;used+=p.weights[i]
    return bits


def baseline(p,**_):
    p.validate();return Solution("baseline","heuristic",_pack(p,range(p.n)))


def greedy(p,**_):
    p.validate();return Solution("greedy","heuristic",_pack(p,density_order(p)),{"order":density_order(p)})


def dynamic_programming(p,max_cells=10_000_000,**_):
    p.validate()
    cells=(p.n+1)*(p.capacity+1)
    if cells>max_cells:
        return Solution("dp","resource_limit",None,{"table_cells":cells,"max_cells":max_cells})
    table=np.zeros((p.n+1,p.capacity+1),dtype=np.int64)
    for i,(value,weight) in enumerate(zip(p.values,p.weights),1):
        table[i]=table[i-1]
        if weight<=p.capacity:
            # Read the previous row: each item can be used at most once.
            table[i,weight:]=np.maximum(table[i,weight:],table[i-1,:p.capacity+1-weight]+value)
    bits=np.zeros(p.n,dtype=int);capacity=p.capacity
    for i in range(p.n,0,-1):
        if table[i,capacity]!=table[i-1,capacity]:
            bits[i-1]=1;capacity-=p.weights[i-1]
    return Solution("dp","optimal",bits,{"objective":int(table[-1,-1]),"table_cells":cells,
        "table_bytes":table.nbytes,"complexity":"O(n*C) pseudo-polynomial; full table retained for reconstruction"})


def fractional_bound(p,order,level,weight,value):
    """Integer floor of fractional-relaxation upper bound; exact arithmetic."""
    remaining=p.capacity-weight;upper=value
    if remaining<0:return -1
    for i in order[level:]:
        if p.weights[i]<=remaining:
            upper+=p.values[i];remaining-=p.weights[i]
        else:
            upper+=(p.values[i]*remaining)//p.weights[i]
            break
    return upper


def branch_bound(p,time_limit=2.0,node_limit=100_000,**_):
    p.validate()
    if not np.isfinite(time_limit) or time_limit<=0 or not isinstance(node_limit,int) or node_limit<1:
        raise ValueError("Positive time limit and integer node limit required")
    start=perf_counter();order=density_order(p);initial=_pack(p,order)
    checked=audit(p,initial);best=checked["value"];best_mask=sum(int(b)<<i for i,b in enumerate(initial))
    upper=fractional_bound(p,order,0,0,0)
    heap=[(-upper,0,0,0,0,0)] if upper>best else []
    serial=0;nodes=0;peak_frontier=len(heap);reason=None
    while heap:
        if perf_counter()-start>=time_limit:reason="time_limit";break
        if nodes>=node_limit:reason="node_limit";break
        neg_bound,_,level,weight,value,mask=heapq.heappop(heap)
        if -neg_bound<=best:continue
        nodes+=1
        if level==p.n:continue
        i=order[level]
        # Both include and exclude children are bounded by the same relaxation.
        children=[(weight,value,mask)]
        if weight+p.weights[i]<=p.capacity:
            included=(weight+p.weights[i],value+p.values[i],mask|(1<<i))
            children.append(included)
            if included[1]>best:best=included[1];best_mask=included[2]
        for child_weight,child_value,child_mask in children:
            bound=fractional_bound(p,order,level+1,child_weight,child_value)
            if bound>best:
                serial+=1;heapq.heappush(heap,(-bound,serial,level+1,child_weight,child_value,child_mask))
        peak_frontier=max(peak_frontier,len(heap))
    # Entries dominated by the final incumbent do not leave a proof gap.
    final_upper=max(best,-heap[0][0] if heap else best)
    optimal=final_upper<=best
    status="optimal" if optimal else reason+"_with_candidate"
    bits=np.array([(best_mask>>i)&1 for i in range(p.n)],dtype=int)
    return Solution("branch_bound",status,bits,{"objective":best,"upper_bound":final_upper,
        "absolute_bound_gap":final_upper-best,"nodes":nodes,"peak_frontier":peak_frontier,
        "time_limit_s":time_limit,"node_limit":node_limit,"bound":"floor of exact fractional relaxation"})


def integer_programming(p,time_limit=2.0,**_):
    p.validate()
    if not np.isfinite(time_limit) or time_limit<=0:raise ValueError("Positive finite time limit required")
    if p.n==0:return Solution("ilp","optimal",np.zeros(0,dtype=int),{"objective":0,"upper_bound":0,"mip_gap":0})
    result=milp(c=-np.array(p.values,dtype=float),integrality=np.ones(p.n),bounds=Bounds(0,1),
        constraints=LinearConstraint(np.array(p.weights,dtype=float)[None,:],-np.inf,p.capacity),
        options={"time_limit":time_limit,"mip_rel_gap":0.0,"presolve":True})
    status={0:"optimal",1:"time_limit",2:"infeasible",3:"unbounded",4:"solver_error"}.get(result.status,"solver_error")
    if result.status==1 and result.x is not None:status="time_limit_with_candidate"
    def number(name):
        v=getattr(result,name,None)
        return float(v) if v is not None and np.isfinite(v) else None
    objective=number("fun");bound=number("mip_dual_bound")
    return Solution("ilp",status,result.x,{"objective":None if objective is None else -objective,
        "upper_bound":None if bound is None else -bound,"mip_gap":number("mip_gap"),
        "mip_nodes":number("mip_node_count"),"solver_status":int(result.status),"message":str(result.message)})


def exhaustive(p,max_states=1_100_000):
    p.validate()
    if (1<<p.n)>max_states:raise ValueError("Exhaustive oracle state limit exceeded")
    best=0;mask_best=0
    for mask in range(1<<p.n):
        weight=sum(w for i,w in enumerate(p.weights) if (mask>>i)&1)
        if weight>p.capacity:continue
        value=sum(v for i,v in enumerate(p.values) if (mask>>i)&1)
        if value>best:best=value;mask_best=mask
    return Solution("exhaustive","optimal",[(mask_best>>i)&1 for i in range(p.n)],{"objective":best,"states":1<<p.n})


SOLVERS={"baseline":baseline,"greedy":greedy,"dp":dynamic_programming,"branch_bound":branch_bound,"ilp":integer_programming}
