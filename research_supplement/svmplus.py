"""SVM+ convex dual and a small grid-island genetic search experiment.

Source: Fernández et al., Journal of Heuristics 2026, Eq. 2, Sections 4.2–4.3.
Search ranges/populations reduced; secondary privileged-space tie model is
explicitly an independent SVC, not an undocumented paper-code reconstruction.
"""
from concurrent.futures import ThreadPoolExecutor
import time
import numpy as np
from scipy.optimize import minimize,linprog
from sklearn.svm import SVC


def rbf(x,z,sigma):
    return np.exp(-np.maximum(0,np.sum(x*x,1)[:,None]+np.sum(z*z,1)[None,:]-2*x@z.T)/(2*sigma*sigma))


def fit(x,y,privileged,parameters):
    c,gamma,sigma,sigma_star=map(float,parameters);n=len(y);kernel=rbf(x,x,sigma);star=rbf(privileged,privileged,sigma_star)
    def value_gradient(z):
        alpha,beta=z[:n],z[n:];corrected=alpha+beta-c;weighted=alpha*y
        value=-alpha.sum()+.5*weighted@kernel@weighted+.5/gamma*corrected@star@corrected
        common=star@corrected/gamma
        gradient=np.r_[y*(kernel@weighted)-1+common,common]
        return float(value),gradient
    aeq=np.array([np.r_[y,np.zeros(n)],np.ones(2*n)])
    target=np.array([0,n*c]);initial=np.r_[np.zeros(n),np.full(n,c)]
    result=minimize(value_gradient,initial,jac=True,method='SLSQP',bounds=[(0,None)]*(2*n),constraints={'type':'eq','fun':lambda z:aeq@z-target,'jac':lambda z:aeq},options={'ftol':1e-9,'maxiter':400})
    alpha,beta=result.x[:n],result.x[n:];normal=alpha*y;correcting=(alpha+beta-c)/gamma
    decision=kernel@normal;slack_no_bias=star@correcting
    # Solve for two unregularized intercepts, explicitly preserving both
    # nonnegative slacks and primal margin inequalities.
    constraints=np.vstack([np.column_stack([-y,-np.ones(n)]),np.tile([0.,-1.],(n,1))]);rhs=np.r_[y*decision+slack_no_bias-1,slack_no_bias]
    intercept=linprog([0,1],A_ub=constraints,b_ub=rhs,bounds=[(None,None),(None,None)],method='highs')
    if not intercept.success:raise RuntimeError('SVM+ intercept LP failed')
    b,b_star=intercept.x;slack=slack_no_bias+b_star
    norms=.5*normal@kernel@normal+.5*gamma*correcting@star@correcting
    primal=float(norms+c*slack.sum());dual=float(alpha.sum()-norms);gap=primal-dual
    feasibility=max(float(np.max(np.abs(aeq@result.x-target))),float(max(0,-slack.min())),float(max(0,np.max(1-slack-y*(decision+b)))))
    valid=bool(result.success and gap>=-1e-6 and gap<.005 and feasibility<1e-6)
    return {'x':x,'coefficients':normal,'intercept':float(b),'sigma':sigma,'alpha':alpha,'beta':beta,'correcting_coefficients':correcting,'privileged_intercept':float(b_star),'slacks':slack,'C':c,'gamma':gamma,'sigma_star':sigma_star,'primal':primal,'dual':dual,'gap':gap,'feasibility_error':feasibility,'valid':valid,'solver_success':bool(result.success),'solver_message':str(result.message)}


def predict(model,x):
    return np.where(rbf(x,model['x'],model['sigma'])@model['coefficients']+model['intercept']>=0,1,-1)


def run():
    rows=[];levels=np.array([np.linspace(-1,1,7),np.linspace(-1,1,7),np.linspace(-.7,.3,7),np.linspace(-.7,.3,7)])
    for seed in range(3):
        rng=np.random.default_rng(7100+seed);latent=np.r_[rng.normal(-1,.7,size=36),rng.normal(1,.7,size=36)];y=np.r_[np.full(36,-1),np.ones(36)]
        x=np.column_stack([latent+rng.normal(scale=1.1,size=72),rng.normal(size=72)]);priv=np.column_stack([latent,rng.normal(scale=.1,size=72)])
        train=np.r_[np.arange(12),np.arange(36,48)];validation=np.r_[np.arange(12,24),np.arange(48,60)];test=np.r_[np.arange(24,36),np.arange(60,72)]
        mean=x[train].mean(0);scale=x[train].std(0);x=(x-mean)/scale;pm=priv[train].mean(0);ps=priv[train].std(0);priv=(priv-pm)/ps
        for method in ['random_search','grid_island_ga']:
            random=np.random.default_rng(7200+seed);records={};models={};start=time.perf_counter()
            def evaluate(key):
                params=10**np.array([levels[j,key[j]] for j in range(4)]);begin=time.perf_counter();model=fit(x[train],y[train],priv[train],params)
                accuracy=float(np.mean(predict(model,x[validation])==y[validation]))
                privileged=SVC(C=params[0],gamma=1/(2*params[3]**2)).fit(priv[train],y[train]);secondary=float(np.mean(privileged.predict(priv[validation])==y[validation]))
                record={'grid_indices':key,'parameters':params,'validation_accuracy':accuracy,'privileged_validation_tiebreak':secondary,'dual_value':model['dual'],'qp_valid':model['valid'],'qp_gap':model['gap'],'qp_feasibility_error':model['feasibility_error'],'qp_message':model['solver_message'],'evaluation_s':time.perf_counter()-begin}
                return key,record,model
            def ranking(key):
                r=records[key];return (int(r['qp_valid']),r['validation_accuracy'],r['privileged_validation_tiebreak'],-r['dual_value'])
            def fresh(island=None):
                for _ in range(1000):
                    key=tuple(random.integers(0,7,size=4))
                    if island is not None:key=((int(random.integers(0,3)) if island==0 else int(random.integers(3,7))),)+key[1:]
                    if key not in records:return key
                raise RuntimeError('Search failed to generate fresh candidate')
            with ThreadPoolExecutor(max_workers=2) as pool:
                if method=='random_search':
                    batch=set()
                    while len(batch)<16:batch.add(fresh())
                    for key,record,model in pool.map(evaluate,sorted(batch)):records[key]=record;models[key]=model
                else:
                    islands=[[],[]]
                    for island in range(2):
                        keys=set()
                        while len(keys)<4:keys.add(fresh(island))
                        for key,record,model in pool.map(evaluate,sorted(keys)):records[key]=record;models[key]=model;islands[island].append(key)
                    for generation in range(4):
                        new=[]
                        for island in range(2):
                            parents=sorted(islands[island],key=ranking,reverse=True)[:2]
                            key=tuple(int(np.clip(round((parents[0][j]+parents[1][j])/2+random.normal(0,1)),0,6)) for j in range(4))
                            if (island==0 and key[0]>=3) or (island==1 and key[0]<3) or key in records:key=fresh(island)
                            new.append(key)
                        for island,(key,record,model) in enumerate(pool.map(evaluate,new)):
                            records[key]=record;models[key]=model;islands[island].append(key)
            winner=max(records,key=ranking);model=models[winner]
            if not model['valid']:raise RuntimeError('No valid SVM+ fit')
            rows.append({'seed':seed,'method':method,'unique_candidate_evaluations':len(records),'selected_grid_indices':winner,'validation_accuracy':records[winner]['validation_accuracy'],'test_accuracy':float(np.mean(predict(model,x[test])==y[test])),'elapsed_s':time.perf_counter()-start,'failed_candidate_count':sum(not r['qp_valid'] for r in records.values()),'train_indices':train,'validation_indices':validation,'test_indices':test,'features':x,'privileged_features':priv,'labels':y,'trials':list(records.values()),'selected_model':model})
    return {'runs':rows,'scope':'Convex RBF SVM+ dual Eq. 2 with independently computed feasible primal and primal-dual gap. GAGS-inspired two-island log-grid GA, crossover/mutation and fresh diversity seeds; actual two-worker candidate evaluations. Random search has the same 16 unique-candidate budget. Narrow ranges, small synthetic LUPI data and independent privileged-space SVC tiebreak are explicit adaptations. No MNIST/CWRU or paper-speedup reproduction; test privileged features are never used for inference or selection.'}
