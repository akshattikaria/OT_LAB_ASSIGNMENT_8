"""Full-participation FedAvg with unequal client sizes and explicit accounting."""
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def data(seed):
    rng=np.random.default_rng(seed+2000);teacher=np.array([1.2,-.9,.6,.3,-.4,.7,.1])
    def sample(n):
        X=np.column_stack((rng.normal(size=(n,6)),np.ones(n)))
        y=rng.binomial(1,expit(X@teacher)).astype(float)
        return X,y
    X,y=sample(512);Xt,yt=sample(256)
    return {'Xtrain':X,'ytrain':y,'Xtest':Xt,'ytest':yt,'initial':rng.normal(scale=.1,size=7)}


def partition(y,kind,seed):
    sizes=(64,96,160,192)
    indices=np.random.default_rng(seed+2100).permutation(len(y))
    if kind=='label_skew':indices=indices[np.argsort(y[indices],kind='stable')]
    elif kind!='iid':raise ValueError('Unknown partition')
    if len(y)!=sum(sizes):raise ValueError('Expected 512 training examples')
    return [chunk.copy() for chunk in np.split(indices,np.cumsum(sizes)[:-1])]


def objective(w,X,y,l2=.01):
    z=X@w;mask=np.ones(len(w));mask[-1]=0
    value=np.mean(np.logaddexp(0,z)-y*z)+.5*l2*np.sum((w*mask)**2)
    gradient=X.T@(expit(z)-y)/len(y)+l2*w*mask
    return float(value),gradient


def aggregate(models,sizes):
    sizes=np.asarray(sizes,dtype=float);models=np.asarray(models,dtype=float)
    if models.ndim!=2 or len(models)!=len(sizes) or np.any(sizes<=0) or not np.all(np.isfinite(models)):raise ValueError('Invalid aggregation inputs')
    return np.average(models,axis=0,weights=sizes)


def metrics(w,d):
    value,_=objective(w,d['Xtrain'],d['ytrain']);z=d['Xtest']@w
    return {'train_objective':value,'test_logloss':float(np.mean(np.logaddexp(0,z)-d['ytest']*z)),
            'test_accuracy':float(np.mean((z>=0)==d['ytest']))}


def centralized(d,steps,rate=.2):
    w=d['initial'].copy();trace=[];clock=perf_counter()
    for k in range(steps+1):
        if k==0 or k==steps or k%max(1,steps//20)==0:trace.append({'step':k,'theta':w.tolist(),**metrics(w,d)})
        if k<steps:w-=rate*objective(w,d['Xtrain'],d['ytrain'])[1]
    return {'method':'centralized','steps':steps,'theta':w.tolist(),'trace':trace,'sample_visits':steps*len(d['ytrain']),
        'gradient_calls':steps,'runtime_s':perf_counter()-clock,**metrics(w,d)}


def fedavg(d,clients,local_steps,rounds,rate=.2):
    if local_steps<1 or rounds<1:raise ValueError('Positive local-step and round budgets required')
    joined=np.concatenate(clients)
    if sorted(joined.tolist())!=list(range(len(d['ytrain']))):raise ValueError('Clients must partition the training data exactly once')
    w=d['initial'].copy();sizes=[len(c) for c in clients];trace=[{'round':0,'local_passes':0,'theta':w.tolist(),'drift':0.,**metrics(w,d)}];clock=perf_counter()
    for r in range(1,rounds+1):
        models=[]
        for client in clients:
            local=w.copy()
            for k in range(local_steps):local-=rate*objective(local,d['Xtrain'][client],d['ytrain'][client])[1]
            models.append(local)
        drift=float(np.average([np.linalg.norm(local-w) for local in models],weights=sizes));w=aggregate(models,sizes)
        trace.append({'round':r,'local_passes':r*local_steps,'theta':w.tolist(),'drift':drift,**metrics(w,d)})
    return {'method':'FedAvg','local_steps':local_steps,'rounds':rounds,'theta':w.tolist(),'trace':trace,
        'sample_visits':rounds*local_steps*sum(sizes),'gradient_calls':rounds*local_steps*len(clients),
        'logical_model_bytes':2*len(clients)*len(w)*8*rounds,'runtime_s':perf_counter()-clock,**metrics(w,d)}


def reference(d):
    result=minimize(lambda w:objective(w,d['Xtrain'],d['ytrain']),d['initial'],jac=True,method='L-BFGS-B',options={'gtol':1e-10,'ftol':1e-14,'maxiter':1000})
    return {'theta':result.x.tolist(),'success':bool(result.success),'objective':float(result.fun),**metrics(result.x,d)}
