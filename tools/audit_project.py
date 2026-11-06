"""Retained-data checks; does not replace historical measurements."""
import hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def main():
    hashes=read('provenance/imported_files.json')
    for name,digest in hashes.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    sources=read('provenance/source_archives.json');assert {r['track'] for r in sources}==set('ABCDEFGHIJ')
    hosts=read('validation/host_tracks/summary.json');assert all(r['passed'] and r['exit_code']==0 for r in hosts);assert sum(r['tests'] for r in hosts)==243
    assert 'Ran 7 tests' in (ROOT/'validation/supplement_tests.log').read_text() and '\nOK' in (ROOT/'validation/supplement_tests.log').read_text()
    candidate=read('ai_tool_comparison/chatgpt_result_01.json');assert candidate['passed'] and candidate['tests']==9
    assert hashlib.sha256((ROOT/'ai_tool_comparison/chatgpt_candidate.py').read_bytes()).hexdigest()==candidate['sha256']
    checklist=read('docs/CHAPTER6_CHECKLIST.json')
    for row in checklist['topics']:
        for p in row['evidence']:assert (ROOT/p).is_file(),p
    hp=read('chapter_supplement/results/hpo.json');assert len(hp['summary'])==30 and len(hp['raw'])==5
    expected={}
    for item in hp['raw']:
        trace=item['traces'];assert len(trace)==27 and all(len(t['epochs'])==27 for t in trace)
        for t in trace:
            assert all(r['training_ns']>0 and math.isfinite(r['validation_mse']) and math.isfinite(r['test_mse']) for r in t['epochs'])
        workers={};done={};work=0;last=-1.
        for event in item['asha']['events']:
            assert event['time']>=last;last=event['time']
            if event['kind']=='start':
                assert event['worker'] not in workers and event['from']==done.get(event['trial'],0)
                workers[event['worker']]=event['trial'];work+=event['to']-event['from']
            else:assert workers.pop(event['worker'])==event['trial'];done[event['trial']]=event['resource']
        assert not workers
        for method,ids,units in [('input_first',[0],27),('grid_all',list(range(27)),729),('random_9',item['random_ids'],243),('bayesian_9',item['bayesian_ids'],243),('successive_halving',item['halving'][-1]['ranking'][:1],81),('asha_replay',item['asha']['completed_final'],work)]:
            chosen=min(ids,key=lambda k:(trace[k]['epochs'][-1]['validation_mse'],k));r=next(r for r in hp['summary'] if r['seed']==item['seed'] and r['method']==method);assert r['selected']==chosen and r['epoch_units']==units
            assert r['validation_mse']==trace[chosen]['epochs'][-1]['validation_mse'] and r['test_mse']==trace[chosen]['epochs'][-1]['test_mse']
    comp=read('chapter_supplement/results/compression.json');assert len(comp['runs'])==20
    for r in comp['runs']:
        assert math.isfinite(r['objective']) and r['wall_s']>0
        if 'error_feedback' in r['method']:assert r['conservation_error']<1e-10
        assert r['logical_bytes']==(256000 if r['method']=='dense' else 40000 if r['method'].startswith('int8') else 24000)
    layout=read('chapter_supplement/results/layouts.json');assert len(layout['layouts'])==28 and all(r['d']*r['t']*r['p']==64 for r in layout['layouts'])
    optimum=min(r['modeled_s'] for r in layout['layouts'] if r['feasible']);assert layout['layouts'][layout['finite_optimum_index']]['modeled_s']==optimum
    for r in layout['ga']:assert math.isclose(r['gap'],layout['layouts'][r['selected']]['modeled_s']-optimum,abs_tol=1e-12)
    embedding=read('chapter_supplement/results/embedding.json')
    for r in embedding['rows']:
        if r['strength']>1:assert r['broken']==0
    schedules=read('chapter_supplement/results/scheduling.json')
    for r in schedules['rows']:assert sorted(e['job'] for e in r['events'])==list(range(8))
    assert next(r for r in schedules['rows'] if r['method']=='block')['makespan']==15
    assert next(r for r in schedules['rows'] if r['method']=='dynamic')['makespan']==9
    native=read('chapter_supplement/results/false_sharing.json');assert native['executed'] and len(native['rows'])==14
    for rep in range(7):assert {r['stride'] for r in native['rows'] if r['repeat']==rep}=={1,8}
    assert all(r['increments']==2000000 and r['seconds']>0 for r in native['rows'])
    e=read('tracks/E/results/summary.json');assert sum(r['methods']['baseline']['feasible'] for r in e)==64;assert sum(r['methods']['greedy']['feasible'] for r in e)==70;assert sum(r['methods']['ilp']['feasible'] for r in e)==75
    assert math.isclose(e[0]['comparisons']['baseline']['mean_savings_pct'],49.44032880029046,abs_tol=1e-10)
    j=read('tracks/J/results/summary.json');assert j['ilp']['tests']==74 and j['ilp']['full_killed_retained']==13 and j['ilp']['full_killed_total']==16
    assert math.isclose(j['ilp']['wall_speedup'],j['full']['wall_median_s']/j['ilp']['wall_median_s'],rel_tol=1e-12)
    video=read('validation/video_check.json');assert 99<=video['duration_s']<=102 and video['source_cli_verified']
    from pypdf import PdfReader
    pdf=PdfReader(ROOT/'reports/Assignment_8_Integrated_Technical_Report.pdf');assert len(pdf.pages)==21
    text='\n'.join(p.extract_text() for p in pdf.pages);assert all('Track '+l+':' in text for l in 'ABCDEFGHIJ');assert '\ufffd' not in text
    result={'passed':True,'imported_files_verified':len(hashes),'tracks':len(sources),'fresh_track_host_tests':243,'supplement_tests':7,'comparison_baseline_tests':9,'course_topic_entries':len(checklist['topics']),'research_reference_entries':len(checklist['research_references']),'hpo_policy_rows':30,'compression_runs':20,'native_control_trials':14,'pdf_pages':21,'demo_seconds':video['duration_s'],'scope':'Integrity, evidence links and retained arithmetic. Original track histories/timings remain unchanged; pending comparison/publication/research items remain open.'}
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':main()
