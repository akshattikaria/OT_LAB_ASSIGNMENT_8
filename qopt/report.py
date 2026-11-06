"""Offline report from retained results. Figures use the measured data only."""
import base64
from html import escape
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORS={'ShiftGD':'#087f8c','ShiftAdam':'#df8036','SPSA':'#8b5fbf','QNG':'#2166ac'}


def build_report(directory):
    root=Path(directory);figures=root/'figures';figures.mkdir(exist_ok=True)
    read=lambda name:json.loads((root/name).read_text())
    vqe=read('vqe_runs.json');qaoa=read('qaoa_runs.json');shots=read('shot_study.json')
    noise=read('noise_study.json');finite=read('finite_shot_training.json');qnn=read('qnn_runs.json')
    barren=read('barren_plateaus.json');ref=read('vqe_reference.json');baseline=read('classical_baselines.json')
    protocol=read('protocol.json');ground=ref['ground_energy'];summary={}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':125,
                         'axes.titleweight':'bold','axes.grid':True,'grid.alpha':.18})
    plot_files=[]
    def save(fig,name):
        fig.tight_layout();fig.savefig(figures/name,bbox_inches='tight');plt.close(fig);plot_files.append(name)

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for method,color in COLORS.items():
        rows=[r for r in vqe if r['method']==method];gaps=np.array([[t['exact_energy']-ground for t in r['trace']] for r in rows])
        for ax,key in zip(axes,('objective_calls','state_preparations')):
            x=[t['work'][key] for t in rows[0]['trace']]
            ax.plot(x,np.maximum(np.median(gaps,axis=0),1e-12),label=method,color=color)
            ax.fill_between(x,np.maximum(np.min(gaps,axis=0),1e-12),np.maximum(np.max(gaps,axis=0),1e-12),color=color,alpha=.12)
            ax.set_yscale('log');ax.set_xlabel(key.replace('_',' '));ax.set_ylabel('Exact energy gap (dimensionless)')
        summary[method]={'mean_gap':float(np.mean(gaps[:,-1])),'max_gap':float(np.max(gaps[:,-1])),
            'objective_calls':rows[0]['work']['objective_calls'],'state_preparations':rows[0]['work']['state_preparations'],
            'metric_preparations':rows[0]['work']['metric_preparations'],'mean_runtime_s':float(np.mean([r['runtime_s'] for r in rows]))}
    axes[0].set_title('VQE: median and range over seeds');axes[1].set_title('Including exact metric preparations');axes[0].legend()
    save(fig,'vqe_cost.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    qsummary=[]
    for ax,model in zip(axes,('maxcut_4bit','knapsack_6bit')):
        for depth,color in ((1,'#087f8c'),(2,'#df8036')):
            rows=[r for r in qaoa if r['model']==model and r['p']==depth]
            values=[r['metrics']['expected_energy'] for r in rows]
            ax.scatter([depth]*len(rows),values,color=color,alpha=.7)
            ax.plot([depth-.15,depth+.15],[np.mean(values)]*2,color=color,lw=3)
            qsummary.append({'model':model,'p':depth,'seeds':len(rows),'mean_energy':float(np.mean(values)),
                'mean_ground_probability':float(np.mean([r['metrics']['ground_probability'] for r in rows])),
                'mean_original_feasibility':float(np.mean([r['metrics']['original_feasibility_probability'] for r in rows])),
                'mean_encoded_feasibility':float(np.mean([r['metrics']['encoded_feasibility_probability'] for r in rows])),
                'local_success':sum(r['optimizer_success'] for r in rows),'mean_calls':float(np.mean([r['objective_calls'] for r in rows])),
                'mean_runtime_s':float(np.mean([r['runtime_s'] for r in rows])),
                'classical_minimum':rows[0]['classical_minimum'],'uniform_energy':rows[0]['uniform_baseline']['expected_energy']})
        ax.axhline(rows[0]['classical_minimum'],ls='--',color='#444',label='Classical minimum')
        ax.axhline(rows[0]['uniform_baseline']['expected_energy'],ls=':',color='#777',label='Uniform distribution')
        ax.set_xticks([1,2]);ax.set_xlabel('QAOA depth p');ax.set_ylabel('Expected raw QUBO energy');ax.set_title(model.replace('_',' '));ax.legend(fontsize=8)
    save(fig,'qaoa_quality.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2));shot_summary=[]
    for ax,model in zip(axes,('maxcut_4bit','knapsack_6bit')):
        for depth,color in ((1,'#087f8c'),(2,'#df8036')):
            exact=next(r['metrics']['expected_energy'] for r in qaoa if r['model']==model and r['p']==depth and r['seed']==0)
            budgets=sorted(set(r['shots'] for r in shots));errors=[]
            for budget in budgets:
                rows=[r for r in shots if r['model']==model and r['p']==depth and r['shots']==budget]
                rmse=float(np.sqrt(np.mean([(r['expected_energy']-exact)**2 for r in rows])));errors.append(rmse)
                shot_summary.append({'model':model,'p':depth,'shots':budget,'repetitions':len(rows),'energy_rmse':rmse})
            ax.loglog(budgets,errors,'o-',label=f'p={depth}',color=color)
        ax.set_xlabel('Shots per sampled distribution');ax.set_ylabel('Energy estimate RMSE');ax.set_title(model.replace('_',' '));ax.legend()
    save(fig,'shot_accuracy.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,method in zip(axes,('ShiftGD','SPSA')):
        for budget,color in ((128,'#df8036'),(1024,'#087f8c')):
            rows=[r for r in finite if r['method']==method and r['shots_per_term']==budget]
            gap=np.array([[t['exact_energy']-ground for t in r['trace']] for r in rows])
            x=[t['step'] for t in rows[0]['trace']];ax.plot(x,np.mean(gap,axis=0),label=f'{budget} shots/term',color=color)
            ax.fill_between(x,np.min(gap,axis=0),np.max(gap,axis=0),alpha=.12,color=color)
        ax.set_xlabel('Updates');ax.set_ylabel('True energy gap');ax.set_title(f'{method}: finite-shot training');ax.legend()
    save(fig,'finite_shot_training.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2));labels=['ideal','gate_only','readout_only','both']
    for model,depth,color in (('maxcut_4bit',1,'#087f8c'),('maxcut_4bit',2,'#2166ac'),('knapsack_6bit',1,'#df8036'),('knapsack_6bit',2,'#8b5fbf')):
        rows=[next(r for r in noise['fixed_parameters'] if r['model']==model and r['p']==depth and r['noise']==label) for label in labels]
        axes[0].plot(range(4),[r['ground_probability'] for r in rows],'o-',label=f'{model.split("_")[0]}, p={depth}',color=color)
    axes[0].set_xticks(range(4),['Ideal','Gate','Readout','Both']);axes[0].set_ylabel('Ground-state sampling probability');axes[0].set_title('Fixed seed-0 QAOA parameters');axes[0].legend(fontsize=8)
    for depth,style in ((2,'-'),(4,'--')):
        for error,color in ((.01,'#087f8c'),(.03,'#df8036')):
            rows=[r for r in noise['growth'] if r['depth']==depth and r['depolarizing_strength']==error]
            axes[1].plot([r['n'] for r in rows],[r['fidelity'] for r in rows],'o'+style,label=f'depth={depth}, noise={error}',color=color)
    axes[1].set_xlabel('Qubits');axes[1].set_ylabel('Fidelity to ideal prepared state');axes[1].set_title('Generic local depolarizing channel');axes[1].legend(fontsize=8)
    save(fig,'noise_effects.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for name,color in (('global','#df8036'),('local','#087f8c')):
        for label,style in (('shallow','--'),('growing','-')):
            rows=[r for r in barren if r['cost']==name and r['depth_label']==label]
            axes[0].semilogy([r['n'] for r in rows],[max(r['gradient_variance'],1e-18) for r in rows],'o'+style,label=f'{name}, {label}',color=color)
        rows=[r for r in barren if r['cost']==name and r['depth_label']=='growing']
        axes[1].semilogy([r['n'] for r in rows],[r['gradient_rms'] for r in rows],'o-',label=f'{name}: true gradient RMS',color=color)
    rows=[r for r in barren if r['cost']=='global' and r['depth_label']=='growing']
    for budget,style in ((128,'--'),(1024,':')):axes[1].semilogy([r['n'] for r in rows],[r['shot_rmse'][str(budget)] for r in rows],style,label=f'{budget} shots: gradient RMSE',color='#555')
    axes[0].set_title('Gradient concentration in this circuit family');axes[0].set_ylabel('Sample gradient variance');axes[1].set_title('Signal compared with shot error');axes[1].set_ylabel('Gradient RMS / estimation RMSE')
    for ax in axes:ax.set_xlabel('Qubits');ax.set_xticks([2,4,6,8,10]);ax.legend(fontsize=8)
    save(fig,'barren_plateaus.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for r in qnn:axes[0].plot([t['step'] for t in r['trace']],[t['loss'] for t in r['trace']],label=f'Seed {r["seed"]}')
    axes[0].set_xlabel('Minibatch updates');axes[0].set_ylabel('Training binary cross-entropy');axes[0].set_title('Data-encoded two-qubit PQC');axes[0].legend()
    pos=np.arange(len(qnn));axes[1].bar(pos-.17,[r['test']['accuracy'] for r in qnn],.34,label='PQC: 8 parameters',color='#087f8c')
    axes[1].bar(pos+.17,[r['classical_logistic']['test_accuracy'] for r in qnn],.34,label='Logistic: 3 parameters',color='#df8036')
    axes[1].set_xticks(pos,[str(r['seed']) for r in qnn]);axes[1].set_xlabel('Independent dataset seed');axes[1].set_ylabel('Held-out accuracy');axes[1].set_ylim(0,1);axes[1].set_title('Toy linear labels; no advantage claim');axes[1].legend(fontsize=8)
    save(fig,'qnn_classifier.png')

    def table(headers,rows):
        return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
    sections=[]
    def add(title,text):sections.append((title,text))
    def image(name,caption):return f'![{caption}](figures/{name})\n\n{caption}\n'
    add('Track C: Quantum Optimization','Simulator experiments for Assignment 8. All quantities below come from the retained JSON records. No physical quantum computer or calibrated device was used. This package uses an authored NumPy simulator, checked against independent dense-matrix calculations.\n\nThe main findings are conditional on tiny synthetic problems, fixed optimizer settings and the recorded seeds. Classical exact methods already solve these examples cheaply; there is no speedup or quantum-advantage claim.')
    add('Protocol and scope',table(['Experiment','Recorded work'],[
        ['Ideal VQE',f'{len(vqe)} runs; four methods; {len(protocol["seeds"])} seeds; {protocol["vqe_steps"]} updates'],
        ['QAOA',f'{len(qaoa)} runs; two unchanged Track B QUBOs; p=1,2; all seeds'],
        ['Born sampling',f'{len(shots):,} distributions; 4 shot budgets; 100 repeats/configuration'],
        ['Finite-shot training',f'{len(finite)} runs; ShiftGD and SPSA; 128/1,024 shots per Pauli term'],
        ['Noise',f'{len(noise["fixed_parameters"])} fixed-parameter cases + {len(noise["growth"])} size/depth controls'],
        ['PQC classifier',f'{len(qnn)} datasets; 24 train and 64 test observations each'],
        ['Gradient concentration',f'{len(barren)} summaries; {protocol["barren_samples"]} random parameters each; 2–10 qubits']])+'\nMain VQE comparisons use the same initialization and update count, with unequal evaluation costs shown explicitly. Seed 0 was designated for post-training shots/noise before inspecting results. QAOA uses local Powell search; the objective-call cap is recorded in protocol.json and is not a ground-state certificate. Exact objectives use zero physical or sampled measurement shots.\n\nSource arrays, parameters, distributions, individual samples, optimizer status and CPU timings are retained. Statevector memory scales as 2^n; density matrices as 4^n.')
    add('VQE and optimizer cost',f'The synthetic Hamiltonian is H = 0.7 Z0 + 0.3 Z1 + 0.6 X0X1 − 0.2 Z0Z1. Its exact classical ground energy is **{ground:.12f}**, in dimensionless units. This is not a molecular H2 calculation.\n\n'+table(['Method','Mean final gap','Largest final gap','Objective calls/run','State preparations/run','Metric subset','Mean CPU seconds'],[[m,f'{r["mean_gap"]:.3g}',f'{r["max_gap"]:.3g}',r['objective_calls'],r['state_preparations'],r['metric_preparations'],f'{r["mean_runtime_s"]:.4f}'] for m,r in summary.items()])+'\n'+image('vqe_cost.png','Lines show medians; shading shows the full seed range. Gaps below 1e-12 are clipped only for the logarithmic display.')+'\nQNG uses the full Fubini–Study metric from exact simulator amplitudes, with damping 1e-3 and update norm capped at 1. Metric evaluations are included in state preparations. That access is a simulator convenience, not a hardware measurement implementation. SPSA uses two objective evaluations per update; its weaker result at the same number of updates must be considered alongside its smaller budget. Hyperparameters were fixed, not equally tuned.')
    add('QAOA on unchanged Track B objectives',table(['Model','p','Mean energy','Exact minimum','Mean ground probability','Original feasible','Encoded feasible','Local convergence'],[[r['model'],r['p'],f'{r["mean_energy"]:.5f}',r['classical_minimum'],f'{r["mean_ground_probability"]:.2%}',f'{r["mean_original_feasibility"]:.2%}',f'{r["mean_encoded_feasibility"]:.2%}',f'{r["local_success"]}/{r["seeds"]}'] for r in qsummary])+'\n'+image('qaoa_quality.png','Dots are individual seeds; short horizontal bars are means. Raw QUBO penalties retain their original scale.')+'\nMax-Cut improved at p=2 in these runs. Constrained knapsack remains far from its ground energy; extra depth does not ensure improvement under a difficult periodic local search. The original capacity constraint and exact slack equality have different feasibility probabilities. An original-feasible sample with incorrect slack can still have a high penalized energy. Finding a good sampled bitstring does not imply a good expected energy. All optimizer outcomes, including poor ones, remain in the data.\n\nThe mixer is exp(−i β ΣX); the cost unitary is exp(−i γ E). Gate decomposition omits only the global phase from the constant offset; every reported energy includes that offset. Shared QAOA angles control multiple gates, so the simple two-point single-gate parameter-shift formula is not applied to them.')
    classical_rows=[]
    for b in baseline['results']:
        comparable=[r for r in qsummary if r['model']==b['model']]
        classical_rows.append([b['model'],b['method'],b['minimum'],f'{b["median_runtime_s"]:.6f}',
            ', '.join(f'p={r["p"]}: {r["mean_runtime_s"]:.4f}s / {r["mean_calls"]:.0f} calls' for r in comparable) if comparable else 'See VQE cost table'])
    add('Classical references and resources',table(['Model','Classical method','Exact energy','Median CPU seconds','Quantum-method CPU simulation'],classical_rows)+'\nClassical timings use 31 repeats after one warmup, excluding input I/O. They are tiny-problem demonstrations rather than robust performance rankings. QAOA here stores all 2^n diagonal energies classically before optimization; this exponential simulation work is not a quantum oracle implementation. Primitive gates and CNOT counts per prepared QAOA circuit are in qaoa_runs.json. No timing includes hardware queueing, physical gates, coherence limits or device measurement latency.')
    add('Finite shots and stochastic training',image('shot_accuracy.png','Energy RMSE uses 100 independent multinomial samples at each budget, from each fixed seed-0 distribution.')+'\n'+image('finite_shot_training.png','Training plots use independent ideal diagnostics at retained iterates, not the noisy energy estimate used for each update. Shading is the seed range.')+'\nEach finite-shot VQE objective estimates four Pauli terms independently; S shots/term means 4S total shots per objective. No commuting-term grouping is claimed. A sampled energy estimate may lie below the exact ground energy because of sampling error; the exact diagnostic must still satisfy the variational bound. Shot totals count all gradient and logged training objectives. Diagnostic state preparations are reported separately. The shot study samples cached simulator probabilities, so its CPU time is not a hardware execution estimate.')
    add('Synthetic noise controls',image('noise_effects.png','Gate noise uses strength 0.01; readout uses independent 0.02 bit-flip probability. Parameters are fixed rather than reoptimized.')+'\nAfter each primitive gate, each involved qubit receives Dp(ρ)=(1−3p/4)ρ+(p/4)(XρX+YρY+ZρZ). A CNOT is followed by a local channel on both qubits. This convention makes p=1 complete depolarization on the affected qubit. Pauli measurement-basis rotations are ideal.\n\nReadout changes observed probabilities but not prepared-state fidelity or purity. Noise can accidentally improve a poor heuristic distribution; it is not guaranteed to worsen every objective in every case. This is a generic synthetic channel with no device calibration, connectivity routing, correlated noise, relaxation or mitigation. Density-matrix cases stop at six qubits.')
    global_growing=[r for r in barren if r['cost']=='global' and r['depth_label']=='growing']
    first,last=global_growing[0],global_growing[-1]
    add('Barren-plateau diagnostic',image('barren_plateaus.png','The derivative is with respect to the first Ry angle. Global cost is the product of all Zs; local cost is Z0. Shallow depth=2; growing depth=n.')+f'\nGlobal-cost variance for growing depth changes from {first["gradient_variance"]:.4g} at n=2 to {last["gradient_variance"]:.4g} at n=10. This is an empirical concentration diagnostic for one ansatz, initialization and parameter choice. It is not proof of exponential scaling or a universal barren plateau. Local and shallow controls expose dependence on the cost and circuit family.\n\nEach exact gradient uses two shifted states. For each shift and shot budget, independent binomial outcomes estimate the ±1 observable; 20 repeated estimates are retained per parameter point. Shot RMSE can exceed the shrinking gradient signal. Sample variances use ddof=1; duplicate n=2 depth controls intentionally share the same configuration. Raw angles and shifted expectations allow recomputation.')
    add('Trainable PQC / QNN',image('qnn_classifier.png','A two-qubit circuit encodes features with Ry(πx/2), then uses two Ry/Rz and CNOT layers. Minibatch Adam trains binary cross-entropy.')+'\n'+table(['Seed','PQC test accuracy','Logistic test accuracy','PQC state preparations','PQC CPU seconds','Logistic CPU seconds'],[[r['seed'],f'{r["test"]["accuracy"]:.2%}',f'{r["classical_logistic"]["test_accuracy"]:.2%}',r['work']['state_preparations'],f'{r["runtime_s"]:.4f}',f'{r["classical_logistic"]["runtime_s"]:.4f}'] for r in qnn])+'\nLabels are deliberately linear: x0+0.5x1>0, from synthetic uniform features. The regularized logistic baseline has three parameters; the PQC has eight and uses a different training procedure and budget. This is a functional learning demonstration, not a capacity-matched model comparison. Training data alone supplies gradients; test data is evaluated only at the end. The circuit expectation is shifted first, then the classical nonlinear loss chain rule is applied. Shifting the entire cross-entropy with the single-gate formula would be incorrect.')
    add('Validation and limits','The 32 unit tests cover independent dense gates and QAOA exponentials, CNOT bit order, density positivity and trace, Y-basis measurement, readout/depolarization endpoints, parameter-shift versus finite differences, Fubini–Study metric and global-phase removal, SPSA call counts, QNN loss gradients, Track B hashes and every-state energies. A separate audit recomputes retained outputs and samples.\n\nThese experiments implement the core Track C items. They do not complete the ten-track assignment. The original and fixed defects from A/B remain the two genuine AI failure cases so far; no third is invented here. A second independent AI-tool comparison, full chat exports, public GitHub publication, remaining tracks and the combined submission still need completion. See docs/COVERAGE.md and docs/VALIDATION_RECORD.md.')
    add('Primary references','- Farhi, Goldstone & Gutmann, QAOA: https://arxiv.org/abs/1411.4028\n- Peruzzo et al., VQE: https://arxiv.org/abs/1304.3061\n- Schuld et al., analytic quantum gradients: https://arxiv.org/abs/1811.11184\n- Stokes et al., Quantum Natural Gradient: https://arxiv.org/abs/1909.02108\n- McClean et al., barren plateaus: https://arxiv.org/abs/1803.11173\n- Spall, SPSA overview: https://www.jhuapl.edu/SPSA/PDF-SPSA/Spall_An_Overview.PDF\n- Qiskit Aer depolarizing convention: https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html\n- Supplied Assignment 8 and Chapter 6 lecture slides; acknowledged, not redistributed. Public references accessed 2026-11-03.')
    markdown='\n\n'.join('# '+title+'\n\n'+body for title,body in sections)+'\n'
    (root/'REPORT.md').write_text(markdown,encoding='utf-8')
    # Small explicit renderer keeps the report offline and avoids another dependency.
    def render(body):
        lines=body.splitlines();html=[];i=0
        while i<len(lines):
            line=lines[i]
            if line.startswith('| '):
                table_lines=[]
                while i<len(lines) and lines[i].startswith('| '):table_lines.append(lines[i]);i+=1
                rows=[[cell.strip() for cell in row.strip('|').split('|')] for row in table_lines]
                html.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in rows[0])+'</tr></thead><tbody>')
                for row in rows[2:]:html.append('<tr>'+''.join('<td>'+escape(x)+'</td>' for x in row)+'</tr>')
                html.append('</tbody></table></div>');continue
            if line.startswith('!['):
                name=line.split('(figures/',1)[1].rstrip(')');data=base64.b64encode((figures/name).read_bytes()).decode()
                html.append(f'<img alt="{escape(line[2:line.index("]")])}" src="data:image/png;base64,{data}">')
            elif line.startswith('- '):html.append('<p class="reference">'+escape(line[2:])+'</p>')
            elif line:html.append('<p>'+escape(line).replace('**','')+'</p>')
            i+=1
        return '\n'.join(html)
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Track C Quantum Optimization</title><style>body{margin:0;background:#eef3f5;color:#18333e;font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:32px auto;padding:36px;background:white;border-top:8px solid #087f8c;border-radius:12px}h1{font-size:32px;line-height:1.2}h2{font-size:24px;margin:42px 0 16px;color:#075764}img{width:100%;height:auto;margin:18px 0}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;border-bottom:1px solid #d9e5e9;text-align:left}th{background:#e7f3f3}.reference{font-size:13px;overflow-wrap:anywhere}@media(max-width:700px){main{margin:0;padding:20px}h1{font-size:27px}}</style><main>'
    for index,(title,body) in enumerate(sections):html+=f'<h{1 if index==0 else 2}>{escape(title)}</h{1 if index==0 else 2}>'+render(body)
    html+='</main></html>';(root/'report.html').write_text(html,encoding='utf-8')
    (root/'summary.json').write_text(json.dumps({'vqe':summary,'qaoa':qsummary,'shots':shot_summary,
        'qnn_mean_test_accuracy':float(np.mean([r['test']['accuracy'] for r in qnn])),
        'logistic_mean_test_accuracy':float(np.mean([r['classical_logistic']['test_accuracy'] for r in qnn]))},indent=2)+'\n')
    return plot_files
