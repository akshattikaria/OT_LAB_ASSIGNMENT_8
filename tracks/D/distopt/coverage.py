"""Nonnegative weighted coverage, a normalized monotone submodular objective."""
from dataclasses import dataclass
import heapq
import itertools
import numpy as np


@dataclass
class Coverage:
    sets:list
    weights:list
    k:int

    def __post_init__(self):
        self.sets=[frozenset(x) for x in self.sets];self.weights=np.asarray(self.weights,dtype=float)
        if not len(self.sets) or self.weights.ndim!=1 or not np.all(np.isfinite(self.weights)) or np.min(self.weights)<0:
            raise ValueError('Nonempty sets and nonnegative finite weights required')
        if not isinstance(self.k,int) or not 1<=self.k<=len(self.sets):raise ValueError('Invalid cardinality budget')
        if any(any(not isinstance(x,(int,np.integer)) or not 0<=x<len(self.weights) for x in subset) for subset in self.sets):raise ValueError('Unknown universe item')

    def value(self,selection):
        indices=list(selection)
        if len(indices)!=len(set(indices)) or any(not 0<=i<len(self.sets) for i in indices):raise ValueError('Invalid selected indices')
        union=set().union(*(self.sets[i] for i in indices))
        return float(sum(self.weights[x] for x in union))

    def json(self):return {'sets':[sorted(x) for x in self.sets],'weights':self.weights.tolist(),'k':self.k}


def solve(problem,method):
    n=len(problem.sets);selected=[];evaluations=0;trace=[]
    def value(S):
        nonlocal evaluations
        evaluations+=1;return problem.value(S)
    if method=='exact':
        if n>20:raise ValueError('Exhaustive search restricted to at most 20 candidates')
        best=-1
        for candidate in itertools.combinations(range(n),problem.k):
            score=value(candidate)
            if score>best:best=score;selected=list(candidate)
    elif method in ('input_order','singleton'):
        selected=list(range(n))[:problem.k] if method=='input_order' else sorted(range(n),key=lambda i:(-value([i]),i))[:problem.k]
    elif method in ('greedy','lazy_greedy'):
        heap=[(-value([i]),i) for i in range(n)] if method=='lazy_greedy' else []
        heapq.heapify(heap);score=0.
        while len(selected)<problem.k:
            if method=='greedy':
                gains=[(value(selected+[i])-score,i) for i in range(n) if i not in selected]
                gain,index=min(gains,key=lambda item:(-item[0],item[1]))
            else:
                while True:
                    _,index=heapq.heappop(heap);gain=value(selected+[index])-score
                    if not heap or (-gain,index)<=heap[0]:break
                    heapq.heappush(heap,(-gain,index))
            selected.append(index);score+=gain;trace.append({'selected':index,'marginal_gain':gain,'value':score})
    else:raise ValueError('Unknown coverage method')
    score=problem.value(selected)
    return {'method':method,'selected':selected,'value':score,'oracle_evaluations':evaluations,'trace':trace}


def generate(n,seed,family):
    rng=np.random.default_rng(seed+100*n);m=2*n;sets=[]
    for i in range(n):
        if family=='independent':mask=rng.random(m)<.14
        elif family=='clustered':
            group=i%4;mask=rng.random(m)<.025;mask[np.arange(m)%4==group]|=rng.random(sum(np.arange(m)%4==group))<.65
        elif family=='redundant':
            mask=rng.random(m)<.025;mask[:m//3]|=rng.random(m//3)<.85
        else:raise ValueError('Unknown coverage family')
        sets.append(np.flatnonzero(mask).tolist())
    return Coverage(sets,rng.integers(1,6,m).tolist(),min({10:3,16:4,80:12}.get(n,3),n))


def exhaustive_assumptions(problem):
    """Every A subset B and e outside B, for small instances only."""
    n=len(problem.sets)
    if n>9:raise ValueError('Assumption oracle limited to nine candidates')
    scores={mask:problem.value([i for i in range(n) if mask>>i&1]) for mask in range(1<<n)}
    comparisons=0
    for B in range(1<<n):
        A=B
        while True:
            for e in range(n):
                if B>>e&1:continue
                small=scores[A|1<<e]-scores[A];large=scores[B|1<<e]-scores[B]
                if small+1e-10<large or large< -1e-10:raise AssertionError('Coverage assumptions failed')
                comparisons+=1
            if A==0:break
            A=(A-1)&B
    return {'normalized':scores[0]==0,'monotone':True,'submodular':True,'comparisons':comparisons}
