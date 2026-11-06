"""Numerics and immutable experiment output helpers."""
import hashlib
import json
from pathlib import Path
import numpy as np


def sigmoid(x):
    x=np.asarray(x,dtype=float)
    return np.exp(-np.logaddexp(0,-x))


def softmax(x):
    x=np.asarray(x);z=x-x.max(axis=-1,keepdims=True)
    p=np.exp(z);return p/p.sum(axis=-1,keepdims=True)


def jsonable(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,(set,tuple)):return [jsonable(v) for v in sorted(x)]
    if isinstance(x,list):return [jsonable(v) for v in x]
    if isinstance(x,dict):return {str(k):jsonable(v) for k,v in x.items()}
    return x


def save(path,value):
    path=Path(path)
    if path.exists():raise FileExistsError(f'Preserve previous evidence: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(jsonable(value),indent=2,allow_nan=False)+'\n')


def array_digest(*arrays):
    h=hashlib.sha256()
    for a in arrays:
        a=np.ascontiguousarray(a);h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()


class Adam:
    def __init__(self,shape,rate=.01):
        self.m=np.zeros(shape);self.v=np.zeros(shape);self.t=0;self.rate=rate

    def step(self,x,g):
        self.t+=1;self.m=.9*self.m+.1*g;self.v=.999*self.v+.001*g*g
        return x-self.rate*(self.m/(1-.9**self.t))/(np.sqrt(self.v/(1-.999**self.t))+1e-8)
