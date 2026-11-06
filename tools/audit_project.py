"""Retained-data checks; does not replace historical measurements."""
import hashlib,json,math,re,random,statistics,sys,io
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def read(p):return json.loads((ROOT/p).read_text())
def main():
    from tools.restore_large_files import restore_large_files
    restore_large_files(ROOT)
    hashes=read('provenance/imported_files.json')
    for name,digest in hashes.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    sources=read('provenance/source_archives.json');assert {r['track'] for r in sources}==set('ABCDEFGHIJ')
    hosts=read('validation/host_tracks/summary.json');assert all(r['passed'] and r['exit_code']==0 for r in hosts);assert sum(r['tests'] for r in hosts)==243
    assert 'Ran 7 tests' in (ROOT/'validation/supplement_tests.log').read_text() and '\nOK' in (ROOT/'validation/supplement_tests.log').read_text()
    candidate=read('ai_tool_comparison/chatgpt_result_01.json');assert candidate['passed'] and candidate['tests']==9
    assert hashlib.sha256((ROOT/'ai_tool_comparison/chatgpt_candidate.py').read_bytes()).hexdigest()==candidate['sha256']
    comparison=read('ai_tool_comparison/comparison_record.json')
    assert comparison['status']=='comparison_recorded_from_supplied_response'
    assert comparison['generation_latency_comparable'] is False
    assert comparison['second_tool']['exact_model_label']=='Argon High'
    latency=comparison['second_tool']['user_reported_generation_latency']
    assert latency['estimate_s']==60 and latency['approximate_uncertainty_s']==3 and latency['instrumented'] is False
    assert comparison['chatgpt']['ai_generation_latency_s'] is None and comparison['second_tool']['ai_generation_latency_s'] is None
    benchmark=read('ai_tool_comparison/benchmark_results.json')
    for method,source,result in [('chatgpt','chatgpt_candidate.py','chatgpt_result_20261106.json'),('gemini','gemini_candidate_01.py','gemini_result_01.json')]:
        result=read('ai_tool_comparison/'+result)
        digest=hashlib.sha256((ROOT/'ai_tool_comparison'/source).read_bytes()).hexdigest()
        assert digest==result['sha256']==benchmark['source_sha256'][method]
        assert result['passed'] and result['tests']==9 and result['failures']==result['errors']==0
        assert result['ai_generation_latency_s'] is None
    assert benchmark['repetitions']==7 and len(benchmark['cases'])==4 and len(benchmark['rows'])==56
    specs=[('small',12,25,80),('medium_tight',35,150,500),('large_tight',50,500,5000),('large_loose',50,100,10000)]
    assert benchmark['seed']==241070005
    for index,(name,n,max_weight,capacity) in enumerate(specs):
        case=benchmark['cases'][index];rng=random.Random(241070005+index)
        assert case['name']==name and case['capacity']==capacity
        assert case['weights']==[rng.randint(1,max_weight) for _ in range(n)]
        assert case['values']==[rng.randint(0,200) for _ in range(n)]
        summary=benchmark['summary'][index];assert summary['case']==name
        for method in ['chatgpt','gemini']:
            rows=[r for r in benchmark['rows'] if r['case']==name and r['method']==method]
            assert sorted(r['repetition'] for r in rows)==list(range(7)) and all(r['elapsed_ns']>0 for r in rows)
            times=[r['elapsed_ns']/1e6 for r in rows]
            for key,value in [('median_ms',statistics.median(times)),('min_ms',min(times)),('max_ms',max(times))]:assert math.isclose(summary[method][key],value,rel_tol=1e-12)
        assert math.isclose(summary['chatgpt_over_gemini_time_ratio'],summary['chatgpt']['median_ms']/summary['gemini']['median_ms'],rel_tol=1e-12)
    checklist=read('docs/CHAPTER6_CHECKLIST.json')
    assert len(checklist['research_references'])==22
    quantum_refs={'TensorHyper-VQC','Negative learning-rate phases','Quantum measurement temperature','Quantum-gradient nested optimization','QML-Liver'}
    assert quantum_refs <= {r['topic'] for r in checklist['research_references']}
    review_hosts=read('validation/final-review-host/summary.json')
    assert {r['track'] for r in review_hosts}==set('ABCDEFGHIJ')
    assert all(r['passed'] and r['exit_code']==0 for r in review_hosts) and sum(r['tests'] for r in review_hosts)==243
    review_supplement=(ROOT/'validation/final_review_supplement.log').read_text()
    assert 'Ran 7 tests' in review_supplement and '\nOK' in review_supplement
    for method,source in [('chatgpt','chatgpt_candidate.py'),('gemini','gemini_candidate_01.py')]:
        result=read(f'validation/final_review_{method}_result.json')
        assert result['passed'] and result['tests']==9 and result['sha256']==hashlib.sha256((ROOT/'ai_tool_comparison'/source).read_bytes()).hexdigest()
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
    pdf=PdfReader(ROOT/'reports/Assignment_8_Integrated_Technical_Report.pdf');assert len(pdf.pages)==27
    text='\n'.join(p.extract_text() for p in pdf.pages);assert all('Track '+l+':' in text for l in 'ABCDEFGHIJ');assert '\ufffd' not in text
    assert 'Two-tool comparison: ChatGPT and Gemini' in text and 'Argon High' in text
    from research_supplement.audit import main as research_audit
    with redirect_stdout(io.StringIO()):research=research_audit()
    assert research['passed'] and research['new_mathematical_tests']==20
    assert checklist['fidelity_counts']==read('research_supplement/SOURCE_REGISTRY.json')['fidelity_counts']
    assert 'QML-Liver on author data' in text and 'six mechanism-only' in text
    result={'passed':True,'imported_files_verified':len(hashes),'tracks':len(sources),'retained_track_host_tests':243,'retained_host_test_date':'2026-11-04','supplement_tests':7,'comparison_baseline_tests':9,'comparison_tools':2,'shared_tests_per_tool':9,'exhaustive_small_cases_per_tool':100,'timed_function_calls':56,'generation_latency_comparable':False,'course_topic_entries':len(checklist['topics']),'research_reference_entries':len(checklist['research_references']),'hpo_policy_rows':30,'compression_runs':20,'native_control_trials':14,'pdf_pages':len(pdf.pages),'demo_seconds':video['duration_s'],'scope':'Integrity, evidence links and retained arithmetic. Original A-J code/results unchanged; supplied Gemini comparison recorded. Full chat exports, publication and research interpretation remain open.'}
    result.update(final_review_track_host_tests=243,final_review_supplement_tests=7,final_review_shared_tests_per_tool=9,submission_ready=False,research=research)
    result['scope']='Integrity, source links and retained arithmetic/certificates. Original A-J code/results unchanged; 22 research experiments/controls added. Public repository is supplied. Authentic AI platform evidence and six exact published policies remain open.'
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':main()
