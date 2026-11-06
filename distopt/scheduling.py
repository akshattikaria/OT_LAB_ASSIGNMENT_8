"""Actual CPU processes: static, central task pool, and locked deque stealing."""
import hashlib
import heapq
import multiprocessing as mp
import os
import queue
from time import perf_counter,process_time


def kernel(job,iterations_per_unit):
    index,units=job
    return hashlib.pbkdf2_hmac('sha256',f'job-{index}'.encode(),b'track-d-fixed-salt',int(units*iterations_per_unit)).hex()


def assignments(jobs,p,kind):
    if kind=='static_lpt':
        queues=[[] for _ in range(p)];loads=[(0,i) for i in range(p)];heapq.heapify(loads)
        for job in sorted(jobs,key=lambda x:(-x[1],x[0])):
            load,rank=heapq.heappop(loads);queues[rank].append(job);heapq.heappush(loads,(load+job[1],rank))
        return queues
    size,extra=divmod(len(jobs),p);queues=[];offset=0
    for rank in range(p):
        end=offset+size+(rank<extra);queues.append(jobs[offset:end]);offset=end
    return queues


def _deque_pop(deque,back=False):
    """Caller holds the deque's lock. Fixed storage, moving head/tail bounds."""
    buffer,head,tail=deque
    if head.value>=tail.value:return None
    if back:tail.value-=1;index=tail.value
    else:index=head.value;head.value+=1
    return (int(buffer[2*index]),int(buffer[2*index+1]))


def _worker(rank,kind,own,shared,locks,barrier,ready,results,iterations):
    rows=[];cpu=process_time()
    try:
        ready.put({'worker':rank,'at':perf_counter()})
        barrier.wait(timeout=120)
        while True:
            donor=rank
            if kind=='dynamic_pool':
                job=shared.get()
                if job is None:break
            elif kind=='work_stealing':
                job=None
                with locks[rank]:
                    job=_deque_pop(shared[rank])
                if job is None:
                    # Only unstarted jobs can be moved. Never execute under a queue lock.
                    for victim in [(rank+offset)%len(shared) for offset in range(1,len(shared))]:
                        with locks[victim]:
                            job=_deque_pop(shared[victim],back=True)
                            if job is not None:donor=victim;break
                if job is None:break
            else:
                if not own:break
                job=own.pop(0)
            start=perf_counter();digest=kernel(job,iterations);end=perf_counter()
            rows.append({'job':job[0],'units':job[1],'worker':rank,'donor':donor,'stolen':donor!=rank,
                'start':start,'finish':end,'digest':digest})
        results.put({'worker':rank,'pid':os.getpid(),'jobs':rows,'cpu_s':process_time()-cpu})
    except Exception as error:results.put({'worker':rank,'error':repr(error)})


def schedule(jobs,p,kind,iterations_per_unit=30000):
    if kind not in ('static_block','static_lpt','dynamic_pool','work_stealing') or not isinstance(p,int) or p<1:raise ValueError('Invalid scheduling method/workers')
    if not jobs or len(set(j[0] for j in jobs))!=len(jobs) or any(j[1]<1 for j in jobs):raise ValueError('Invalid jobs')
    ctx=mp.get_context('spawn');outer=perf_counter();shared=None;locks=None
    local=assignments(jobs,p,kind);barrier=ctx.Barrier(p+1);results=ctx.Queue();ready=ctx.Queue()
    if kind=='dynamic_pool':
        shared=ctx.Queue()
        for job in jobs:shared.put(job)
        for _ in range(p):shared.put(None)
    elif kind=='work_stealing':
        shared=[(ctx.Array('q',[value for job in q for value in job],lock=False),
                 ctx.Value('q',0,lock=False),ctx.Value('q',len(q),lock=False)) for q in local]
        locks=[ctx.Lock() for _ in range(p)]
    processes=[ctx.Process(target=_worker,args=(rank,kind,local[rank],shared,locks,barrier,ready,results,iterations_per_unit)) for rank in range(p)]
    try:
        for process in processes:process.start()
        readiness=[ready.get(timeout=120) for _ in range(p)]
        start=perf_counter();barrier.wait(timeout=120)
        workers=[results.get(timeout=120) for _ in range(p)];end=perf_counter()
        for process in processes:process.join(timeout=120)
        if any(process.is_alive() for process in processes):raise RuntimeError('Worker did not exit')
        if any('error' in worker for worker in workers):raise RuntimeError(str(workers))
        rows=[row for worker in workers for row in worker['jobs']]
        if sorted(row['job'] for row in rows)!=sorted(j[0] for j in jobs):raise AssertionError('Lost or duplicated job')
        for row in rows:row['start']-=start;row['finish']-=start
        active=[sum(row['finish']-row['start'] for row in rows if row['worker']==rank) for rank in range(p)]
        return_value={'method':kind,'workers':p,'steady_s':end-start,'jobs':rows,'worker_records':[{k:v for k,v in w.items() if k!='jobs'} for w in workers],
            'active_compute_s':active,'observed_utilization':sum(active)/(p*(end-start)),'stolen_jobs':sum(row['stolen'] for row in rows),
            'predicted_total_units':sum(job[1] for job in jobs),'iterations_per_unit':iterations_per_unit,'start_method':'spawn',
            'worker_readiness':[{'worker':r['worker'],'ready_s':r['at']-outer} for r in readiness],
            'steady_start_s':start-outer,'steady_finish_s':end-outer}
    finally:
        for process in processes:
            if process.is_alive():process.terminate();process.join()
        if kind=='dynamic_pool':shared.close();shared.join_thread()
        results.close();results.join_thread()
        ready.close();ready.join_thread()
    return_value['end_to_end_s']=perf_counter()-outer
    return_value['setup_cleanup_s']=return_value['end_to_end_s']-return_value['steady_s']
    return return_value


def _counter_worker(count,mode,counter,barrier,ready,results):
    try:
        ready.put(perf_counter())
        barrier.wait(timeout=120)
        if mode=='locked_each':
            for _ in range(count):
                with counter.get_lock():counter.value+=1
        else:
            local=0
            for _ in range(count):local+=1
            with counter.get_lock():counter.value+=local
        results.put(True)
    except Exception as error:results.put(repr(error))


def synchronization(p,mode,total=120000):
    if mode not in ('locked_each','private_reduce'):raise ValueError('Unknown synchronization mode')
    ctx=mp.get_context('spawn');counter=ctx.Value('q',0);barrier=ctx.Barrier(p+1);results=ctx.Queue();ready=ctx.Queue();outer=perf_counter()
    sizes=[total//p+(rank<total%p) for rank in range(p)]
    processes=[ctx.Process(target=_counter_worker,args=(size,mode,counter,barrier,ready,results)) for size in sizes]
    for process in processes:process.start()
    readiness=[ready.get(timeout=120) for _ in processes]
    start=perf_counter();barrier.wait(timeout=120);states=[results.get(timeout=120) for _ in processes];seconds=perf_counter()-start
    for process in processes:process.join(timeout=120)
    if states!=[True]*p or counter.value!=total:raise AssertionError('Reduction correctness failure')
    results.close();results.join_thread()
    ready.close();ready.join_thread()
    return {'workers':p,'mode':mode,'total_increments':total,'result':counter.value,'steady_s':seconds,'end_to_end_s':perf_counter()-outer,
        'steady_start_s':start-outer,'last_ready_s':max(readiness)-outer}


def _echo(connection):
    try:
        while True:
            message=connection.recv_bytes()
            if not message:break
            connection.send_bytes(message)
    finally:connection.close()


def communication(messages,bytes_per_message):
    ctx=mp.get_context('spawn');a,b=ctx.Pipe();process=ctx.Process(target=_echo,args=(b,));outer=perf_counter();process.start();b.close()
    payload=bytes((i%251 for i in range(bytes_per_message)));a.send_bytes(b'warmup');assert a.recv_bytes()==b'warmup'
    start=perf_counter()
    for _ in range(messages):
        a.send_bytes(payload)
        if a.recv_bytes()!=payload:raise AssertionError('Message corruption')
    seconds=perf_counter()-start;a.send_bytes(b'');a.close();process.join(timeout=120)
    if process.is_alive():process.terminate();process.join();raise RuntimeError('Echo process did not stop')
    return {'messages':messages,'bytes_per_message':bytes_per_message,'one_way_payload_bytes':messages*bytes_per_message,
        'round_trip_s':seconds,'mean_round_trip_s':seconds/messages,'end_to_end_s':perf_counter()-outer,'transport':'local multiprocessing Pipe, not a network'}
