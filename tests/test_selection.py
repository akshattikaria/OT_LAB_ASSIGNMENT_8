import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from selci.common import ROOT,SUBJECT
from selci.selection import greedy,integer_program,covered


def brute(covers,costs,universe):
    choices=[]
    for flags in itertools.product((0,1),repeat=len(covers)):
        selected=[i for i,x in enumerate(flags) if x]
        if set(universe)<=covered(selected,list(map(set,covers))):choices.append(sum(costs[i] for i in selected))
    return min(choices)


class SelectionTests(unittest.TestCase):
    def test_overlap_coverage_preserved(self):
        covers=[{1,2},{2,3},{1,3}]
        for solver in (greedy,integer_program):
            result=solver(covers,[4,3,2],{1,2,3});self.assertTrue({1,2,3}<=covered(result['selected'],covers))
    def test_random_ilp_matches_all_subsets(self):
        r=random.Random(27)
        for _ in range(25):
            covers=[{j for j in range(8) if r.random()<.4} for _ in range(7)];universe=set().union(*covers);costs=[r.randint(1,30) for _ in covers]
            exact=integer_program(covers,costs,universe);self.assertEqual(exact['estimated_cost_us'],brute(covers,costs,universe));self.assertTrue(exact['optimal'])
    def test_weighted_and_count_greedy_are_distinct(self):
        covers=[{1,2,3,4},{1,2},{3,4}];costs=[100,2,2]
        self.assertEqual(greedy(covers,costs,{1,2,3,4},weighted=False)['selected'],[0]);self.assertEqual(greedy(covers,costs,{1,2,3,4})['estimated_cost_us'],4)
    def test_empty_tests_are_not_selected(self):
        for solver in (greedy,integer_program):self.assertNotIn(0,solver([set(),{1}],[1,2],{1})['selected'])
    def test_bad_models_rejected(self):
        for covers,costs,universe in [([{1}],[0],{1}),([{1}],[1],{1,2}),([],[],{1}),([{1}],[],{1}),([{1}],[1.1],{1})]:
            for solver in (greedy,integer_program):
                with self.assertRaises(ValueError):solver(covers,costs,universe)
    def test_redundant_tests_pruned(self):
        result=greedy([{1,2},{1},{2}],[3,1,1],{1,2});self.assertEqual(result['estimated_cost_us'],2)
    def test_runner_resolves_subject_from_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            env=os.environ.copy();env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1');command=[sys.executable,'-m','selci.runner','--subject',str(SUBJECT),'--out',directory]
            run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=30);self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            result=json.loads((Path(directory)/'run.json').read_text());self.assertEqual(len(result['collected']),391);self.assertEqual(result['outcomes']['passed'],391);self.assertFalse(result['failed_reports'])


if __name__=='__main__':unittest.main()
