import random
import unittest
import numpy as np

from discopt.model import Knapsack,audit
from discopt.data import teaching,controls,generate
from discopt.solvers import SOLVERS,branch_bound,dynamic_programming,exhaustive,fractional_bound,density_order
from discopt.qubo import QUBO,knapsack_qubo,enumerate_qubo,maxcut_qubo


class KnownAnswers(unittest.TestCase):
    def test_teaching(self):
        p=teaching()
        for name,f in SOLVERS.items():
            r=f(p);a=audit(p,r.selection);self.assertTrue(a['feasible'])
            self.assertEqual(a['value'],5 if name=='baseline' else 6)
    def test_greedy_counterexample(self):
        p=controls()[1]
        self.assertEqual(audit(p,SOLVERS['greedy'](p).selection)['value'],160)
        for name in ('dp','branch_bound','ilp'):
            self.assertEqual(audit(p,SOLVERS[name](p).selection)['value'],220)
    def test_empty_and_zero(self):
        for p in controls()[2:]:
            for f in SOLVERS.values():
                a=audit(p,f(p).selection);self.assertTrue(a['feasible']);self.assertEqual(a['value'],0)
    def test_item_used_once_in_dp(self):
        p=Knapsack('single',(3,),(2,),4)
        self.assertEqual(audit(p,dynamic_programming(p).selection)['value'],3)
    def test_large_item_does_not_block_later_items(self):
        p=Knapsack('large',(100,8,7),(100,4,3),7)
        for f in SOLVERS.values():self.assertEqual(audit(p,f(p).selection)['value'],15)
    def test_all_zero_values(self):
        p=Knapsack('zero',(0,0),(1,2),3)
        for f in SOLVERS.values():
            a=audit(p,f(p).selection);self.assertTrue(a['feasible']);self.assertEqual(a['value'],0)
    def test_dp_memory_guard(self):
        p=Knapsack('huge',(1,2),(1,2),10**9)
        self.assertEqual(dynamic_programming(p).status,'resource_limit')
    def test_node_limit_retains_feasible_incumbent_and_bound(self):
        p=controls()[1];r=branch_bound(p,node_limit=1)
        a=audit(p,r.selection);self.assertTrue(a['feasible'])
        self.assertGreaterEqual(r.details['upper_bound'],220)
        self.assertLessEqual(a['value'],220)


class OracleTests(unittest.TestCase):
    def test_one_hundred_random_instances_against_exhaustive(self):
        for seed in range(100):
            rng=random.Random(seed);n=rng.randint(0,10)
            p=Knapsack(f'r{seed}',tuple(rng.randint(0,40) for _ in range(n)),tuple(rng.randint(1,20) for _ in range(n)),rng.randint(0,70))
            optimum=exhaustive(p).details['objective']
            for name in ('dp','branch_bound','ilp'):
                with self.subTest(seed=seed,method=name):
                    result=SOLVERS[name](p);a=audit(p,result.selection)
                    self.assertEqual(result.status,'optimal');self.assertTrue(a['feasible']);self.assertEqual(a['value'],optimum)
            self.assertGreaterEqual(fractional_bound(p,density_order(p),0,0,0),optimum)
    def test_integer_density_order_avoids_float_rounding(self):
        p=Knapsack('ratios',(1000000001,1000000000),(1000000000,999999999),1)
        self.assertEqual(density_order(p),[1,0])
    def test_generators_reproduce(self):
        self.assertEqual(generate(20,4),generate(20,4))
    def test_oracle_guard(self):
        with self.assertRaises(ValueError):exhaustive(generate(80),max_states=1000)


class Validation(unittest.TestCase):
    def test_malformed_inputs(self):
        for p in (Knapsack('x',(1,),(0,),1),Knapsack('x',(-1,),(1,),1),Knapsack('x',(1,),(1,),-1),
                  Knapsack('x',(1.5,),(1,),2),Knapsack('x',(1,),(1,),True),Knapsack('x',(1,2),(1,),2)):
            with self.subTest(p=p),self.assertRaises(ValueError):p.validate()
    def test_audit_budget(self):self.assertFalse(audit(teaching(),[1,1,0,0])['feasible'])
    def test_audit_fractional(self):self.assertFalse(audit(teaching(),[.5,0,0,0])['feasible'])
    def test_audit_shape_and_nan(self):
        for x in (None,[0],[np.nan,0,0,0]):self.assertFalse(audit(teaching(),x)['feasible'])
    def test_audit_recomputes_values(self):
        a=audit(teaching(),[0,1,0,1]);self.assertEqual(a['value'],6);self.assertEqual(a['weight'],3)


class QuantumMapping(unittest.TestCase):
    def test_large_coefficient_cancellation_is_rejected(self):
        p=Knapsack('large_coefficients',(1,),(1,),1_000_000_000)
        with self.assertRaisesRegex(ValueError,'validated range'):knapsack_qubo(p)

    def test_all_teaching_qubo_states(self):
        q=knapsack_qubo(teaching());r=enumerate_qubo(q)
        self.assertEqual(q.n,6);self.assertEqual(len(r['states']),64)
        self.assertAlmostEqual(r['minimum_energy'],-6);self.assertTrue(r['all_ground_states_encoded_feasible'])
        self.assertLess(r['max_energy_identity_error'],1e-8)
        self.assertTrue(all(s['value']==6 for s in r['ground_states']))
    def test_weak_penalty_can_change_problem(self):
        r=enumerate_qubo(knapsack_qubo(teaching(),penalty=.1))
        self.assertFalse(r['all_ground_states_encoded_feasible'])
        self.assertTrue(any(not s['original_feasible'] for s in r['ground_states']))
    def test_twenty_random_constrained_models(self):
        for seed in range(20):
            rng=random.Random(seed);p=Knapsack(str(seed),tuple(rng.randint(0,10) for _ in range(3)),tuple(rng.randint(1,5) for _ in range(3)),rng.randint(0,7))
            r=enumerate_qubo(knapsack_qubo(p));opt=exhaustive(p).details['objective']
            self.assertAlmostEqual(r['minimum_energy'],-opt)
            self.assertTrue(r['all_ground_states_encoded_feasible'])
    def test_four_node_maxcut(self):
        q=maxcut_qubo(4,[(0,1,1),(1,2,1),(2,3,1),(3,0,1),(0,2,1)])
        r=enumerate_qubo(q);self.assertEqual(r['minimum_energy'],-4)
        self.assertEqual({s['variable_order_bits'] for s in r['ground_states']},{'0101','1010'})
    def test_triangle_maxcut(self):
        r=enumerate_qubo(maxcut_qubo(3,[(0,1,1),(1,2,1),(0,2,1)]))
        self.assertEqual(r['minimum_energy'],-2);self.assertEqual(len(r['ground_states']),6)
    def test_spin_convention_and_offsets(self):
        q=QUBO(np.array([[2.,-4.],[0.,3.]]),7,['a','b'],{'problem':'maxcut','edges':[]})
        ising=q.ising()
        for x in ([0,0],[0,1],[1,0],[1,1]):
            z=1-2*np.array(x);energy=ising['offset']+np.array(ising['h'])@z+z@np.array(ising['J_upper'])@z
            self.assertEqual(q.energy(x),energy)
    def test_bad_qubo_inputs(self):
        with self.assertRaises(ValueError):QUBO(np.ones((2,2)),0,['a','b'],{}).validate()
        with self.assertRaises(ValueError):knapsack_qubo(teaching(),penalty=-1)
        with self.assertRaises(ValueError):maxcut_qubo(2,[(0,0,1)])
    def test_bit_order_roundtrip(self):
        r=enumerate_qubo(knapsack_qubo(teaching()))
        for s in r['states']:
            self.assertEqual(sum(b*(1<<i) for i,b in enumerate(s['bits'])),s['index'])
            self.assertEqual(s['statevector_label'],s['variable_order_bits'][::-1])


if __name__=='__main__':unittest.main(verbosity=2)
