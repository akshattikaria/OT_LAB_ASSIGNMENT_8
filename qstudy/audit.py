"""Recompute scientific evidence; retained timings are never replaced."""
import json
import math
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from qiskit import qpy
from qiskit.quantum_info import Operator,Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from sklearn.metrics.pairwise import rbf_kernel
from .common import ROOT,dump,sha_file,distribution_close
from .circuits import marginal,grover,grover_rounds,vqe_energy,qaoa,cut_values,factor_from_sample,annealing,HAM
from .learning import dataset,analytic_feature_state
from .experiment import FrozenManila


def audit(directory,replay_noise=False):
    root=Path(directory);read=lambda name:json.loads((root/name).read_text());protocol=read('protocol.json');env=read('environment.json');checks=0;expectations=0
    for name,digest in read('evidence_sha256.json').items():
        if sha_file(root/name)!=digest:raise AssertionError('Raw evidence checksum changed: '+name)
        checks+=1
    for name,digest in env['source_sha256'].items():
        if sha_file(ROOT/'qstudy'/name)!=digest:raise AssertionError('Measured source changed: '+name)
        checks+=1
    for row in json.loads((ROOT/'inputs/provenance.json').read_text())['files']:
        if sha_file(ROOT/row['delivered'])!=row['sha256']:raise AssertionError('Reference/calibration identity changed')
        checks+=1
    algorithms=read('algorithm_runs.json')
    if len(algorithms)!=22 or len({r['name'] for r in algorithms})!=22:raise AssertionError('Algorithm cases incomplete')
    circuit_cache={}
    def load(name):
        if name not in circuit_cache:
            with (root/name).open('rb') as stream:circuit_cache[name]=qpy.load(stream)[0]
        return circuit_cache[name]
    for row in algorithms:
        qc=load(row['circuit_file']);probs=marginal(qc,row['output_bits']);distribution_close(probs,row['probabilities'])
        if sum(row['counts'].values())!=row['shots'] or row['shots']!=protocol['shots']:raise AssertionError('Wrong ideal Born sample count')
        if row['algorithm'] in ('Deutsch','Deutsch-Jozsa'):
            expected=float(sum(row['truth']) in (0,len(row['truth'])))
            if abs(probs[0]-expected)>1e-9:raise AssertionError('Promise classification incorrect')
        elif row['algorithm']=='Bernstein-Vazirani':
            if abs(probs[row['secret']]-1)>1e-9:raise AssertionError('Hidden string not recovered')
        elif row['algorithm']=='QFT':
            size=len(probs);fourier=np.exp(2j*np.pi*np.outer(np.arange(size),np.arange(size))/size)/np.sqrt(size);distribution_close(Operator(qc).data,fourier)
        elif row['algorithm']=='QPE':
            size=len(probs);expected=np.abs([np.exp(2j*np.pi*np.arange(size)*(row['phase']-m/size)).sum()/size for m in range(size)])**2;distribution_close(probs,expected)
        elif row['algorithm']=='Shor order finding':
            a=row['multiplier'];modulus=row['modulus'];order=1
            while pow(a,order,modulus)!=1:order+=1
            expected=np.zeros(len(probs));expected[np.arange(order)*(len(probs)//order)]=1/order;distribution_close(probs,expected)
            for i,item in enumerate(row['postprocessing']):
                if item!=factor_from_sample(i,row['output_bits'],modulus,a):raise AssertionError('Shor postprocessing differs')
                if any(modulus%factor or factor in (1,modulus) for factor in item['factors']):raise AssertionError('Invalid factor')
        checks+=3
    grover_rows=read('grover_runs.json');expected={(n,s) for n in protocol['grover_qubits'] for s in protocol['seeds']}
    if len(grover_rows)!=len(expected) or {(r['n'],r['seed']) for r in grover_rows}!=expected:raise AssertionError('Grover grid incomplete')
    for row in grover_rows:
        size=1<<row['n'];r=grover_rounds(row['n']);p=float(np.sin((2*r+1)*np.arcsin(1/np.sqrt(size)))**2)
        if size!=row['size'] or r!=row['grover_rounds'] or row['classical_checks']!=row['marked']+1 or row['classical_uniform_expected_checks']!=(size+1)/2 or abs(p-row['success_probability'])>1e-8:raise AssertionError('Grover reference/counts mismatch')
        if abs(marginal(grover(row['n'],row['marked']),row['n'])[row['marked']]-p)>1e-8:raise AssertionError('Fresh Grover circuit differs')
        if row['sample_verified']!=(row['sample']==row['marked']) or abs(row['simulator_end_to_end_s']-sum(row[k] for k in ('build_s','transpile_s','simulate_s','sample_verify_s')))>1e-10:raise AssertionError('Grover verification/timing boundary mismatch')
        if min(row[k] for k in ('classical_s','build_s','simulate_s','transpile_s'))<0:raise AssertionError('Negative timing')
        checks+=4
    vq=read('vqe_runs.json');qa=read('qaoa_runs.json');cuts=cut_values()
    if len(vq)!=len(protocol['seeds']) or {r['seed'] for r in vq}!=set(protocol['seeds']):raise AssertionError('VQE grid incomplete')
    if len(qa)!=2*len(protocol['seeds']) or {(r['seed'],r['depth']) for r in qa}!={(s,p) for s in protocol['seeds'] for p in (1,2)}:raise AssertionError('QAOA grid incomplete')
    exact=float(np.linalg.eigvalsh(HAM.to_matrix())[0])
    for row in vq:
        if len(row['trace'])!=protocol['vqe_steps']+1 or row['circuit_evaluations']!=1+9*protocol['vqe_steps']:raise AssertionError('VQE call/step count differs')
        for point in row['trace']:
            if abs(vqe_energy(point['theta'])-point['energy'])>1e-9:raise AssertionError('VQE retained expectation differs')
            expectations+=1;checks+=1
        if abs(row['gap']-(row['energy']-exact))>1e-9 or row['gap']<-1e-8:raise AssertionError('Variational bound/gap mismatch')
    for row in qa:
        if row['circuit_evaluations']!=len(row['history']) or row['circuit_evaluations']>protocol['qaoa_maxfev']:raise AssertionError('QAOA call budget differs')
        for point in row['history']:
            if abs(-marginal(qaoa(point['theta']),4)@cuts-point['energy'])>1e-8:raise AssertionError('QAOA retained objective differs')
            expectations+=1;checks+=1
        probs=marginal(qaoa(row['theta']),4);distribution_close(probs,row['probabilities'])
        if abs(probs@cuts-row['expected_cut'])>1e-9 or abs(probs[cuts==4].sum()-row['ground_probability'])>1e-9:raise AssertionError('QAOA solution metrics differ')
    anneal=read('annealing_runs.json')
    if len(anneal['gate_based_adiabatic_simulation'])!=4:raise AssertionError('Annealing schedules incomplete')
    driver=np.zeros((16,16),complex)
    for basis in range(16):
        for qubit in range(4):driver[basis^(1<<qubit),basis]-=1
    for row in anneal['gate_based_adiabatic_simulation']:
        probs=marginal(annealing(row['total_time'],row['steps']),4)
        if abs(probs[cuts==4].sum()-row['ground_probability'])>1e-9 or abs(probs@cuts-row['expected_cut'])>1e-9:raise AssertionError('Annealing circuit differs')
        dense=np.ones(16,dtype=complex)/4;dt=row['total_time']/row['steps']
        for k in range(row['steps']):
            s=(k+.5)/row['steps'];dense=expm(-1j*dt*((1-s)*driver-s*np.diag(cuts)))@dense
        state=Statevector.from_instruction(annealing(row['total_time'],row['steps'])).data
        if abs((abs(dense)**2)[cuts==4].sum()-row['dense_ground_probability'])>1e-9 or abs(abs(np.vdot(dense,state))**2-row['dense_state_fidelity'])>1e-9:raise AssertionError('Dense annealing reference differs')
        checks+=3
    classical=anneal['classical_simulated_annealing']
    if len(classical)!=len(protocol['seeds']) or {r['seed'] for r in classical}!=set(protocol['seeds']):raise AssertionError('Classical annealing cells incomplete')
    for row in classical:
        rng=np.random.default_rng(row['seed']);x=int(rng.integers(16));energy=-cuts[x];best=energy
        for beta in np.linspace(.1,5,128):
            for _ in range(4):
                trial=x^(1<<int(rng.integers(4)));candidate=-cuts[trial]
                if candidate<energy or rng.random()<np.exp(-beta*(candidate-energy)):x=trial;energy=candidate
                best=min(best,energy)
        if row['objective_evaluations']!=513 or row['best_cut']!=-best:raise AssertionError('Classical annealing replay differs')
        checks+=1
    noise_rows=read('noise_runs.json');expected={(name,s,condition) for name in ('bv','dj','grover','qpe') for s in protocol['seeds'] for condition in ('ideal','calibrated')}
    if len(noise_rows)!=len(expected) or {(r['program'],r['seed'],r['condition']) for r in noise_rows}!=expected:raise AssertionError('Noise grid incomplete')
    replayed=0;noise=NoiseModel.from_backend(FrozenManila()) if replay_noise else None
    for row in noise_rows:
        counts=row['counts'];success=sum(value for key,value in counts.items() if int(key.replace(' ',''),2) in row['success_outcomes'])
        if sum(counts.values())!=row['shots'] or success!=row['success_count'] or success/row['shots']!=row['success_probability']:raise AssertionError('Noise shot metrics differ')
        if replay_noise:
            simulator=AerSimulator(method='density_matrix',noise_model=noise if row['condition']=='calibrated' else None,max_parallel_threads=1)
            fresh=simulator.run(load(row['circuit_file']),shots=row['shots'],seed_simulator=row['seed']).result().get_counts()
            if fresh!=counts:raise AssertionError('Seeded Aer shot replay differs (use pinned versions)')
            replayed+=1
        checks+=3
    qml=read('qml_runs.json');expected={(family,s,model) for family in ('moons','circles') for s in protocol['seeds'] for model in ('quantum','rbf')}
    if len(qml)!=len(expected) or {(r['family'],r['seed'],r['model']) for r in qml}!=expected:raise AssertionError('QML grid incomplete')
    validated_files=set();kernel_entries=0;classifications=0
    for row in qml:
        with np.load(root/row['data_file'],allow_pickle=False) as data:
            if row['data_file'] not in validated_files:
                regenerated=dataset(row['family'],row['seed'],protocol['qml_train'],protocol['qml_test'])
                for name,value in regenerated.items():distribution_close(data[name],value)
                a=np.array([analytic_feature_state(x) for x in data['x_train']]);b=np.array([analytic_feature_state(x) for x in data['x_test']]);train=abs(a.conj()@a.T)**2;test=abs(b.conj()@a.T)**2
                distribution_close(train,data['quantum_train']);distribution_close(test,data['quantum_test']);kernel_entries+=train.size+test.size
                gamma=1/(data['x_train'].shape[1]*data['x_train'].var());distribution_close(rbf_kernel(data['x_train'],gamma=gamma),data['rbf_train']);distribution_close(rbf_kernel(data['x_test'],data['x_train'],gamma=gamma),data['rbf_test']);kernel_entries+=train.size+test.size
                validated_files.add(row['data_file'])
            model=row['model'];support=data[model+'_support'];dual=data[model+'_dual'].ravel();bias=data[model+'_intercept'][0];prediction=(data[model+'_test'][:,support]@dual+bias>0).astype(int)
            np.testing.assert_array_equal(prediction,data[model+'_prediction']);classifications+=len(prediction)
            if row['accuracy']!=float(np.mean(prediction==data['y_test'])) or row['learned_classifier_scalars']!=len(dual)+1 or row['support_vectors']!=len(support) or row['trainable_circuit_parameters']!=0:raise AssertionError('Classifier metrics/parameter count mismatch')
            if abs(row['training_total_s']-row['training_kernel_s']-row['svc_fit_s'])>1e-10 or abs(row['inference_total_s']-row['test_kernel_s']-row['predict_s'])>1e-10:raise AssertionError('Kernel timing boundary mismatch')
            expected_calls=row['train_size']*(row['train_size']-1)//2+row['train_size']*row['test_size'] if model=='quantum' else 0
            if row['overlap_circuit_evaluations']!=expected_calls:raise AssertionError('Circuit evaluation count mismatch')
            if model=='quantum' and np.linalg.eigvalsh(data['quantum_train']).min()<-1e-8:raise AssertionError('Non-PSD ideal kernel')
            checks+=6
    shot_rows=read('kernel_shots.json')
    if len(shot_rows)!=6*len(protocol['seeds']):raise AssertionError('Kernel-shot cells incomplete')
    for row in shot_rows:
        with np.load(root/'qml_data'/f'{row["family"]}_{row["seed"]}.npz',allow_pickle=False) as data:
            shots=row['shots_per_overlap'];counts=data[f'shot_{shots}_counts'];support=data['quantum_support'];dual=data['quantum_dual'].ravel();bias=data['quantum_intercept'][0];prediction=(counts[:,support]/shots@dual+bias>0).astype(int)
            np.testing.assert_array_equal(prediction,data[f'shot_{shots}_prediction'])
            if np.any(counts<0) or np.any(counts>shots) or row['accuracy']!=float(np.mean(prediction==data['y_test'])) or row['synthetic_binary_samples']!=counts.size*shots:raise AssertionError('Synthetic shot sensitivity metrics differ')
            checks+=2
    result={'passed':True,'tracked_checks':checks,'algorithm_cases':len(algorithms),'grover_runs':len(grover_rows),'retained_hybrid_expectations_recomputed':expectations,'kernel_entries_checked':kernel_entries,'heldout_predictions_checked':classifications,'qml_models':len(qml),'aer_shot_rows_checked':len(noise_rows),'seeded_aer_replays':replayed,'overlap_circuits_in_main_run':sum(r['overlap_circuit_evaluations'] for r in qml),'note':'No timings replaced. Algorithm QPY/distributions and independent mathematics, raw hybrid objectives, analytical-feature kernels, manual SVC predictions, counters, shot metrics and source/input identities verified. Aer exact-count replay uses the pinned package versions.'}
    dump(root/'audit.json',result);return result
