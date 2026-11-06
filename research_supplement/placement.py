"""Verifiable finite controls for grouping, locality and packing spotlights.

The primary abstracts establish the mechanisms; unavailable detailed policies
are not silently reconstructed or called exact paper implementations.
"""
from itertools import product
import numpy as np


def mcl(affinity,inflation=2.,iterations=80):
    a=np.asarray(affinity,dtype=float)+np.eye(len(affinity));a/=a.sum(0,keepdims=True)
    for _ in range(iterations):
        before=a.copy();a=a@a;a=np.power(a,inflation);a[a<1e-10]=0;a/=a.sum(0,keepdims=True)
        if np.linalg.norm(a-before)<1e-9:break
    # Supports of attractor rows yield disjoint hard clusters for our
    # block-diagonal-plus-weak-cross-edge inputs; overlap is rejected.
    clusters=[];used=set()
    for row in a:
        cluster=set(np.flatnonzero(row>1e-5))
        if cluster and not cluster<=used:
            cluster-=used;clusters.append(sorted(cluster));used|=cluster
    clusters.extend([[i] for i in set(range(len(a)))-used])
    return clusters,a


def placement_score(mapping,work,speeds,affinity):
    loads=np.array([sum(work[i] for i,w in enumerate(mapping) if w==node)/speed for node,speed in enumerate(speeds)])
    remote=sum(affinity[i,j]*abs(mapping[i]-mapping[j]) for i in range(len(mapping)) for j in range(i+1,len(mapping)))
    return float(loads.max()+.02*remote),loads,float(remote)


def grouping_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(5000+seed);n=12;affinity=rng.uniform(0,.03,size=(n,n));affinity=(affinity+affinity.T)/2
        for i in range(n):
            for j in range(n):
                if i//3==j//3:affinity[i,j]+=2
        groups,transition=mcl(affinity);work=rng.integers(1,8,size=n);speeds=[1.,1.7,2.8]
        assignments=[]
        for method in ['round_robin','heterogeneity_only','grouped_heterogeneity']:
            mapping=[-1]*n;loads=np.zeros(3)
            blocks=[[i] for i in range(n)] if method!='grouped_heterogeneity' else groups
            for index,group in enumerate(sorted(blocks,key=lambda g:-sum(work[i] for i in g))):
                node=index%3 if method=='round_robin' else int(np.argmin(loads+sum(work[i] for i in group)/np.array(speeds)))
                for i in group:mapping[i]=node
                loads[node]+=sum(work[i] for i in group)/speeds[node]
            score,loads,remote=placement_score(mapping,work,speeds,affinity)
            assignments.append({'method':method,'mapping':mapping,'modeled_score':score,'modeled_compute_makespan':float(loads.max()),'remote_affinity_hops':remote})
        optimum=float('inf');best=None
        for choice in product(range(3),repeat=len(groups)):
            mapping=[-1]*n
            for group,node in zip(groups,choice):
                for i in group:mapping[i]=node
            score,_,_=placement_score(mapping,work,speeds,affinity)
            if score<optimum:optimum=score;best=mapping
        rows.append({'seed':seed,'affinity':affinity,'mcl_groups':groups,'mcl_column_sum_error':float(np.max(np.abs(transition.sum(0)-1))),'work':work,'speeds':speeds,'assignments':assignments,'exact_group_constrained_optimum':optimum,'optimum_mapping':best})
    return rows


def curry_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(5400+seed);blocks=rng.normal(size=(9,32));owners=np.arange(9);receiver=0
        def hops(a,b):return abs(a//3-b//3)+abs(a%3-b%3)
        for theta in [.2,.8,1.5]:
            direct=float(np.sin(blocks+theta).sum());partials=[];trace=[]
            for block,owner in zip(blocks,owners):
                # A partial application closes over theta and runs beside
                # its block, then only its scalar result is transported.
                partial=float(np.sin(block+theta).sum());partials.append(partial)
                trace.append({'owner':int(owner),'destination':receiver,'partial_value':partial,'hop_distance':hops(int(owner),receiver),'radius':0,'postponed_until_reduction':True})
            curried=float(sum(partials));raw_bytes=sum(32*8*hops(int(owner),receiver) for owner in owners);partial_bytes=sum(8*hops(int(owner),receiver) for owner in owners)
            rows.append({'seed':seed,'theta':theta,'direct_result':direct,'curried_result':curried,'absolute_error':abs(direct-curried),'baseline_logical_byte_hops':raw_bytes,'curried_logical_byte_hops':partial_bytes,'trace':trace})
    return rows


def packing_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(5700+seed);weights=rng.integers(1,12,size=40);initial=[0]*28+[1]*6+[2]*4+[3]*2
        for packing in [False,True]:
            nodes=[[i for i,w in enumerate(initial) if w==node] for node in range(4)];migrations=messages=0;trace=[]
            for iteration in range(100):
                load=[sum(weights[i] for i in node) for node in nodes];donor=int(np.argmax(load));receiver=int(np.argmin(load))
                if load[donor]-load[receiver]<=2*min(weights[i] for i in nodes[donor]):break
                maximum=(load[donor]-load[receiver])/2
                ordered=sorted(nodes[donor],key=lambda i:(weights[i],i));pack=[];amount=0
                for item in ordered:
                    if amount+weights[item]<=maximum:
                        pack.append(item);amount+=weights[item]
                        if not packing:break
                if not pack:break
                before=max(load)
                for item in pack:nodes[donor].remove(item);nodes[receiver].append(item)
                messages+=2;migrations+=len(pack);trace.append({'donor':donor,'receiver':receiver,'pack':pack,'pack_load':int(amount),'before_makespan':int(before),'after_makespan':int(max(sum(weights[i] for i in node) for node in nodes))})
            assert sorted(i for node in nodes for i in node)==list(range(40))
            rows.append({'seed':seed,'method':'packed_transfer' if packing else 'single_task_transfer','weights':weights,'initial_mapping':initial,'final_nodes':nodes,'modeled_makespan':int(max(sum(weights[i] for i in node) for node in nodes)),'logical_request_reply_messages':messages,'migrated_tasks':migrations,'trace':trace})
    return rows


def run():
    return {'grouping':grouping_study(),'currying':curry_study(),'packing':packing_study(),'scope':'Finite mechanism demonstrations: MCL grouping plus speed-aware placement (GSHetero-related); partial application, delegated near-data work and final reduction on a 3x3 mesh (currying-related); task-pack migration vs single-item transfer (PackStealLB-related). Detailed published policies were unavailable, so these original policies are explicitly abstract-level controls, not exact implementations of those papers. Logical scores/messages/byte-hops are not measured Hadoop, Charm++ or near-data hardware performance.'}
