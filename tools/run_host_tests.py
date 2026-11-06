import argparse
from concurrent.futures import ThreadPoolExecutor
import json,os,re,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--python',default='python3');p.add_argument('--out',default='validation/host_tracks');a=p.parse_args();out=ROOT/a.out
    if out.exists() and any(out.iterdir()):p.error('Use a new empty output folder')
    out.mkdir(parents=True,exist_ok=True)
    def run(l):
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1');start=time.monotonic()
        with (out/(l+'.log')).open('w') as f:
            try:code=subprocess.run([a.python,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT/'tracks'/l,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240).returncode
            except subprocess.TimeoutExpired:code='timeout'
        s=(out/(l+'.log')).read_text();m=re.search(r'Ran (\d+) tests?',s);r={'track':l,'exit_code':code,'tests':int(m[1]) if m else None,'passed':code==0 and '\nOK' in s,'validation_wall_s':time.monotonic()-start};print(json.dumps(r),flush=True);return r
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,'ABCDEFGHIJ'))
    (out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    if not all(r['passed'] for r in rows):raise SystemExit(1)
if __name__=='__main__':main()
