import argparse,hashlib,importlib.util,itertools,json,random,time,unittest
from pathlib import Path
def oracle(w,v,c):
    options=[]
    for flags in itertools.product((0,1),repeat=len(w)):
        ids=[i for i,b in enumerate(flags) if b];weight=sum(w[i] for i in ids)
        if weight<=c:options.append((sum(v[i] for i in ids),weight,ids))
    value,weight,ids=min(options,key=lambda r:(-r[0],r[1],r[2]));return {'value':value,'weight':weight,'indices':ids}
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args();path=Path(a.candidate);out=Path(a.out)
    if out.exists():p.error('Use a new result file')
    spec=importlib.util.spec_from_file_location('candidate',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);solve=module.solve_knapsack
    class Tests(unittest.TestCase):
        def test_basic(self):self.assertEqual(solve([3,2,2,1],[5,4,3,2],3),{'value':6,'weight':3,'indices':[1,3]})
        def test_empty_and_zero_and_none_fit(self):
            for w,v,c in [([],[],3),([1],[3],0),([3,4],[8,9],2)]:self.assertEqual(solve(w,v,c),{'value':0,'weight':0,'indices':[]})
        def test_no_item_reuse(self):self.assertEqual(solve([2],[3],4)['value'],3)
        def test_minimum_weight_tie(self):self.assertEqual(solve([3,2],[5,5],3)['indices'],[1])
        def test_lexicographic_tie(self):self.assertEqual(solve([1,1,2],[1,1,2],2)['indices'],[0,1])
        def test_zero_values(self):self.assertEqual(solve([1,2],[0,0],3)['indices'],[])
        def test_inputs_unchanged(self):
            w,v=[2,1,3],[5,1,8];solve(w,v,4);self.assertEqual(w,[2,1,3]);self.assertEqual(v,[5,1,8])
        def test_invalid(self):
            for w,v,c in [([0],[1],1),([-1],[1],1),([1],[-1],2),([True],[1],2),([1],[True],2),([1.],[1],2),([1],[1.],2),([1],[1],True),([1],[1],1.),([1],[1],-1),([1],[],2)]:
                with self.assertRaises(ValueError):solve(w,v,c)
        def test_random_exhaustive_oracles(self):
            rng=random.Random(241070005)
            for _ in range(100):
                n=rng.randrange(1,10);w=[rng.randrange(1,8) for _ in range(n)];v=[rng.randrange(0,12) for _ in range(n)];c=rng.randrange(0,22)
                self.assertEqual(solve(w,v,c),oracle(w,v,c))
    start=time.perf_counter();r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));record={'candidate':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tests':r.testsRun,'passed':r.wasSuccessful(),'failures':len(r.failures),'errors':len(r.errors),'code_test_execution_s':time.perf_counter()-start,'ai_generation_latency_s':None}
    out.write_text(json.dumps(record,indent=2)+'\n')
    if not r.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
