"""Live asynchronous halving, implicit hypergradients and LMO controls."""
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from itertools import product
import math
import time
import numpy as np
from scipy.stats import qmc


def ridge_solution(x,y,loglam):
    lam=np.exp(loglam);a=x.T@x/len(x)+lam*np.eye(x.shape[1]);w=np.linalg.solve(a,x.T@y/len(x))
    return w,a


def hypergradient(x,y,vx,vy,loglam):
    w,a=ridge_solution(x,y,loglam);validation_gradient=vx.T@(vx@w-vy)/len(vy)
    return float(-np.exp(loglam)*validation_gradient@np.linalg.solve(a,w))


def implicit_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(6000+seed);x=rng.normal(size=(24,12));truth=rng.normal(size=12);y=x@truth+rng.normal(scale=1.2,size=24)
        vx=rng.normal(size=(24,12));vy=vx@truth+rng.normal(scale=1.2,size=24);tx=rng.normal(size=(100,12));ty=tx@truth+rng.normal(scale=1.2,size=100)
        low,high=-8.,3.
        candidates={'grid':np.linspace(low,high,19),'random':rng.uniform(low,high,size=19),'sobol':low+(high-low)*qmc.Sobol(1,scramble=True,seed=seed).random_base2(5)[:19,0]}
        for method,values in candidates.items():
            start=time.perf_counter();trace=[]
            for value in values:
                w,_=ridge_solution(x,y,value);trace.append({'log_lambda':float(value),'validation_loss':float(np.mean((vx@w-vy)**2)/2)})
            choice=min(trace,key=lambda r:r['validation_loss']);w,_=ridge_solution(x,y,choice['log_lambda'])
            rows.append({'seed':seed,'method':method,'validation_loss':choice['validation_loss'],'test_loss':float(np.mean((tx@w-ty)**2)/2),'log_lambda':choice['log_lambda'],'linear_solves':20,'elapsed_s':time.perf_counter()-start,'trace':trace})
        value=0.;trace=[];start=time.perf_counter()
        for step in range(9):
            gradient=hypergradient(x,y,vx,vy,value);trace.append({'step':step,'log_lambda':value,'hypergradient':gradient});value=float(np.clip(value-.8*gradient,low,high))
        w,_=ridge_solution(x,y,value)
        rows.append({'seed':seed,'method':'implicit_hypergradient','validation_loss':float(np.mean((vx@w-vy)**2)/2),'test_loss':float(np.mean((tx@w-ty)**2)/2),'log_lambda':value,'linear_solves':19,'elapsed_s':time.perf_counter()-start,'trace':trace})
    return rows


def lmo(gradient,norm):
    g=np.asarray(gradient)
    if norm=='l2':return -g/max(np.linalg.norm(g),1e-15)
    if norm=='linf':return -np.sign(g)
    if norm=='l1':
        d=np.zeros_like(g);index=np.argmax(np.abs(g));d.flat[index]=-np.sign(g.flat[index]);return d
    if norm=='spectral':
        u,_,v=np.linalg.svd(g,full_matrices=False);return -u@v
    raise ValueError(norm)


def lmo_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(6300+seed);a=np.diag([.1,.3,1.,3.,10.,30.]);target=rng.normal(size=6);initial=rng.normal(size=6)
        for norm in ['l1','l2','linf']:
            w=initial.copy();trace=[]
            for step in range(100):
                g=a@(w-target);direction=lmo(g,norm);denom=direction@a@direction
                alpha=float(-(g@direction)/denom) if denom>1e-15 else 0.
                w+=alpha*direction;trace.append(float((w-target)@a@(w-target)/2))
            rows.append({'seed':seed,'norm':norm,'final_objective':trace[-1],'trace':trace,'initial':initial,'target':target})
        matrix=rng.normal(size=(6,4));d=lmo(matrix,'spectral')
        rows.append({'seed':seed,'norm':'spectral_certificate','oracle_inner_product':float(np.sum(matrix*d)),'negative_dual_norm':float(-np.linalg.svd(matrix,compute_uv=False).sum()),'primal_norm':float(np.linalg.norm(d,2))})
    return rows


def segment(config,state,begin,end,x,y,vx,vy,seed,origin):
    start=time.perf_counter()-origin;w,velocity=[v.copy() for v in state];lr,l2,momentum=config
    for epoch in range(begin,end):
        ids=np.random.default_rng(seed+epoch).permutation(len(x))
        for index in range(0,len(x),32):
            batch=ids[index:index+32];g=x[batch].T@(x[batch]@w-y[batch])/len(batch)+l2*w
            velocity=momentum*velocity+g;w-=lr*velocity
    score=float(np.mean((vx@w-vy)**2));finish=time.perf_counter()-origin
    return (w,velocity),score,start,finish


def live_policy(configs,x,y,vx,vy,seed,method,workers=4):
    rungs=[1,3,9,27];states={i:(np.zeros(x.shape[1]),np.zeros(x.shape[1])) for i in range(len(configs))};scores={r:[] for r in rungs};events=[];units=0;origin=time.perf_counter();completed=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        if method in ['full_grid','synchronous_halving']:
            active=list(range(len(configs)));previous=0
            for rung in ([27] if method=='full_grid' else rungs):
                futures={pool.submit(segment,configs[i],states[i],previous,rung,x,y,vx,vy,seed+i*100,origin):i for i in active}
                rung_values=[]
                for future in futures:
                    i=futures[future];state,score,start,finish=future.result();states[i]=state;units+=rung-previous;rung_values.append((score,i));events.append({'trial':i,'from':previous,'to':rung,'start':start,'finish':finish,'validation_mse':score})
                if rung==27:completed=rung_values
                else:active=[i for _,i in sorted(rung_values)[:max(1,len(active)//3)]]
                previous=rung
        else:
            pending={};next_trial=0
            def submit(i,begin,end):pending[pool.submit(segment,configs[i],states[i],begin,end,x,y,vx,vy,seed+i*100,origin)]=(i,begin,end)
            for _ in range(min(workers,len(configs))):submit(next_trial,0,1);next_trial+=1
            while pending:
                done,_=wait(pending,return_when=FIRST_COMPLETED)
                for future in sorted(done,key=lambda f:f.result()[3]):
                    i,begin,rung=pending.pop(future);state,score,start,finish=future.result();states[i]=state;units+=rung-begin;scores[rung].append((score,i))
                    ranking=sorted(scores[rung]);quota=max(1,math.ceil(len(ranking)/3));promote=rung<27 and (len(ranking)<3 or i in [trial for _,trial in ranking[:quota]])
                    events.append({'trial':i,'from':begin,'to':rung,'start':start,'finish':finish,'decision_time':time.perf_counter()-origin,'validation_mse':score,'observed_rung_trials':[j for _,j in scores[rung]],'continue':promote})
                    if rung==27:completed.append((score,i))
                    if promote:submit(i,rung,rungs[rungs.index(rung)+1])
                    elif next_trial<len(configs):submit(next_trial,0,1);next_trial+=1
    elapsed=time.perf_counter()-origin;score,selected=min(completed)
    return {'method':method,'selected_trial':selected,'validation_mse':score,'epoch_units':units,'wall_s':elapsed,'completed_max_resource':len(completed),'events':events},states[selected][0]


def asynchronous_study():
    rows=[];configs=list(product([.005,.02,.06],[0.,.03,.2],[0.,.5,.8]))
    for seed in range(3):
        rng=np.random.default_rng(6600+seed);x=rng.normal(size=(160,12));truth=rng.normal(size=12);y=x@truth+rng.normal(scale=.5,size=160);vx=rng.normal(size=(60,12));vy=vx@truth+rng.normal(scale=.5,size=60);tx=rng.normal(size=(80,12));ty=tx@truth+rng.normal(scale=.5,size=80)
        for method in ['full_grid','synchronous_halving','asynchronous_stopping']:
            row,w=live_policy(configs,x,y,vx,vy,seed,method);row.update(seed=seed,test_mse=float(np.mean((tx@w-ty)**2)),selected_configuration=configs[row['selected_trial']]);rows.append(row)
    return {'runs':rows,'configs':configs}


def run():
    return {'implicit_hypergradient':implicit_study(),'norm_oracles':lmo_study(),'live_halving':asynchronous_study(),'scope':'HPO survey: implicit differentiation of exact ridge solution and grid/random/Sobol controls; 19 vs 20 linear solves are disclosed. OmniOpt is a taxonomy/survey, so norm-LMO mechanisms are demonstrated rather than inventing a single OmniOpt optimizer. ASHA-related stopping policy uses real four-worker training segments, completion-only validation observations and checkpoint continuation. Warm-start rule continues until three rung results exist; this explicit variant is not the paper 500-worker system or promotion queue. Timings include scheduler/worker overhead on shared cloud CPU.'}
