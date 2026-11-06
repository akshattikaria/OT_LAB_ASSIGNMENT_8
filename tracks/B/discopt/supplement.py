"""Feature selection, pseudo-polynomial scaling and Track C interchange files."""
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from time import perf_counter
import numpy as np

from .data import generate,teaching
from .model import audit
from .solvers import dynamic_programming
from .qubo import knapsack_qubo,maxcut_qubo,enumerate_qubo


def feature_dataset(seed):
    rng=np.random.default_rng(seed+9000)
    def block(n):
        X=rng.normal(size=(n,8));X[:,3]=.8*X[:,0]+.2*X[:,3];X[:,4]=.8*X[:,1]+.2*X[:,4];X[:,7]=X[:,6]+.1*X[:,7]
        y=2*X[:,0]-1.5*X[:,1]+.8*X[:,6]+rng.normal(scale=.2,size=n)
        return X,y
    train,y=block(128);val,yval=block(128);test,ytest=block(256)
    return {"Xtrain":train,"ytrain":y,"Xval":val,"yval":yval,"Xtest":test,"ytest":ytest}


def feature_select(data,method,k=3):
    d=data['Xtrain'].shape[1]
    if not isinstance(k,int) or not 0<=k<=d:raise ValueError("k must be between zero and feature count")
    cache={};start=perf_counter();path=[]
    def design(X,subset):return np.column_stack((np.ones(len(X)),X[:,list(subset)]))
    def score(subset):
        subset=tuple(sorted(subset))
        if subset not in cache:
            theta=np.linalg.lstsq(design(data['Xtrain'],subset),data['ytrain'],rcond=None)[0]
            mse=float(np.mean((design(data['Xval'],subset)@theta-data['yval'])**2))
            cache[subset]=(mse,theta)
        return cache[subset][0]
    if method=='baseline':selected=tuple(range(k))
    elif method=='forward':
        selected=()
        while len(selected)<k:
            selected=min((tuple(sorted(selected+(j,))) for j in range(d) if j not in selected),key=lambda s:(score(s),s))
            path.append(list(selected))
    elif method=='backward':
        selected=tuple(range(d));score(selected)
        while len(selected)>k:
            selected=min((tuple(j for j in selected if j!=drop) for drop in selected),key=lambda s:(score(s),s))
            path.append(list(selected))
    elif method=='exhaustive':selected=min(combinations(range(d),k),key=lambda s:(score(s),s))
    else:raise ValueError("Unknown feature-selection method")
    validation=score(selected);theta=cache[selected][1]
    # Test data are used only after the feature subset is selected.
    test=float(np.mean((design(data['Xtest'],selected)@theta-data['ytest'])**2))
    return {"method":method,"selected":list(selected),"theta":theta.tolist(),"validation_mse":validation,
            "test_mse":test,"model_fits":len(cache),"path":path,"runtime_s":perf_counter()-start,
            "candidate_scores":[{"subset":list(s),"validation_mse":value[0]} for s,value in sorted(cache.items())]}


def supplementary(output,write_json,seeds=range(5),repeats=3):
    output=Path(output);quantum=output/'quantum_baselines';quantum.mkdir(exist_ok=True)
    exported=[]
    models=[('knapsack_6bit',knapsack_qubo(teaching())),
            ('maxcut_4bit',maxcut_qubo(4,[(0,1,1),(1,2,1),(2,3,1),(3,0,1),(0,2,1)]))]
    for name,model in models:
        classical=enumerate_qubo(model)
        write_json(quantum/f'{name}_model.json',model.to_dict())
        write_json(quantum/f'{name}_classical.json',classical)
        exported.append({"name":name,"variables":model.n,"minimum_energy":classical['minimum_energy'],
                         "ground_state_count":len(classical['ground_states']),"state_count":len(classical['states']),
                         "energy_identity_error":classical['max_energy_identity_error']})
    penalties=[]
    for penalty in (0,.1,.5,1,3,15):
        exact=enumerate_qubo(knapsack_qubo(teaching(),penalty))
        ground=exact['ground_states']
        penalties.append({"penalty":penalty,"minimum_energy":exact['minimum_energy'],"ground_state_count":len(ground),
            "encoded_feasible_ground_states":sum(s['encoded_feasible'] for s in ground),
            "original_feasible_ground_states":sum(s['original_feasible'] for s in ground),
            "all_encoded_feasible":exact['all_ground_states_encoded_feasible'],"ground_states":ground})
    features=[];folder=output/'feature_datasets';folder.mkdir(exist_ok=True)
    for seed in seeds:
        data=feature_dataset(seed);np.savez_compressed(folder/f'seed{seed}.npz',**data)
        for method in ('baseline','forward','backward','exhaustive'):
            result=feature_select(data,method);result['seed']=seed;features.append(result)
    # Same feasible subsets; budget expressed in progressively smaller units.
    # GCD reduction would remove this deliberate capacity-inflation effect.
    base=generate(20,71);scaling=[]
    for factor in (1,10,100):
        case=replace(base,name=f'dp_scale_{factor}',weights=tuple(w*factor for w in base.weights),capacity=base.capacity*factor)
        for repeat in range(repeats):
            start=perf_counter();solution=dynamic_programming(case);seconds=perf_counter()-start
            checked=audit(case,solution.selection)
            scaling.append({"factor":factor,"repeat":repeat,"capacity":case.capacity,"runtime_s":seconds,
                "value":checked['value'],"feasible":checked['feasible'],"status":solution.status,**solution.details})
    result={"quantum_exports":exported,"penalty_sweep":penalties,"feature_selection":features,
            "feature_protocol":{"d":8,"k":3,"train":128,"validation":128,"test":256,
                "objective":"minimize validation MSE of training-only least-squares fits",
                "test_note":"Test MSE is reported after selection; exhaustive is optimal for the validation objective, not guaranteed best on test data."},
            "dp_scaling":scaling,"dp_scale_note":"Integer units are multiplied for identical feasible subsets; GCD preprocessing is deliberately not applied."}
    write_json(output/'supplementary.json',result)
    return result
