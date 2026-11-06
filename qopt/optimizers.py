from dataclasses import asdict
from time import perf_counter
import numpy as np

from .models import VQEOracle,parameter_shift,fs_metric


def spsa_gradient(cost,theta,c,rng):
    delta=rng.choice([-1.,1.],size=len(theta))
    gradient=(cost(theta+c*delta)-cost(theta-c*delta))*delta/(2*c)
    return gradient


def train_vqe(method,seed,steps=80,shots=None):
    if method not in ('ShiftGD','ShiftAdam','SPSA','QNG'):raise ValueError('Unknown VQE optimizer')
    rng=np.random.default_rng(seed+1000);theta=rng.uniform(-np.pi/2,np.pi/2,8)
    initial=theta.copy();oracle=VQEOracle(shots,seed+2000);m=np.zeros(8);v=np.zeros(8);trace=[];clipped=0;start=perf_counter()
    def record(k):
        estimate=oracle(theta);exact=estimate if shots is None else oracle.exact(theta)
        trace.append({'step':k,'estimated_energy':estimate,'exact_energy':exact,'theta':theta.tolist(),'work':asdict(oracle.work)})
    record(0)
    for k in range(1,steps+1):
        if method=='SPSA':
            gradient=spsa_gradient(oracle,theta,.1/(k**.101),rng)
            update=.5/((k+10)**.602)*gradient
        else:
            gradient=parameter_shift(oracle,theta)
            if method=='QNG':
                metric=fs_metric(lambda q:oracle.state(q,metric=True),theta)
                update=.08*np.linalg.solve(metric+1e-3*np.eye(8),gradient)
                length=np.linalg.norm(update)
                if length>1:update/=length;clipped+=1
            elif method=='ShiftAdam':
                m=.9*m+.1*gradient;v=.999*v+.001*gradient**2
                update=.08*(m/(1-.9**k))/(np.sqrt(v/(1-.999**k))+1e-8)
            else:update=.15*gradient
        theta-=update
        if not np.all(np.isfinite(theta)):raise AssertionError('Nonfinite optimizer state')
        if k%5==0 or k==steps:record(k)
    return {'method':method,'seed':seed,'shots_per_term':shots,'initial':initial.tolist(),'theta':theta.tolist(),
            'trace':trace,'final_exact_energy':trace[-1]['exact_energy'],'final_estimated_energy':trace[-1]['estimated_energy'],
            'work':asdict(oracle.work),'runtime_s':perf_counter()-start,'qng_limited_steps':clipped}
