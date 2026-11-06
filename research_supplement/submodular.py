"""Curvature rewiring, dynamic level data structure and private selection.

Tiny instances permit exhaustive independent optima and privacy distributions.
"""
from itertools import combinations
import math
import numpy as np


def subsets(items,k):
    items=sorted(items)
    for size in range(min(k,len(items))+1):
        yield from map(set,combinations(items,size))


def optimum(f,items,k):
    return max(subsets(items,k),key=lambda s:(f(s),-len(s),tuple(-x for x in sorted(s))))


def greedy(f,items,k):
    s=set()
    for _ in range(min(k,len(items))):
        e=min(set(items)-s,key=lambda e:(-(f(s|{e})-f(s)),e));s.add(e)
    return s


def curvature(f,s,remaining):
    ratios=[(f(s|{e})-f(s))/f({e}) for e in remaining if f({e})>0]
    return 1-min(ratios) if ratios else 0.


def resque(f,items,k):
    """Alg. 2 + Definitions 4/5; prefix curvatures recomputed after a rewire.

    The final-step exchange is guarded against deterioration, and raw greedy
    is also retained as the returned incumbent, not a claimed new guarantee.
    """
    selected=[];events=[]
    for step in range(min(k,len(items))):
        s=set(selected);e=min(set(items)-s,key=lambda e:(-(f(s|{e})-f(s)),e))
        history=[curvature(f,set(selected[:j]),set(items)-set(selected[:j])) for j in range(len(selected)+1)]
        tentative=selected+[e]
        trigger=len(history)>1 and history[-1]<=max(history[:-1])+1e-14
        removed=None
        if trigger:
            dominant=int(np.argmax(history))
            # Definition 5 attributes the rise at prefix j to element j-1.
            if dominant>0:
                removed=selected[dominant-1];base=set(tentative)-{removed}
                replacement=min(set(items)-base,key=lambda e:(-(f(base|{e})-f(base)),e))
                candidate=base|{replacement}
                if f(candidate)>=f(set(tentative))-1e-12:tentative=[q for q in tentative if q!=removed]+[replacement]
        selected=tentative
        events.append({'step':step+1,'prefix_curvatures':history,'trigger':trigger,'removed':removed,'selected':sorted(selected),'value':f(set(selected))})
    raw=set(selected);baseline=greedy(f,items,k)
    best=raw if f(raw)>=f(baseline) else baseline
    return best,events,raw


class DynamicLevels:
    """Banihashem et al. level/reservoir mechanism, fixed threshold instance.

    Uses an exact offline solver on the selected union, rather than the
    paper's polynomial alpha-approximation. No paper update-time claim.
    """
    def __init__(self,f,k,threshold,p=3,seed=0):
        self.f=f;self.k=k;self.threshold=threshold;self.p=p;self.rng=np.random.default_rng(seed)
        self.active=set();self.levels=[];self.rebuilds=0;self.checks=0

    def suitable(self,solutions,e):
        self.checks+=1
        if e in set().union(*solutions):return None
        for j,s in enumerate(solutions):
            if len(s)<self.k and e not in s and self.f(s|{e})-self.f(s)>=self.threshold:return j
        return None

    def construct(self,prefix,candidates,solutions):
        self.levels=self.levels[:prefix];self.rebuilds+=1
        remaining=set(candidates)
        while remaining:
            order=list(sorted(remaining));self.rng.shuffle(order);e=order[0]
            j=self.suitable(solutions,e)
            if j is None:
                remaining.remove(e);continue
            before=[s.copy() for s in solutions];after=[s.copy() for s in solutions];after[j].add(e)
            self.levels.append({'reservoir':remaining.copy(),'element':e,'solution_index':j,'before':before,'after':after})
            solutions=after
            remaining={v for v in remaining-{e} if self.suitable(solutions,v) is not None}

    def insert(self,e):
        if e in self.active:raise ValueError('Duplicate insertion')
        self.active.add(e)
        for i,level in enumerate(self.levels):
            j=self.suitable(level['before'],e)
            if j is None:return
            level['reservoir'].add(e)
            if self.rng.random()<1/len(level['reservoir']):
                before=[s.copy() for s in level['before']];after=[s.copy() for s in before];after[j].add(e)
                self.levels[i]={'reservoir':level['reservoir'],'element':e,'solution_index':j,'before':before,'after':after}
                candidates={v for v in level['reservoir']-{e} if self.suitable(after,v) is not None}
                self.construct(i+1,candidates,after);return
        solutions=[s.copy() for s in self.levels[-1]['after']] if self.levels else [set() for _ in range(self.p)]
        if self.suitable(solutions,e) is not None:self.construct(len(self.levels),{e},solutions)

    def delete(self,e):
        if e not in self.active:raise ValueError('Missing deletion')
        self.active.remove(e)
        for i,level in enumerate(self.levels):
            if e not in level['reservoir']:break
            level['reservoir'].remove(e)
            if level['element']==e:
                self.construct(i,level['reservoir'],level['before']);return

    def solution(self):
        candidates=self.levels[-1]['after'] if self.levels else [set()]
        union=set().union(*candidates)
        offline=optimum(self.f,union,self.k)
        return max(candidates+[offline],key=lambda s:(self.f(s),-len(s)))

    def check_invariants(self):
        before=[set() for _ in range(self.p)]
        remaining={e for e in self.active if self.suitable(before,e) is not None}
        for level in self.levels:
            assert level['before']==before
            assert level['reservoir']==remaining
            e=level['element'];assert e in remaining
            j=self.suitable(before,e);assert j==level['solution_index']
            before=[s.copy() for s in before];before[j].add(e)
            assert before==level['after'] and all(len(s)<=self.k for s in before)
            remaining={v for v in remaining-{e} if self.suitable(before,v) is not None}
        assert not remaining


def private_distribution(dataset,coverage,costs,budget,epsilon):
    """Finite-support exponential mechanism for a sensitivity-one objective.

    This is a rigorously auditable DP knapsack control, not the paper's
    scalable GRNM/DP-2GG implementation or its approximation guarantee.
    """
    candidates=[s for s in subsets(range(len(costs)),len(costs)) if sum(costs[i] for i in s)<=budget]
    scores=np.array([sum(bool(set(row)&set().union(*(coverage[i] for i in s))) for row in dataset) for s in candidates],dtype=float)
    logits=epsilon*scores/2;weights=np.exp(logits-logits.max());p=weights/weights.sum()
    return candidates,scores,p


def generalized_noisy_max(scores,sensitivities,epsilon,beta,rng):
    """Zadicario/Milo Appendix A Algorithm 5, exponential-noise GRNM."""
    q=np.asarray(scores);d=np.asarray(sensitivities)
    if epsilon<=0 or not 0<beta<1 or np.any(d<=0):raise ValueError('Invalid GRNM parameters')
    t=2/epsilon*np.log(len(q)/beta);adjusted=q-t*d
    auxiliary=np.min((adjusted[:,None]-adjusted[None,:])/(d[:,None]+d[None,:]),axis=1)
    index=int(np.argmax(auxiliary+rng.exponential(2/epsilon,size=len(q))))
    return index,auxiliary


def dp_density_greedy_plus(f,costs,budget,epsilon,rng,beta=.1):
    """Paper Algorithms 1,4,5,7 with conservative pure-DP composition.

    eps/(2k) replaces advanced-composition eps0; final RNM receives eps/2.
    Public nonnegative costs; f has add/remove-one sensitivity <= 1.
    """
    k=min(len(costs),int(budget/min(costs)));eps0=epsilon/(2*max(1,k));s=set();partials=[set()];trace=[]
    while True:
        candidates=[i for i in range(len(costs)) if i not in s and sum(costs[j] for j in s)+costs[i]<=budget]
        if not candidates:break
        scores=np.array([(f(s|{i})-f(s))/costs[i] for i in candidates]);sensitivity=1/np.array([costs[i] for i in candidates])
        index,aux=generalized_noisy_max(scores,sensitivity,eps0,beta/max(k,1),rng);selected=candidates[index]
        s=s|{selected};partials.append(s.copy());trace.append({'candidates':candidates,'density_scores':scores,'auxiliary_scores':aux,'selected':selected})
    extensions={tuple(sorted(s))}
    for prefix in partials:
        for i in range(len(costs)):
            candidate=prefix|{i}
            if sum(costs[j] for j in candidate)<=budget:extensions.add(tuple(sorted(candidate)))
    candidates=sorted(extensions);values=np.array([f(set(s)) for s in candidates]);noisy=values+rng.exponential(4/epsilon,size=len(values));result=set(candidates[int(np.argmax(noisy))])
    return result,trace,{'per_step_epsilon':eps0,'maximum_greedy_steps':k,'final_selection_epsilon':epsilon/2,'total_pure_epsilon_upper_bound':eps0*k+epsilon/2,'delta':0.,'final_candidates':candidates}


def run():
    rewired=[];dynamic=[];private=[];paper_private=[]
    for seed in range(5):
        rng=np.random.default_rng(241070005+seed)
        sets=[set(np.flatnonzero(rng.random(18)<.35)) for _ in range(10)]
        f=lambda s:float(len(set().union(*(sets[i] for i in s))))
        best,events,raw=resque(f,set(range(10)),4);base=greedy(f,set(range(10)),4);opt=optimum(f,set(range(10)),4)
        rewired.append({'seed':seed,'coverage_sets':sets,'greedy':sorted(base),'raw_resque':sorted(raw),'guarded_incumbent':sorted(best),'optimum':sorted(opt),'greedy_value':f(base),'resque_value':f(best),'raw_value':f(raw),'optimum_value':f(opt),'events':events})
        w=rng.integers(0,8,size=(10,10));w=np.triu(w,1);w=w+w.T
        def cut(s):return float(sum(w[i,j] for i in s for j in set(range(10))-s))
        instances=[DynamicLevels(cut,3,t,p=3,seed=seed*100+index) for index,t in enumerate([1.,4.,8.,16.])]
        updates=[('insert',i) for i in range(10)]+[('delete',i) for i in [2,5,0]]+[('insert',i) for i in [5,0]]+[('delete',i) for i in [9,4,6]]
        trace=[]
        for kind,e in updates:
            for ds in instances:
                getattr(ds,kind)(e);ds.check_invariants()
            active=instances[0].active;choice=max((ds.solution() for ds in instances),key=cut);opt=optimum(cut,active,3)
            trace.append({'operation':kind,'element':e,'active':sorted(active),'selected':sorted(choice),'value':cut(choice),'optimum':cut(opt),'levels':[len(ds.levels) for ds in instances],'reconstructions':[ds.rebuilds for ds in instances]})
        dynamic.append({'seed':seed,'cut_weights':w,'thresholds':[1,4,8,16],'trace':trace})
        cover=[set(np.flatnonzero(rng.random(8)<.4)) for _ in range(6)];cost=[1,2,1,3,2,1]
        dataset=[set(np.flatnonzero(rng.random(8)<.4)) for _ in range(20)];neighbor=dataset+[set([0,3])]
        for epsilon in [.2,1.,4.]:
            candidates,scores,p=private_distribution(dataset,cover,cost,4,epsilon)
            _,_,q=private_distribution(neighbor,cover,cost,4,epsilon)
            ratio=float(np.max(np.abs(np.log(p/q))))
            assert ratio<=epsilon+1e-12
            samples=rng.choice(len(p),size=200,p=p)
            private.append({'seed':seed,'epsilon':epsilon,'coverage_sets':cover,'dataset':dataset,'neighbor_added':[0,3],'costs':cost,'budget':4,'candidate_sets':candidates,'scores':scores,'probabilities':p,'neighbor_probabilities':q,'max_abs_log_likelihood_ratio':ratio,'expected_utility':float(p@scores),'optimum':float(scores.max()),'sampled_utility_mean':float(scores[samples].mean())})
            objective=lambda s:float(sum(bool(set(row)&set().union(*(cover[i] for i in s))) for row in dataset))
            chosen,path,account=dp_density_greedy_plus(objective,cost,4,epsilon,rng)
            paper_private.append({'seed':seed,'epsilon':epsilon,'selected':sorted(chosen),'utility':objective(chosen),'cost':sum(cost[i] for i in chosen),'optimum':float(scores.max()),'greedy_trace':path,'privacy_accounting':account})
    return {'resque':rewired,'dynamic':dynamic,'private_reference':private,'paper_private':paper_private,'scope':'ResQue uses source curvature trigger and step-back with explicit incumbent safeguard. Dynamic experiment implements level reservoirs and partial rebuilds at fixed thresholds; exact offline solver, disjoint candidate sets and finite threshold grid replace asymptotic machinery. Private density greedy+ ports Algorithms 1/4/5/7 with stricter basic composition eps/(2k), rather than advanced composition, plus an independently enumerable exponential-mechanism reference. No claimed 0.277 or (1-1/e) DP theorem from these small controls.'}
