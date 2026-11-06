from concurrent.futures import ThreadPoolExecutor
import itertools
from pathlib import Path
import unittest
import numpy as np
from threadpoolctl import threadpool_limits
from distopt import coverage as c,federated as f,multitask as m,parallel as p,scheduling as s,locality


class TrackDTests(unittest.TestCase):
    def close(self,a,b,tol=1e-9):np.testing.assert_allclose(a,b,atol=tol,rtol=0)

    def test_coverage_union_and_empty(self):
        problem=c.Coverage([{0,1},{1,2}],[1,2,4],1)
        self.assertEqual(problem.value([]),0);self.assertEqual(problem.value([0,1]),7)

    def test_coverage_validation(self):
        for args in (([{0}],[-1],1),([{1}],[1],1),([{0}],[1],2)):
            with self.assertRaises(ValueError):c.Coverage(*args)

    def test_exhaustive_submodular_assumptions(self):
        problem=c.Coverage([{0,1},{1,2},{2,3},{0,3}],[1,2,3,4],2)
        checks=c.exhaustive_assumptions(problem);self.assertTrue(checks['normalized'] and checks['monotone'] and checks['submodular']);self.assertGreater(checks['comparisons'],0)

    def test_greedy_suboptimal_counterexample(self):
        problem=c.Coverage([{0,1,3,4},{0,1,2},{3,4,5}],[1]*6,2)
        self.assertEqual(c.solve(problem,'greedy')['value'],5);self.assertEqual(c.solve(problem,'exact')['value'],6)

    def test_lazy_matches_greedy(self):
        for seed in range(15):
            for family in ('independent','redundant','clustered'):
                problem=c.generate(16,seed,family);a=c.solve(problem,'greedy');b=c.solve(problem,'lazy_greedy')
                self.assertEqual(a['selected'],b['selected']);self.assertEqual(a['value'],b['value'])

    def test_greedy_guarantee_against_exhaustive(self):
        for seed in range(15):
            problem=c.generate(10,seed,'independent');g=c.solve(problem,'greedy')['value'];opt=c.solve(problem,'exact')['value']
            self.assertGreaterEqual(g+1e-9,(1-(1-1/problem.k)**problem.k)*opt)

    def test_tie_break_and_zero_coverage(self):
        problem=c.Coverage([set(),set(),set()],[1],2)
        for method in ('greedy','lazy_greedy','singleton','exact'):self.assertEqual(c.solve(problem,method)['selected'],[0,1])

    def test_partition_exhaustive_and_unequal(self):
        d=f.data(0)
        for kind in ('iid','label_skew'):
            clients=f.partition(d['ytrain'],kind,0);self.assertEqual([len(x) for x in clients],[64,96,160,192]);self.assertEqual(sorted(np.concatenate(clients)),list(range(512)))

    def test_client_weighted_average(self):
        self.close(f.aggregate([[0.,1.],[8.,5.]],[1,3]),[6.,4.])
        with self.assertRaises(ValueError):f.aggregate([[1.],[2.]],[0,1])

    def test_logistic_gradient_finite_difference(self):
        d=f.data(1);w=d['initial'];eps=1e-5;value,gradient=f.objective(w,d['Xtrain'],d['ytrain'])
        fd=[(f.objective(w+eps*e,d['Xtrain'],d['ytrain'])[0]-f.objective(w-eps*e,d['Xtrain'],d['ytrain'])[0])/(2*eps) for e in np.eye(7)]
        self.close(gradient,fd,1e-8)

    def test_fedavg_e1_equals_centralized(self):
        for seed in range(3):
            d=f.data(seed)
            for kind in ('iid','label_skew'):
                a=f.fedavg(d,f.partition(d['ytrain'],kind,seed),1,10);b=f.centralized(d,10)
                self.close(a['theta'],b['theta'],1e-12)

    def test_fedavg_compute_and_communication_counts(self):
        d=f.data(0);r=f.fedavg(d,f.partition(d['ytrain'],'iid',0),5,6)
        self.assertEqual(r['sample_visits'],512*30);self.assertEqual(r['gradient_calls'],4*30);self.assertEqual(r['logical_model_bytes'],2*4*7*8*6)

    def test_client_duplicates_rejected(self):
        d=f.data(0);clients=f.partition(d['ytrain'],'iid',0);clients[0][0]=clients[1][0]
        with self.assertRaises(ValueError):f.fedavg(d,clients,1,1)

    def test_federated_test_data_unchanged_by_partition(self):
        d=f.data(0);copy=d['Xtest'].copy();f.partition(d['ytrain'],'label_skew',0);self.close(copy,d['Xtest'])

    def test_multitask_analytic_gradients(self):
        d=m.data(0,'conflict_10x');w=d['initial'];losses,grads=m.losses_gradients(w,d['Xtrain'],d['Ytrain'],d['scales']);eps=1e-5
        fd=np.column_stack([(m.losses_gradients(w+eps*e,d['Xtrain'],d['Ytrain'],d['scales'])[0]-m.losses_gradients(w-eps*e,d['Xtrain'],d['Ytrain'],d['scales'])[0])/(2*eps) for e in np.eye(7)])
        self.close(grads,fd,1e-8)

    def test_mgda_matches_dense_simplex_search(self):
        rng=np.random.default_rng(1)
        for _ in range(20):
            g=rng.normal(size=(2,7));w=m.mgda_weights(g);self.assertAlmostEqual(w.sum(),2);self.assertTrue(np.all(w>=0))
            score=np.linalg.norm(w@g/2)**2
            grid=min(np.linalg.norm(a*g[0]+(1-a)*g[1])**2 for a in np.linspace(0,1,1001))
            self.assertLessEqual(score,grid+1e-12)

    def test_mgda_conflicting_and_equal_gradients(self):
        self.close(m.mgda_weights([[1.,0.],[-1.,0.]]),[1,1]);self.close(m.mgda_weights([[1.,0.],[1.,0.]]),[1,1])
        self.close(m.mgda_weights([[1.,0.],[3.,0.]]),[2,0])

    def test_gradnorm_frozen_target_gradient(self):
        w=np.array([.3,1.7]);g=np.array([[1.,0.],[0.,2.]]);loss=np.array([.8,1.7]);updated,record=m.gradnorm_update(w,g,loss,np.ones(2))
        target=np.array(record['targets']);norms=np.linalg.norm(g,axis=1);eps=1e-6
        objective=lambda a:np.sum(abs(a*norms-target))
        fd=[(objective(w+eps*e)-objective(w-eps*e))/(2*eps) for e in np.eye(2)]
        self.close(record['weight_gradient'],fd,1e-8);self.assertAlmostEqual(updated.sum(),2);self.assertTrue(np.all(updated>0))

    def test_multitask_same_initialization_and_finite(self):
        d=m.data(0,'conflict_10x');runs=[m.train(d,method,30) for method in ('Equal','MGDA','GradNorm')]
        for r in runs:self.close(r['trace'][0]['theta'],d['initial']);self.assertTrue(np.all(np.isfinite(r['test_mse'])))

    def test_data_parallel_matches_serial(self):
        X,W1,W2=p.data(batch=13,dim=4,hidden=7,out=3)
        with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=3) as pool:self.close(p.partitioned(X,W1,W2,3,'data',pool),p.serial(X,W1,W2))

    def test_model_parallel_matches_serial(self):
        X,W1,W2=p.data(batch=13,dim=4,hidden=7,out=3)
        with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=3) as pool:self.close(p.partitioned(X,W1,W2,3,'model',pool),p.serial(X,W1,W2))

    def test_pipeline_preserves_microbatch_order(self):
        X,W1,W2=p.data(batch=13,dim=4,hidden=7,out=3)
        with threadpool_limits(limits=1):
            for count in (1,4,13):
                output,row=p.pipeline(X,W1,W2,count);self.close(output,p.serial(X,W1,W2));self.assertEqual(len([e for e in row['events'] if 'microbatch' in e]),2*count)

    def test_pipeline_ideal_formula_and_invalid(self):
        X,W1,W2=p.data(batch=4,dim=2,hidden=2,out=2);_,row=p.pipeline(X,W1,W2,4)
        self.assertAlmostEqual(row['ideal_balanced_stage_bubble_fraction'],.2);self.assertAlmostEqual(row['ideal_balanced_stage_speedup'],1.6)
        with self.assertRaises(ValueError):p.pipeline(X,W1,W2,5)

    def test_lpt_assignment_conserves_work(self):
        jobs=[(i,8-i) for i in range(8)];queues=s.assignments(jobs,4,'static_lpt');self.assertEqual(sorted(x for q in queues for x in q),jobs)
        self.assertEqual([sum(job[1] for job in q) for q in queues],[9]*4)

    def test_all_schedulers_exact_once(self):
        jobs=[(i,1+i%3) for i in range(6)];reference={j[0]:s.kernel(j,500) for j in jobs}
        for method in ('static_block','static_lpt','dynamic_pool','work_stealing'):
            r=s.schedule(jobs,2,method,500);self.assertEqual(sorted(x['job'] for x in r['jobs']),list(range(6)))
            for x in r['jobs']:self.assertEqual(x['digest'],reference[x['job']])

    def test_steady_timer_starts_after_all_workers_ready(self):
        r=s.schedule([(i,1) for i in range(4)],2,'static_block',1)
        self.assertGreaterEqual(r['steady_start_s'],max(w['ready_s'] for w in r['worker_readiness']))
        self.assertAlmostEqual(r['steady_s'],r['steady_finish_s']-r['steady_start_s'],places=9)
        self.assertGreaterEqual(r['end_to_end_s'],r['steady_s'])

    def test_synchronization_preserves_count(self):
        for mode in ('locked_each','private_reduce'):
            r=s.synchronization(2,mode,total=2001);self.assertEqual(r['result'],2001);self.assertGreaterEqual(r['steady_start_s'],r['last_ready_s'])

    def test_pipe_integrity_and_bytes(self):
        r=s.communication(5,101);self.assertEqual(r['one_way_payload_bytes'],505);self.assertGreater(r['round_trip_s'],0)

    def test_native_locality_partial_tile(self):
        lib,_=locality.library();array=np.arange(13*13,dtype=float).reshape(13,13)/7
        for name in ('row_sum','column_sum','blocked_sum'):self.assertAlmostEqual(getattr(lib,name)(array,13),array.sum())


if __name__=='__main__':unittest.main()
