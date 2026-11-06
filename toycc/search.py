"""Exact stateful DP pass ordering, greedy lookahead, and independent permutations."""
from functools import lru_cache
import itertools
from .ir import canonical,score
from .passes import PASSES,PASS_NAMES,apply_order


FIXED=('fold','cse','strength','dce')


def greedy(ir):
    current=canonical(ir);remaining=list(PASS_NAMES);order=[];evaluations=0
    while remaining:
        candidates=[(score(PASSES[name](current)),index,name,PASSES[name](current)) for index,name in enumerate(remaining)]
        evaluations+=len(candidates);_,_,name,current=min(candidates,key=lambda item:(item[0],item[1]));order.append(name);remaining.remove(name)
    return current,{'order':order,'transition_evaluations':evaluations,'method':'immediate-score greedy'}


def dynamic_programming(ir):
    transitions=0;all_used=(1<<len(PASS_NAMES))-1
    @lru_cache(maxsize=None)
    def visit(mask,state):
        nonlocal transitions
        if mask==all_used:return (score(state),(),state)
        choices=[]
        for index,name in enumerate(PASS_NAMES):
            if mask>>index&1:continue
            transitions+=1;next_state=PASSES[name](state);cost,path,terminal=visit(mask|1<<index,next_state)
            choices.append((cost,(index,)+path,terminal))
        return min(choices,key=lambda item:(item[0],item[1]))
    optimum,path,result=visit(0,canonical(ir));info=visit.cache_info()
    return result,{'order':[PASS_NAMES[i] for i in path],'optimal_score':optimum,'states':info.currsize,
        'cache_hits':info.hits,'transition_evaluations':transitions,'method':'DP over (used-pass mask, canonical transformed IR)',
        'certificate_scope':'Optimal weighted IR score among all 24 permutations of four passes used exactly once; no runtime-optimality claim.'}


def exhaustive(ir):
    rows=[]
    for indices in itertools.permutations(range(len(PASS_NAMES))):
        order=[PASS_NAMES[i] for i in indices];result=apply_order(ir,order);rows.append({'order':order,'score':score(result),'instructions':len(result.code)})
    minimum=min(r['score'] for r in rows);return {'minimum_score':minimum,'rows':rows,'number_of_orders':len(rows)}
