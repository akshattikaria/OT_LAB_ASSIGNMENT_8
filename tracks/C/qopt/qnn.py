"""A data-encoded PQC classifier; shift expectations, then apply loss chain rule."""
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from .simulator import hardware_state,pauli_expectation


def dataset(seed):
    rng=np.random.default_rng(seed+5000)
    X=rng.uniform(-1,1,(24,2));test=rng.uniform(-1,1,(64,2))
    y=(X[:,0]+.5*X[:,1]>0).astype(float);yt=(test[:,0]+.5*test[:,1]>0).astype(float)
    return {'Xtrain':X,'ytrain':y,'Xtest':test,'ytest':yt}


def outputs(theta,X,work=None):
    if work is not None:work['state_preparations']+=len(X)
    return np.array([pauli_expectation(hardware_state(theta,2,2,np.pi*x/2),[(0,'Z')]) for x in X])


def loss_and_gradient(theta,X,y,work=None):
    z=outputs(theta,X,work);prob=.02+.96*(1-z)/2
    loss=float(np.mean(-y*np.log(prob)-(1-y)*np.log(1-prob)))
    multiplier=(prob-y)/(prob*(1-prob))*(-.48)
    g=np.empty(len(theta))
    for j in range(len(theta)):
        delta=np.zeros(len(theta));delta[j]=np.pi/2
        dz=.5*(outputs(theta+delta,X,work)-outputs(theta-delta,X,work))
        g[j]=np.mean(multiplier*dz)
    return loss,g


def train(seed,steps=60):
    data=dataset(seed);rng=np.random.default_rng(seed+6000);theta=rng.normal(scale=.3,size=8)
    initial=theta.copy();work={'state_preparations':0};trace=[];m=np.zeros(8);v=np.zeros(8);start=perf_counter()
    def metrics(X,y):
        z=outputs(theta,X,work);p=.02+.96*(1-z)/2
        return {'loss':float(np.mean(-y*np.log(p)-(1-y)*np.log(1-p))),'accuracy':float(np.mean((p>=.5)==y))}
    trace.append({'step':0,**metrics(data['Xtrain'],data['ytrain'])})
    for k in range(1,steps+1):
        indices=rng.choice(len(data['Xtrain']),8,replace=False)
        _,g=loss_and_gradient(theta,data['Xtrain'][indices],data['ytrain'][indices],work)
        m=.9*m+.1*g;v=.999*v+.001*g*g;theta-=.08*(m/(1-.9**k))/(np.sqrt(v/(1-.999**k))+1e-8)
        if k%5==0 or k==steps:trace.append({'step':k,**metrics(data['Xtrain'],data['ytrain'])})
    test=metrics(data['Xtest'],data['ytest']);seconds=perf_counter()-start
    # A transparent strong classical baseline for this deliberately linear task.
    A=np.column_stack((np.ones(24),data['Xtrain']));At=np.column_stack((np.ones(64),data['Xtest']));y=data['ytrain']
    def value(w):
        z=A@w;return float(np.mean(np.logaddexp(0,z)-y*z)+.0005*(w@w))
    def grad(w):return A.T@(expit(A@w)-y)/len(y)+.001*w
    clock=perf_counter();reference=minimize(value,np.zeros(3),jac=grad,method='L-BFGS-B',options={'maxiter':200,'gtol':1e-10,'ftol':1e-13})
    classical={'parameters':3,'theta':reference.x.tolist(),'test_accuracy':float(np.mean((At@reference.x>=0)==data['ytest'])),
               'runtime_s':perf_counter()-clock,'objective':float(reference.fun),'success':bool(reference.success),'nfev':int(reference.nfev)}
    return {'seed':seed,'parameters':8,'initial':initial.tolist(),'theta':theta.tolist(),'trace':trace,
            'test':test,'work':work,'runtime_s':seconds,'classical_logistic':classical}
