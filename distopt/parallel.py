"""Real shared-memory CPU inference: data, hidden-unit tensor, two-stage pipeline."""
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from time import perf_counter,thread_time
import numpy as np
from threadpoolctl import threadpool_limits


def data(seed=0,batch=8192,dim=256,hidden=512,out=256):
    rng=np.random.default_rng(seed+4000)
    return (rng.normal(size=(batch,dim)),rng.normal(size=(dim,hidden))/np.sqrt(dim),rng.normal(size=(hidden,out))/np.sqrt(hidden))


def serial(X,W1,W2):return np.tanh(X@W1)@W2


def partitioned(X,W1,W2,workers,kind,pool):
    if kind=='data':
        pieces=np.array_split(X,workers)
        return np.concatenate(list(pool.map(lambda chunk:serial(chunk,W1,W2),pieces)))
    if kind=='model':
        pieces=np.array_split(np.arange(W1.shape[1]),workers)
        partials=list(pool.map(lambda columns:np.tanh(X@W1[:,columns])@W2[columns,:],pieces))
        return sum(partials,np.zeros((len(X),W2.shape[1])))
    raise ValueError('Unknown parallel inference mode')


def pipeline(X,W1,W2,microbatches):
    if not 1<=microbatches<=len(X):raise ValueError('Invalid microbatch count')
    pieces=np.array_split(X,microbatches);channel=queue.Queue(maxsize=2);ready=queue.Queue();barrier=threading.Barrier(3);outputs=[None]*microbatches;stages=[];errors=[]
    def first():
        try:
            ready.put(True)
            barrier.wait(timeout=120);cpu=thread_time()
            for index,chunk in enumerate(pieces):
                start=perf_counter();activation=np.tanh(chunk@W1);finish=perf_counter()
                stages.append({'stage':0,'microbatch':index,'start':start,'finish':finish});channel.put((index,activation),timeout=120)
            channel.put(None,timeout=120);stages.append({'stage':0,'thread_cpu_s':thread_time()-cpu})
        except Exception as error:errors.append(repr(error))
    def second():
        try:
            ready.put(True)
            barrier.wait(timeout=120);cpu=thread_time()
            while True:
                message=channel.get(timeout=120)
                if message is None:break
                index,activation=message;start=perf_counter();outputs[index]=activation@W2;finish=perf_counter()
                stages.append({'stage':1,'microbatch':index,'start':start,'finish':finish})
            stages.append({'stage':1,'thread_cpu_s':thread_time()-cpu})
        except Exception as error:errors.append(repr(error))
    threads=[threading.Thread(target=first),threading.Thread(target=second)];outer=perf_counter()
    for thread in threads:thread.start()
    for _ in threads:ready.get(timeout=120)
    start=perf_counter();barrier.wait(timeout=120)
    for thread in threads:thread.join(timeout=120)
    if errors or any(thread.is_alive() for thread in threads):raise RuntimeError(str(errors))
    result=np.concatenate(outputs);seconds=perf_counter()-start
    for event in stages:
        if 'start' in event:event['start']-=start;event['finish']-=start
    return result,{'microbatches':microbatches,'workers':2,'steady_s':seconds,'end_to_end_s':perf_counter()-outer,'events':stages,
        'ideal_balanced_stage_bubble_fraction':1/(microbatches+1),'ideal_balanced_stage_speedup':2*microbatches/(microbatches+1)}


def measure_inference(workers=(1,2,4,8),repeats=3,batches=(2048,8192),forwards=3):
    rows=[];pipelines=[];references={}
    with threadpool_limits(limits=1):
        for batch in batches:
            X,W1,W2=data(batch=batch);expected=serial(X,W1,W2);references[str(batch)]={'shape':list(expected.shape),'sum':float(np.sum(expected)),'squared_norm':float(np.sum(expected**2))}
            for repeat in range(repeats):
                clock=perf_counter()
                for _ in range(forwards):result=serial(X,W1,W2)
                rows.append({'kind':'serial','batch':batch,'workers':1,'repeat':repeat,'forwards':forwards,'seconds':perf_counter()-clock,'max_abs_error':float(np.max(abs(result-expected)))})
            # Predeclared shuffled trial order reduces systematic method-order bias.
            trials=[(kind,p,r) for kind in ('data','model') for p in workers for r in range(repeats)]
            order=np.random.default_rng(4200+batch).permutation(len(trials))
            for position in order:
                kind,p,repeat=trials[position];outer=perf_counter()
                with ThreadPoolExecutor(max_workers=p) as pool:
                    partitioned(X,W1,W2,p,kind,pool) # Warmup excluded from steady time.
                    start=perf_counter()
                    for _ in range(forwards):result=partitioned(X,W1,W2,p,kind,pool)
                    seconds=perf_counter()-start
                error=float(np.max(abs(result-expected)))
                if not np.allclose(result,expected,atol=1e-9,rtol=1e-10):raise AssertionError('Parallel model changed its output')
                rows.append({'kind':kind,'batch':batch,'workers':p,'repeat':repeat,'forwards':forwards,'seconds':seconds,
                    'end_to_end_s':perf_counter()-outer,'max_abs_error':error})
            print(f'Data/model inference batch={batch} complete',flush=True)
            if batch==max(batches):
                for m in (1,4,16,64):
                    pipeline(X,W1,W2,m) # Per-configuration warmup.
                    for repeat in range(repeats):
                        result,row=pipeline(X,W1,W2,m);error=float(np.max(abs(result-expected)))
                        if not np.allclose(result,expected,atol=1e-9,rtol=1e-10):raise AssertionError('Pipeline output changed')
                        pipelines.append({**row,'repeat':repeat,'batch':batch,'max_abs_error':error})
    return {'inference':rows,'pipeline':pipelines,'references':references,
        'note':'Shared-memory CPU threads with native BLAS limited to one thread per kernel. Model parallelism splits hidden units and sums partial outputs. Pipeline is forward inference only, not GPipe training or a GPU measurement. Steady inference includes partition/sum/concatenation, excludes pool warmup.'}
