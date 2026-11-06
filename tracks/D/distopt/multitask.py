"""Two related regression tasks sharing all coefficients; fixed identity readouts."""
from time import perf_counter
import numpy as np


def data(seed,family):
    rng=np.random.default_rng(seed+3000);v1=np.array([1,.5,-.3,0.,0.,0.,.1]);v2=v1.copy()
    if family.startswith('conflict'):v2=np.array([-1,.5,.3,0.,0.,0.,-.1])
    elif family=='aligned_10x':v2+=np.array([.2,0,.1,0,0,0,0])
    else:raise ValueError('Unknown task family')
    def sample(n):
        X=np.column_stack((rng.normal(size=(n,6)),np.ones(n)))
        Y=X@np.column_stack((v1,v2))+rng.normal(scale=.1,size=(n,2))
        return X,Y
    X,Y=sample(256);Xt,Yt=sample(256)
    scales=np.array([1.,1. if family=='conflict_equal' else 10.])
    return {'Xtrain':X,'Ytrain':Y,'Xtest':Xt,'Ytest':Yt,'scales':scales,'initial':rng.normal(scale=.15,size=7)}


def losses_gradients(w,X,Y,scales):
    residual=(X@w)[:,None]-Y
    losses=.5*np.mean(residual**2,axis=0)*scales
    gradients=(X.T@residual/len(X)).T*scales[:,None]
    return losses,gradients


def mgda_weights(gradients):
    g1,g2=np.asarray(gradients);difference=g1-g2;denominator=float(difference@difference)
    alpha=.5 if denominator<1e-24 else float(np.clip(-g2@difference/denominator,0,1))
    return np.array([2*alpha,2*(1-alpha)]) # Sum two, matching equal-weight step scale.


def gradnorm_update(weights,gradients,losses,initial_losses,rate=.01,alpha=1.5):
    norms=np.linalg.norm(gradients,axis=1);G=weights*norms
    ratios=losses/np.maximum(initial_losses,1e-15);inverse_rate=ratios/np.mean(ratios)
    targets=np.mean(G)*inverse_rate**alpha
    # Targets are stop-gradient constants in the GradNorm weight objective.
    gradient_weights=np.sign(G-targets)*norms
    updated=np.maximum(weights-rate*gradient_weights,1e-6);updated*=2/updated.sum()
    return updated,{'G':G.tolist(),'targets':targets.tolist(),'weight_gradient':gradient_weights.tolist(),'gradnorm_loss':float(np.sum(abs(G-targets)))}


def metrics(w,d):
    losses,_=losses_gradients(w,d['Xtrain'],d['Ytrain'],d['scales'])
    error=(d['Xtest']@w)[:,None]-d['Ytest']
    return {'train_losses':losses.tolist(),'test_mse':np.mean(error**2,axis=0).tolist()}


def train(d,method,steps=400,rate=.03):
    if method not in ('Equal','MGDA','GradNorm'):raise ValueError('Unknown multi-task method')
    w=d['initial'].copy();weights=np.ones(2);initial_losses,_=losses_gradients(w,d['Xtrain'],d['Ytrain'],d['scales']);trace=[];clock=perf_counter();updates=[]
    for step in range(steps+1):
        losses,gradients=losses_gradients(w,d['Xtrain'],d['Ytrain'],d['scales'])
        if method=='MGDA':weights=mgda_weights(gradients)
        if step==0 or step%10==0 or step==steps:
            norm_product=np.linalg.norm(gradients[0])*np.linalg.norm(gradients[1])
            trace.append({'step':step,'theta':w.tolist(),'weights':weights.tolist(),**metrics(w,d),
                'gradient_cosine':float(gradients[0]@gradients[1]/max(norm_product,1e-15)),
                'mgda_stationarity_norm':float(np.linalg.norm(mgda_weights(gradients)@gradients/2))})
        if step==steps:break
        update=weights@gradients
        if method=='GradNorm':weights,record=gradnorm_update(weights,gradients,losses,initial_losses);updates.append({'step':step,**record})
        w-=rate*update
        if not np.all(np.isfinite(w)):raise AssertionError('Nonfinite multi-task update')
    separate=[]
    for task in range(2):
        coef=np.linalg.lstsq(d['Xtrain'],d['Ytrain'][:,task],rcond=None)[0]
        separate.append(float(np.mean((d['Xtest']@coef-d['Ytest'][:,task])**2)))
    return {'method':method,'steps':steps,'theta':w.tolist(),'weights':weights.tolist(),'trace':trace,
        'weight_updates':updates,'runtime_s':perf_counter()-clock,'gradient_calls':2*steps,
        'single_task_test_mse':separate,**metrics(w,d)}
