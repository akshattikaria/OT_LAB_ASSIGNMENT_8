"""Small synthetic problems with explicit loss, gradients and curvature."""
from __future__ import annotations

import numpy as np
from scipy.special import expit


def validate_data(X,y,l2):
    X,y = np.array(X,dtype=float,copy=True),np.array(y,dtype=float,copy=True)
    if X.ndim != 2 or min(X.shape) < 1 or y.shape != (len(X),):
        raise ValueError("X must be a nonempty matrix and y a matching vector")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("Data must be finite")
    if not np.isfinite(l2) or l2 < 0:
        raise ValueError("l2 must be finite and nonnegative")
    return X,y


class Ridge:
    kind = "ridge"
    def __init__(self,X,y,l2=.01):
        self.X,self.y = validate_data(X,y,l2)
        self.l2,self.n,self.d = float(l2),*self.X.shape
    def value(self,w,indices=None):
        X,y = (self.X,self.y) if indices is None else (self.X[indices],self.y[indices])
        residual = X@w-y
        return float(.5*np.mean(residual**2)+.5*self.l2*(w@w))
    def grad(self,w,indices=None):
        X,y = (self.X,self.y) if indices is None else (self.X[indices],self.y[indices])
        return X.T@(X@w-y)/len(y)+self.l2*w
    def hess(self,w):
        return self.X.T@self.X/self.n+self.l2*np.eye(self.d)
    def residual_jac(self,w):
        r = (self.X@w-self.y)/np.sqrt(self.n)
        J = self.X/np.sqrt(self.n)
        if self.l2:
            r = np.concatenate((r,np.sqrt(self.l2)*w))
            J = np.vstack((J,np.sqrt(self.l2)*np.eye(self.d)))
        return r,J
    def reference(self):
        _,J = self.residual_jac(np.zeros(self.d))
        rhs = np.concatenate((self.y/np.sqrt(self.n),np.zeros(self.d))) if self.l2 else self.y/np.sqrt(self.n)
        return np.linalg.lstsq(J,rhs,rcond=None)[0]


class MLP:
    """2 -> 8 tanh units -> one logit; gradient is hand-coded backprop."""
    kind = "mlp"
    def __init__(self,X,y,l2=.001,hidden=8):
        self.X,self.y = validate_data(X,y,l2)
        if self.X.shape[1] != 2 or np.any((self.y != 0)&(self.y != 1)):
            raise ValueError("MLP requires two inputs and binary labels")
        if not isinstance(hidden,int) or hidden < 1:
            raise ValueError("hidden must be a positive integer")
        self.hidden,self.l2,self.n,self.d = hidden,float(l2),len(y),4*hidden+1
    def unpack(self,w):
        h=self.hidden
        return w[:2*h].reshape(2,h),w[2*h:3*h],w[3*h:4*h],w[-1]
    def forward(self,w,X=None):
        X=self.X if X is None else X
        W,b,v,c = self.unpack(w)
        hidden=np.tanh(X@W+b)
        return hidden,hidden@v+c
    def value(self,w,indices=None):
        X,y = (self.X,self.y) if indices is None else (self.X[indices],self.y[indices])
        _,z=self.forward(w,X)
        return float(np.mean(np.logaddexp(0,z)-y*z)+.5*self.l2*(w@w))
    def grad(self,w,indices=None):
        X,y = (self.X,self.y) if indices is None else (self.X[indices],self.y[indices])
        hidden,z=self.forward(w,X)
        _,_,v,_=self.unpack(w)
        dz=(expit(z)-y)/len(y)
        dpre=(dz[:,None]*v)*(1-hidden**2)
        g=np.concatenate(((X.T@dpre).ravel(),dpre.sum(axis=0),hidden.T@dz,np.array([dz.sum()])))
        return g+self.l2*w
    def accuracy(self,w,X=None,y=None):
        X=self.X if X is None else X; y=self.y if y is None else y
        return float(np.mean((self.forward(w,X)[1]>=0)==y))


class ExpFit:
    """Nonlinear least squares: a*exp(b*x), with exact Hessian and GN matrix."""
    kind="exp_fit"
    def __init__(self,x,y):
        self.X,self.y=validate_data(np.asarray(x)[:,None],y,0)
        self.x=self.X[:,0]; self.n=len(y); self.d=2
    def residual_jac(self,w):
        a,b=w; e=np.exp(b*self.x)
        return (a*e-self.y)/np.sqrt(self.n),np.column_stack((e,a*self.x*e))/np.sqrt(self.n)
    def value(self,w,indices=None):
        a,b=w
        return float(.5*np.mean((a*np.exp(b*self.x)-self.y)**2))
    def grad(self,w,indices=None):
        r,J=self.residual_jac(w); return J.T@r
    def hess(self,w):
        a,b=w; e=np.exp(b*self.x); r=a*e-self.y
        _,J=self.residual_jac(w)
        correction=np.array([[0,np.mean(r*self.x*e)],[np.mean(r*self.x*e),np.mean(r*a*self.x**2*e)]])
        return J.T@J+correction


class Logistic:
    kind="logistic"
    def __init__(self,X,y,l2=.01):
        self.X,self.y=validate_data(X,y,l2)
        if np.any((self.y != 0)&(self.y != 1)):raise ValueError("Binary labels required")
        self.l2,self.n,self.d=float(l2),*self.X.shape
    def value(self,w):
        z=self.X@w
        return float(np.mean(np.logaddexp(0,z)-self.y*z)+.5*self.l2*(w@w))
    def grad(self,w):
        return self.X.T@(expit(self.X@w)-self.y)/self.n+self.l2*w
    def fisher(self,w):
        p=expit(self.X@w)
        return self.X.T@((p*(1-p))[:,None]*self.X)/self.n
    def empirical_fisher(self,w):
        sample_grad=(expit(self.X@w)-self.y)[:,None]*self.X
        return sample_grad.T@sample_grad/self.n
    def hess(self,w):return self.fisher(w)+self.l2*np.eye(self.d)
    def hvp(self,w,v):
        p=expit(self.X@w)
        return self.X.T@((p*(1-p))*(self.X@v))/self.n+self.l2*v


def make_dataset(kind,seed,n=256):
    rng=np.random.default_rng(seed)
    if kind=="ridge":
        d=8; U=np.linalg.qr(rng.normal(size=(n,d)),mode="reduced")[0]
        V=np.linalg.qr(rng.normal(size=(d,d)))[0]
        eig=np.geomspace(.2,20,d); transform=np.diag(np.sqrt(eig))@V.T
        X=np.sqrt(n)*U@transform; truth=rng.normal(size=d)
        y=X@truth+rng.normal(scale=.05,size=n)
        Xtest=rng.normal(size=(256,d))@transform
        ytest=Xtest@truth+rng.normal(scale=.05,size=256)
        problem=Ridge(X,y); initial=np.zeros(d)
    elif kind=="mlp":
        X=rng.uniform(-1,1,size=(n,2)); y=np.logical_xor(X[:,0]>0,X[:,1]>0).astype(float)
        Xtest=rng.uniform(-1,1,size=(256,2)); ytest=np.logical_xor(Xtest[:,0]>0,Xtest[:,1]>0).astype(float)
        problem=MLP(X,y)
        initial=np.random.default_rng(seed+10000).normal(scale=.6,size=problem.d)
    else:raise ValueError("kind must be ridge or mlp")
    return problem,initial,Xtest,ytest
