"""Paired function runtimes; never substituted for AI response-generation time."""
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import random
import statistics
import time

ROOT=Path(__file__).resolve().parents[1]


def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.solve_knapsack


def value_weight_oracle(weights,values,capacity):
    # Independent capacity-at-most DP, without index tuples or exact-weight
    # states: certifies optimal value and its least sufficient capacity.
    previous=[0]*(capacity+1)
    for weight,value in zip(weights,values):
        current=previous.copy()
        for room in range(weight,capacity+1):current[room]=max(previous[room],previous[room-weight]+value)
        previous=current
    value=previous[-1]
    return value,next(room for room,v in enumerate(previous) if v==value)


def check(result,weights,values,capacity,reference):
    assert set(result)=={'value','weight','indices'}
    ids=result['indices'];assert ids==sorted(set(ids)) and all(isinstance(i,int) and 0<=i<len(weights) for i in ids)
    assert sum(weights[i] for i in ids)==result['weight']<=capacity
    assert sum(values[i] for i in ids)==result['value']
    assert (result['value'],result['weight'])==reference


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'ai_tool_comparison/benchmark_results.json')
    out=parser.parse_args().out
    if out.exists():raise FileExistsError('Preserve existing benchmark evidence')
    names={'chatgpt':'chatgpt_candidate.py','gemini':'gemini_candidate_01.py'}
    candidates={k:load(ROOT/'ai_tool_comparison'/v) for k,v in names.items()}
    specs=[('small',12,25,80),('medium_tight',35,150,500),('large_tight',50,500,5000),('large_loose',50,100,10000)]
    cases=[];rows=[]
    for index,(name,n,max_weight,capacity) in enumerate(specs):
        rng=random.Random(241070005+index);weights=[rng.randint(1,max_weight) for _ in range(n)];values=[rng.randint(0,200) for _ in range(n)]
        reference=value_weight_oracle(weights,values,capacity)
        cases.append({'name':name,'weights':weights,'values':values,'capacity':capacity,'reference_value':reference[0],'reference_min_weight':reference[1]})
        warm={k:fn(weights,values,capacity) for k,fn in candidates.items()}
        for result in warm.values():check(result,weights,values,capacity,reference)
        assert warm['chatgpt']==warm['gemini']
        order_rng=random.Random(241070005+100+index)
        for repetition in range(7):
            order=list(candidates);order_rng.shuffle(order)
            for method in order:
                start=time.perf_counter_ns();result=candidates[method](weights,values,capacity);elapsed=time.perf_counter_ns()-start
                check(result,weights,values,capacity,reference);assert result==warm[method]
                rows.append({'case':name,'method':method,'repetition':repetition,'elapsed_ns':elapsed})
    summary=[]
    for case in cases:
        row={'case':case['name']}
        for method in candidates:
            values=[r['elapsed_ns']/1e6 for r in rows if r['case']==case['name'] and r['method']==method]
            row[method]={'median_ms':statistics.median(values),'min_ms':min(values),'max_ms':max(values)}
        row['chatgpt_over_gemini_time_ratio']=row['chatgpt']['median_ms']/row['gemini']['median_ms'];summary.append(row)
    record={'python':platform.python_version(),'platform':platform.platform(),'seed':241070005,'repetitions':7,'cases':cases,'rows':rows,'summary':summary,
            'source_sha256':{k:hashlib.sha256((ROOT/'ai_tool_comparison'/v).read_bytes()).hexdigest() for k,v in names.items()},
            'scope':'Seven paired, seeded-order trials per function/case; one warmup each; function call only. Shared cloud Python host, not student laptop. Validation/import/oracle/data generation excluded. AI generation latency is separate. Large cases use independent value/min-weight reference plus pair agreement; lexicographic ties are independently checked by the common tiny exhaustive tests. No universal speed ranking.'}
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
