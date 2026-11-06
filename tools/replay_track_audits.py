"""Run original audit CLIs in disposable copies to preserve imported bytes."""
from concurrent.futures import ThreadPoolExecutor
import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'validation/track_audit_replays';out.mkdir(exist_ok=True)
    modules={'C':'qopt.audit','D':'distopt','F':'toycc','G':'oslab','H':'dblab','I':'qstudy','J':'selci.audit'}
    def run(item):
        letter,module=item
        with tempfile.TemporaryDirectory(prefix='a8-audit-') as directory:
            target=Path(directory)/letter;shutil.copytree(ROOT/'tracks'/letter,target)
            command=[sys.executable,'-m',module]
            command+=['--out','results'] if letter=='J' else ['results'] if letter=='C' else ['audit','results']
            env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            with (out/(letter+'.log')).open('w') as log:
                try:code=subprocess.run(command,cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240).returncode
                except subprocess.TimeoutExpired:code='timeout'
        result={'track':letter,'exit_code':code,'passed':code==0,'scope':'Original retained-data audit in isolated copy; no source timing overwritten.'};print(json.dumps(result),flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,modules.items()))
    (out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    if not all(r['passed'] for r in rows):raise SystemExit(1)
if __name__=='__main__':main()
