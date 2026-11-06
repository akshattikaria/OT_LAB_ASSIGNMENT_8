"""Explicit heterogeneous-pipeline cost search with exhaustive/LP references."""
from itertools import combinations,product
import numpy as np
from scipy.optimize import linprog


def pipeline_time(forward,backward,links,microbatches):
    p=len(forward);f=np.zeros((microbatches,p));b=np.zeros_like(f)
    for m in range(microbatches):
        for s in range(p):
            f[m,s]=max(f[m-1,s] if m else 0.,f[m,s-1]+links[s-1] if s else 0.)+forward[s]
    barrier=f[-1,-1]
    for m in range(microbatches-1,-1,-1):
        for s in range(p-1,-1,-1):
            b[m,s]=max(b[m+1,s] if m<microbatches-1 else barrier,b[m,s+1]+links[s] if s<p-1 else barrier)+backward[s]
    return float(b[0,0]),f,b


def catalog():
    # Fully specified synthetic profiles, not measurements of named GPUs.
    devices=[{'name':'fast_small','flops_s':12e12,'memory_bytes':16e9,'hourly_cost':2.}, {'name':'slow_large','flops_s':5e12,'memory_bytes':32e9,'hourly_cost':.7}]
    layers=np.array([2,3,4,2,5,4,3,2],dtype=float)*1e11;parameters=np.array([1,2,3,1,4,3,2,1])*100_000_000
    plans=[]
    for dp,tp,pipeline in product([1,2,4],[1,2,4],[1,2,4]):
        gpu_count=dp*tp*pipeline
        if gpu_count>8:continue
        for cuts in combinations(range(1,len(layers)),pipeline-1):
            boundaries=(0,)+cuts+(len(layers),)
            for types in product(range(2),repeat=pipeline):
                forward=[];memory=[];hourly=0.;feasible=True
                for stage,kind in enumerate(types):
                    first,last=boundaries[stage:stage+2];device=devices[kind]
                    communication=2*(tp-1)/tp*(32*4096*4)/20e9 if tp>1 else 0.
                    forward.append(float(layers[first:last].sum()/(tp*device['flops_s'])+communication))
                    used=float(16*parameters[first:last].sum()/tp+pipeline*32*4096*4/tp);memory.append(used)
                    feasible&=used<=device['memory_bytes'];hourly+=dp*tp*device['hourly_cost']
                if not feasible:continue
                links=[float(32*4096*4/(12e9 if types[s]!=types[s+1] else 20e9)+1e-6) for s in range(pipeline-1)]
                elapsed,_,_=pipeline_time(forward,[2*v for v in forward],links,4)
                elapsed+=2*(dp-1)/dp*float(parameters.sum()*4/tp)/20e9 if dp>1 else 0.
                plans.append({'dp':dp,'tp':tp,'pipeline':pipeline,'cuts':cuts,'device_types':types,'gpu_count':gpu_count,'stage_memory_bytes':memory,'modeled_iteration_s':elapsed,'hourly_cost':hourly,'modeled_samples_s':4*32*dp/elapsed,'modeled_cost_per_1000_samples':hourly/3600/(4*32*dp/elapsed)*1000})
    return plans,devices,layers,parameters


def run():
    plans,devices,layers,parameters=catalog();budget=8.;feasible=[i for i,p in enumerate(plans) if p['hourly_cost']<=budget]
    fastest=max(feasible,key=lambda i:plans[i]['modeled_samples_s']);target=.8*plans[fastest]['modeled_samples_s']
    economical=min((i for i in feasible if plans[i]['modeled_samples_s']>=target),key=lambda i:plans[i]['modeled_cost_per_1000_samples'])
    costs=np.array([p['modeled_iteration_s'] for p in plans]);allowed=[(0,1) if i in set(feasible) else (0,0) for i in range(len(plans))]
    # A one-hot strategy selector is an LP whose simplex vertices are
    # integral. This is an independent finite-model reference, not EAHP's
    # unavailable full published linear program.
    reference=linprog(costs,A_eq=np.ones((1,len(plans))),b_eq=[1],bounds=allowed,method='highs');assert reference.success
    optimum=int(np.argmax(reference.x));runs=[]
    for seed in range(5):
        rng=np.random.default_rng(7800+seed);population=list(rng.choice(feasible,size=12,replace=False));observed={};trace=[]
        for generation in range(8):
            for i in population:observed[i]=plans[i]['modeled_iteration_s']
            ranked=sorted(population,key=lambda i:plans[i]['modeled_iteration_s']);trace.append({'generation':generation,'best_index':int(ranked[0]),'best_iteration_s':plans[ranked[0]]['modeled_iteration_s'],'unique_models_queried':len(observed)})
            parents=ranked[:4];next_population=parents.copy()
            while len(next_population)<12:
                a,b=map(int,rng.choice(parents,size=2));pa,pb=plans[a],plans[b]
                # Cross over actual parallelism genes, then choose an
                # available placement/cut variant; mutate to preserve reach.
                dp=pa['dp'];tp=pb['tp'];pipeline=pa['pipeline'] if rng.random()<.5 else pb['pipeline']
                candidates=[i for i in feasible if (plans[i]['dp'],plans[i]['tp'],plans[i]['pipeline'])==(dp,tp,pipeline)]
                child=int(rng.choice(candidates or feasible)) if rng.random()>.2 else int(rng.choice(feasible))
                next_population.append(child)
            population=next_population
        selected=min(observed,key=observed.get)
        runs.append({'seed':seed,'selected_index':int(selected),'selected_time':observed[selected],'exact_model_optimum':float(reference.fun),'model_optimality_gap':observed[selected]-float(reference.fun),'unique_cost_queries':len(observed),'trace':trace})
    return {'plans':plans,'devices':devices,'layer_flops':layers,'layer_parameters':parameters,'hourly_budget':budget,'astra_throughput_choice':fastest,'astra_economical_choice':economical,'throughput_target':target,'exact_time_optimum_index':optimum,'ga_runs':runs,'scope':'Astra-related explicit device-configuration/parallelism enumeration, memory filtering, heterogeneous stage costs, GPipe forward/backward event model and throughput/money trade-off. EAHP-related structured GA plus one-hot LP reference on the SAME finite cost model. Profiles/bandwidths are declared synthetic; this is not Astra Megatron calibration or EAHP full published planner (full chapter unavailable), and not measured GPU training. Enumerating the catalog for audit costs full compute; GA query savings are policy counts only.'}
