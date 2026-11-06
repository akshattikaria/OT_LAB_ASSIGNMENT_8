"""One report page from the retained Q-FLAIR paired experiment."""
import json
import statistics as st
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def qflair_page(root):
    data=json.loads((root/'research_supplement/results/qflair.json').read_text())
    groups=[(kind,d) for kind in ['linear','xor'] for d in [4,12]]
    rows=[];qacc=[];lacc=[];qstd=[];lstd=[];ratios=[]
    for kind,d in groups:
        cases=[r for r in data['runs'] if r['dataset']==kind and r['dimensions']==d]
        a=[r['methods']['qflair']['test_accuracy']*100 for r in cases];b=[r['logistic']['test_accuracy']*100 for r in cases];rr=[r['query_ratio'] for r in cases]
        qacc.append(st.mean(a));lacc.append(st.mean(b));qstd.append(st.stdev(a));lstd.append(st.stdev(b));ratios.append(st.mean(rr))
        rows.append([kind,str(d),f'{st.mean(a):.1f} ± {st.stdev(a):.1f}%',f'{st.mean(b):.1f} ± {st.stdev(b):.1f}%',f'{st.mean(rr):.1f}x'])
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.1),layout='constrained')
    x=np.arange(4);axes[0].bar(x-.18,qacc,.36,yerr=qstd,capsize=3,label='Q-FLAIR QNN',color='#195680');axes[0].bar(x+.18,lacc,.36,yerr=lstd,capsize=3,label='Logistic',color='#278a91')
    axes[0].set(xticks=x,xticklabels=['Linear 4','Linear 12','XOR 4','XOR 12'],ylim=(0,105),ylabel='Held-out accuracy (%)',title='Three seeds; mean ± sample SD');axes[0].legend(fontsize=7)
    axes[1].bar(x,ratios,color='#d58645');axes[1].set(xticks=x,xticklabels=['Linear 4','Linear 12','XOR 4','XOR 12'],ylabel='Direct / reconstruction logical queries',title='Same finite search; matching circuit outputs')
    fig.savefig(root/'reports/figures/qflair_comparison.png',dpi=180);plt.close(fig)
    cap=sum(r['methods']['qflair']['stopping_reason']=='gate_cap' for r in data['runs'])
    return ('Research extension: Q-FLAIR feature-map learning',[
      ('p','Q-FLAIR (PPT3 slide 37) learns its quantum feature map gate by gate. This scoped QNN port grows a two-qubit circuit, reconstructs candidate outputs using shared zero and ±π/2 evaluations, then classically selects gate, feature and weight. Source: Jäger et al., arXiv:2510.03389v2, Sec. III / Algorithm 1 / Appendix A.1; author code commit 4f331783.'),
      ('table',['Synthetic task','Features','Q-FLAIR accuracy','Logistic accuracy','Query ratio'],rows,[.20,.12,.24,.24,.20]),
      ('image','reports/figures/qflair_comparison.png','Every seed is retained. The paired direct-grid QNN matches Q-FLAIR output; logistic is a separate classical reference.',175),
      ('p','Twelve paired cases use 64 training/64 disjoint test rows, 41 weight values and an eight-generator pool. Train-only scaling and threshold selection prevent test leakage. Nine new tests compare author reconstruction, dense matrix exponentials, exhaustive candidates and Qiskit circuits. Independent replay agrees within 6e-16.'),
      ('p',f'{cap}/12 cases reach the 12-gate cap. XOR generalization is mixed; classical logistic wins on several splits. The query ratio counts logical black-box output evaluations, not measured QPU time or CPU speedup. Classical feature/weight scoring still grows with dimension. This is not the paper\'s QSVM, MNIST or IBM-hardware reproduction.'),
      ('evidence','research_supplement/qflair.py; test_qflair.py; QFLAIR.md; results/qflair.json; author_checks/; provenance/qflair_completion_20261106.json')])
