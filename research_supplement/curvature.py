"""One-layer specializations of GRNG and AdaFisher; no big-model claim.

GRNG: Dash et al., AISTATS 2026, Eq. 10 and Appendix B Algorithms 1/2.
AdaFisher: Gomes et al., ICLR 2025, Eq. 3/4 and Algorithm 1.
"""
import time
import numpy as np
from .common import sigmoid,softmax,Adam


def logistic(w,x,y,ridge=.01):
    p=sigmoid(x@w);g=x.T@(p-y)/len(y)+ridge*w
    h=(x.T*(p*(1-p)))@x/len(y)+ridge*np.eye(len(w))
    loss=np.mean(np.logaddexp(0,x@w)-y*(x@w))+ridge*(w@w)/2
    return float(loss),g,h


def minmax(v):
    v=np.asarray(v);span=float(np.ptp(v))
    return (v-v.min())/(span+1e-12)


def grng_direction(x,p,g,h,method,rho=.05):
    activation=x.T@x/len(x)
    error=float(np.mean(p*(1-p)))  # exact model-Fisher expectation, no label draw
    if method=='ring':
        da=np.sqrt(rho)*np.linalg.norm(activation,2);de=np.sqrt(rho)*abs(error)
        numerator=g
    elif method=='reng':
        da=de=np.sqrt(rho)
        # Analytic double-backprop for L + rho/2 ||grad L||².
        numerator=g+rho*(h@g)
    else:raise ValueError(method)
    return np.linalg.solve(activation+da*np.eye(len(g)),numerator)/(error+de)


def regularized_kalman(x,y,rho=.05,beta=.8):
    """Exact scalar-output linear-model specialization of Appendix B Alg. 2."""
    mu=np.zeros(x.shape[1]);cov=np.eye(x.shape[1]);r=0.;rows=[]
    for row,target in zip(x,y):
        prediction=float(row@mu);residual=float(target-prediction)
        rhat=residual**2+float(row@cov@row)
        r=beta*r+(1-beta)*rhat
        effective_noise=r/(1+rho*r)
        gain=cov@row/(float(row@cov@row)+effective_noise)
        mu=mu+gain*residual
        cov=cov-np.outer(gain,row@cov);cov=(cov+cov.T)/2
        rows.append({'squared_residual':residual**2,'min_cov_eigenvalue':float(np.linalg.eigvalsh(cov).min()),'noise':r})
    return mu,cov,rows


def run():
    rows=[]
    for seed in [241070005,241070006,241070007,241070008,241070009]:
        rng=np.random.default_rng(seed);x=rng.normal(size=(100,4))*np.array([.2,.6,1.,2.])
        truth=np.array([1.,-.5,.8,-.3]);y=rng.binomial(1,sigmoid(x@truth))
        w0=rng.normal(scale=.1,size=4)
        from scipy.optimize import minimize
        ref=minimize(lambda w:logistic(w,x,y)[:2],w0,jac=True,method='BFGS',options={'gtol':1e-10})
        for method in ['gd','natural_gradient','ring','reng']:
            w=w0.copy();m=np.zeros(4);a_ema=np.ones(4);s_ema=np.ones(1);trace=[];start=time.perf_counter()
            for step in range(1,121):
                loss,g,h=logistic(w,x,y);p=sigmoid(x@w)
                if method=='gd':direction=g;rate=.08
                elif method=='natural_gradient':direction=np.linalg.solve(h,g);rate=.08
                elif method in ['ring','reng']:
                    direction=grng_direction(x,p,g,h,method);rate=.03
                else:
                    # Linear-layer empirical Kronecker factors; batch mean
                    # errors are rescaled to per-example backprop errors.
                    a_ema=.8*a_ema+.2*np.mean(x*x,axis=0)
                    s_ema=.8*s_ema+.2*np.array([np.mean((p-y)**2)])
                    diagonal=minmax(a_ema)*minmax(s_ema)[0]+.001
                    m=.9*m+.1*g;direction=(m/(1-.9**step))/diagonal;rate=.001
                w=w-rate*direction
                trace.append({'step':step,'loss':loss,'gradient_norm':float(np.linalg.norm(g))})
            elapsed=time.perf_counter()-start;loss,g,_=logistic(w,x,y)
            rows.append({'seed':seed,'problem':'binary_logistic','method':method,'final_loss':loss,'reference_gap':loss-float(ref.fun),'reference_gradient_norm':float(np.linalg.norm(ref.jac)),'gradient_norm':float(np.linalg.norm(g)),'function_training_s':elapsed,'weights':w,'initial_weights':w0,'trace':trace})
        continuous=x@truth+rng.normal(scale=.1,size=len(x))
        for rho in [0.,.05]:
            mu,cov,trace=regularized_kalman(x,continuous,rho)
            rows.append({'seed':seed,'method':'kalman' if rho==0 else 'regularized_kalman','mse':float(np.mean((x@mu-continuous)**2)),'weights':mu,'covariance':cov,'trace':trace})
        multiclass=rng.choice(3,size=len(x),p=[.2,.3,.5]);winit=rng.normal(scale=.1,size=(4,3))
        for method in ['gd_softmax','adam_softmax','adafisher_softmax']:
            w=winit.copy();h_ema=np.zeros(4);s_ema=np.zeros(3);m=np.zeros_like(w);opt=Adam(w.shape,.01);trace=[];start=time.perf_counter()
            for step in range(1,121):
                probabilities=softmax(x@w);error=probabilities-np.eye(3)[multiclass];g=x.T@error/len(x)+.01*w
                loss=float(-np.log(probabilities[np.arange(len(x)),multiclass]+1e-15).mean()+.005*np.sum(w*w))
                if method=='gd_softmax':w-=.03*g
                elif method=='adam_softmax':w=opt.step(w,g)
                else:
                    # Follow printed paper Eq. 3 literally: gamma multiplies
                    # the new factor. The authors' current code differs; this
                    # paper-equation port is recorded explicitly in the scope.
                    h_ema=.8*np.mean(x*x,axis=0)+.2*h_ema
                    s_ema=.8*np.mean(error*error,axis=0)+.2*s_ema
                    diagonal=np.outer(minmax(h_ema),minmax(s_ema))+.001
                    m=.9*m+.1*g;w-=.001*(m/(1-.9**step))/diagonal
                trace.append({'step':step,'loss':loss,'gradient_norm':float(np.linalg.norm(g))})
            rows.append({'seed':seed,'problem':'three_class_softmax','method':method,'final_loss':trace[-1]['loss'],'function_training_s':time.perf_counter()-start,'weights':w,'initial_weights':winit,'trace':trace})
    return {'runs':rows,'scope':'Original CPU NumPy ports of one-layer equations, with full-batch Fisher refreshed every step (skip S=1). RENG uses analytic Hessian-vector double-backprop. Exact model Fisher replaces sampled model labels; no inverse-update approximation. AdaFisher uses a three-class softmax model, printed Eq. 3 new-factor coefficient gamma=.8, min-max normalized diagonal Kronecker factors, damping and first-moment bias correction. Authors code has a different running-factor rule; no code-equivalence claim. Fixed transparent rates, not equal-FLOP or tuned universal optimizer ranking; no large-model reproduction.'}
