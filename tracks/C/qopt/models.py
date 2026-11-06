from dataclasses import dataclass,field
import json
from pathlib import Path
import numpy as np

from .simulator import hardware_state,hardware_gates,statevector,one,rotation,probabilities,measured_pauli,pauli_expectation,dense_pauli

VQE_TERMS=[(.7,[(0,'Z')]),(.3,[(1,'Z')]),(.6,[(0,'X'),(1,'X')]),(-.2,[(0,'Z'),(1,'Z')])]


def hamiltonian():return sum((c*dense_pauli(2,term) for c,term in VQE_TERMS),np.zeros((4,4),dtype=complex))


@dataclass
class Work:
    objective_calls:int=0
    state_preparations:int=0
    metric_preparations:int=0
    diagnostic_preparations:int=0
    measurement_circuits:int=0
    shots:int=0


class VQEOracle:
    def __init__(self,shots=None,seed=0):
        self.shots=shots;self.rng=np.random.default_rng(seed);self.work=Work();self.n=2;self.depth=2;self.d=8
    def state(self,theta,metric=False):
        self.work.state_preparations+=1;self.work.metric_preparations+=int(metric)
        return hardware_state(theta,self.n,self.depth)
    def __call__(self,theta):
        self.work.objective_calls+=1;state=self.state(theta)
        if self.shots is None:return sum(c*pauli_expectation(state,term) for c,term in VQE_TERMS)
        self.work.measurement_circuits+=len(VQE_TERMS);self.work.shots+=len(VQE_TERMS)*self.shots
        return sum(c*measured_pauli(state,term,self.shots,self.rng) for c,term in VQE_TERMS)
    def exact(self,theta):
        self.work.diagnostic_preparations+=1;state=hardware_state(theta,2,2)
        return float(np.real(np.vdot(state,hamiltonian()@state)))


def parameter_shift(expectation,theta):
    """Only for parameters occurring once in a standard Pauli rotation."""
    gradient=np.empty(len(theta))
    for i in range(len(theta)):
        shift=np.zeros(len(theta));shift[i]=np.pi/2
        gradient[i]=.5*(expectation(theta+shift)-expectation(theta-shift))
    return gradient


def fs_metric(state_function,theta):
    """Exact simulator metric; state derivative shift has factor 1/(2*sqrt(2))."""
    psi=state_function(theta);derivatives=[]
    for i in range(len(theta)):
        shift=np.zeros(len(theta));shift[i]=np.pi/2
        derivatives.append((state_function(theta+shift)-state_function(theta-shift))/(2*np.sqrt(2)))
    D=np.stack(derivatives,axis=1);overlap=D.conj().T@psi
    metric=np.real(D.conj().T@D-np.outer(overlap,overlap.conj()))
    metric=(metric+metric.T)/2
    if np.linalg.eigvalsh(metric)[0]<-1e-9:raise AssertionError('Fubini-Study metric is not PSD')
    return metric


class DiagonalProblem:
    def __init__(self,model_path,classical_path):
        self.model=json.loads(Path(model_path).read_text());self.classical=json.loads(Path(classical_path).read_text())
        self.n=len(self.model['variables']);self.Q=np.array(self.model['Q_upper']);self.offset=self.model['offset']
        if self.Q.shape!=(self.n,self.n) or np.any(np.tril(self.Q,-1)!=0):raise ValueError('Bad upper-triangular QUBO')
        self.states=np.array([[(index>>q)&1 for q in range(self.n)] for index in range(1<<self.n)])
        self.energies=self.offset+np.einsum('bi,ij,bj->b',self.states,self.Q,self.states)
        ising=self.model['ising'];self.h=np.array(ising['h']);self.J=np.array(ising['J_upper']);self.ising_offset=ising['offset']
        spin=1-2*self.states
        other=self.ising_offset+spin@self.h+np.einsum('bi,ij,bj->b',spin,self.J,spin)
        saved=np.array([s['energy'] for s in self.classical['states']])
        if not np.allclose(self.energies,other,atol=1e-9) or not np.allclose(self.energies,saved,atol=1e-9):raise AssertionError('Track B energy mismatch')
        self.minimum=float(np.min(self.energies));self.ground=np.isclose(self.energies,self.minimum,atol=1e-9)
        self.original_feasible=np.array([s['original_feasible'] for s in self.classical['states']])
        self.encoded_feasible=np.array([s['encoded_feasible'] for s in self.classical['states']])
        self.utility=np.array([s.get('value',s.get('cut')) for s in self.classical['states']],dtype=float)
    def metrics(self,prob):
        return {'expected_energy':float(prob@self.energies),'ground_probability':float(prob@self.ground),
                'original_feasibility_probability':float(prob@self.original_feasible),
                'encoded_feasibility_probability':float(prob@self.encoded_feasible)}
    def qaoa_state(self,theta,p):
        theta=np.asarray(theta)
        if theta.shape!=(2*p,) or not np.all(np.isfinite(theta)):raise ValueError('Wrong QAOA parameter vector')
        state=np.ones(1<<self.n,dtype=complex)/np.sqrt(1<<self.n)
        for layer in range(p):
            state*=np.exp(-1j*theta[layer]*self.energies)
            for q in range(self.n):state=one(state,q,rotation('X',2*theta[p+layer]))
        return state
    def qaoa_gates(self,theta,p):
        gates=[('h',q) for q in range(self.n)]
        for layer in range(p):
            gamma=theta[layer];beta=theta[p+layer]
            for q,value in enumerate(self.h):
                if abs(value)>1e-14:gates.append(('rz',q,2*gamma*value))
            for i in range(self.n):
                for j in range(i+1,self.n):
                    if abs(self.J[i,j])>1e-14:gates.extend((('cx',i,j),('rz',j,2*gamma*self.J[i,j]),('cx',i,j)))
            gates.extend(('rx',q,2*beta) for q in range(self.n))
        return gates  # Constant energy shift is a global phase, absent from gates only.
