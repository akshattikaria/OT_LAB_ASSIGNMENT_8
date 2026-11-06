"""Executable small instances of four source-specific quantum training ideas."""
import time
from functools import reduce
import numpy as np
from scipy.optimize import minimize
from .common import Adam,softmax
from .quantum import states,energy,energy_gradient,output_jacobian,outputs,block_encoding


def tt_generate(cores,z,length):
    # Rank-one TT-matrix specialization, with Gaussian input as in paper Eq. 2.
    return (reduce(np.kron,cores)@z)[:length]


def tt_pullback(cores,z,gradient):
    result=np.zeros_like(cores)
    for k in range(len(cores)):
        for i in range(2):
            for j in range(2):
                factors=[g.copy() for g in cores];factors[k]=np.zeros((2,2));factors[k][i,j]=1
                result[k,i,j]=gradient@(reduce(np.kron,factors)@z)[:len(gradient)]
    return result


def tensorhyper():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(300+seed);initial=rng.normal(scale=.2,size=27)
        # This is a shared initial distribution, not matched initial states:
        # the architectures impose different feasible parameter manifolds.
        cores=np.stack([np.eye(2)+rng.normal(scale=.12,size=(2,2)) for _ in range(5)])
        for method in ['direct','tt_hypernetwork']:
            variable=initial.copy() if method=='direct' else cores.copy();opt=Adam(variable.shape,.025);trace=[];start=time.perf_counter();noise_rng=np.random.default_rng(700+seed)
            for step in range(120):
                z=noise_rng.normal(size=32)
                theta=variable if method=='direct' else tt_generate(variable,z,27)
                value=energy(theta);g=energy_gradient(theta)
                gradient=g if method=='direct' else tt_pullback(variable,z,g)
                variable=opt.step(variable,gradient)
                trace.append({'step':step,'energy':value,'gradient_norm':float(np.linalg.norm(gradient))})
            elapsed=time.perf_counter()-start
            eval_z=np.random.default_rng(999).normal(size=(20,32))
            energies=[energy(variable if method=='direct' else tt_generate(variable,z,27)) for z in eval_z]
            rows.append({'seed':seed,'method':method,'trainable_scalars':int(variable.size),'final_evaluation_mean':float(np.mean(energies)),'final_evaluation_std':float(np.std(energies)),'training_s':elapsed,'trace':trace,'final_variables':variable,'evaluation_noise_seed':999})
    return {'runs':rows,'scope':'TensorHyper Eq. 1/2 parameter generation: rank-one TT-matrix, Gaussian noise, classical core-chain rule and fixed 3-qubit/3-layer evaluator. Exact statevector parameter-shift supplies the derivative to the classical chain rule. This small specialization does not establish the paper NTK bounds, noise resilience or hardware results; distinct initial parameter manifolds are disclosed.'}


def negative_learning():
    rows=[]
    for seed in range(5):
        initial=np.random.default_rng(1000+seed).normal(scale=.1,size=18)
        for method in ['descent','source_negative_rule']:
            theta=initial.copy();rng=np.random.default_rng(1700+seed);trace=[];start=time.perf_counter()
            for step in range(100):
                current=energy(theta);g=energy_gradient(theta,shots=256,rng=rng)
                candidate=theta-.08*g;tentative=energy(candidate);negative=method=='source_negative_rule' and tentative>current
                theta=theta+.02*g if negative else candidate
                trace.append({'step':step,'energy':current,'tentative_energy':tentative,'negative_step':negative,'gradient_norm':float(np.linalg.norm(g)),'result_energy':energy(theta)})
            rows.append({'seed':seed,'method':method,'final_energy':energy(theta),'negative_steps':sum(r['negative_step'] for r in trace),'training_s':time.perf_counter()-start,'trace':trace,'final_angles':theta})
    return {'runs':rows,'scope':'Rahman/Nguyen Algorithm 1, including the loss-triggered ascent branch, not an arbitrary periodic schedule. 3 qubits, 2 layers, 256-shot gradient measurements, exact acceptance losses as allowed by the analysis. Negative steps need not improve loss; all deterioration is retained. No QIoT hardware or general barren-plateau escape claim.'}


def qmt():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(2000+seed);centers=rng.uniform(-2.5,2.5,size=(6,3))
        y=np.repeat(np.arange(6),20);x=centers[y]+rng.normal(scale=.3,size=(len(y),3))
        ids=np.arange(len(y));train=np.concatenate([ids[y==c][:12] for c in range(6)]);test=np.setdiff1d(ids,train)
        theta0=rng.normal(scale=.15,size=18)
        for method in ['fixed_temperature','learned_temperature']:
            theta=theta0.copy();logt=np.array(0.);opt=Adam(theta.shape,.025);topt=Adam((),.025);trace=[];start=time.perf_counter()
            for step in range(100):
                z,jac,_=output_jacobian(theta,x[train],masks=[1,2,3,4,5,6]);scaled=z/np.exp(logt);p=softmax(scaled)
                loss=float(-np.log(p[np.arange(len(train)),y[train]]+1e-15).mean());d=p.copy();d[np.arange(len(train)),y[train]]-=1;d/=len(train)
                gradient=np.einsum('bc,bcp->p',d/np.exp(logt),jac)
                temp_gradient=-np.sum(d*scaled)
                theta=opt.step(theta,gradient)
                if method=='learned_temperature':logt=np.clip(topt.step(logt,temp_gradient),-4,3)
                trace.append({'step':step,'loss':loss,'temperature':float(np.exp(logt)),'gradient_norm':float(np.linalg.norm(gradient))})
            probabilities=softmax(outputs(theta,x[test],masks=[1,2,3,4,5,6])/np.exp(logt))
            rows.append({'seed':seed,'method':method,'temperature':float(np.exp(logt)),'test_accuracy':float(np.mean(probabilities.argmax(1)==y[test])),'test_cross_entropy':float(-np.log(probabilities[np.arange(len(test)),y[test]]+1e-15).mean()),'training_s':time.perf_counter()-start,'train_indices':train,'test_indices':test,'features':x,'labels':y,'final_angles':theta,'trace':trace})
    return {'runs':rows,'scope':'Mondal et al. Section 3.4: jointly learn positive T via log T and circuit angles, logits z/T before softmax. Fixed vs learned T share initial angles, data and 100 updates. Synthetic six-class data and six bounded Pauli-Z product readouts; no microscopy/Fashion-MNIST reproduction or medical inference.'}


def nom():
    rows=[]
    h=np.array([[.4,.3,0,0],[.3,-.5,.2,0],[0,.2,-.8,.4],[0,0,.4,.2]])
    eigen=np.linalg.eigvalsh(h);xi=.12;k=np.eye(4)-xi*h;scale=np.linalg.norm(k,2);k/=scale;unitary=block_encoding(k)
    for seed in range(5):
        theta=np.random.default_rng(2900+seed).normal(scale=.2,size=8);trace=[]
        for step in range(12):
            psi=states(theta,np.zeros((1,2)),n=2,axes='y')[0]
            extended=unitary@np.r_[psi,np.zeros(4)];branch=extended[:4];prob=float(np.vdot(branch,branch).real);target=branch/np.sqrt(prob)
            def loss(a):
                candidate=states(a,np.zeros((1,2)),n=2,axes='y')[0]
                return float(1-abs(np.vdot(target,candidate))**2)
            fit=minimize(loss,theta,method='BFGS',options={'gtol':1e-8,'maxiter':80});theta=fit.x
            fitted=states(theta,np.zeros((1,2)),n=2,axes='y')[0]
            trace.append({'step':step,'energy_before':float(np.vdot(psi,h@psi).real),'energy_after':float(np.vdot(fitted,h@fitted).real),'postselection_probability':prob,'fit_infidelity':loss(theta),'fit_success':bool(fit.success),'fit_evaluations':fit.nfev})
        rows.append({'seed':seed,'final_energy':trace[-1]['energy_after'],'exact_ground_energy':float(eigen[0]),'ground_energy_gap':trace[-1]['energy_after']-float(eigen[0]),'trace':trace,'final_angles':theta})
    return {'runs':rows,'hamiltonian':h,'step_size':xi,'block_encoding_scale':scale,'unitarity_error':float(np.linalg.norm(unitary.conj().T@unitary-np.eye(8))),'scope':'Li et al. NOM Table 1, p=1 Hermitian-quadratic specialization. Actual ancilla dilation and postselected gradient-filter state, followed by PQC fidelity fitting. Dense 8x8 simulator replaces the paper scalable sparse-oracle/LCU implementation; fixed real ansatz replaces RL structure search. Quantum query or runtime advantage is not claimed.'}
