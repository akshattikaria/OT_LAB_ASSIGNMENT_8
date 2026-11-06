"""Stage the reviewed package, including deliberately isolated track imports.

No remote creation, push or publication is performed by this script.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def main():
    from tools.restore_large_files import restore_large_files
    restore_large_files(ROOT)
    split_targets={i['path'] for i in json.loads((ROOT/'provenance/large_files.json').read_text())['files']} if (ROOT/'provenance/large_files.json').exists() else set()
    p=argparse.ArgumentParser();p.add_argument('--stage',action='store_true');a=p.parse_args();files=json.loads((ROOT/'provenance/imported_files.json').read_text())
    for name,digest in files.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    if not a.stage:print('Verified',len(files),'original imported files. Use --stage to stage these exact files and authored integration files; no push occurs.');return
    if not (ROOT/'.git').is_dir():subprocess.run(['git','init','-b','main'],cwd=ROOT,check=True)
    subprocess.run(['git','add','.'],cwd=ROOT,check=True)
    names=[name for name in files if name not in split_targets]
    for i in range(0,len(names),100):subprocess.run(['git','add','-f','--',*names[i:i+100]],cwd=ROOT,check=True)
    for name in ['FILE_SHA256.json','integration_history.bundle']:
        if (ROOT/name).is_file():subprocess.run(['git','add','-f','--',name],cwd=ROOT,check=True)
    print('Staged the reviewed project. Inspect git status/diff, commit, then add the correct repository remote yourself.')
if __name__=='__main__':main()
