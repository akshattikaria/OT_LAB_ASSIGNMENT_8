"""Recompute retained research evidence; never replace measured timings."""
import hashlib
import json
from pathlib import Path
import re
from collections import Counter
import numpy as np
from .svmplus import rbf,predict

ROOT=Path(__file__).resolve().parents[1]


def read(name):return json.loads((ROOT/'research_supplement'/name).read_text())


def main():
    registry=read('SOURCE_REGISTRY.json');assert len(registry['entries'])==22
    counts=dict(Counter(r['fidelity'] for r in registry['entries']))
    assert counts==registry['fidelity_counts'] and counts['mechanism_only']==6
    assert registry['strict_paper_method_coverage_complete'] is False
    for r in registry['entries']:
        assert (ROOT/r['code']).is_file() and (ROOT/r['result']).is_file()
        result=json.loads((ROOT/r['result']).read_text());assert result[r['result_section']]
        assert r['full_paper_reproduction'] is False
    c=read('results/curvature.json');assert len(c['runs'])==45
    for r in c['runs']:
        if 'reference_gap' in r:assert r['reference_gap']>=-1e-8 and r['reference_gradient_norm']<1e-6
        if 'covariance' in r:assert np.linalg.eigvalsh(r['covariance']).min()>-1e-10
    d=read('results/submodular.json');assert len(d['resque'])==len(d['dynamic'])==5 and len(d['paper_private'])==15
    for r in d['resque']:assert r['resque_value']<=r['optimum_value'] and r['resque_value']>=r['greedy_value']
    for r in d['dynamic']:
        for event in r['trace']:assert len(event['selected'])<=3 and set(event['selected'])<=set(event['active']) and event['value']<=event['optimum']
    for r in d['paper_private']:assert r['cost']<=4 and r['privacy_accounting']['total_pure_epsilon_upper_bound']<=r['epsilon']+1e-12
    certificate=read('results/privacy_certificate.json')
    for r in certificate['rows']:
        p,q=np.array(r['p']),np.array(r['q']);assert abs(p.sum()-1)<1e-10 and abs(q.sum()-1)<1e-10
        maximum=float(np.max(np.abs(np.log(p/q))));assert abs(maximum-r['maximum_absolute_log_ratio'])<1e-10 and maximum<=r['epsilon']+1e-10
    for name,count in [('tensorhyper',10),('negative_learning',10),('qmt',10),('nom',5)]:
        q=read(f'results/{name}.json');assert len(q['runs'])==count
        if name=='nom':assert q['unitarity_error']<1e-10
        for r in q['runs']:
            assert np.isfinite(np.array([v for key,v in r.items() if isinstance(v,(int,float))])).all()
            if 'test_accuracy' in r:assert 0<=r['test_accuracy']<=1
            if name=='nom':
                assert r['ground_energy_gap']>=-1e-8
                assert all(0<e['postselection_probability']<=1+1e-10 for e in r['trace'])
    com=read('results/communication.json')
    for r in com['subspace']:
        assert r['max_trajectory_difference']<1e-9 and r['final_parameter_difference']<1e-9 and r['max_activation_reconstruction_error']<1e-9
        assert r['grassmann_orthogonality_error']<1e-10 and r['grassmann_residual_after']<=r['grassmann_residual_before']+1e-10
    for r in com['low_rank_fl']:assert max(t['feedback_conservation_error'] for t in r['trace'])<1e-10
    svm=read('results/svmplus.json');assert len(svm['runs'])==6
    for r in svm['runs']:
        assert r['unique_candidate_evaluations']==16
        model=r['selected_model'];x=np.array(r['features']);priv=np.array(r['privileged_features']);y=np.array(r['labels']);ids=r['train_indices'];test=r['test_indices']
        normal=np.array(model['coefficients']);correct=np.array(model['correcting_coefficients']);kernel=rbf(x[ids],x[ids],model['sigma']);star=rbf(priv[ids],priv[ids],model['sigma_star']);alpha=np.array(model['alpha']);beta=np.array(model['beta'])
        slack=star@correct+model['privileged_intercept'];margin=y[ids]*(kernel@normal+model['intercept'])
        assert slack.min()>-1e-6 and np.min(margin+slack)>1-1e-6
        norms=.5*normal@kernel@normal+.5*model['gamma']*correct@star@correct
        primal=float(norms+model['C']*slack.sum());dual=float(alpha.sum()-norms)
        assert abs(primal-model['primal'])<1e-5 and abs(dual-model['dual'])<1e-5 and -1e-6<=primal-dual<.005
        assert abs(alpha@y[ids])<1e-6 and abs(np.sum(alpha+beta)-len(ids)*model['C'])<1e-6
        model_arrays={**model,'x':np.array(model['x']),'coefficients':normal}
        assert np.mean(predict(model_arrays,x[test])==y[test])==r['test_accuracy']
    data=read('data/provenance.json');assert hashlib.sha256((ROOT/'research_supplement/data/ilpd.csv').read_bytes()).hexdigest()==data['dataset_sha256']
    liver=read('results/liver.json');assert liver['rows']==583 and len(liver['runs'])==9
    for r in liver['runs']:
        train,val,test=map(set,[r['train_indices'],r['validation_indices'],r['test_indices']]);assert not(train&val or train&test or val&test) and len(train|val|test)==583
        p=np.array(r['test_probabilities']);y=np.array(r['test_labels']);assert np.isfinite(p).all() and np.mean((p>=.5)==y)==r['accuracy']
        if r['method']=='hybrid_quantum':assert r['circuit_parameter_count']==8 and r['simulated_circuit_instances']==r['epochs']*(len(train)*21+len(val))+len(test)
    native=read('results/spmv.json');assert len(native['runs'])==15
    for r in native['runs']:
        assert r['threads']==2 and len(r['trials'])==14
        assert all(t['seconds']>0 and t['max_error']<=1e-8 for t in r['trials'])
        for method,name in [(0,'row_static'),(1,'runtime_adaptive_nnz_tiles')]:
            trials=[t['seconds'] for t in r['trials'] if t['method']==method];assert abs(np.median(trials)-r['summary'][name]['median_s'])<1e-12
    placement=read('results/placement.json')
    for r in placement['grouping']:assert sorted(i for group in r['mcl_groups'] for i in group)==list(range(12)) and r['mcl_column_sum_error']<1e-9
    for r in placement['currying']:assert r['absolute_error']<1e-10
    for r in placement['packing']:assert sorted(i for node in r['final_nodes'] for i in node)==list(range(40))
    hpo=read('results/hpo.json');assert len(hpo['live_halving']['runs'])==9
    for r in hpo['live_halving']['runs']:
        assert sum(e['to']-e['from'] for e in r['events'])==r['epoch_units']
        for e in r['events']:
            assert e['finish']>=e['start']
            if 'decision_time' in e:assert e['decision_time']>=e['finish']
        assert r['completed_max_resource']>=1
    strategies=read('results/strategies.json');plans=strategies['plans']
    feasible=[i for i,p in enumerate(plans) if p['hourly_cost']<=strategies['hourly_budget']]
    exact=min(plans[i]['modeled_iteration_s'] for i in feasible)
    assert abs(plans[strategies['exact_time_optimum_index']]['modeled_iteration_s']-exact)<1e-10
    for r in strategies['ga_runs']:
        assert r['selected_index'] in feasible
        assert abs(r['selected_time']-plans[r['selected_index']]['modeled_iteration_s'])<1e-10
        assert abs(r['model_optimality_gap']-(r['selected_time']-exact))<1e-10
        assert r['model_optimality_gap']>=-1e-8
    for key in ['astra_throughput_choice','astra_economical_choice']:assert plans[strategies[key]]['hourly_cost']<=strategies['hourly_budget']
    log=(ROOT/'validation/research_tests_final.log').read_text();match=re.search(r'Ran (\d+) tests',log);assert match and '\nOK' in log
    assert len(list((ROOT/'research_supplement/results').glob('*.json')))==14
    record={'passed':True,'source_entries':22,'source_ports':10,'algorithm_variants':4,'survey_demonstrations':2,'mechanism_only_entries':6,'result_json_files':14,'new_mathematical_tests':int(match[1]),'native_spmv_timed_trials':210,'liver_splits':3,'svmplus_candidate_fits':96,'strict_paper_method_coverage_complete':False,'scope':'Recomputed stored mathematical certificates, data/source integrity and units; retained timings are not replaced. Six exact published policies remain unavailable; controls are explicitly not relabeled paper implementations.'}
    print(json.dumps(record,indent=2));return record


if __name__=='__main__':main()
