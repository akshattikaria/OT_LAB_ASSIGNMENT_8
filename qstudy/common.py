import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);text=json.dumps(value,indent=2,allow_nan=False)+'\n';temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as f:f.write(text);f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)
    if path.read_text()!=text:raise IOError('Saved evidence differs: '+str(path))


def sha_file(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution_close(a,b,tolerance=1e-9):
    import numpy as np
    if not np.allclose(a,b,atol=tolerance,rtol=tolerance):raise AssertionError('Independent distribution mismatch')
