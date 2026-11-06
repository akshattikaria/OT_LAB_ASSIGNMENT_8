"""Actual numerical training plus declared policy/architecture models.

Search policies replay recorded learning curves; simulated clocks and logical
payloads must never be presented as measured cluster/GPU/network speedups.
"""
import argparse
import heapq
import itertools
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import time
import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]


def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def curves(seed):
    rng=np.random.default_rng(seed+8100)
    X=rng.normal(size=(384,8))*np.geomspace(.5,3,8)
    truth=rng.normal(size=8);y=X@truth+rng.normal(scale=.35,size=384)
    result=[]
    for i,(lr,l2,momentum) in enumerate(itertools.product([.003,.015,.06],[0,.01,.1],[0,.5,.9])):
        w=np.zeros(8);v=np.zeros(8);order=np.random.default_rng(seed+8200);epochs=[]
        for epoch in range(1,28):
            start=time.perf_counter_ns()
            for batch in np.array_split(order.permutation(192),6):
                g=X[batch].T@(X[batch]@w-y[batch])/len(batch)+l2*w
                v=momentum*v+g;w-=lr*v
            ns=time.perf_counter_ns()-start
            epochs.append({'epoch':epoch,'training_ns':ns,'validation_mse':float(np.mean((X[192:288]@w-y[192:288])**2)),'test_mse':float(np.mean((X[288:]@w-y[288:])**2))})
        result.append({'id':i,'lr':lr,'l2':l2,'momentum':momentum,'epochs':epochs})
    return result


def bayesian(trace,seed):
    f=np.array([[math.log(t['lr']),t['l2'],t['momentum']] for t in trace]);f=(f-f.min(0))/np.ptp(f,axis=0)
    chosen=list(map(int,np.random.default_rng(seed+8300).choice(27,3,replace=False)));proposals=[]
    while len(chosen)<9:
        observed=np.array([trace[i]['epochs'][-1]['validation_mse'] for i in chosen])
        gp=GaussianProcessRegressor(kernel=Matern(length_scale=.5,nu=2.5),optimizer=None,alpha=1e-7,normalize_y=True).fit(f[chosen],observed)
        remaining=[i for i in range(27) if i not in chosen];mu,sd=gp.predict(f[remaining],return_std=True)
        gain=observed.min()-mu-.01;z=np.divide(gain,sd,out=np.zeros_like(sd),where=sd>1e-12)
        ei=np.where(sd>1e-12,gain*norm.cdf(z)+sd*norm.pdf(z),0)
        pick=remaining[int(np.argmax(ei))];proposals.append({'observed':chosen.copy(),'selected':pick});chosen.append(pick)
    return chosen,proposals


def halving(trace):
    active=list(range(27));previous=0;work=0;rungs=[]
    for resource in [1,3,9,27]:
        work+=len(active)*(resource-previous)
        ranked=sorted(active,key=lambda i:(trace[i]['epochs'][resource-1]['validation_mse'],i))
        rungs.append({'resource':resource,'evaluated':active.copy(),'ranking':ranked})
        active=ranked[:max(1,len(active)//3)];previous=resource
    return active,work,rungs


def asha(trace,workers=4):
    resources=[1,3,9,27];records=[{} for _ in resources];promoted=[set() for _ in resources]
    used={i:0 for i in range(27)};free=list(range(workers));events=[];log=[];next_id=0;now=0.;work=0;final=[]
    while True:
        for worker in free.copy():
            task=None
            for rung in range(2,-1,-1):
                ranked=sorted(records[rung],key=lambda i:(records[rung][i],i))
                eligible=[i for i in ranked[:len(ranked)//3] if i not in promoted[rung]]
                if eligible:promoted[rung].add(eligible[0]);task=(eligible[0],rung+1);break
            if task is None and next_id<27:task=(next_id,0);next_id+=1
            if task is None:continue
            trial,rung=task;resource=resources[rung]
            duration=sum(e['training_ns'] for e in trace[trial]['epochs'][used[trial]:resource])/1e9
            work+=resource-used[trial]
            log.append({'kind':'start','time':now,'worker':worker,'trial':trial,'from':used[trial],'to':resource})
            used[trial]=resource;heapq.heappush(events,(now+duration,worker,trial,rung));free.remove(worker)
        if not events:break
        now,worker,trial,rung=heapq.heappop(events);value=trace[trial]['epochs'][resources[rung]-1]['validation_mse'];records[rung][trial]=value
        log.append({'kind':'finish','time':now,'worker':worker,'trial':trial,'resource':resources[rung]})
        if rung==3:final.append(trial)
        free.append(worker)
    assert final
    best=min(final,key=lambda i:(trace[i]['epochs'][-1]['validation_mse'],i))
    return [best],work,{'events':log,'event_clock_s':now,'completed_final':final,'workers':workers}


def hpo():
    raw=[];summary=[]
    for seed in range(5):
        trace=curves(seed);random=list(map(int,np.random.default_rng(seed+8400).choice(27,9,replace=False)))
        b,proposals=bayesian(trace,seed);sh,sw,rungs=halving(trace);aa,aw,events=asha(trace)
        for method,ids,work in [('input_first',[0],27),('grid_all',list(range(27)),729),('random_9',random,243),('bayesian_9',b,243),('successive_halving',sh,sw),('asha_replay',aa,aw)]:
            chosen=min(ids,key=lambda i:(trace[i]['epochs'][-1]['validation_mse'],i));last=trace[chosen]['epochs'][-1]
            summary.append({'seed':seed,'method':method,'selected':chosen,'epoch_units':work,'validation_mse':last['validation_mse'],'test_mse':last['test_mse']})
        raw.append({'seed':seed,'traces':trace,'random_ids':random,'bayesian_ids':b,'bayesian_proposals':proposals,'halving':rungs,'asha':events})
    return {'raw':raw,'summary':summary,'scope':'Actual five-seed learning curves. Policy replay reveals only authorized validation observations. Held-out labels never select models. Full reference generation still costs all training; epoch-units are policy accounting. ASHA event time is offline simulation, not measured concurrent HPO. Halving resumes checkpoints (81 units versus 108 with restarts). Budgets differ and are explicit.'}


def topk(v,k):
    if not 1<=k<=len(v):raise ValueError('Invalid k')
    out=np.zeros_like(v);out[np.argsort(-abs(v),kind='stable')[:k]]=v[np.argsort(-abs(v),kind='stable')[:k]];return out


def compression():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(seed+8500);Q,_=np.linalg.qr(rng.normal(size=(32,32)));H=(Q*np.linspace(1,20,32))@Q.T;target=rng.normal(size=32)
        for method in ['dense','topk','topk_error_feedback','int8_error_feedback']:
            w=np.zeros(32);residual=np.zeros(32);total=np.zeros(32);sent_total=np.zeros(32);history=[];start=time.perf_counter_ns()
            for step in range(1000):
                update=.002*(H@(w-target));feedback='error_feedback' in method;p=update+residual if feedback else update
                if method=='dense':sent=p
                elif method.startswith('int8'):
                    scale=max(float(abs(p).max())/127,1e-30);sent=np.rint(p/scale).clip(-127,127).astype(np.int8).astype(float)*scale
                else:sent=topk(p,2)
                residual=p-sent if feedback else np.zeros(32);w-=sent;total+=update;sent_total+=sent
                if step%25==0 or step==999:history.append({'step':step+1,'objective':.5*float((w-target)@H@(w-target))})
            error=float(np.linalg.norm(total-sent_total-residual)) if feedback else None
            if feedback:assert error<1e-10
            payload=256 if method=='dense' else 40 if method.startswith('int8') else 24
            rows.append({'seed':seed,'method':method,'objective':history[-1]['objective'],'logical_bytes':payload*1000,'wall_s':(time.perf_counter_ns()-start)/1e9,'conservation_error':error,'history':history})
    rng=np.random.default_rng(8600);A=rng.normal(size=(96,8))@rng.normal(size=(8,32))+.05*rng.normal(size=(96,32));W=rng.normal(size=(32,8));U,s,V=np.linalg.svd(A,full_matrices=False);lowrank=[]
    for rank in [1,4,8,16,32]:
        B=(U[:,:rank]*s[:rank])@V[:rank];lowrank.append({'rank':rank,'dense_numbers':A.size,'factor_numbers':rank*(96+32+1),'relative_output_error':float(np.linalg.norm((A-B)@W)/np.linalg.norm(A@W))})
    return {'runs':rows,'lowrank':lowrank,'scope':'Actual SPD quadratic optimization; same starts, 1000 steps, eta=.002. Logical payload is float64 dense or top-2 float64+uint32 indices or int8 codes+float64 scale. Excludes protocol; no measured network. SVD control is not Subspace Networks/OFLight.'}


def schedule(jobs,p,kind):
    queues=[[] for _ in range(p)]
    if kind=='block':queues=[list(map(int,a)) for a in np.array_split(np.arange(len(jobs)),p)]
    elif kind=='cyclic':
        for i in range(len(jobs)):queues[i%p].append(i)
    elif kind not in ['dynamic','guided']:raise ValueError(kind)
    heap=[(0.,i) for i in range(p)];heapq.heapify(heap);next_id=0;events=[]
    while heap:
        at,rank=heapq.heappop(heap)
        if kind in ['dynamic','guided']:
            remaining=len(jobs)-next_id
            if not remaining:continue
            size=1 if kind=='dynamic' else math.ceil(remaining/p);ids=list(range(next_id,min(len(jobs),next_id+size)));next_id+=len(ids)
        else:
            if not queues[rank]:continue
            ids=[queues[rank].pop(0)]
        for i in ids:events.append({'worker':rank,'job':i,'start':at,'end':at+jobs[i]});at+=jobs[i]
        heapq.heappush(heap,(at,rank))
    assert sorted(e['job'] for e in events)==list(range(len(jobs)))
    return {'method':kind,'makespan':max(e['end'] for e in events),'events':events}


def layouts():
    rows=[]
    for a in range(7):
        for b in range(7-a):
            d,t,p=2**a,2**b,2**(6-a-b);memory=160/(t*p)+8/p;cost=8/d+.12*(t-1)+.08*(p-1)+.01*(d-1)
            rows.append({'d':d,'t':t,'p':p,'memory_gb':memory,'modeled_s':cost,'feasible':memory<=24 and p<=16})
    feasible=[i for i,r in enumerate(rows) if r['feasible']];best=min(feasible,key=lambda i:rows[i]['modeled_s']);ga=[];pso=[]
    def f(x):return 20+np.sum(x*x-10*np.cos(2*np.pi*x),axis=-1)
    for seed in range(5):
        rng=np.random.default_rng(seed+8700);pop=list(map(int,rng.choice(feasible,12)));trace=[]
        for _ in range(20):
            ranked=sorted(pop,key=lambda i:rows[i]['modeled_s']);trace.append(rows[ranked[0]]['modeled_s']);pop=ranked[:2]
            while len(pop)<12:
                pa,pb=rng.choice(ranked[:6],2);targetd,targett=rows[int(pa)]['d'],rows[int(pb)]['t'];child=min(feasible,key=lambda i:abs(math.log2(rows[i]['d']/targetd))+abs(math.log2(rows[i]['t']/targett)))
                pop.append(int(rng.choice(feasible)) if rng.random()<.2 else child)
        winner=min(pop,key=lambda i:rows[i]['modeled_s']);ga.append({'seed':seed,'selected':winner,'gap':rows[winner]['modeled_s']-rows[best]['modeled_s'],'history':trace})
        rng=np.random.default_rng(seed+8800);x=rng.uniform(-5.12,5.12,(24,2));v=np.zeros_like(x);pb=x.copy();values=f(x)
        for _ in range(100):
            gb=pb[np.argmin(values)].copy();v=.7*v+1.4*rng.random(x.shape)*(pb-x)+1.4*rng.random(x.shape)*(gb-x);x=np.clip(x+v,-5.12,5.12);now=f(x);improved=now<values;pb[improved]=x[improved];values[improved]=now[improved]
        rand=np.random.default_rng(seed+8800).uniform(-5.12,5.12,(2424,2));pso.append({'seed':seed,'objective':float(values.min()),'random_best':float(f(rand).min()),'evaluations_each':2424})
    return {'layouts':rows,'finite_optimum_index':best,'ga':ga,'pso':pso,'scope':'28 ordered layouts for 64 modeled devices; fictional memory/time. GA mechanism, not EAHP/Astra. Separate bounded 2D Rastrigin PSO control with equal random-search calls.'}


def embedding():
    states=list(itertools.product([-1,1],repeat=4));rows=[]
    for C in [0,.25,1,2,4]:
        energy=[s[1]*s[2]+s[2]*s[3]+s[3]*s[0]-C*s[0]*s[1] for s in states];ground=[s for s,e in zip(states,energy) if e==min(energy)]
        rows.append({'strength':C,'ground_energy':min(energy),'ground_states':ground,'broken':sum(s[0]!=s[1] for s in ground),'rescaled_logical_coupling':1/max(1,C)})
    return {'physical_edges':[[0,1],[1,2],[2,3],[3,0]],'chains':[[0,1],[2],[3]],'logical_ground_energy':-1,'rows':rows,'scope':'Exact classical enumeration of triangle minor embedding; 4 physical spins for 3 logical variables. No hardware annealer or dynamics.'}


def foundations():
    rng=np.random.default_rng(241070005);W=rng.normal(size=(32,8)).astype(np.float32);X=rng.normal(size=(128,32)).astype(np.float32);scale=float(abs(W).max()/127);q=np.rint(W/scale).clip(-127,127).astype(np.int8);restored=q.astype(np.float32)*scale;mask=abs(W)>=np.partition(abs(W).ravel(),128)[128]
    quant={'original_bytes':W.nbytes,'quantized_bytes_including_scale':q.nbytes+4,'relative_output_error':float(np.linalg.norm(X@(W-restored))/np.linalg.norm(X@W)),'pruned_nonzeros':int(mask.sum()),'pruning_output_error':float(np.linalg.norm(X@(W*(~mask)))/np.linalg.norm(X@W))}
    target=[1,2,3,4,0,1]
    def cost(c):return sum((a-b)**2 for a,b in zip(c,target))+sum(c[i]==c[i+1] for i in range(5))
    choices=list(itertools.product(range(5),repeat=6));best=min(choices,key=lambda c:(cost(c),c));stale=[]
    for delay in [0,2,8]:
        w=np.array([3.,-2.]);history=[w.copy()];trace=[]
        for i in range(80):
            old=history[max(0,len(history)-1-delay)];w=w-.05*np.array([old[0],4*old[1]]);history.append(w.copy());trace.append(float(.5*(w[0]**2+4*w[1]**2)))
        stale.append({'delay':delay,'objective_trace':trace})
    placements=[];access=[[90,10],[20,80]]
    for nodes in itertools.product([0,1],repeat=2):placements.append({'nodes':nodes,'feasible':len(set(nodes))==2,'cost':sum(access[pg][cpu]*(1 if nodes[pg]==cpu else 3) for pg in range(2) for cpu in range(2))})
    inputs=[[1,2],[3,4],[5,6],[7,8]];reduced=np.sum(inputs,axis=0).tolist()
    return {'quantization_pruning':quant,'architecture_choice':{'count':len(choices),'best':best,'objective':cost(best),'baseline_objective':cost([0]*6)},'stale_gradients':stale,'collectives':{'inputs':inputs,'broadcast':[inputs[0]]*4,'gather':sum(inputs,[]),'reduce':reduced,'allreduce':[reduced]*4},'lost_update':{'initial':5,'reads':[5,5],'writes':[6,6],'actual':6,'serial_or_atomic':7},'deadlock_wait_cycle':['T1','lockB','T2','lockA','T1'],'ordered_lock_fix':['lockA','lockB'],'numa_placements':placements,'arithmetic':{'amdahl_s02_p8':1/(.2+.8/8),'gustafson_s01_p16':14.5,'ring_200MB_p4_per_rank_bytes':300000000,'overlap_10ms_compute_5ms_comm_lower_s':.010},'scope':'Actual toy matrix quantization/pruning; synthetic 5^6 architecture choices, NUMA/interleaving/collective/delayed-gradient models. No trained NAS, actual MPI, NUMA hardware or asynchronous cluster timing.'}


def false_sharing(out):
    binary=out/'false_sharing';source=ROOT/'chapter_supplement/false_sharing.c'
    build=subprocess.run(['cc','-O2','-std=c11','-fopenmp',str(source),'-o',str(binary)],capture_output=True,text=True);(out/'native_build.log').write_text(build.stdout+build.stderr)
    if build.returncode:return {'executed':False,'reason':'OpenMP build failed; log retained'}
    env=os.environ.copy();env.update(OMP_PROC_BIND='true',OMP_PLACES='cores');rows=[]
    for stride in [1,8]:subprocess.run([str(binary),str(stride)],env=env,capture_output=True,text=True,check=True)
    rng=np.random.default_rng(241070005)
    for rep in range(7):
        for stride in rng.permutation([1,8]):
            r=subprocess.run([str(binary),str(stride)],env=env,capture_output=True,text=True,check=True);count,seconds=r.stdout.split();assert int(count)==2000000
            rows.append({'repeat':rep,'stride':int(stride),'increments':int(count),'seconds':float(seconds)})
    binary.unlink();return {'executed':True,'rows':rows,'scope':'Two real OpenMP CPU threads, adjacent versus 64-byte-spaced relaxed atomic counters. Seven seeded paired trial orders. No hardware coherence counters; not a universal padding speedup.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='chapter_supplement/results');args=parser.parse_args();out=Path(args.out)
    if out.exists() and any(out.iterdir()):parser.error('Use a new empty output folder')
    out.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=1):
        for name,fn in [('hpo',hpo),('compression',compression),('layouts',layouts),('embedding',embedding),('foundations',foundations)]:print('Running '+name,flush=True);save(out/(name+'.json'),fn())
    save(out/'scheduling.json',{'jobs':[8,7,6,5,4,3,2,1],'workers':4,'rows':[schedule([8,7,6,5,4,3,2,1],4,k) for k in ['block','cyclic','dynamic','guided']],'scope':'Zero-overhead discrete-event scheduling, not measured runtime.'})
    save(out/'false_sharing.json',false_sharing(out))
    import importlib.metadata,platform,datetime
    save(out/'environment.json',{'python':platform.python_version(),'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','matplotlib']}})
    save(out/'completion.json',{'complete':True,'sections':['hpo','compression','layouts','embedding','foundations','scheduling','false_sharing']});print('Complete',flush=True)


if __name__=='__main__':main()
