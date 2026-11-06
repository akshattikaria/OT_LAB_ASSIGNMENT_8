from contextlib import closing
from datetime import datetime,timezone
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import platform
import time
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit import QuantumCircuit,ClassicalRegister,transpile,qpy
from qiskit.quantum_info import Statevector,Operator
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from threadpoolctl import threadpool_limits
from .common import ROOT,dump,sha_file,distribution_close
from .circuits import deutsch_jozsa,bernstein_vazirani,qft,phase_estimation,grover,grover_rounds,shor_order_circuit,factor_from_sample,cut_values,qaoa,vqe,vqe_energy,HAM,marginal,annealing,EDGES
from .learning import dataset,fit_pair


class FrozenManila(FakeManilaV2):
    dirname=str(ROOT/'inputs/fake_manila')


def basis_resources(circuit):
    start=time.perf_counter();compiled=transpile(circuit,basis_gates=['u','cx'],optimization_level=0,seed_transpiler=0)
    return {'basis':'u,cx','basis_operations':dict(compiled.count_ops()),'basis_depth':compiled.depth(),'transpile_s':time.perf_counter()-start}


def sample_counts(probs,shots,seed):
    p=np.maximum(0,np.asarray(probs));p/=p.sum();values=np.random.default_rng(seed).multinomial(shots,p)
    return {format(i,f'0{int(math.log2(len(p)))}b'):int(v) for i,v in enumerate(values) if v}


def save_circuit(output,name,circuit):
    path=output/'circuits'/f'{name}.qpy';path.parent.mkdir(exist_ok=True)
    with path.open('wb') as f:qpy.dump(circuit,f)
    return {'circuit_file':str(path.relative_to(output)),'circuit_sha256':sha_file(path),'qubits':circuit.num_qubits,'logical_depth':circuit.depth(),'logical_operations':dict(circuit.count_ops())}


def algorithm_suite(output,shots):
    rows=[];index=0
    def add(name,algorithm,circuit,nbits,expected=None,**details):
        nonlocal index
        start=time.perf_counter();probs=marginal(circuit,nbits);elapsed=time.perf_counter()-start
        if expected is not None:distribution_close(probs,expected)
        record={'name':name,'algorithm':algorithm,'output_bits':nbits,'probabilities':probs.tolist(),'counts':sample_counts(probs,shots,100+index),'shots':shots,'statevector_s':elapsed,**details,**save_circuit(output,name,circuit)}
        rows.append(record);index+=1
    for i,table in enumerate(((0,0),(1,1),(0,1),(1,0))):add(f'deutsch_{i}','Deutsch',deutsch_jozsa(table),1,[float(table[0]==table[1]),float(table[0]!=table[1])],truth=list(table),oracle_queries=1)
    tables=[([0]*8,'constant'),([1]*8,'constant'),([int((x&5).bit_count()%2) for x in range(8)],'balanced'),([0,0,0,1,1,1,0,1],'balanced')]
    for i,(table,kind) in enumerate(tables):
        qc=deutsch_jozsa(table);probs=marginal(qc,3)
        if abs(probs[0]-float(kind=='constant'))>1e-9:raise AssertionError('DJ decision incorrect')
        add(f'dj_{i}','Deutsch-Jozsa',qc,3,truth=table,promise_class=kind,oracle_queries=1)
    for secret in (0,3,5,7):
        expected=np.zeros(8);expected[secret]=1;add(f'bv_{secret}','Bernstein-Vazirani',bernstein_vazirani(3,secret),3,expected,secret=secret,oracle_queries=1,classical_queries=3)
    for n in (2,3,4):
        qc=qft(n);size=1<<n;dense=np.exp(2j*np.pi*np.outer(np.arange(size),np.arange(size))/size)/np.sqrt(size);error=float(np.max(abs(Operator(qc).data-dense)))
        if error>1e-10:raise AssertionError('QFT unitary mismatch')
        add(f'qft_{n}','QFT',qc,n,np.ones(size)/size,dense_unitary_max_error=error)
    for i,(bits,phase) in enumerate(((3,0),(3,3/8),(4,1/3))):
        size=1<<bits;expected=np.abs([np.exp(2j*np.pi*np.arange(size)*(phase-m/size)).sum()/size for m in range(size)])**2
        add(f'qpe_{i}','QPE',phase_estimation(bits,phase),bits,expected,phase=phase,controlled_power_gates=bits,equivalent_base_unitary_queries=size-1)
    for a in (2,7,11,14):
        qc=shor_order_circuit(15,a,4);expected=np.zeros(16);expected[[0,4,8,12] if a in (2,7) else [0,8]]=.25 if a in (2,7) else .5
        add(f'shor_{a}','Shor order finding',qc,4,expected,modulus=15,multiplier=a,postprocessing=[factor_from_sample(m,4,15,a) for m in range(16)],warning='Dense reversible modular multiplication for toy N=15; no scalable arithmetic or factoring runtime advantage is claimed.')
    dump(output/'algorithm_runs.json',rows);return rows


def grover_study(output,seeds,sizes):
    rows=[]
    for n in sizes:
        size=1<<n;rounds=grover_rounds(n)
        for seed in seeds:
            mark=int(np.random.default_rng(seed+1000*n).integers(size));start=time.perf_counter();checks=0;found=None
            for x in range(size):
                checks+=1
                if x==mark:found=x;break
            classical_s=time.perf_counter()-start
            if found!=mark:raise AssertionError('Classical search failed')
            start=time.perf_counter();qc=grover(n,mark);build_s=time.perf_counter()-start;resources=basis_resources(qc);start=time.perf_counter();probs=marginal(qc,n);simulate_s=time.perf_counter()-start;analytic=float(np.sin((2*rounds+1)*np.arcsin(1/np.sqrt(size)))**2)
            if abs(probs[mark]-analytic)>1e-8:raise AssertionError('Grover amplification probability mismatch')
            start=time.perf_counter();sample=int(np.random.default_rng(seed+5000*n).choice(size,p=np.maximum(probs,0)/probs.sum()));verified=sample==mark;sample_s=time.perf_counter()-start
            rows.append({'n':n,'size':size,'seed':seed,'marked':mark,'grover_rounds':rounds,'verification_queries':1,'success_probability':float(probs[mark]),'analytic_probability':analytic,
                         'sample':sample,'sample_verified':verified,'classical_checks':checks,'classical_uniform_expected_checks':(size+1)/2,'classical_s':classical_s,'build_s':build_s,'simulate_s':simulate_s,'sample_verify_s':sample_s,'simulator_end_to_end_s':build_s+resources['transpile_s']+simulate_s+sample_s,**resources})
        dump(output/'grover_runs.json',rows);print(f'Grover n={n}: query counts and actual simulator times retained',flush=True)
    return rows


def hybrid_study(output,seeds,steps,maxfev):
    energies=np.linalg.eigvalsh(HAM.to_matrix());values=cut_values();ground=values==values.max();vqe_rows=[];qaoa_rows=[]
    for seed in seeds:
        theta=np.random.default_rng(seed).normal(size=4);trace=[];calls=0;start=time.perf_counter();moment=np.zeros(4);variance=np.zeros(4)
        def energy(x):
            nonlocal calls
            calls+=1;return vqe_energy(x)
        trace.append({'theta':theta.tolist(),'energy':energy(theta)})
        for k in range(1,steps+1):
            gradient=np.array([(energy(theta+np.pi/2*e)-energy(theta-np.pi/2*e))/2 for e in np.eye(4)])
            moment=.9*moment+.1*gradient;variance=.999*variance+.001*gradient**2;theta=theta-.08*(moment/(1-.9**k))/(np.sqrt(variance/(1-.999**k))+1e-8);trace.append({'theta':theta.tolist(),'energy':energy(theta)})
        value=trace[-1]['energy']
        if value<energies[0]-1e-8:raise AssertionError('VQE violates variational lower bound')
        vqe_rows.append({'seed':seed,'steps':steps,'theta':theta.tolist(),'energy':value,'exact_energy':float(energies[0]),'gap':float(value-energies[0]),'circuit_evaluations':calls,'runtime_s':time.perf_counter()-start,'trace':trace})
        for depth in (1,2):
            calls=0;history=[];initial=np.random.default_rng(seed+100*depth).uniform(-np.pi,np.pi,2*depth);start=time.perf_counter()
            def cost(x):
                nonlocal calls
                calls+=1;value=-float(marginal(qaoa(x),4)@values);history.append({'theta':list(map(float,x)),'energy':value});return value
            result=minimize(cost,initial,method='Powell',options={'maxfev':maxfev,'xtol':1e-5,'ftol':1e-7});probs=marginal(qaoa(result.x),4)
            qaoa_rows.append({'seed':seed,'depth':depth,'theta':result.x.tolist(),'expected_cut':float(probs@values),'optimal_cut':float(values.max()),'ground_probability':float(probs[ground].sum()),'circuit_evaluations':calls,'distribution_checks':1,'runtime_s':time.perf_counter()-start,'optimizer_success':bool(result.success),'message':str(result.message),'history':history,'probabilities':probs.tolist()})
        print(f'Hybrid VQE/QAOA seed {seed} complete',flush=True)
    dump(output/'vqe_runs.json',vqe_rows);dump(output/'qaoa_runs.json',qaoa_rows)
    anneal_rows=[];driver=np.zeros((16,16),complex)
    for basis in range(16):
        for qubit in range(4):driver[basis^(1<<qubit),basis]-=1
    for total_time in (.2,1,5,20):
        start=time.perf_counter();qc=annealing(total_time,128);state=Statevector.from_instruction(qc).data;runtime=time.perf_counter()-start;dense=np.ones(16,dtype=complex)/4;dt=total_time/128
        for k in range(128):
            s=(k+.5)/128;dense=expm(-1j*dt*((1-s)*driver-s*np.diag(values)))@dense
        anneal_rows.append({'total_time':total_time,'steps':128,'ground_probability':float((abs(state)**2)[ground].sum()),'expected_cut':float(abs(state)**2@values),'dense_ground_probability':float((abs(dense)**2)[ground].sum()),'dense_state_fidelity':float(abs(np.vdot(dense,state))**2),'runtime_s':runtime,'logical_operations':dict(qc.count_ops())})
    classical=[]
    for seed in seeds:
        rng=np.random.default_rng(seed);start=time.perf_counter();x=int(rng.integers(16));energy=-values[x];best=energy;calls=1
        for beta in np.linspace(.1,5,128):
            for _ in range(4):
                trial=x^(1<<int(rng.integers(4)));candidate=-values[trial];calls+=1
                if candidate<energy or rng.random()<np.exp(-beta*(candidate-energy)):x=trial;energy=candidate
                best=min(best,energy)
        classical.append({'seed':seed,'best_cut':float(-best),'objective_evaluations':calls,'runtime_s':time.perf_counter()-start})
    dump(output/'annealing_runs.json',{'gate_based_adiabatic_simulation':anneal_rows,'classical_simulated_annealing':classical,'exact_cut':float(values.max()),'interpretation':'Gate-based Trotter approximation to a closed-system annealing schedule, not an execution on annealing hardware or evidence of tunneling advantage.'})


def noise_metadata(backend,noise):
    return {'backend':backend.name,'calibration_date':backend.properties().last_update_date.isoformat(),'basis_gates':noise.basis_gates,'coupling_map':[list(edge) for edge in backend.coupling_map.get_edges()],'source':'Pinned qiskit-ibm-runtime FakeManila snapshot copied into inputs/fake_manila, loaded by FrozenManila','models':'Aer NoiseModel.from_backend with gate/depolarizing, thermal relaxation and readout errors; incomplete approximation, not all device effects.','physical_hardware_used':False}


def noise_study(output,seeds,shots):
    backend=FrozenManila();noise=NoiseModel.from_backend(backend);dump(output/'calibrated_noise_model.json',noise.to_dict(serializable=True))
    programs=[('bv',bernstein_vazirani(3,5),3,[5]),('dj',deutsch_jozsa([int((x&5).bit_count()%2) for x in range(8)]),3,list(range(1,8))),('grover',grover(3,3),3,[3]),('qpe',phase_estimation(3,3/8),3,[3])];rows=[]
    for name,program,bits,success in programs:
        measured=program.copy();measured.add_register(ClassicalRegister(bits));measured.measure(list(range(bits)),list(range(bits)));compiled=transpile(measured,backend=backend,initial_layout=list(range(program.num_qubits)),optimization_level=1,seed_transpiler=17)
        circuit_record=save_circuit(output,'device_'+name,compiled)
        for seed in seeds:
            for condition,model in [('ideal',None),('calibrated',noise)]:
                simulator=AerSimulator(method='density_matrix',noise_model=model,max_parallel_threads=1);start=time.perf_counter();counts=simulator.run(compiled,shots=shots,seed_simulator=seed).result().get_counts();elapsed=time.perf_counter()-start
                success_count=sum(value for key,value in counts.items() if int(key.replace(' ',''),2) in success)
                if sum(counts.values())!=shots:raise AssertionError('Noise shot count mismatch')
                rows.append({'program':name,'seed':seed,'condition':condition,'shots':shots,'counts':counts,'success_count':success_count,'success_probability':success_count/shots,'success_outcomes':success,'runtime_s':elapsed,'native_operations':dict(compiled.count_ops()),'native_depth':compiled.depth(),**circuit_record})
        dump(output/'noise_runs.json',rows);print('Historical calibrated noise and paired ideal control: '+name,flush=True)
    dump(output/'noise_provenance.json',noise_metadata(backend,noise))


def learning_study(output,seeds,train_size,test_size):
    records=[];shot_records=[];folder=output/'qml_data';folder.mkdir()
    for family in ('moons','circles'):
        for seed in seeds:
            data=dataset(family,seed,train_size,test_size);order=('quantum','rbf') if seed%2==0 else ('rbf','quantum');rows,matrices,shots=fit_pair(data,order);name=f'{family}_{seed}.npz';np.savez_compressed(folder/name,**data,**matrices)
            for row in rows:records.append({'family':family,'seed':seed,'train_size':train_size,'test_size':test_size,'data_file':'qml_data/'+name,**row})
            for row in shots:shot_records.append({'family':family,'seed':seed,**row})
            dump(output/'qml_runs.json',records);dump(output/'kernel_shots.json',shot_records);print(f'Kernel classifiers {family}, seed {seed}: exact circuits and RBF control complete',flush=True)


def run(directory,seeds=(0,1,2),shots=4096,train_size=60,test_size=60,steps=60,maxfev=300,quick=False):
    output=Path(directory).resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty result folder')
    if not seeds or len(set(seeds))!=len(seeds) or min(shots,train_size,test_size,steps,maxfev)<1:raise ValueError('Positive distinct seeds and budgets required')
    output.mkdir(parents=True,exist_ok=True);source_files=['common.py','circuits.py','learning.py','experiment.py'];quota=Path('/sys/fs/cgroup/cpu.max')
    provenance=json.loads((ROOT/'inputs/provenance.json').read_text())
    for record in provenance['files']:
        if sha_file(ROOT/record['delivered'])!=record['sha256']:raise AssertionError('Reference or calibration input changed')
    dump(output/'environment.json',{'utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'versions':{name:md.version(name) for name in ('qiskit','qiskit-aer','qiskit-ibm-runtime','numpy','scipy','scikit-learn','matplotlib')},'logical_cpus':os.cpu_count(),'affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'cpu_max':quota.read_text().strip() if quota.exists() else None,'thread_limit':1,'source_sha256':{name:sha_file(ROOT/'qstudy'/name) for name in source_files}})
    sizes=(2,4,6) if quick else tuple(range(2,9));protocol={'seeds':list(seeds),'shots':shots,'qml_train':train_size,'qml_test':test_size,'vqe_steps':steps,'qaoa_maxfev':maxfev,'grover_qubits':sizes,'quick':quick,'endianness':'Qubit 0 is least significant; output-register integers match q[n-1]...q[0].','oracle_accounting':'Logical oracle query counts differ from decomposed gate count, circuit construction, transpilation and simulator CPU time. Grover charges r search calls plus one verification call; sample success is retained.','qml':'Same transformed features, train/test split, C=1 and precomputed-kernel SVC. Quantum kernel uses explicit compute-uncompute Statevector circuits, upper-triangle train Gram and full test Gram. No amplitude-cache shortcut in measured kernel construction.','noise':'Historical 2024-05-27 FakeManila calibration, Aer density-matrix shots, paired ideal control on identical transpiled circuits. No physical QPU execution or current calibration claim.','sampling':'Algorithm-suite counts are classical Born draws from SDK statevectors. Only the calibrated/paired noise study uses actual Aer shot execution. Kernel-shot sensitivity is synthetic binomial test-kernel noise with ideal-trained SVC, not noisy training.','reuse':'Unchanged earlier C/D summaries/protocols/audit are included with hashes; they are earlier measurements, not fresh Track I executions.'}
    dump(output/'protocol.json',protocol)
    with threadpool_limits(limits=1):
        algorithm_suite(output,shots);grover_study(output,seeds,sizes);hybrid_study(output,seeds,steps,maxfev);noise_study(output,seeds,shots);learning_study(output,seeds,train_size,test_size)
    expected={'algorithm_runs.json':22,'grover_runs.json':len(sizes)*len(seeds),'vqe_runs.json':len(seeds),'qaoa_runs.json':2*len(seeds),'noise_runs.json':8*len(seeds),'qml_runs.json':4*len(seeds),'kernel_shots.json':6*len(seeds)}
    for name,count in expected.items():
        if len(json.loads((output/name).read_text()))!=count:raise AssertionError('Incomplete saved experiment cells: '+name)
    dump(output/'evidence_sha256.json',{str(path.relative_to(output)):sha_file(path) for path in sorted(output.rglob('*')) if path.is_file()});return output
