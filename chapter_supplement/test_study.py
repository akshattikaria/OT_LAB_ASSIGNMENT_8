import copy
import unittest
import numpy as np
from .study import topk,halving,asha,bayesian,schedule,embedding


def toy():
    return [{'id':i,'lr':[.003,.015,.06][i//9],'l2':[0,.01,.1][(i//3)%3],'momentum':[0,.5,.9][i%3],
             'epochs':[{'validation_mse':float(28-i)+1/(j+1),'test_mse':1000+i,'training_ns':100+i} for j in range(27)]} for i in range(27)]


class Checks(unittest.TestCase):
    def test_topk_ties_and_validation(self):
        np.testing.assert_array_equal(topk(np.array([3.,-3.,2.]),1),[3,0,0])
        with self.assertRaises(ValueError):topk(np.ones(3),0)
    def test_feedback_conservation(self):
        total=np.zeros(8);sent=np.zeros(8);residual=np.zeros(8)
        for gradient in np.random.default_rng(4).normal(size=(10,8)):
            p=gradient+residual;q=topk(p,2);residual=p-q;sent+=q;total+=gradient
        np.testing.assert_allclose(total,sent+residual,atol=1e-13)
    def test_halving_work_and_winner(self):
        selected,work,rungs=halving(toy());self.assertEqual(selected,[26]);self.assertEqual(work,81);self.assertEqual([len(r['evaluated']) for r in rungs],[27,9,3,1])
    def test_test_labels_cannot_choose_bayesian_proposals(self):
        t=toy();other=copy.deepcopy(t)
        for config in other:
            for epoch in config['epochs']:epoch['test_mse']=-1e100
        self.assertEqual(bayesian(t,1),bayesian(other,1))
    def test_asha_worker_and_checkpoint_constraints(self):
        chosen,work,data=asha(toy());workers={};done={};count=0
        for e in data['events']:
            if e['kind']=='start':
                self.assertNotIn(e['worker'],workers);self.assertEqual(e['from'],done.get(e['trial'],0));workers[e['worker']]=e['trial'];count+=e['to']-e['from']
            else:self.assertEqual(workers.pop(e['worker']),e['trial']);done[e['trial']]=e['resource']
        self.assertFalse(workers);self.assertEqual(work,count);self.assertIn(chosen[0],data['completed_final'])
    def test_scheduling_example_and_once_only(self):
        jobs=[8,7,6,5,4,3,2,1]
        for kind in ['block','cyclic','dynamic','guided']:
            r=schedule(jobs,4,kind);self.assertEqual(sorted(e['job'] for e in r['events']),list(range(8)))
            for e in r['events']:self.assertEqual(e['end']-e['start'],jobs[e['job']])
        self.assertEqual(schedule(jobs,4,'block')['makespan'],15);self.assertEqual(schedule(jobs,4,'dynamic')['makespan'],9)
    def test_embedding_chain_threshold(self):
        data=embedding();self.assertGreater(data['rows'][0]['broken'],0)
        for r in data['rows']:
            if r['strength']>1:self.assertEqual(r['broken'],0)


if __name__=='__main__':unittest.main()
