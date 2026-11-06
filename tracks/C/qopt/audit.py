"""Recompute retained outputs; a data audit, independent of optimizer decisions."""
import hashlib
import json
from pathlib import Path
import numpy as np
from .experiment import load_problems,write_json
from .models import hamiltonian
from .qnn import outputs
from .simulator import hardware_state,probabilities,parity


def audit(directory):
    root=Path(directory);load=lambda n:json.loads((root/n).read_text());checks=0
    def close(a,b,tol=1e-8):
        nonlocal checks
        np.testing.assert_allclose(a,b,atol=tol,rtol=0);checks+=1
    inputs=Path(__file__).resolve().parents[1]/'inputs'/'track_b';problems=load_problems(inputs);H=hamiltonian();ground=np.linalg.eigvalsh(H)[0]
    for name,sha in load('track_b_sha256.json').items():
        if hashlib.sha256((inputs/name).read_bytes()).hexdigest()!=sha:raise AssertionError('Input hash mismatch')
        checks+=1
    trace_count=0
    for r in load('vqe_runs.json')+load('finite_shot_training.json'):
        for t in r['trace']:
            state=hardware_state(t['theta'],2,2);energy=np.vdot(state,H@state).real
            close(np.linalg.norm(state),1);close(energy,t['exact_energy'])
            if energy<ground-1e-9:raise AssertionError('Exact variational bound')
            trace_count+=1
        close(r['final_exact_energy'],r['trace'][-1]['exact_energy'])
        if r['shots_per_term'] is not None:close(r['work']['shots'],4*r['shots_per_term']*r['work']['objective_calls'])
    call_count=0
    for r in load('qaoa_runs.json'):
        p=problems[r['model']];prob=probabilities(p.qaoa_state(r['theta'],r['p']));close(prob,r['probabilities'])
        for k,v in p.metrics(prob).items():close(v,r['metrics'][k])
        close(len(r['trace']),r['objective_calls'])
        for t in r['trace']:
            energy=probabilities(p.qaoa_state(t['theta'],r['p']))@p.energies;close(energy,t['energy'])
            if energy<p.minimum-1e-8:raise AssertionError('QAOA lower bound')
            call_count+=1
    shot_rows=load('shot_study.json')
    for r in shot_rows:
        p=problems[r['model']];counts=np.asarray(r['counts']);close(counts.sum(),r['shots'])
        if np.any(counts<0) or not np.issubdtype(counts.dtype,np.integer):raise AssertionError('Invalid counts')
        for k,v in p.metrics(counts/r['shots']).items():close(v,r[k])
        valid=(counts>0)&p.original_feasible
        expected=float(np.max(p.utility[valid])) if np.any(valid) else None
        if expected!=r['best_observed_feasible_value']:raise AssertionError('Sample decoding mismatch')
    for r in load('qnn_runs.json'):
        with np.load(root/'qnn_data'/f'seed{r["seed"]}.npz') as data:
            prob=.02+.96*(1-outputs(r['theta'],data['Xtest']))/2
            close(np.mean((prob>=.5)==data['ytest']),r['test']['accuracy'])
            close(np.mean(-data['ytest']*np.log(prob)-(1-data['ytest'])*np.log(1-prob)),r['test']['loss'])
            A=np.column_stack((np.ones(len(data['Xtest'])),data['Xtest']))
            close(np.mean((A@r['classical_logistic']['theta']>=0)==data['ytest']),r['classical_logistic']['test_accuracy'])
    gradients=0
    for r in load('barren_plateaus.json'):
        gs=[];observable=parity(r['n'],list(range(r['n'])) if r['cost']=='global' else [0])
        # Audit every stored gradient and summary, using retained shifted expectations.
        for index,point in enumerate(r['raw']):
            record=point[r['cost']];g=.5*(record['plus']-record['minus']);close(g,record['exact_gradient']);gs.append(g);gradients+=1
            # Re-simulate predeclared first/middle/last points per summary.
            if index in (0,len(r['raw'])//2,len(r['raw'])-1):
                theta=np.array(point['theta']);delta=np.zeros_like(theta);delta[0]=np.pi/2
                plus=probabilities(hardware_state(theta+delta,r['n'],r['depth']))@observable
                minus=probabilities(hardware_state(theta-delta,r['n'],r['depth']))@observable
                close(plus,record['plus']);close(minus,record['minus'])
                eps=1e-5;delta[0]=eps
                fd=(probabilities(hardware_state(theta+delta,r['n'],r['depth']))@observable-probabilities(hardware_state(theta-delta,r['n'],r['depth']))@observable)/(2*eps)
                close(fd,g,1e-7)
        close(np.var(gs,ddof=1),r['gradient_variance']);close(np.sqrt(np.mean(np.square(gs))),r['gradient_rms'])
        for shots in (128,1024):
            errors=[(x-point[r['cost']]['exact_gradient'])**2 for point in r['raw'] for x in point[r['cost']]['shot_gradients'][str(shots)]]
            close(np.sqrt(np.mean(errors)),r['shot_rmse'][str(shots)])
    result={'passed':True,'numeric_comparisons':checks,'retained_vqe_iterates':trace_count,'qaoa_objective_calls':call_count,
        'sample_distributions':len(shot_rows),'retained_gradients':gradients,'resimulated_barren_points':len(load('barren_plateaus.json'))*3,
        'note':'Every retained VQE iterate and QAOA objective recomputed; all shot counts/metrics checked; all gradient arithmetic/summary recomputed, with first/middle/last circuit points per summary additionally resimulated and finite-differenced. Noise channels independently covered by unit tests.'}
    write_json(root/'audit.json',result);return result


if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'results'),indent=2))
