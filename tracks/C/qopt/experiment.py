from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter
import numpy as np
import scipy
from scipy.optimize import minimize

from .models import DiagonalProblem,VQE_TERMS,hamiltonian
from .optimizers import train_vqe
from .simulator import probabilities,statevector,density,hardware_gates,hardware_state,pauli_expectation,measured_pauli,readout,parity
from .qnn import train as train_qnn,dataset as qnn_dataset


def write_json(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def environment():
    return {'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,
            'platform':platform.platform(),'logical_cpus':os.cpu_count(),
            'affinity_cpus':len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
            'cpu_quota':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,
            'note':'CPU NumPy statevector/density simulator authored in this package. No SDK, GPU, physical quantum hardware or device calibration used.'}


def load_problems(folder):
    folder=Path(folder)
    return {name:DiagonalProblem(folder/f'{name}_model.json',folder/f'{name}_classical.json') for name in ('maxcut_4bit','knapsack_6bit')}


def classical_baselines(problems,repeats=31):
    """Fresh exhaustive search/eigensolve, with input I/O excluded from timing."""
    rows=[]
    for name,problem in problems.items():
        timings=[]
        for repeat in range(repeats+1):
            clock=perf_counter();energies=[]
            for index in range(1<<problem.n):
                bits=np.array([(index>>q)&1 for q in range(problem.n)])
                energies.append(float(problem.offset+bits@problem.Q@bits))
            minimum=min(energies);indices=[i for i,e in enumerate(energies) if abs(e-minimum)<1e-9]
            elapsed=perf_counter()-clock
            if repeat:timings.append(elapsed)
        if minimum!=problem.minimum:raise AssertionError('Independent enumeration mismatch')
        rows.append({'model':name,'method':'exhaustive binary enumeration','states':1<<problem.n,
            'minimum':minimum,'ground_indices':indices,'timings_s':timings,'median_runtime_s':float(np.median(timings))})
    timings=[]
    for repeat in range(repeats+1):
        clock=perf_counter();eigenvalues=np.linalg.eigvalsh(hamiltonian());elapsed=perf_counter()-clock
        if repeat:timings.append(elapsed)
    rows.append({'model':'vqe_2qubit','method':'dense Hermitian eigensolve','matrix_dimension':4,
        'minimum':float(eigenvalues[0]),'timings_s':timings,'median_runtime_s':float(np.median(timings))})
    return {'results':rows,'timing_note':'31 timed repeats after one warmup. Tiny CPU baselines exclude input I/O. Quantum entries also run on CPU; these comparisons cannot establish quantum speedup.'}


def qaoa_train(problem,name,p,seed,maxfev=600):
    rng=np.random.default_rng(seed+3000);initial=np.concatenate((rng.uniform(0,2*np.pi,p),rng.uniform(0,np.pi,p)))
    trace=[];clock=perf_counter()
    def cost(theta):
        prob=probabilities(problem.qaoa_state(theta,p));value=float(prob@problem.energies)
        trace.append({'call':len(trace)+1,'energy':value,'theta':theta.tolist()});return value
    result=minimize(cost,initial,method='Powell',bounds=[(0,2*np.pi)]*p+[(0,np.pi)]*p,
        options={'maxfev':maxfev,'maxiter':150,'xtol':1e-7,'ftol':1e-9})
    seconds=perf_counter()-clock;prob=probabilities(problem.qaoa_state(result.x,p))
    gates=problem.qaoa_gates(result.x,p)
    return {'model':name,'p':p,'seed':seed,'initial':initial.tolist(),'theta':result.x.tolist(),
        'trace':trace,'probabilities':prob.tolist(),'metrics':problem.metrics(prob),'runtime_s':seconds,
        'objective_calls':int(result.nfev),'optimizer_success':bool(result.success),'optimizer_message':str(result.message),
        'primitive_gates':len(gates),'cnot_gates':sum(g[0]=='cx' for g in gates),'measurements':0,
        'classical_minimum':problem.minimum,'uniform_baseline':problem.metrics(np.ones(1<<problem.n)/(1<<problem.n))}


def shot_study(problems,qaoa,repetitions=100):
    records=[]
    for run in qaoa:
        if run['seed']!=0:continue
        p=problems[run['model']];prob=np.array(run['probabilities'])
        for shots in (64,256,1024,4096):
            rng=np.random.default_rng(7000+shots+run['p']+p.n)
            for repeat in range(repetitions):
                counts=rng.multinomial(shots,prob);estimate=counts/shots
                observed=np.flatnonzero((counts>0)&p.original_feasible)
                records.append({'model':run['model'],'p':run['p'],'shots':shots,'repeat':repeat,
                    'counts':counts.tolist(),**p.metrics(estimate),
                    'best_observed_feasible_value':float(np.max(p.utility[observed])) if len(observed) else None})
    return records


def noise_study(problems,qaoa,vqe):
    rows=[]
    configs=[('ideal',0.,0.),('gate_only',.01,0.),('readout_only',0.,.02),('both',.01,.02)]
    for run in qaoa:
        if run['seed']!=0:continue
        p=problems[run['model']];gates=p.qaoa_gates(run['theta'],run['p']);ideal=p.qaoa_state(run['theta'],run['p'])
        for label,gate_error,measurement_error in configs:
            rho=density(p.n,gates,gate_error);prob=readout(probabilities(rho),p.n,measurement_error)
            rows.append({'model':run['model'],'p':run['p'],'noise':label,'depolarizing_strength':gate_error,'readout_error':measurement_error,
                'probabilities':prob.tolist(),**p.metrics(prob),'fidelity_to_ideal':float(np.real(np.vdot(ideal,rho@ideal))),
                'purity':float(np.real(np.trace(rho@rho))),'primitive_gates':len(gates),
                'min_density_eigenvalue':float(np.linalg.eigvalsh(rho)[0])})
    run=next(r for r in vqe if r['seed']==0 and r['method']=='ShiftAdam');gates=hardware_gates(run['theta'],2,2);ideal=hardware_state(run['theta'],2,2)
    for label,gate_error,measurement_error in configs:
        rho=density(2,gates,gate_error)
        measured=sum(c*measured_pauli(rho,term,None,None,measurement_error) for c,term in VQE_TERMS)
        rows.append({'model':'vqe_2qubit','p':2,'noise':label,'depolarizing_strength':gate_error,'readout_error':measurement_error,
            'expected_energy':measured,'state_energy_before_readout':float(np.real(np.trace(rho@hamiltonian()))),
            'fidelity_to_ideal':float(np.real(np.vdot(ideal,rho@ideal))),'purity':float(np.real(np.trace(rho@rho))),
            'primitive_gates':len(gates),'min_density_eigenvalue':float(np.linalg.eigvalsh(rho)[0])})
    growth=[]
    for n in (2,4,6):
        for depth in (2,4):
            theta=np.random.default_rng(8000+n*10+depth).uniform(-np.pi,np.pi,2*n*depth)
            gates=hardware_gates(theta,n,depth);ideal=statevector(n,gates)
            for error in (0.,.01,.03):
                rho=density(n,gates,error)
                growth.append({'n':n,'depth':depth,'depolarizing_strength':error,'primitive_gates':len(gates),
                    'fidelity':float(np.real(np.vdot(ideal,rho@ideal))),'purity':float(np.real(np.trace(rho@rho)))})
    return {'fixed_parameters':rows,'growth':growth,
            'model':'After each primitive gate, local D_p(rho)=(1-3p/4)rho+(p/4)(XrhoX+YrhoY+ZrhoZ) on every involved qubit; final independent bit flips model readout.',
            'measurement_basis_note':'Pauli measurement-basis rotations are ideal; noise acts on circuit preparation gates. Generic synthetic noise, not a calibrated device.'}


def barren_plateaus(samples=64):
    rows=[]
    for n in (2,4,6,8,10):
        for depth_label,depth in (('shallow',2),('growing',n)):
            global_z=parity(n,list(range(n)));local_z=parity(n,[0]);grads={'global':[],'local':[]};raw=[]
            rng=np.random.default_rng(9000+n*10+depth)
            for sample in range(samples):
                theta=rng.uniform(-np.pi,np.pi,2*n*depth);shift=np.zeros_like(theta);shift[0]=np.pi/2
                plus=probabilities(hardware_state(theta+shift,n,depth));minus=probabilities(hardware_state(theta-shift,n,depth))
                row={'sample':sample,'theta':theta.tolist()}
                for name,observable in (('global',global_z),('local',local_z)):
                    ep=float(plus@observable);em=float(minus@observable);g=.5*(ep-em);grads[name].append(g)
                    estimates={}
                    for shots in (128,1024):
                        ep_est=2*rng.binomial(shots,np.clip((1+ep)/2,0,1),size=20)/shots-1
                        em_est=2*rng.binomial(shots,np.clip((1+em)/2,0,1),size=20)/shots-1
                        estimates[str(shots)]=(.5*(ep_est-em_est)).tolist()
                    row[name]={'plus':ep,'minus':em,'exact_gradient':g,'shot_gradients':estimates}
                raw.append(row)
            for name in ('global','local'):
                rmse={str(S):float(np.sqrt(np.mean([(estimate-r[name]['exact_gradient'])**2 for r in raw for estimate in r[name]['shot_gradients'][str(S)]]))) for S in (128,1024)}
                rows.append({'n':n,'depth':depth,'depth_label':depth_label,'cost':name,'samples':samples,
                    'gradient_mean':float(np.mean(grads[name])),'gradient_variance':float(np.var(grads[name],ddof=1)),
                    'gradient_rms':float(np.sqrt(np.mean(np.square(grads[name])))),'shot_rmse':rmse,
                    'raw':[{k:r[k] for k in ('sample','theta',name)} for r in raw]})
            print(f'Barren-plateau control: n={n}, depth={depth}',flush=True)
    return rows


def run_benchmark(directory,seeds=(0,1,2,3,4),steps=80,qaoa_maxfev=600,barren_samples=64):
    if not seeds or len(set(seeds))!=len(seeds) or 0 not in seeds:raise ValueError('Unique seeds including canonical seed 0 required')
    if not isinstance(steps,int) or steps<5 or not isinstance(barren_samples,int) or barren_samples<2:raise ValueError('Invalid iteration/sample budgets')
    output=Path(directory)
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output directory')
    output.mkdir(parents=True,exist_ok=True)
    inputs=Path(__file__).resolve().parents[1]/'inputs'/'track_b';problems=load_problems(inputs)
    write_json(output/'environment.json',environment())
    write_json(output/'classical_baselines.json',classical_baselines(problems))
    write_json(output/'protocol.json',{'seeds':list(seeds),'vqe_steps':steps,'qaoa_maxfev':qaoa_maxfev,'barren_samples':barren_samples,
        'simulator':'Authored NumPy exact statevector and density-matrix simulator; dense-matrix independent tests',
        'hardware':'No physical quantum hardware; generic local depolarizing/readout model only',
        'vqe':'Two-qubit synthetic Pauli Hamiltonian, two Ry/Rz-CNOT layers, 8 distinct gate parameters',
        'vqe_comparison':'Same initial parameters and updates per seed, unequal objective/state/metric costs explicitly recorded. No best-run selection for main tables.',
        'qaoa':'Raw Track B Hamiltonian, min-energy convention, gamma in [0,2pi], beta in [0,pi]. Powell local search, all trials retained; no global certificate.',
        'canonical_noise_and_shots':'Seed 0 fixed before inspecting quality. No retraining in the channel-noise post-analysis.',
        'qng':'Full Fubini-Study metric from exact simulator amplitudes with 1e-3 damping and maximum update norm 1. Not a hardware-scalable metric measurement demonstration.',
        'gradients':'Parameter-shift only for distinct single Pauli-rotation parameters; QAOA shared angles use Powell, QNN nonlinear loss uses a classical chain rule.',
        'shots':'Sampled via Born probabilities, not physical device runs. Exact expectations consume zero measurement shots. Cached distributions accelerate repeated sampling.',
        'timing':'CPU simulation timings, not quantum runtime/speedup; no hardware queue/coherence or physical gate times.',
        'qubit_limits':'Statevectors at most 10 in experiments; density matrices at most 6; exponential simulator memory.'})
    reference=hamiltonian();eigenvalues=np.linalg.eigvalsh(reference)
    write_json(output/'vqe_reference.json',{'terms':VQE_TERMS,'eigenvalues':eigenvalues.tolist(),'ground_energy':float(eigenvalues[0]),
        'dimensionless':True,'note':'Synthetic Hamiltonian; not a molecular H2 calculation.'})
    vqe=[]
    for seed in seeds:
        for method in ('ShiftGD','ShiftAdam','SPSA','QNG'):
            run=train_vqe(method,seed,steps);vqe.append(run)
            if run['final_exact_energy']<eigenvalues[0]-1e-9:raise AssertionError('Variational bound violated by exact expectation')
        print(f'VQE seed {seed} complete',flush=True)
    write_json(output/'vqe_runs.json',vqe)
    qaoa=[]
    for name,problem in problems.items():
        for p in (1,2):
            for seed in seeds:qaoa.append(qaoa_train(problem,name,p,seed,qaoa_maxfev))
            print(f'QAOA {name}, p={p} complete',flush=True)
    write_json(output/'qaoa_runs.json',qaoa)
    write_json(output/'shot_study.json',shot_study(problems,qaoa))
    write_json(output/'noise_study.json',noise_study(problems,qaoa,vqe))
    finite=[]
    for shots in (128,1024):
        for seed in seeds[:3]:
            for method in ('ShiftGD','SPSA'):finite.append(train_vqe(method,seed,min(steps,60),shots))
    write_json(output/'finite_shot_training.json',finite)
    qnn=[]
    for seed in seeds[:3]:
        d=qnn_dataset(seed);folder=output/'qnn_data';folder.mkdir(exist_ok=True);np.savez_compressed(folder/f'seed{seed}.npz',**d)
        qnn.append(train_qnn(seed,min(steps,60)));print(f'PQC classifier seed {seed} complete',flush=True)
    write_json(output/'qnn_runs.json',qnn)
    write_json(output/'barren_plateaus.json',barren_plateaus(barren_samples))
    write_json(output/'track_b_sha256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs.glob('*.json'))})
    return {'vqe':vqe,'qaoa':qaoa,'qnn':qnn}
