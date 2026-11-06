"""Research-extension pages and figures, derived only from retained records."""
import json
import statistics as st
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def research_pages(root):
    def read(name):return json.loads((root/'research_supplement/results'/f'{name}.json').read_text())
    def mean(rows,key):return st.mean(r[key] for r in rows)
    def p(s):return ('p',s)
    def t(head,rows,widths):return ('table',head,rows,widths)
    def im(name,caption,height=180):return ('image','reports/figures/'+name,caption,height)
    def ev(s):return ('evidence',s)
    pages=[]
    def page(title,*blocks):pages.append((title,list(blocks)))
    c=read('curvature');sub=read('submodular');qmt=read('qmt');tt=read('tensorhyper');neg=read('negative_learning');nom=read('nom');liver=read('liver');spmv=read('spmv');com=read('communication');hpo=read('hpo');svm=read('svmplus');plans=read('strategies');privacy=read('privacy_certificate')
    colors=['#195680','#278a91','#d58645']
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.15),layout='constrained')
    for k,m in enumerate(['fixed_temperature','learned_temperature']):
        rows=[r for r in qmt['runs'] if r['method']==m]
        axes[0].plot(range(5),[r['test_accuracy']*100 for r in rows],'o-',color=colors[k],label=m.replace('_',' '))
    axes[0].set(xticks=range(5),xlabel='Synthetic-data seed',ylabel='Test accuracy (%)',ylim=(0,100),title='Measurement temperature: 5 paired cases');axes[0].legend(fontsize=7)
    for k,m in enumerate(['hybrid_quantum','matched_classical','logistic_reference']):
        rows=[r for r in liver['runs'] if r['method']==m]
        axes[1].plot([r['seed'] for r in rows],[r['accuracy']*100 for r in rows],'o-',color=colors[k],label=m.replace('_',' '))
    axes[1].set(xticks=[31,41,51],xlabel='ILPD split seed',ylabel='Test accuracy (%)',ylim=(45,80),title='Author liver dataset: 3 held-out splits');axes[1].legend(fontsize=7)
    fig.savefig(root/'reports/figures/research_quantum_data.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.15),layout='constrained')
    for k,m in enumerate(['row_static','runtime_adaptive_nnz_tiles']):
        med=[];lo=[];hi=[]
        for family in ['uniform','skewed','empty_rows']:
            values=[r['summary'][m]['median_s']*1e6 for r in spmv['runs'] if r['family']==family]
            med.append(st.median(values));lo.append(st.median(values)-min(values));hi.append(max(values)-st.median(values))
        axes[0].errorbar(np.arange(3)+(k-.5)*.08,med,yerr=[lo,hi],fmt='o',capsize=4,color=colors[k],label=m.replace('_',' '))
    axes[0].set(xticks=range(3),xticklabels=['uniform','skewed','empty rows'],ylabel='Microseconds',title='SpMV: median of 5 case medians');axes[0].legend(fontsize=7)
    methods=['full_grid','synchronous_halving','asynchronous_stopping']
    for k,m in enumerate(methods):
        r=[r for r in hpo['live_halving']['runs'] if r['method']==m];axes[1].bar(k,mean(r,'epoch_units'),color=colors[k]);axes[1].text(k,mean(r,'epoch_units')+15,f"{mean(r,'epoch_units'):.1f}",ha='center',fontsize=8)
    axes[1].set(xticks=range(3),xticklabels=['full grid','sync halving','async stopping'],ylabel='Training epoch units',ylim=(0,850),title='Live four-thread search: mean over 3 seeds')
    fig.savefig(root/'reports/figures/research_native_search.png',dpi=180);plt.close(fig)
    curvature_rows=[]
    for m in ['gd','natural_gradient','ring','reng']:
        r=[r for r in c['runs'] if r['method']==m];curvature_rows.append([m,f"{mean(r,'reference_gap'):.5f}",f"{mean(r,'function_training_s')*1000:.2f}"])
    page('Research extension: optimization and privacy',
         p('The 6 November extension adds experiments for all 23 research entries: 11 scoped equation/code ports, four algorithm variants, two survey demonstrations and six mechanism-only controls. A port means the stated small specialization is implemented; none reproduces an entire paper or its performance. Detailed sources, equation locators, changes and gaps are in METHOD_COVERAGE.md and SOURCE_REGISTRY.json.'),
         t(['Binary logistic, 5 seeds','Mean reference gap','Training ms'],curvature_rows,[.46,.29,.25]),
         p('GRNG uses the RING/RENG regularizers with exact full-batch Fisher refresh; gradient-norm derivatives use the Hessian-vector expression. A separate regularized Kalman port checks covariance positivity. On the small logistic cases, ordinary natural gradient reaches the reference more closely than the regularized controls. This is no universal ranking.'),
         p('AdaFisher follows the printed running-factor equation on a three-class single-layer model. Mean final cross-entropy is '+f"{mean([r for r in c['runs'] if r['method']=='adafisher_softmax'],'final_loss'):.4f}"+' versus '+f"{mean([r for r in c['runs'] if r['method']=='adam_softmax'],'final_loss'):.4f}"+' for Adam. An initial scalar-output factor normalized to zero; the informative multiclass correction and original diagnostic are retained. The authors\' current factor update differs from the printed equation; code equivalence is not claimed.'),
         p('ResQue implements the curvature trigger/step-back with a declared incumbent safeguard; both raw and guarded outcomes are saved. Guarded exact ratios range '+f"{min(r['resque_value']/r['optimum_value'] for r in sub['resque']):.3f}"+' to 1 over five cases. Dynamic nonmonotone selection uses disjoint level reservoirs and partial rebuilds, a finite threshold grid and an exact offline oracle: 90 insert/delete events, with no asymptotic guarantee claimed.'),
         t(['Private greedy+ epsilon','Max |log(p/q)|, one neighbor pair'],[[str(r['epsilon']),f"{r['maximum_absolute_log_ratio']:.6f}"] for r in privacy['rows']],[.43,.57]),
         p('The paper-specific private density-greedy+ port uses generalized exponential noisy max and conservative pure composition, replacing the source\'s advanced composition. Fifteen sampled runs and an independent exponential-mechanism control retain utility and feasibility. The table integrates every output path on one three-item neighboring-dataset pair; it is a finite certificate, not a universal privacy proof or deployment claim.'),
         ev('research_supplement/curvature.py; submodular.py; results/curvature.json; submodular.json; privacy_certificate.json'))
    page('Research extension: quantum training mechanisms',
         p('All quantum extensions use explicit CPU statevectors. Parameter-shift derivatives and the classical chain rule are checked against finite differences. Reported seconds measure simulator training, not QPU execution or quantum advantage.'),
         im('research_quantum_data.png','Left: each of five synthetic six-class temperature cases. Right: every held-out liver split; different data and tasks.',180),
         t(['Study, 5 seeds','Retained result','Boundary'],[
             ['TensorHyper-VQC',f"Direct energy {mean([r for r in tt['runs'] if r['method']=='direct'],'final_evaluation_mean'):.3f}; TT {mean([r for r in tt['runs'] if r['method']=='tt_hypernetwork'],'final_evaluation_mean'):.3f}",'20 TT scalars generate 27 circuit angles; rank-one variant is worse'],
             ['Negative-rate rule',f"Mean {mean([r for r in neg['runs'] if r['method']=='source_negative_rule'],'negative_steps'):.1f} ascent branches / 100 steps",'Loss-triggered rule, 256-shot gradient; almost identical energy to descent'],
             ['Measurement temperature',f"Mean accuracy {mean([r for r in qmt['runs'] if r['method']=='fixed_temperature'],'test_accuracy')*100:.1f}% to {mean([r for r in qmt['runs'] if r['method']=='learned_temperature'],'test_accuracy')*100:.1f}%",'Joint positive T and angles; synthetic six-class data only'],
             ['Nested optimization',f"Mean energy gap {mean(nom['runs'],'ground_energy_gap'):.3f}",'Actual ancilla dilation/postselection; fixed ansatz replaces RL structure search']],[.23,.34,.43]),
         p('TensorHyper uses a rank-one tensor-train parameter generator driven by Gaussian inputs. Direct optimization performs better here; parameter count alone does not imply a better solver. Negative learning is the source loss-triggered ascent branch, rather than an invented periodic schedule. Measurement temperature learns log T in softmax(z/T) from the same starts and training split as T=1.'),
         p('Nested optimization specializes the Hermitian objective to p=1, constructs a dense unitary dilation, postselects its gradient-filter state and fits a parameterized circuit by fidelity. Unitarity error is '+f"{nom['unitarity_error']:.2g}"+'. Five runs retain every positive ground-state gap. Dense simulation, omitted sparse-oracle construction and fixed circuit structure rule out source-scale complexity claims.'),
         ev('research_supplement/quantum.py; quantum_studies.py; results/{tensorhyper,negative_learning,qmt,nom}.json'))
    liver_rows=[]
    for m in ['hybrid_quantum','matched_classical','logistic_reference']:
        r=[r for r in liver['runs'] if r['method']==m];liver_rows.append([m.replace('_',' '),f"{mean(r,'accuracy')*100:.2f}%",f"{mean(r,'balanced_accuracy')*100:.2f}%",f"{mean(r,'training_s'):.3f}" if 'training_s' in r[0] else 'not timed'])
    page('Research extension: QML-Liver on author data',
         p('The author repository provides the actual 583-row Indian Liver Patient Dataset CSV and a two-qubit notebook. This original NumPy port follows Dense(256)-dropout(.3)-Dense(128)-dropout(.3)-Dense(2), a two-qubit RX encoder with four BasicEntangler layers (eight circuit parameters), and a sigmoid output. The author code is MIT; the UCI dataset is CC BY 4.0, with attribution and hashes included.'),
         t(['Model, 3 splits','Accuracy','Balanced acc.','Training s'],liver_rows,[.37,.21,.22,.20]),
         t(['Split seed','Hybrid accuracy','Matched classical','Logistic'],[[str(seed)]+[f"{next(r for r in liver['runs'] if r['seed']==seed and r['method']==m)['accuracy']*100:.2f}%" for m in ['hybrid_quantum','matched_classical','logistic_reference']] for seed in [31,41,51]],[.19,.27,.27,.27]),
         p('Each split reserves 20% for testing, then 20% of the remainder for validation, stratified by label. Medians and standardization are fitted only on training rows. A maximum of 80 epochs and validation early stopping replace the source\'s 100-epoch setting. Test labels never choose an epoch. The matched classical model keeps the eight-parameter bottleneck and the same dense architecture; both use manual backpropagation, dropout and class-weighted focal loss.'),
         p('The hybrid ties logistic on one split and loses on two; its mean accuracy is below logistic. Hybrid versus matched-classical mean accuracy differs by less than one percentage point, with only three splits. These outcomes do not establish a general quantum benefit or reproduce the paper\'s scores. This educational experiment is not a clinical validation.'),
         p('Saved rows contain split indices, train-only preprocessing, all test probabilities, labels, confusion matrices, ROC AUC, chosen epoch and final parameters. Quantum counters distinguish batched statevector calls from per-example circuit instances, including parameter/input shifts, validation and testing. The initially ambiguous counter is retained as a diagnostic; the corrected counter is audited.'),
         ev('research_supplement/liver.py; data/provenance.json; data/ATTRIBUTION.md; results/liver.json; validation/research_tests_final.log'))
    page('Research extension: native parallel and communication',
         im('research_native_search.png','SpMV whiskers show the full range across five input-case medians, each based on seven timed repetitions. Right: actual search work.',175),
         p('A native GCC/OpenMP SpMV control uses two real threads on identical CSR inputs and a serial reference. Uniform, skewed and empty-row families each use five seeds, two methods and seven timed repetitions: 210 trials. Long rows are split into nonzero tiles; partial sums use atomics and the tile size adapts to prior throughput. Maximum errors are within 1e-8. Method order is fixed, and these tiny shared-host timings are descriptive. This is PANA-related mechanism evidence; its unpublished-to-us SIMD policy is not claimed.'),
         p('The Subspace Networks port uses two residual blocks, frozen high-rank embeddings and a shared width-32/rank-4 subspace. Dense and compressed executions of that same constrained model agree in all five 100-step parameter trajectories; maximum final parameter difference is '+f"{max(r['final_parameter_difference'] for r in com['subspace']):.2g}"+'. Boundary payload is reduced by a factor of eight, excluding the one-time basis transfer. The raw dense backpropagated vector need not lie in the subspace; parameter-gradient equivalence is the checked property. A separate Grassmann step checks orthogonality and residual reduction.'),
         t(['Related paper','What was actually run','Exact method status'],[
             ['OFLight','20 low-rank FL projection/feedback controls; ideal summed uplink','Our SVD/refresh policies; detailed paper policy unavailable'],
             ['GSHetero','Five MCL groupings, speed-aware placements and exact group references','Placement heuristic is original'],
             ['Architecture-aware currying','15 mesh partial-application/near-data controls; byte-hop counts','No source compiler port'],
             ['PackStealLB','10 task-pack/single-task transfer models with task invariants','No source packing-policy port']],[.25,.45,.30]),
         p('All six remaining mechanism-only entries, including PANA and EAHP, are flagged in the registry. Their detailed full texts/code could not be retrieved from public sources. Logical bytes, byte-hops and scheduling models are not network, Hadoop, radio or multi-GPU measurements.'),
         ev('research_supplement/spmv.c; spmv.py; communication.py; placement.py; results/{spmv,communication,placement}.json; SOURCE_REGISTRY.json'))
    live=hpo['live_halving']['runs'];searchrows=[]
    for m in ['full_grid','synchronous_halving','asynchronous_stopping']:
        r=[r for r in live if r['method']==m];searchrows.append([m.replace('_',' '),f"{mean(r,'epoch_units'):.1f}",f"{mean(r,'wall_s'):.4f}",f"{mean(r,'validation_mse'):.5f}"])
    optimum=plans['plans'][plans['exact_time_optimum_index']]
    page('Research extension: search and strategy decisions',
         t(['Live HPO, 3 seeds','Epoch units','Mean wall s','Validation MSE'],searchrows,[.40,.19,.19,.22]),
         p('Four real worker threads train 27 ridge-learning configurations with checkpoint continuation and rungs 1/3/9/27. The asynchronous stopping variant sees only completed rung results and waits for three observations before stopping. Timings include scheduler overhead; synchronous halving uses much less work here. Completion order can alter later decisions. This is not the ASHA paper\'s 500-worker systems experiment.'),
         p('The HPO survey demonstrations also compare exact implicit ridge hypergradients with grid/random/Sobol search: hypergradient descent uses 19 linear solves, versus 20 for each search including selected-model refit. OmniOpt motivates L1/L2/L-infinity/spectral linear minimization oracles, checked against dual-norm certificates. A survey is not presented as one newly invented algorithm.'),
         t(['SVM+ search, 3 seeds','Mean test accuracy','Mean wall s','Candidate fits'],[[m.replace('_',' '),f"{mean([r for r in svm['runs'] if r['method']==m],'test_accuracy')*100:.2f}%",f"{mean([r for r in svm['runs'] if r['method']==m],'elapsed_s'):.3f}",'16 per seed'] for m in ['random_search','grid_island_ga']],[.36,.24,.22,.18]),
         p('The GAGS-inspired two-island GA and random search each evaluate 16 unique log-grid candidates using two threads. The convex RBF SVM+ solver retains feasible primal/dual certificates, independently recomputed gaps and inference without privileged input. All 96 candidate fits succeed. Narrow ranges, small population and the privileged-SVC tiebreak are declared adaptations; results use synthetic LUPI data, not the paper\'s datasets.'),
         p('The Astra-related finite planner enumerates '+str(len(plans['plans']))+' memory-feasible data/tensor/pipeline/device choices using explicit synthetic profiles and a GPipe DAG. Its exact model optimum is '+f"{optimum['modeled_iteration_s']:.4f}"+' s/iteration on '+str(optimum['gpu_count'])+' modeled devices at '+f"${optimum['hourly_cost']:.2f}"+'/hour. The EAHP-related original GA misses that finite optimum in all five runs; the one-hot LP/exhaustive reference exposes the gaps. Profiles are fictional, not measured GPU costs; evaluating the catalog is included in the workflow and GA query counts are not total savings.'),
         p('Twenty new tests check derivatives, unitary/postselection behavior, privacy distributions, exact SVM+ certificates, preprocessing and parallel/search invariants. The research audit verifies all 15 result files. All 2,013 original A-J imported files and their performance evidence remain unchanged.'),
         ev('research_supplement/hpo.py; svmplus.py; strategies.py; test_methods.py; audit.py; results/{hpo,svmplus,strategies}.json'))
    from build_qflair_report import qflair_page
    pages.append(qflair_page(root))
    return pages
