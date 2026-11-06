"""Child-process pytest observer; optional per-test coverage is never timed as CI."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time
import coverage
import pytest
from .common import dump


class Observer:
    def __init__(self,cov=None):self.cov=cov;self.records={};self.collected=[]
    def pytest_collection_finish(self,session):self.collected=[item.nodeid for item in session.items]
    @pytest.hookimpl(hookwrapper=True,tryfirst=True)
    def pytest_runtest_protocol(self,item,nextitem):
        if self.cov:self.cov.switch_context(item.nodeid)
        yield
        if self.cov:self.cov.switch_context('__collection__')
    def pytest_runtest_logreport(self,report):
        self.records.setdefault(report.nodeid,{})[report.when]={'outcome':report.outcome,'duration_s':report.duration}


def execute(subject,output,nodes=None,trace=False):
    subject=Path(subject).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(subject/'src'));cov=None
    if trace:
        cov=coverage.Coverage(data_file=str(output/'contexts.sqlite'),source=[str(subject/'src/cachetools')],branch=True,config_file=False);cov.start();cov.switch_context('__collection__')
    observer=Observer(cov);arguments=['-q','--disable-warnings','-p','no:cacheprovider','-o','addopts=']+(nodes if nodes is not None else ['tests']);start=time.perf_counter_ns();code=int(pytest.main(arguments,plugins=[observer]));elapsed=time.perf_counter_ns()-start
    if cov:cov.stop();cov.save()
    import cachetools
    package_file=Path(cachetools.__file__).resolve()
    if not package_file.is_relative_to(subject/'src/cachetools'):raise AssertionError('Wrong cachetools import: '+str(package_file))
    rows=[]
    for node in observer.collected:
        phases=observer.records.get(node,{});rows.append({'nodeid':node,'phases':phases,'duration_s':sum(p['duration_s'] for p in phases.values()),'call_outcome':phases.get('call',{}).get('outcome','not_called')})
    result={'exit_code':code,'pytest_elapsed_ns':elapsed,'collected':observer.collected,'tests':rows,'outcomes':dict(Counter(row['call_outcome'] for row in rows)),'package_file':str(package_file),'package_version':cachetools.__version__,'trace_enabled':trace}
    dump(output/'run.json',result)
    if cov:
        data=cov.get_data();matrix={node:set() for node in observer.collected};file_paths={};collection=set()
        for filename in sorted(data.measured_files()):
            path=Path(filename);relative=str(path.relative_to(subject)).replace('\\','/');file_paths[relative]=filename
            for line,contexts in data.contexts_by_lineno(filename).items():
                key=relative+':'+str(line)
                for context in contexts:
                    if context in matrix:matrix[context].add(key)
                    elif context=='__collection__':collection.add(key)
        incidence={'test_nodes':observer.collected,'coverage':{node:sorted(lines) for node,lines in matrix.items()},'universe':sorted(set().union(*matrix.values())),'collection_lines':sorted(collection),'measured_files':file_paths,'definition':'Union of source lines exercised in per-test setup/call/teardown contexts, excluding collection-only execution. This is not all possible statement/branch coverage.'}
        dump(output/'incidence.json',incidence);cov.json_report(outfile=str(output/'coverage_report.json'),pretty_print=True,show_contexts=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--subject',required=True);p.add_argument('--out',required=True);p.add_argument('--nodes');p.add_argument('--trace',action='store_true');args=p.parse_args();nodes=json.loads(Path(args.nodes).read_text()) if args.nodes else None
    result=execute(args.subject,args.out,nodes,args.trace);raise SystemExit(result['exit_code'])


if __name__=='__main__':main()
