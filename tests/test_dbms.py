from contextlib import closing
import itertools
import random
import sqlite3
import unittest
import numpy as np
from dblab.core import SCHEMA,INDEXES,QUERIES,CITIES,cases,fingerprint,generate_rows,reference,sqlsum
from dblab.select import greedy,ilp,exhaustive,utility


class SelectionTests(unittest.TestCase):
    def test_overlap_not_double_counted(self):
        gains=[[10,9],[0,0]];self.assertEqual(utility([0,1],gains),10);self.assertEqual(greedy([1,1],gains,2)['selected'],[0])
    def test_greedy_can_be_suboptimal(self):
        costs=[6,5,5];gains=np.diag([12,9,9]);self.assertEqual(greedy(costs,gains,10)['utility_ms'],12);self.assertEqual(ilp(costs,gains,10)['utility_ms'],18)
    def test_random_ilp_matches_every_portfolio(self):
        r=random.Random(92)
        for _ in range(25):
            costs=[r.randint(1,12) for _ in range(6)];gains=[[r.randrange(15)/10 for _ in costs] for _ in range(4)];budget=r.randint(0,sum(costs))
            exact=exhaustive(costs,gains,budget);chosen=ilp(costs,gains,budget);approx=greedy(costs,gains,budget)
            self.assertAlmostEqual(chosen['utility_ms'],exact['best']['utility_ms'],places=7);self.assertLessEqual(chosen['cost_kib'],budget);self.assertLessEqual(approx['utility_ms'],chosen['utility_ms']+1e-7)
    def test_empty_and_zero_benefits(self):
        for solver in (greedy,ilp):
            self.assertEqual(solver([3,5],[[1,2]],0)['selected'],[]);self.assertEqual(solver([3,5],[[0,0]],8)['selected'],[])
    def test_invalid_model_rejected(self):
        for costs,gains,budget in [([0],[[1]],1),([1],[[float('nan')]],1),([1],[[-1]],1),([1],[[1]],-1),([1,2],[[1]],1)]:
            for solver in (greedy,ilp):
                with self.assertRaises(ValueError):solver(costs,gains,budget)
    def test_greedy_is_deterministic_and_respects_budget(self):
        self.assertEqual(greedy([1,1],[[2,2]],1)['selected'],[0]);self.assertEqual(greedy([8,9],[[10,12]],7)['selected'],[])


class QueryTests(unittest.TestCase):
    rows=[(1,1,1,24,'confirmed',100,200),(2,1,1,24,'confirmed',None,None),(3,2,2,48,'cancelled',50,30),
          (4,1,600,24,'pending',0,0),(5,3,600,8759,'expired',70,None),(6,2,2,0,'confirmed',200,80),(7,2,2,100,'confirmed',None,None)]
    def fixture_cases(self):
        params={'customer':[(1,),(999,)],'station':[(1,24,25),(1,24,24),(2,100,101)],'confirmed':[(1,24,25),(2,100,101),(2,0,1)],
                'status':[('confirmed',0,8760),('pending',24,25),('expired',0,8759)],'daily':[(0,8760),(24,24),(24,25)],'city':[('City00',0,8760),('City09',0,8760),('City01',100,101)]}
        return [{'id':kind+str(i),'kind':kind,'params':p} for kind,values in params.items() for i,p in enumerate(values)]
    def database(self):
        c=sqlite3.connect(':memory:');c.execute('PRAGMA foreign_keys=ON');c.executescript(SCHEMA)
        c.executemany('INSERT INTO customers VALUES(?,?)',[(i,'City00') for i in (1,2,3)]);c.executemany('INSERT INTO stations VALUES(?,?)',[(i,CITIES[(i-1)%10]) for i in (1,2,600)])
        c.executemany('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',self.rows);return c
    def test_all_64_real_index_portfolios_preserve_null_ties_and_boundaries(self):
        for flags in itertools.product((0,1),repeat=len(INDEXES)):
            # Match the actual experiment: a fresh schema/connection per portfolio.
            with closing(self.database()) as c:
                for name,enabled in zip(INDEXES,flags):
                    if enabled:c.execute(INDEXES[name])
                c.execute('ANALYZE')
                for case in self.fixture_cases():self.assertEqual(c.execute(QUERIES[case['kind']],case['params']).fetchall(),reference(self.rows,case),(flags,case))
    def test_partial_index_parameter_switch_in_fresh_portfolio(self):
        with closing(self.database()) as c:
            c.execute(INDEXES['confirmed_station']);c.execute('ANALYZE')
            for status in ('confirmed','pending','confirmed','pending'):
                case={'kind':'status','params':(status,0,8760)}
                self.assertEqual(c.execute(QUERIES['status'],case['params']).fetchall(),reference(self.rows,case))
    def test_tied_top_k_is_deterministic(self):
        expected=reference(self.rows,{'kind':'customer','params':[1]});self.assertEqual([r[0] for r in expected],[4,2,1])
    def test_sql_null_sum(self):
        self.assertIsNone(sqlsum([None,None]));self.assertEqual(sqlsum([None,0,2]),2)
        self.assertEqual(reference(self.rows,{'kind':'station','params':[2,100,101]}),[(1,None,None)])
    def test_real_constraints(self):
        with closing(self.database()) as c:
            with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO bookings VALUES(99,999,1,2,'confirmed',1,1)")
            with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO bookings VALUES(99,1,1,8760,'confirmed',1,1)")
    def test_case_split_and_bound_parameters(self):
        data=cases();self.assertEqual(len(data),30);self.assertEqual(sum(c['split']=='train' for c in data),12);self.assertEqual(len({c['id'] for c in data}),30)
        for case in data:self.assertEqual(QUERIES[case['kind']].count('?'),len(case['params']))
    def test_fingerprint_preserves_null_order_and_duplicates(self):
        self.assertEqual(fingerprint([(1,None)]),fingerprint([[1,None]]));self.assertNotEqual(fingerprint([[1],[2]]),fingerprint([[2],[1]]));self.assertNotEqual(fingerprint([[1]]),fingerprint([[1],[1]]))
    def test_generator_reproducibility(self):
        self.assertEqual(generate_rows(200,7),generate_rows(200,7));self.assertNotEqual(generate_rows(200,7),generate_rows(200,8))
    def test_generator_domain_and_input(self):
        for r in generate_rows(1000,7):self.assertTrue(1<=r[1]<=20000 and 1<=r[2]<=600 and 0<=r[3]<8760)
        with self.assertRaises(ValueError):generate_rows(0)


if __name__=='__main__':unittest.main()
