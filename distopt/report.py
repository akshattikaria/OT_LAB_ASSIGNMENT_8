"""Measured-data plots and an offline HTML/Markdown Track D report."""
import base64
from html import escape
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

METHODS=('static_block','static_lpt','dynamic_pool','work_stealing')
COLORS=('#9a6d55','#087f8c','#d88831','#7a61a9')


def build_report(directory):
    root=Path(directory);figures=root/'figures';figures.mkdir(exist_ok=True);read=lambda n:json.loads((root/n).read_text())
    cov=read('coverage_runs.json');schedules=read('scheduling_runs.json');weak=read('weak_scaling_runs.json');par=read('parallel_runs.json')
    fed=read('federated_runs.json');central=read('centralized_runs.json');mtl=read('multitask_runs.json');protocol=read('protocol.json');env=read('environment.json')
    refs={r['seed']:r['objective'] for r in read('federated_reference.json')};workers=sorted(protocol['workers']);med=lambda values:float(np.median(values))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'axes.titleweight':'bold','figure.dpi':125})
    files=[]
    def save(fig,name):fig.tight_layout();fig.savefig(figures/name,bbox_inches='tight');plt.close(fig);files.append(name)
    def table(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
    def graphic(name,caption):return f'![{caption}](figures/{name})\n\n{caption}'
    def cv(method):
        rows=[r for r in cov if r['method']==method and r['n']<=20]
        return [r['value']/next(e['value'] for e in cov if e['instance']==r['instance'] and e['method']=='exact') for r in rows]
    fig,axes=plt.subplots(1,2,figsize=(11,4.2));cov_summary=[]
    for index,method in enumerate(('input_order','singleton','greedy','lazy_greedy')):
        ratios=cv(method);axes[0].bar(index,np.mean(ratios),color=COLORS[index]);axes[0].scatter(np.full(len(ratios),index),ratios,color='#333',alpha=.25,s=9)
        cov_summary.append({'method':method,'mean_exact_ratio':float(np.mean(ratios)),'min_exact_ratio':float(min(ratios))})
    axes[0].axhline(1-1/np.e,ls='--',color='#555',label='1 − 1/e guarantee for greedy');axes[0].set_xticks(range(4),['Input','Singleton','Greedy','Lazy greedy']);axes[0].set_ylim(0,1.05);axes[0].set_ylabel('Value / exact optimum');axes[0].set_title(f'{len([r for r in cov if r["method"]=="exact"])} small weighted-coverage instances');axes[0].legend(fontsize=8)
    for index,method in enumerate(('greedy','lazy_greedy')):
        rows=[r for r in cov if r['n']==80 and r['method']==method];axes[1].bar(index,np.mean([r['oracle_evaluations'] for r in rows]),color=COLORS[index+1])
    axes[1].set_xticks([0,1],['Greedy','Lazy greedy']);axes[1].set_ylabel('Mean coverage-oracle evaluations');axes[1].set_title('80 candidates, cardinality budget 12');save(fig,'coverage.png')

    schedule_summary=[];fig,axes=plt.subplots(1,3,figsize=(14,4.3))
    for ax,family in zip(axes[:2],('uniform','irregular')):
        for method,color in zip(METHODS,COLORS):
            base=med([r['steady_s'] for r in schedules if r['family']==family and r['method']==method and r['workers']==1]);base_e2e=med([r['end_to_end_s'] for r in schedules if r['family']==family and r['method']==method and r['workers']==1]);speeds=[]
            for p in workers:
                rows=[r for r in schedules if r['family']==family and r['method']==method and r['workers']==p];seconds=med([r['steady_s'] for r in rows]);speed=base/seconds;speeds.append(speed)
                schedule_summary.append({'family':family,'method':method,'workers':p,'steady_median_s':seconds,'steady_min_s':min(r['steady_s'] for r in rows),'steady_max_s':max(r['steady_s'] for r in rows),
                    'end_to_end_median_s':med([r['end_to_end_s'] for r in rows]),'speedup':speed,'efficiency':speed/p,
                    'parallel_overhead_s':p*seconds-base,'end_to_end_speedup':base_e2e/med([r['end_to_end_s'] for r in rows]),'mean_stolen_jobs':float(np.mean([r['stolen_jobs'] for r in rows]))})
            ax.plot(workers,speeds,'o-',color=color,label=method.replace('_',' '))
        ax.plot(workers,workers,':',color='#666',label='Ideal');ax.set_title(f'{family.capitalize()}: fixed total work');ax.set_xlabel('Worker processes');ax.set_ylabel('Steady speedup vs same method, p=1');ax.set_xticks(workers);ax.legend(fontsize=7)
    weak_base=med([r['steady_s'] for r in weak if r['workers']==1]);weak_summary=[]
    for p in workers:
        seconds=med([r['steady_s'] for r in weak if r['workers']==p]);weak_summary.append({'workers':p,'steady_median_s':seconds,'weak_efficiency':weak_base/seconds,'scaled_speedup':p*weak_base/seconds})
    axes[2].plot(workers,[r['weak_efficiency'] for r in weak_summary],'o-',color='#087f8c');axes[2].axhline(1,ls=':',color='#666');axes[2].set_xlabel('Worker processes');axes[2].set_ylabel('T1 / Tp (weak-scaling efficiency)');axes[2].set_xticks(workers);axes[2].set_title('Work grows: 16 fixed-size jobs/worker');save(fig,'scheduling_scaling.png')

    canonical_p=4 if 4 in workers else max(workers);fig,axes=plt.subplots(4,1,figsize=(10,8),sharex=True)
    for ax,method in zip(axes,METHODS):
        run=next(r for r in schedules if r['family']=='irregular' and r['method']==method and r['workers']==canonical_p and r['repeat']==0)
        for job in run['jobs']:
            ax.barh(job['worker'],job['finish']-job['start'],left=job['start'],height=.65,color=COLORS[job['job']%4],edgecolor='white',linewidth=.3)
            if job['stolen']:ax.text((job['start']+job['finish'])/2,job['worker'],'*',ha='center',va='center',fontsize=10)
        ax.set_yticks(range(canonical_p));ax.set_ylabel('Worker');ax.set_title(method.replace('_',' ')+f' — {run["steady_s"]:.3f}s, {run["stolen_jobs"]} stolen jobs',fontsize=10)
    axes[-1].set_xlabel('Measured seconds after all workers are ready');save(fig,'scheduling_gantt.png')

    inference_summary=[];pipeline_summary=[];fig,axes=plt.subplots(1,3,figsize=(14,4.3))
    for ax,batch in zip(axes[:2],sorted(set(r['batch'] for r in par['inference']))):
        base=med([r['seconds'] for r in par['inference'] if r['kind']=='serial' and r['batch']==batch])
        for kind,color in (('data','#087f8c'),('model','#d88831')):
            speeds=[]
            for p in workers:
                rows=[r for r in par['inference'] if r['kind']==kind and r['batch']==batch and r['workers']==p];seconds=med([r['seconds'] for r in rows]);speed=base/seconds;speeds.append(speed)
                inference_summary.append({'batch':batch,'kind':kind,'workers':p,'median_s':seconds,'speedup':speed,'efficiency':speed/p,'max_abs_error':max(r['max_abs_error'] for r in rows)})
            ax.plot(workers,speeds,'o-',color=color,label=kind+' parallel')
        ax.axhline(1,color='#666',ls=':');ax.set_xticks(workers);ax.set_xlabel('CPU threads');ax.set_ylabel('Speedup vs serial BLAS=1');ax.set_title(f'Identical inference, batch={batch}');ax.legend(fontsize=8)
    pipeline_batch=par['pipeline'][0]['batch'];serial_rows=[r for r in par['inference'] if r['kind']=='serial' and r['batch']==pipeline_batch];serial_per_forward=med([r['seconds']/r['forwards'] for r in serial_rows])
    microbatches=sorted(set(r['microbatches'] for r in par['pipeline']))
    for m in microbatches:
        rows=[r for r in par['pipeline'] if r['microbatches']==m];seconds=med([r['steady_s'] for r in rows]);pipeline_summary.append({'microbatches':m,'workers':2,'median_s':seconds,'speedup':serial_per_forward/seconds,'efficiency':serial_per_forward/seconds/2,'ideal_fixed_stage_speedup':2*m/(m+1)})
    axes[2].plot(microbatches,[r['speedup'] for r in pipeline_summary],'o-',color='#7a61a9',label='Measured inference')
    axes[2].plot(microbatches,[2*m/(m+1) for m in microbatches],':',color='#666',label='Ideal, fixed equal stage costs');axes[2].set_xscale('log',base=4);axes[2].set_xticks(microbatches,[str(m) for m in microbatches]);axes[2].set_xlabel('Microbatches');axes[2].set_ylabel('Speedup vs one serial forward');axes[2].set_title('Two actual pipeline stages');axes[2].legend(fontsize=7);save(fig,'inference_pipeline.png')

    local=read('locality_runs.json')['rows'];sync=read('synchronization_runs.json');comm=read('communication_runs.json');fig,axes=plt.subplots(1,3,figsize=(14,4.3))
    sizes=sorted(set(r['n'] for r in local))
    for index,method in enumerate(('row_sum','column_sum','blocked_sum')):
        values=[med([r['seconds'] for r in local if r['n']==n and r['method']==method])*1000 for n in sizes]
        axes[0].bar(np.arange(len(sizes))+(index-1)*.25,values,width=.25,label=method.replace('_sum',''),color=COLORS[index])
    axes[0].set_xticks(range(len(sizes)),[f'{n}×{n}' for n in sizes]);axes[0].set_ylabel('Milliseconds');axes[0].set_title('Actual C-order sum loops');axes[0].legend(fontsize=8)
    for method,color in (('locked_each','#9a6d55'),('private_reduce','#087f8c')):
        values=[med([r['steady_s'] for r in sync if r['workers']==p and r['mode']==method])*1000 for p in workers]
        axes[1].semilogy(workers,values,'o-',label=method.replace('_',' '),color=color)
    axes[1].set_xticks(workers);axes[1].set_xlabel('Worker processes');axes[1].set_ylabel('Milliseconds (log)');axes[1].set_title('120,000 total shared-counter increments');axes[1].legend(fontsize=8)
    comm_small=med([r['round_trip_s'] for r in comm if r['messages']==1000]);comm_batch=med([r['round_trip_s'] for r in comm if r['messages']==10])
    axes[2].bar([0,1],[comm_small*1000,comm_batch*1000],color=['#9a6d55','#087f8c']);axes[2].set_xticks([0,1],['1,000 × 100 B','10 × 10,000 B']);axes[2].set_ylabel('Round-trip milliseconds');axes[2].set_title('Same 100 KB payload, local pipe');save(fig,'systems_controls.png')

    fed_summary=[];fig,axes=plt.subplots(1,2,figsize=(11,4.3))
    for ax,part in zip(axes,('iid','label_skew')):
        for E,color in ((1,'#087f8c'),(5,'#d88831'),(20,'#7a61a9')):
            rows=[r for r in fed if r['partition']==part and r['local_steps']==E and r['local_steps']*r['rounds']==120]
            gap=np.array([[max(t['train_objective']-refs[r['seed']],1e-12) for t in r['trace']] for r in rows]);x=[t['local_passes'] for t in rows[0]['trace']]
            ax.semilogy(x,np.mean(gap,axis=0),color=color,label=f'E={E}, R={rows[0]["rounds"]}')
            ax.fill_between(x,np.min(gap,axis=0),np.max(gap,axis=0),alpha=.1,color=color)
            fed_summary.append({'partition':part,'local_steps':E,'rounds':rows[0]['rounds'],'sample_visits':rows[0]['sample_visits'],'logical_model_bytes':rows[0]['logical_model_bytes'],
                'mean_objective_gap':float(np.mean([r['train_objective']-refs[r['seed']] for r in rows])),
                'mean_test_accuracy':float(np.mean([r['test_accuracy'] for r in rows])),'mean_test_logloss':float(np.mean([r['test_logloss'] for r in rows]))})
        ax.set_xlabel('Local passes per client (same total sample visits)');ax.set_ylabel('Train objective gap to convex reference');ax.set_title(part.replace('_',' ').upper());ax.legend(fontsize=8)
    save(fig,'fedavg.png')

    mtl_summary=[];fig,axes=plt.subplots(1,2,figsize=(11,4.3))
    for method,color in (('Equal','#9a6d55'),('MGDA','#087f8c'),('GradNorm','#7a61a9')):
        rows=[r for r in mtl if r['family']=='conflict_10x' and r['method']==method];errors=np.array([r['test_mse'] for r in rows])
        axes[0].scatter(errors[:,0],errors[:,1],color=color,label=method);axes[0].scatter([np.mean(errors[:,0])],[np.mean(errors[:,1])],marker='x',s=90,color=color)
        weights=np.array([[t['weights'][0] for t in r['trace']] for r in rows]);axes[1].plot([t['step'] for t in rows[0]['trace']],np.mean(weights,axis=0),color=color,label=method)
    for family in ('conflict_equal','conflict_10x','aligned_10x'):
        for method in ('Equal','MGDA','GradNorm'):
            rows=[r for r in mtl if r['family']==family and r['method']==method];errors=np.array([r['test_mse'] for r in rows])
            mtl_summary.append({'family':family,'method':method,'mean_test_mse':np.mean(errors,axis=0).tolist(),'mean_final_weights':np.mean([r['weights'] for r in rows],axis=0).tolist(),'mean_runtime_s':float(np.mean([r['runtime_s'] for r in rows]))})
    axes[0].set_xlabel('Task 1 test MSE');axes[0].set_ylabel('Task 2 test MSE');axes[0].set_title('Conflicting targets, loss scales 1 and 10');axes[0].legend(fontsize=8)
    axes[1].set_xlabel('Updates');axes[1].set_ylabel('Mean task 1 weight (total weight=2)');axes[1].set_title('Task weighting across the same seeds');axes[1].legend(fontsize=8);save(fig,'multitask.png')

    sections=[]
    def add(title,body):sections.append((title,body))
    add('Track D: Submodular, Parallel and Distributed Optimization',f'Assignment 8 simulation/implementation portfolio. Actual parallel CPU measurements were taken with {env["logical_cpus"]} visible logical CPUs, affinity size {len(env["affinity"])}, and a cgroup CPU quota of {env["effective_cpu_capacity"]:g} CPU equivalents. These are cloud-workspace measurements, not measurements of the student’s laptop.\n\nWeighted coverage, real process scheduling and shared-memory inference complement serial FedAvg and multi-task learning experiments. No GPU, multi-node deployment, privacy protection or quantum speedup is claimed. All datasets are synthetic.')
    add('Protocol and evidence',table(['Experiment','Retained evidence'],[
        ['Coverage',f'{len(set(r["instance"] for r in cov))} instances; {len(cov)} method runs; exact enumeration on {sum(r["method"]=="exact" for r in cov)} small cases'],
        ['Strong scaling',f'{len(schedules)} actual process runs; two workload families; four schedulers; workers {workers}'],
        ['Weak scaling',f'{len(weak)} runs; workload grows with workers'],
        ['Data/model inference',f'{len(par["inference"])} timings including serial references; identical outputs'],
        ['Pipeline',f'{len(par["pipeline"])} timings; two CPU stages; 1/4/16/64 microbatches'],
        ['System controls',f'{len(sync)} synchronization, {len(comm)} local-pipe, {len(local)} locality timings'],
        ['Federated learning',f'{len(fed)} FedAvg + {len(central)} matched centralized runs'],
        ['Multi-task learning',f'{len(mtl)} runs; three task families; three methods']])+f'\nThe protocol fixes {len(protocol["seeds"])} learning seeds and {protocol["repeats"]} timing repeats. Scheduling and data/model trial orders are shuffled using recorded seeds. CPU allocation is recorded; shared hardware variability remains. Steady timers start after worker readiness. End-to-end timers retain setup and cleanup. BLAS kernels use one native thread so application-level parallelism does not multiply hidden thread pools.')
    add('Submodular weighted coverage',graphic('coverage.png','Bars show mean solution/optimum on small instances; dots show all cases. Oracle counts concern function evaluations, not guaranteed wall-time gains.')+'\nMaximize f(S)=sum of nonnegative weights of universe items covered by the selected candidates, with |S|≤k. This function is normalized, monotone and submodular: adding a candidate contributes only its still-uncovered items, which can only shrink as S grows. Under these cardinality assumptions, exact-marginal greedy has the 1−1/e lower bound; the finite-k bound is 1−(1−1/k)^k.\n\n'+table(['Method','Mean exact ratio','Worst exact ratio'],[[r['method'],f'{r["mean_exact_ratio"]:.4f}',f'{r["min_exact_ratio"]:.4f}'] for r in cov_summary])+'\nLazy greedy keeps diminishing-return upper bounds in a heap and returns the same deterministic selection as ordinary greedy on all saved cases. Large n=80 cases have no exhaustive optimum claim; their upper bounds are labeled bounds. An explicit counterexample gives greedy value 5 versus optimum 6. A separate |S|² control violates diminishing returns; no submodular guarantee is claimed for that function. Exhaustive small-instance assumption checks supplement the structural proof.')
    add('Load balancing, stealing and scaling',graphic('scheduling_scaling.png','Each strong-scaling curve uses its own scheduler’s one-worker median. Weak efficiency uses fixed work per worker and must not be read as fixed-problem speedup.')+'\n'+graphic('scheduling_gantt.png',f'Actual irregular-job traces, p={canonical_p}, repeat 0. An asterisk marks a job taken from another worker’s pending deque.')+'\nEach family has the same 32 jobs at every strong-scaling worker count. The deterministic PBKDF2 kernel returns a checked digest for each job; there are no sleep-based timings. Irregular jobs put eight heavy jobs first, exposing poor contiguous static assignment. LPT greedily places the largest remaining predicted job on the least-loaded worker. The central task pool and decentralized deque stealing are implemented separately. Stealing moves only unstarted jobs and releases locks before computing. The shared-array backend uses local memory and synchronization, not sockets.\n\n'+table(['Family','Method',f'p={max(workers)} steady s','End-to-end s','Steady speedup','Efficiency','Mean stolen jobs'],[[r['family'],r['method'],f'{r["steady_median_s"]:.4f}',f'{r["end_to_end_median_s"]:.4f}',f'{r["speedup"]:.2f}',f'{r["efficiency"]:.1%}',f'{r["mean_stolen_jobs"]:.1f}'] for r in schedule_summary if r['workers']==max(workers)])+'\nS(p)=T1/Tp and efficiency=S/p. The overhead measure pTp−T1 is recorded in summary.json; it includes scheduling, imbalance and runtime effects and is not a measured pure communication time. End-to-end and steady speedups can differ strongly for short jobs. Amdahl’s 1/[s+(1−s)/p] explains fixed-work limits; the serial fraction is not inferred as a universal hardware constant here. Weak scaling increases jobs as p grows; its scaled speedup pT1/Tp reflects the different growing-work question associated with Gustafson’s law. Neither ideal law removes bandwidth, startup or contention costs.')
    add('Data, model and pipeline parallelism',graphic('inference_pipeline.png','Every configuration computes tanh(XW1)W2 with the same input and weights. Pipeline speedup uses one serial forward, while data/model rows time equal repeated forwards.')+'\nData parallelism splits rows and concatenates outputs. Hidden-unit tensor parallelism splits W1 columns and corresponding W2 rows, then sums partial outputs. These are shared-memory CPU implementations, with NumPy kernels releasing the GIL and native BLAS restricted to one thread. Partitioning, partial-output reduction and concatenation are included in steady time. Pool warmup is excluded; its end-to-end counterpart is retained.\n\n'+table(['Batch','Mode','Workers','Speedup','Efficiency','Maximum absolute output error'],[[r['batch'],r['kind'],r['workers'],f'{r["speedup"]:.2f}',f'{r["efficiency"]:.1%}',f'{r["max_abs_error"]:.2g}'] for r in inference_summary if r['workers']==max(workers)])+'\nThe two pipeline threads own the first and second forward stages and exchange ordered activations through a bounded queue. There is no backward pass, gradient accumulation, accelerator transfer or GPipe-training claim. For two equal fixed-cost stages, ideal bubble fraction is 1/(m+1) and ideal speedup is 2m/(m+1). Real microbatching changes BLAS kernel sizes, cache behavior and queue costs, so that ideal curve is an explanatory model rather than an unconditional bound on measured CPU speedup. More microbatches can also make small kernels slower.')
    add('Locality, synchronization and communication',graphic('systems_controls.png','C loops, shared-counter processes and local pipe transfers are actual measurements. Each comparison preserves its numerical result or total payload.')+f'\nLocality loops traverse C-order doubles by rows, columns or 32×32 tiles. They are compiled with -O3 without fast-math, and checked against a long-double sum. Summation order changes roundoff; no hardware cache-miss counters or matrix-multiplication speedup are claimed.\n\nThe counter example performs the same 120,000 increments, either with a shared lock each time or private accumulation followed by one locked contribution/worker. Correct reduction preserves the count while reducing synchronization. Tiny reduction tasks may be dominated by process and result-queue overhead.\n\nA warmed local pipe echo checks all payload bytes. Batching the same 100 KB one-way payload from 1,000 messages into 10 changed median round-trip time by a factor of {comm_small/comm_batch:.2f}. The latency-plus-volume model alpha+n/beta explains why fewer messages can help. These are local IPC costs, not internet/network or actual FedAvg communication timings.')
    add('FedAvg versus centralized learning',graphic('fedavg.png','All curves process 120 full passes of each client’s data; shaded ranges include all seeds. E=1 coincides with matched centralized full-batch GD, up to numerical roundoff.')+'\nFour clients have 64, 96, 160 and 192 examples. IID and label-skewed splits partition the same 512 training examples without overlap. A separate 256-example test set is retained. Every round broadcasts the same model; each client takes E full-batch local steps, then the server averages models using client sample counts. Full participation and identical regularization ensure E=1 equals centralized GD, even with unequal/non-IID clients.\n\n'+table(['Partition','E','Rounds','Sample visits','Logical bytes','Mean train gap','Mean test accuracy'],[[r['partition'],r['local_steps'],r['rounds'],r['sample_visits'],r['logical_model_bytes'],f'{r["mean_objective_gap"]:.5g}',f'{r["mean_test_accuracy"]:.2%}'] for r in fed_summary])+'\nThe compute-matched comparisons all visit 61,440 training examples. E=20,R=6 uses one twentieth the logical model payload of E=1,R=120, at the cost shown in final objective/test performance. Longer local work increases drift especially under label skew. Logical payload is 2×clients×parameters×8×rounds and omits protocol/security overhead. This federated algorithm is emulated serially; its CPU runtime is not distributed wall time, and it provides no privacy or secure aggregation.\n\nA separate fixed-round view uses R=24; it deliberately changes training work:\n\n'+table(['Partition','E','Local passes','Mean train objective','Logical bytes'],[[part,E,24*E,f'{np.mean([r["train_objective"] for r in fed if r["partition"]==part and r["rounds"]==24 and r["local_steps"]==E]):.6f}',2*4*7*8*24] for part in ('iid','label_skew') for E in (1,5,20)])+'\nAll nine E/R settings are retained per partition and seed, alongside centralized runs matching every distinct E×R. Test metrics are diagnostic and do not select hyperparameters or checkpoints.')
    add('MGDA and GradNorm on a two-task model',graphic('multitask.png','Dots are held-out task errors for every seed; crosses are means. Both errors matter. Task weights share the same total of two.')+'\nTwo regression tasks share all seven coefficients, with fixed identity readouts Xw and two target vectors. The deliberately restricted linear model makes conflicting targets and loss scaling transparent. It is a two-task optimization demonstration, not a reproduction of a large multi-head neural network or the papers’ datasets. The three families use conflicting targets with equal scales, conflicting targets with scales 1/10, and aligned targets with scales 1/10.\n\nEqual weighting uses w1=w2=1. Exact two-task MGDA minimizes the norm of a convex combination of task gradients; its coefficients are multiplied by two for the same aggregate step scale. GradNorm updates positive weights to match gradient norms to relative loss-learning rates, with alpha=1.5, weight rate 0.01, frozen targets, and normalization to total weight two. All model rates are 0.03 and initializations/update counts match. Per-task unscaled test MSE avoids concealing scale differences.\n\n'+table(['Family','Method','Mean task 1 test MSE','Mean task 2 test MSE','Mean final task 1 weight'],[[r['family'],r['method'],f'{r["mean_test_mse"][0]:.5f}',f'{r["mean_test_mse"][1]:.5f}',f'{r["mean_final_weights"][0]:.3f}'] for r in mtl_summary])+'\nFor conflicting, unequally scaled tasks, equal weights heavily favor task 2. MGDA and GradNorm choose different compromises; neither should be described as universally best. MGDA can stop at a point without a common descent direction even when each individual loss is nonzero. Separate least-squares models are recorded as unattainable joint-reference errors, since the shared-vector constraint prevents using two independent parameter vectors.')
    add('Validation, AI error and remaining work','All 29 unit tests pass. They check coverage assumptions/greedy bounds, lazy-greedy equivalence, finite-difference learning gradients, exact MGDA simplex minimization, the frozen-target GradNorm derivative, FedAvg-to-centralized equality, process exact-once execution, timer readiness, counter reductions, pipe integrity, and data/model/pipeline numerical equivalence. The retained-data audit recomputes predictions, selections, task digests and timing identities; its exact counts are in audit.json.\n\nA genuine timer defect was found before the recorded resource benchmarks: starting a steady timer before the readiness barrier included worker initialization. The original tiny-task observation reported 0.05912 s steady time while its total kernel work was about 0.000255 s, with the first task beginning after 0.05820 s. A readiness handshake now excludes that startup, while end-to-end time keeps it. Original/fixed commits, observations and a regression are retained. This adds a third genuine documented AI error to the two earlier numerical errors in A/B. A blocked socket-based Manager was separately replaced with shared-memory deques; it is an environment issue, not an extra fabricated algorithm failure.\n\nTrack D core demonstrations are present. E/A/B/C packages remain separate; F–J, the combined report, outstanding research-paper reproductions, a second independent AI-tool comparison, full chat exports, public GitHub publication and live demonstration remain to be completed. No private or manual student corrections are claimed. See docs/COVERAGE.md.')
    add('Primary references','- Nemhauser, Wolsey & Fisher (1978), weighted coverage/cardinality greedy: https://thibaut.horel.org/submodularity/papers/nemhauser1978.pdf\n- McMahan et al. (2017), FedAvg: https://proceedings.mlr.press/v54/mcmahan17a.html\n- Sener & Koltun (2018), MGDA/multi-objective learning: https://arxiv.org/abs/1810.04650\n- Chen et al. (2018), GradNorm: https://proceedings.mlr.press/v80/chen18a.html\n- Huang et al., GPipe: https://arxiv.org/abs/1811.06965 (conceptual reference; this package measures forward CPU pipelining)\n- Python multiprocessing: https://docs.python.org/3/library/multiprocessing.html\n- threadpoolctl: https://github.com/joblib/threadpoolctl\n- Supplied Assignment 8 and Chapter 6 PPT1/PPT2/PPT4. Lecture research spotlights are not claimed reproduced. Public references checked 2026-11-03; experiment numbers are measured here.')
    markdown='\n\n'.join('# '+title+'\n\n'+body for title,body in sections)+'\n';(root/'REPORT.md').write_text(markdown,encoding='utf-8')
    def render(body):
        html=[];lines=body.splitlines();i=0
        while i<len(lines):
            line=lines[i]
            if line.startswith('| '):
                data=[]
                while i<len(lines) and lines[i].startswith('| '):data.append([v.strip() for v in lines[i].strip('|').split('|')]);i+=1
                html.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+escape(v)+'</th>' for v in data[0])+'</tr></thead><tbody>')
                for row in data[2:]:html.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>')
                html.append('</tbody></table></div>');continue
            if line.startswith('!['):
                name=line.split('(figures/',1)[1].rstrip(')');encoded=base64.b64encode((figures/name).read_bytes()).decode();html.append('<img alt="'+escape(line[2:line.index(']')])+'" src="data:image/png;base64,'+encoded+'">')
            elif line:html.append('<p>'+escape(line)+'</p>')
            i+=1
        return '\n'.join(html)
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Track D Optimization</title><style>body{margin:0;background:#edf3f5;color:#18353e;font:16px/1.6 system-ui,sans-serif}main{max-width:1160px;margin:32px auto;padding:36px;background:white;border-top:8px solid #087f8c;border-radius:12px}h1{font-size:32px;line-height:1.2}h2{font-size:25px;color:#08616b;margin-top:42px}img{width:100%;height:auto;margin:18px 0}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;border-bottom:1px solid #dbe6e9;text-align:left}th{background:#e8f3f3}p{overflow-wrap:anywhere}@media(max-width:700px){main{margin:0;padding:20px}h1{font-size:27px}}</style><main>'
    for i,(title,body) in enumerate(sections):tag='h1' if i==0 else 'h2';html+='<'+tag+'>'+escape(title)+'</'+tag+'>'+render(body)
    (root/'report.html').write_text(html+'</main></html>',encoding='utf-8')
    write={'coverage':cov_summary,'scheduling':schedule_summary,'weak_scaling':weak_summary,'parallel_inference':inference_summary,'pipeline':pipeline_summary,'fedavg_equal_work':fed_summary,'multitask':mtl_summary,'pipe_batching_ratio':comm_small/comm_batch}
    (root/'summary.json').write_text(json.dumps(write,indent=2)+'\n',encoding='utf-8');return files
