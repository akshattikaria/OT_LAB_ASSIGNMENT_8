"""Small explicit statevector circuits and exact parameter-shift Jacobians."""
from functools import lru_cache
import numpy as np


@lru_cache(None)
def pairs(n,wire):
    bit=1<<(n-1-wire);a=np.array([i for i in range(1<<n) if not i&bit]);return a,a|bit


def rotation(state,n,wire,angle,axis):
    a,b=pairs(n,wire);u=state[:,a];v=state[:,b]
    angle=np.asarray(angle);c=np.cos(angle/2);s=np.sin(angle/2)
    if angle.ndim:c=c[:,None];s=s[:,None]
    out=state.copy()
    if axis=='x':out[:,a]=c*u-1j*s*v;out[:,b]=-1j*s*u+c*v
    elif axis=='y':out[:,a]=c*u-s*v;out[:,b]=s*u+c*v
    elif axis=='z':out[:,a]=(c-1j*s)*u;out[:,b]=(c+1j*s)*v
    else:raise ValueError(axis)
    return out


@lru_cache(None)
def cnot_permutation(n,control,target):
    return np.array([i^(1<<(n-1-target)) if i&(1<<(n-1-control)) else i for i in range(1<<n)])


def states(theta,features,n=3,axes='zyx',encoding='y'):
    features=np.atleast_2d(features);theta=np.asarray(theta).reshape(-1,n,len(axes))
    psi=np.zeros((len(features),1<<n),complex);psi[:,0]=1
    for q in range(n):psi=rotation(psi,n,q,features[:,q],encoding)
    for layer in theta:
        for q in range(n):
            for j,axis in enumerate(axes):psi=rotation(psi,n,q,layer[q,j],axis)
        for q in range(n-1):psi=psi[:,cnot_permutation(n,q,q+1)]
        if n>2:psi=psi[:,cnot_permutation(n,n-1,0)]
    return psi


def z_observables(n,masks):
    return np.array([[(-1.)**((i&mask).bit_count()) for mask in masks] for i in range(1<<n)])


def outputs(theta,features,n=3,axes='zyx',encoding='y',masks=None):
    masks=masks or [1<<q for q in range(n)]
    psi=states(theta,features,n,axes,encoding)
    return np.abs(psi)**2@z_observables(n,tuple(masks))


def output_jacobian(theta,features,n=3,axes='zyx',encoding='y',masks=None,with_features=False):
    theta=np.asarray(theta);features=np.atleast_2d(features)
    base=outputs(theta,features,n,axes,encoding,masks)
    jac=np.empty(base.shape+(theta.size,))
    for k in range(theta.size):
        p=theta.copy();m=theta.copy();p.flat[k]+=np.pi/2;m.flat[k]-=np.pi/2
        jac[...,k]=(outputs(p,features,n,axes,encoding,masks)-outputs(m,features,n,axes,encoding,masks))/2
    xjac=None
    if with_features:
        xjac=np.empty(base.shape+(n,))
        for k in range(n):
            p=features.copy();m=features.copy();p[:,k]+=np.pi/2;m[:,k]-=np.pi/2
            xjac[...,k]=(outputs(theta,p,n,axes,encoding,masks)-outputs(theta,m,n,axes,encoding,masks))/2
    return base,jac,xjac


def ising_diagonal(n):
    z=z_observables(n,tuple(1<<q for q in range(n)))
    return sum((z[:,q]*z[:,(q+1)%n]-1)/2 for q in range(n))+.13*z[:,0]


def energy(theta,n=3,shots=None,rng=None):
    psi=states(theta,np.zeros((1,n)),n)[0];p=np.abs(psi)**2;diagonal=ising_diagonal(n)
    if shots is not None:return float(diagonal[rng.choice(len(p),size=shots,p=p)].mean())
    return float(p@diagonal)


def energy_gradient(theta,n=3,shots=None,rng=None):
    g=np.empty_like(theta)
    for k in range(theta.size):
        p=theta.copy();m=theta.copy();p.flat[k]+=np.pi/2;m.flat[k]-=np.pi/2
        g.flat[k]=(energy(p,n,shots,rng)-energy(m,n,shots,rng))/2
    return g


def block_encoding(k):
    """Julia dilation; ancilla-0 branch is the non-unitary gradient filter K."""
    k=np.asarray(k,dtype=complex)
    if not np.allclose(k,k.conj().T):raise ValueError('Hermitian contraction required')
    eig,v=np.linalg.eigh(k)
    if np.max(np.abs(eig))>1+1e-10:raise ValueError('Not a contraction')
    root=(v*np.sqrt(np.maximum(0,1-eig*eig)))@v.conj().T
    return np.block([[k,root],[root,-k]])
