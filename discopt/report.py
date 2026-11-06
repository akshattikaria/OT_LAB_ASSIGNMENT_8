"""Plots and an offline technical report built from recorded results."""
import base64
import html
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .data import FAMILIES
from .experiment import summarize,write_json
from .solvers import SOLVERS

NAMES={'baseline':'Input order','greedy':'Density greedy','dp':'DP','branch_bound':'B&B','ilp':'ILP'}
FAMILY_NAMES={'uncorrelated':'Uncorrelated','weakly_correlated':'Weak correlation','strongly_correlated':'Strong correlation','subset_sum':'Subset sum'}
COLORS={'baseline':'#6b7280','greedy':'#cd8624','dp':'#287ba2','branch_bound':'#8a5ea7','ilp':'#147d73'}


def style(ax):
    ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)


def main_plot(output,records,summary,supp):
    fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained');x=np.arange(4)
    for k,method in enumerate(('baseline','greedy')):
        rows=[next(s for s in summary if s['family']==f and s['method']==method) for f in FAMILIES]
        axes[0,0].bar(x+(k-.5)*.34,[r['mean_gap_percent'] for r in rows],.34,
            yerr=[r['sd_gap_percent'] for r in rows],capsize=3,label=NAMES[method],color=COLORS[method])
    axes[0,0].set(title='Heuristic quality versus the same exact DP reference',ylabel='Mean value gap (%)',xticks=x,xticklabels=[FAMILY_NAMES[f] for f in FAMILIES])
    axes[0,0].legend(fontsize=9);axes[0,0].tick_params(axis='x',rotation=15);style(axes[0,0])
    for k,method in enumerate(('dp','branch_bound','ilp')):
        rows=[next(s for s in summary if s['family']==f and s['method']==method) for f in FAMILIES]
        bars=axes[0,1].bar(x+(k-1)*.24,[100*r['certified_optimal']/r['instances'] for r in rows],.24,label=NAMES[method],color=COLORS[method])
        axes[0,1].bar_label(bars,labels=[f"{r['certified_optimal']}/{r['instances']}" for r in rows],fontsize=8,padding=3)
    axes[0,1].set(title='Proven optimal within the configured limits',ylabel='Certified instances (%)',ylim=(0,116),xticks=x,xticklabels=[FAMILY_NAMES[f] for f in FAMILIES])
    axes[0,1].tick_params(axis='x',rotation=15);axes[0,1].legend(fontsize=9,loc='lower left');style(axes[0,1])
    sizes=sorted({r['n'] for r in records if r['family'] in FAMILIES})
    for method in SOLVERS:
        medians=[];low=[];high=[]
        for n in sizes:
            runs=[r for r in records if r['family'] in FAMILIES and r['n']==n and r['method']==method]
            values=[1000*statistics.median(r['runtime_s'] for r in runs if r['instance']==name) for name in sorted({r['instance'] for r in runs})]
            medians.append(statistics.median(values));low.append(np.percentile(values,25));high.append(np.percentile(values,75))
        axes[1,0].plot(sizes,medians,'o-',label=NAMES[method],color=COLORS[method])
        axes[1,0].fill_between(sizes,low,high,color=COLORS[method],alpha=.08)
    axes[1,0].set(title='Runtime across instance families: median and IQR',xlabel='Number of items',ylabel='Method time (ms, log scale)',yscale='log',xticks=sizes)
    axes[1,0].legend(fontsize=9,ncol=2);style(axes[1,0])
    scaling=supp['dp_scaling'];factors=sorted({r['factor'] for r in scaling})
    cap=[next(r['capacity'] for r in scaling if r['factor']==f) for f in factors]
    storage=[next(r['table_bytes'] for r in scaling if r['factor']==f)/2**20 for f in factors]
    axes[1,1].plot(cap,storage,'o-',color=COLORS['dp'])
    axes[1,1].set(title='DP storage grows with numeric capacity',xlabel='Integer capacity (same feasible subsets)',ylabel='Allocated DP table (MiB)',xscale='log',yscale='log')
    style(axes[1,1]);fig.suptitle('Track B | budgeted selection | synthetic integer inputs',fontsize=16)
    fig.savefig(output/'knapsack_comparison.png',dpi=160);plt.close(fig)


def supplement_plot(output,supp):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    sweep=supp['penalty_sweep'];x=np.arange(len(sweep))
    rates=[r['encoded_feasible_ground_states']/r['ground_state_count'] for r in sweep]
    axes[0,0].bar(x,rates,color='#147d73');axes[0,0].set(xticks=x,xticklabels=[str(r['penalty']) for r in sweep],ylim=(0,1.15),
        title='Knapsack penalty: are all energy minima valid?',xlabel='Penalty P',ylabel='Fraction of ground states satisfying equality')
    for i,r in enumerate(sweep):axes[0,0].text(i,rates[i]+.03,f"{r['encoded_feasible_ground_states']}/{r['ground_state_count']}",ha='center',fontsize=9)
    style(axes[0,0])
    states=json.loads((output/'quantum_baselines'/'knapsack_6bit_classical.json').read_text())['states']
    for feasible,color,label in ((False,'#a1a7ae','Constraint violated'),(True,'#147d73','Constraint satisfied')):
        points=[s for s in states if s['encoded_feasible']==feasible]
        axes[0,1].scatter([s['index'] for s in points],[s['energy'] for s in points],s=18,color=color,label=label)
    axes[0,1].axhline(-6,color='#6b7280',linestyle='--',linewidth=1)
    axes[0,1].set(title='Verified 6-bit energy spectrum, P=15',xlabel='Statevector basis index',ylabel='QUBO / Ising energy',yscale='symlog',ylim=(-10,None))
    axes[0,1].legend(fontsize=8);style(axes[0,1])
    methods=('baseline','forward','backward','exhaustive');features=supp['feature_selection'];x=np.arange(4)
    for k,metric in enumerate(('validation_mse','test_mse')):
        groups=[[r[metric] for r in features if r['method']==m] for m in methods]
        means=[statistics.mean(v) for v in groups];sd=[statistics.stdev(v) if len(v)>1 else 0 for v in groups]
        axes[1,0].bar(x+(k-.5)*.34,means,.34,yerr=sd,capsize=3,label='Validation' if k==0 else 'Held-out test',color='#287ba2' if k==0 else '#cd8624')
    axes[1,0].set(title='Feature selection: mean MSE and sample SD',ylabel='Prediction MSE',xticks=x,xticklabels=methods)
    axes[1,0].legend(fontsize=9);style(axes[1,0])
    counts=[statistics.mean(r['model_fits'] for r in features if r['method']==m) for m in methods]
    bars=axes[1,1].bar(x,counts,color='#287ba2');axes[1,1].bar_label(bars,fmt='%.0f',padding=3)
    axes[1,1].set(title='Eight features, choose three: search cost',ylabel='Distinct fitted subsets',xticks=x,xticklabels=methods);style(axes[1,1])
    fig.suptitle('Constraint encoding and a separate feature-selection experiment',fontsize=16)
    fig.savefig(output/'qubo_and_features.png',dpi=160);plt.close(fig)


def markdown_html(lines,output):
    parts=[];paragraph=[];table=[]
    def flush_p():
        if paragraph:parts.append('<p>'+html.escape(' '.join(paragraph))+'</p>');paragraph.clear()
    def flush_t():
        if not table:return
        headers=[v.strip() for v in table[0].strip('|').split('|')]
        body='<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+html.escape(v)+'</th>' for v in headers)+'</tr></thead><tbody>'
        for row in table[2:]:body+='<tr>'+''.join('<td>'+html.escape(v.strip())+'</td>' for v in row.strip('|').split('|'))+'</tr>'
        parts.append(body+'</tbody></table></div>');table.clear()
    for line in lines:
        if line.startswith('|'):flush_p();table.append(line);continue
        flush_t()
        if not line:flush_p();continue
        if line.startswith('#'):
            flush_p();level=len(line)-len(line.lstrip('#'));parts.append(f'<h{level}>'+html.escape(line[level:].strip())+f'</h{level}>')
        elif line.startswith('!['):
            flush_p();alt=line[2:].split(']',1)[0];name=line.split('](',1)[1][:-1]
            encoded=base64.b64encode((output/name).read_bytes()).decode();parts.append(f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{encoded}">')
        else:paragraph.append(line)
    flush_p();flush_t()
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Track B discrete optimization</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#172b35;max-width:1080px;margin:40px auto;padding:0 24px}h1{font-size:32px;line-height:1.2}h2{font-size:23px;border-bottom:1px solid #d7e2e5;padding:18px 0 6px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;border-bottom:1px solid #d7e2e5;text-align:left}th{background:#eff5f5}.table-wrap{overflow:auto}img{max-width:100%;height:auto}@media print{body{margin:0;font-size:11px}h2{break-after:avoid}tr,img{break-inside:avoid}}</style><main>'+'\n'.join(parts)+'</main></html>'


def build_report(directory):
    output=Path(directory);records=json.loads((output/'raw_runs.json').read_text());supp=json.loads((output/'supplementary.json').read_text())
    protocol=json.loads((output/'protocol.json').read_text());env=json.loads((output/'environment.json').read_text())
    summary=summarize(records);write_json(output/'summary.json',summary)
    main_plot(output,records,summary,supp);supplement_plot(output,supp)
    main_cases=len({r['instance'] for r in records if r['family'] in FAMILIES})
    canonical=[r for r in records if r['repeat']==0]
    L=['# Track B: Discrete Optimization','','Measured classical software experiments on synthetic selection problems. Quantum hardware and QAOA are not used in this track; exact QUBO/Ising references are exported for Track C.','',
       '## Problem and formulation','','Choose binary item decisions x_i to maximize sum(value_i*x_i), subject to sum(weight_i*x_i) <= capacity. Values are nonnegative integers; costs are positive integers. The empty selection is always feasible, including when no item fits. A separate feature-selection experiment minimizes validation MSE subject to exactly three of eight features.','',
       'The baseline considers items in input order and takes each one if it fits. Density greedy sorts by decreasing value/cost using exact integer cross-products. Neither heuristic has an optimality guarantee in this implementation. Dynamic programming, a custom Branch-and-Bound and a library binary ILP solve the same knapsack formulation.','',
       '## Experimental protocol','',
       f"{main_cases} main instances: four synthetic families, sizes {protocol['sizes']}, seeds {protocol['seeds']}, plus five diagnostic cases. Each method is measured {protocol['repeats']} times, giving {len(records)} main/control method runs. Quality summaries use repetition 0; timing uses medians of per-instance median repetitions. Every candidate is independently checked for binary decisions, budget and objective value.",'',
       f"Branch-and-Bound uses a {protocol['search_time_limit_s']} s limit and 100,000 expanded-node limit. ILP has the same time limit and a zero relative MIP-gap target. DP has a 10,000,000-cell allocation guard. The generated workloads fit within that guard, allowing an exact DP reference on every case. Search methods may return a feasible candidate without completing a proof.",'',
       'Method order is deterministically shuffled. Timing includes validation, model construction and solver execution, but excludes reference generation, independent auditing, plots and imports. One tiny ILP call warms up the library. All data and stopping rules are recorded. No measured parallel speedup is claimed and internal numerical-library threading is uncontrolled.','',
       '## Results: quality and computation','','| Family | Method | Feasible | Proven optimal | Matches DP optimum | Value gap mean +/- SD | Median ms |','|---|---|---:|---:|---:|---:|---:|']
    for s in summary:L.append(f"| {FAMILY_NAMES[s['family']]} | {NAMES[s['method']]} | {s['feasible']}/{s['instances']} | {s['certified_optimal']}/{s['instances']} | {s['matches_optimal_value']}/{s['instances']} | {s['mean_gap_percent']:.4f}% +/- {s['sd_gap_percent']:.4f} pp | {1000*s['median_runtime_s']:.4f} |")
    L += ['', 'Gap is 100*(DP optimum - candidate value)/DP optimum, with zero when both are zero. A heuristic matching the known optimum is different from that heuristic proving optimality. Quality uses feasible returned candidates; all failures/limit statuses remain in raw_runs.json. Error bars describe dataset variability, not confidence intervals.','',
          '![Main comparison](knapsack_comparison.png)','','Density greedy is generally much better than the input-order baseline on these generated families, yet can miss the optimum. Equal value/weight ratios make tie handling relevant: the subset-sum family intentionally gives greedy the same order as the baseline. DP is effective at these integer capacities. Search methods trade proof effort against time/node limits; small nonzero gaps remain meaningful outcomes. These results do not establish a universal method ranking.','',
          '## Diagnostic cases','','| Case | Method | Value | Used budget | Reference value | Status |','|---|---|---:|---:|---:|---|']
    for r in canonical:
        if r['family']=='control':L.append(f"| {r['instance']} | {NAMES[r['method']]} | {r['audit']['value']} | {r['audit']['weight']} | {r['reference_value']} | {r['status']} |")
    L += ['', 'The three-item greedy trap has values (60,100,120), costs (10,20,30), capacity 50. Density greedy selects the first two for value 160; selecting the last two gives 220. This is a deliberate heuristic counterexample, not an AI implementation defect. Empty/zero-capacity/no-fit cases correctly allow selecting nothing.','',
          '## Exact methods and storage','','DP stores the recurrence D[i,c] = max(D[i-1,c], value_i + D[i-1,c-weight_i]) when item i fits. The previous row prevents reusing an item. Backtracking produces a binary selection. Time and full-table storage are O(n*C), pseudo-polynomial in numeric capacity rather than polynomial in its bit length.','',
          'Branch-and-Bound explores include/exclude decisions with a feasible density-greedy incumbent. A fractional-knapsack relaxation bounds remaining profit. The bound uses exact ratio ordering and integer arithmetic; flooring is valid because attainable total values are integers. Only nodes with an upper bound above the incumbent remain relevant. A nonempty unresolved frontier leaves an explicit proof gap.','',
          'ILP minimizes the negative total value using SciPy/HiGHS with bounds 0..1, integer variables and a single capacity inequality. The solver is acknowledged as external. Claimed optima are cross-checked against DP; smaller random cases are independently enumerated without DP tables or solver matrices.','',
          '| Capacity multiplier | Capacity | DP table cells | Table MiB | Median DP ms | Value |','|---|---:|---:|---:|---:|---:|']
    scaling=supp['dp_scaling']
    for factor in sorted({r['factor'] for r in scaling}):
        rows=[r for r in scaling if r['factor']==factor];r=rows[0]
        L.append(f"| {factor} | {r['capacity']} | {r['table_cells']} | {r['table_bytes']/2**20:.4f} | {statistics.median(q['runtime_s'] for q in rows)*1000:.4f} | {r['value']} |")
    L += ['', 'Multiplying weights and capacity changes integer units while preserving feasible subsets. This exposes capacity dependence, but GCD preprocessing would remove this particular inflation. It is a controlled illustration, not an inherent hardness claim about the rescaled instance. Table bytes are measured from the allocated array; overall process peak memory is not reported.','',
          '## QUBO with explicit constraint penalties','','For the four-item teaching case, introduce nonnegative slack s=b0+2*b1 and encode E(x,b) = -sum(v_i*x_i) + P*(sum(w_i*x_i)+s-C)^2. The six binary variables comprise four items and two slack bits. All feasible original selections have representable slack; overweight selections cannot satisfy the equality.','',
          'Writing z for all item/slack bits, a for their costs/slack weights and v_bar for rewards padded with zeros: Q_ii = P*(a_i^2-2*C*a_i)-v_bar_i, Q_ij=2*P*a_i*a_j for i<j, offset=P*C^2. Q is upper triangular and each off-diagonal pair is counted once. The constant offset is retained in every comparison.','',
          'A sufficient penalty is P > sum(values). Any equality violation has integer residual magnitude at least one, hence energy at least P-sum(values)>0, while a feasible empty item selection has energy zero. Therefore every global energy minimum is feasible, and within feasible states energy is negative selected value. The chosen P=15 satisfies this sufficient condition; smaller penalties can work for this particular case without meeting the general bound.','',
          '| Penalty | Minimum energy | Ground states | Equality-valid ground states | Original-budget-valid ground states |','|---|---:|---:|---:|---:|']
    for r in supp['penalty_sweep']:L.append(f"| {r['penalty']:g} | {r['minimum_energy']:.6g} | {r['ground_state_count']} | {r['encoded_feasible_ground_states']} | {r['original_feasible_ground_states']} |")
    L += ['', 'Too small a penalty can change the problem or create invalid ties. The experiment checks all minimizing states rather than accepting the first minimum that happens to be feasible. Large penalties increase coefficient scales and may complicate later quantum sampling; no hardware advantage is claimed. The encoder rejects total absolute coefficient magnitude above 2^45 to avoid known unsafe floating-point ranges.','',
          '## Ising conversion and Track C handoff','','The spin convention is s_i=1-2*z_i. For upper-triangular Q, h_i=-Q_ii/2 - sum_(j!=i) Q_min(i,j),max(i,j)/4; J_ij=Q_ij/4 for i<j; Ising offset=QUBO offset+sum_i Q_ii/2+sum_(i<j) Q_ij/4. Every exported bitstring is checked against the direct objective, expanded QUBO and Ising energy.','',
          '| Model | Bits | Enumerated states | Minimum energy | Ground states | Max energy identity error |','|---|---:|---:|---:|---:|---:|']
    for r in supp['quantum_exports']:L.append(f"| {r['name']} | {r['variables']} | {r['state_count']} | {r['minimum_energy']:.6g} | {r['ground_state_count']} | {r['energy_identity_error']:.3e} |")
    L += ['', 'The four-node Max-Cut graph has edges (0,1),(1,2),(2,3),(3,0),(0,2), all weight one. Its unconstrained QUBO minimizes negative cut. Diagonal Q entries are negative weighted degrees, edge pair entries are twice edge weight; minimum energy -4 means cut value 4. The constrained knapsack case independently supplies the required penalty demonstration.','',
          'The quantum_baselines folder contains model coefficients, offsets, variable names, every classical state energy, every ground state and checksums. Basis index is sum(z_i*2^i), with variable 0 least significant. variable_order_bits lists z0 first, while statevector_label prints the most significant bit first. A later simulator must preserve this mapping and restore any positive energy rescaling before comparing objective values.','',
          '## Forward/backward feature selection','','A separate synthetic regression task has eight candidate features and three selected features. Each candidate least-squares model is fit using 128 training samples. Validation MSE on 128 separate samples determines the subset; test MSE on 256 held-out samples is evaluated only after selection. Exhaustive selection considers all 56 three-feature subsets. Forward selection adds features; backward elimination starts with all features and removes them.','',
          '| Method | Mean validation MSE | Mean test MSE | Distinct model fits |','|---|---:|---:|---:|']
    for method in ('baseline','forward','backward','exhaustive'):
        rows=[r for r in supp['feature_selection'] if r['method']==method]
        L.append(f"| {method} | {statistics.mean(r['validation_mse'] for r in rows):.6g} | {statistics.mean(r['test_mse'] for r in rows):.6g} | {statistics.mean(r['model_fits'] for r in rows):.0f} |")
    L += ['', 'Arbitrary validation performance is not assumed additive, monotone or submodular. No 1-1/e guarantee is claimed for this feature objective. The knapsack ILP is not misrepresented as a linear formulation of black-box validation error. Exhaustive validation optimality also does not guarantee the lowest unseen test error.','',
          '![QUBO and feature selection](qubo_and_features.png)','','## Correctness, failures and limitations','',
          'Tests compare DP, Branch-and-Bound and ILP with exhaustive enumeration on 100 random small instances, and verify the constrained QUBO optimum on 20 random tiny knapsacks. Adversarial checks include fractional candidates, capacity violations, single-use DP recurrence, exact-ratio sorting, resource guards, weak penalties, bit ordering, energy offsets and feature test-data isolation. Every recorded main candidate is independently audited.','',
          'A genuine AI-generated numerical defect was found before the benchmark: a huge-capacity knapsack expanded in float coefficients gave energy 0 for a state whose direct energy is -1. A conservative coefficient-range guard now rejects that unsafe mapping, with a regression test. Original code and correction are retained in git history. Designed heuristic failures and configured search limits are not counted as implementation bugs.','',
          'Limitations: synthetic additive values/costs, single budget, small feature dimension, integer DP capacities, fixed search budgets, and classical enumeration limited to tiny QUBOs. These tests do not establish scalability to arbitrary large instances, real application gains or quantum advantage. Full assignment integration, remaining tracks, the second AI-tool comparison and public GitHub publication remain pending.','',
          '## Environment and references','',f"UTC {env['utc']}; Python {env['python'].splitlines()[0]}; NumPy {env['numpy']}; SciPy {env['scipy']}.",
          f"CPU {env['cpu']}; logical/affinity CPUs {env['logical_cpus']}/{env['affinity_cpus']}; cpu.max {env['cpu_quota']}. {env['note']}",'',
          'Sources: supplied Assignment 8 Track B/Section 5 and Chapter 6 PPT1/PPT3. SciPy milp documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html. D-Wave QUBO/Ising conventions: https://docs.dwavequantum.com/en/latest/quantum_research/qubo_ising.html (the spin sign convention used here is stated explicitly). Google OR-Tools knapsack description: https://developers.google.com/optimization/pack/knapsack; OR-Tools itself is not used in this code. Public references accessed 2026-11-03.','']
    (output/'REPORT.md').write_text('\n'.join(L),encoding='utf-8')
    (output/'report.html').write_text(markdown_html(L,output),encoding='utf-8')
    return summary
