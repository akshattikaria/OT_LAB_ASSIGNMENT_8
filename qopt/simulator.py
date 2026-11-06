"""Little-endian statevector/density simulator, with explicit local noise."""
from functools import lru_cache
import numpy as np

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],dtype=complex)
Y=np.array([[0,-1j],[1j,0]],dtype=complex)
Z=np.diag([1,-1]).astype(complex)
H=np.array([[1,1],[1,-1]],dtype=complex)/np.sqrt(2)
S_DAG=np.diag([1,-1j])
PAULI={'I':I,'X':X,'Y':Y,'Z':Z}


def zero(n):
    if not isinstance(n,int) or not 1<=n<=12:raise ValueError('Statevector n must be 1..12')
    v=np.zeros(1<<n,dtype=complex);v[0]=1;return v


def rotation(axis,angle):
    if axis not in ('X','Y','Z') or not np.isfinite(angle):raise ValueError('Invalid rotation')
    return np.cos(angle/2)*I-1j*np.sin(angle/2)*PAULI[axis]


def one(state,q,U):
    """Apply a 2x2 matrix to qubit q along the last statevector axis."""
    v=np.asarray(state,dtype=complex);d=v.shape[-1]
    if d<2 or d&(d-1) or not isinstance(q,int) or not 0<=q<d.bit_length()-1:raise ValueError('Invalid state dimension or qubit')
    if np.shape(U)!=(2,2):raise ValueError('Gate must be 2x2')
    blocks=v.reshape(-1,2,1<<q);a=blocks[:,0,:];b=blocks[:,1,:]
    out=np.empty_like(blocks);out[:,0,:]=U[0,0]*a+U[0,1]*b;out[:,1,:]=U[1,0]*a+U[1,1]*b
    return out.reshape(v.shape)


@lru_cache(maxsize=512)
def cx_permutation(n,control,target):
    if control==target or not 0<=control<n or not 0<=target<n:raise ValueError('Invalid CNOT qubits')
    indices=np.arange(1<<n);return indices^(((indices>>control)&1)*(1<<target))


def cx(state,control,target):
    d=state.shape[-1];return state[...,cx_permutation(d.bit_length()-1,control,target)]


def gate_unitary(gate):
    name=gate[0]
    if name=='h':return H
    if name=='sdg':return S_DAG
    if name in ('rx','ry','rz'):return rotation(name[-1].upper(),gate[2])
    raise ValueError('Unknown single-qubit gate')


def statevector(n,gates):
    state=zero(n)
    for gate in gates:
        state=cx(state,gate[1],gate[2]) if gate[0]=='cx' else one(state,gate[1],gate_unitary(gate))
    return state


def probabilities(state):
    if state.ndim==1:prob=np.abs(state)**2
    elif state.ndim==2:prob=np.real(np.diag(state))
    else:raise ValueError('State must be vector or density matrix')
    if not np.all(np.isfinite(prob)) or np.min(prob)<-1e-10 or abs(prob.sum()-1)>1e-8:
        raise ValueError('Invalid state probabilities/normalization')
    prob=np.maximum(prob,0);return prob/prob.sum()


def density_one(rho,q,U):
    left=one(rho.T,q,U).T
    return one(left,q,U.conj())


def depolarize(rho,q,p):
    if not 0<=p<=1:raise ValueError('Depolarizing strength must be 0..1')
    if not p:return rho
    return (1-3*p/4)*rho+(p/4)*sum((density_one(rho,q,P) for P in (X,Y,Z)),np.zeros_like(rho))


def density(n,gates,noise=0.0):
    if n>6:raise ValueError('Density simulator is limited to six qubits')
    state=zero(n);rho=np.outer(state,state.conj())
    for gate in gates:
        if gate[0]=='cx':
            perm=cx_permutation(n,gate[1],gate[2]);rho=rho[np.ix_(perm,perm)];qubits=gate[1:3]
        else:rho=density_one(rho,gate[1],gate_unitary(gate));qubits=(gate[1],)
        for q in qubits:rho=depolarize(rho,q,noise)
    if np.linalg.norm(rho-rho.conj().T)>1e-8 or abs(np.trace(rho)-1)>1e-8:raise AssertionError('Density trace/Hermiticity failure')
    return rho


def readout(prob,n,p):
    if not 0<=p<=1:raise ValueError('Readout error must be 0..1')
    result=np.asarray(prob,dtype=float).copy();indices=np.arange(1<<n)
    for q in range(n):result=(1-p)*result+p*result[indices^(1<<q)]
    return result


def parity(n,qubits):
    result=np.ones(1<<n);indices=np.arange(1<<n)
    for q in qubits:result*=1-2*((indices>>q)&1)
    return result


def pauli_expectation(state,term):
    if state.ndim==1:
        transformed=state
        for q,axis in term:transformed=one(transformed,q,PAULI[axis])
        return float(np.real(np.vdot(state,transformed)))
    transformed=state
    for q,axis in term:transformed=one(transformed.T,q,PAULI[axis]).T
    return float(np.real(np.trace(transformed)))


def measured_pauli(state,term,shots,rng,readout_error=0):
    n=(state.shape[-1]).bit_length()-1;rotated=state
    for q,axis in term:
        gates=[S_DAG,H] if axis=='Y' else [H] if axis=='X' else []
        for U in gates:rotated=one(rotated,q,U) if state.ndim==1 else density_one(rotated,q,U)
    prob=readout(probabilities(rotated),n,readout_error)
    if shots is None:return float(prob@parity(n,[q for q,_ in term]))
    if not isinstance(shots,int) or shots<1:raise ValueError('shots must be a positive integer')
    counts=rng.multinomial(shots,prob)
    return float(counts@parity(n,[q for q,_ in term])/shots)


def hardware_gates(theta,n,depth,features=None):
    theta=np.asarray(theta,dtype=float)
    if theta.shape!=(2*n*depth,) or not np.all(np.isfinite(theta)):raise ValueError('Wrong ansatz parameters')
    gates=[]
    if features is not None:
        if len(features)!=n:raise ValueError('One encoded feature per qubit required')
        gates.extend(('ry',q,float(features[q])) for q in range(n))
    index=0
    for layer in range(depth):
        for q in range(n):
            gates.extend((('ry',q,float(theta[index])),('rz',q,float(theta[index+1]))));index+=2
        gates.extend(('cx',q,q+1) for q in range(n-1))
    return gates


def hardware_state(theta,n,depth,features=None):return statevector(n,hardware_gates(theta,n,depth,features))


def dense_pauli(n,term):
    mapping=dict(term);matrix=np.array([[1]],dtype=complex)
    for q in range(n-1,-1,-1):matrix=np.kron(matrix,PAULI.get(mapping.get(q,'I'),I))
    return matrix
