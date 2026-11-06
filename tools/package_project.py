"""Export source, evidence, histories, report and demo with a full manifest."""
import hashlib,json,shutil,subprocess,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent
sys.path.insert(0,str(ROOT))
def main():
    from tools.restore_large_files import restore_large_files
    restore_large_files(ROOT)
    subprocess.run(['git','diff','--exit-code'],cwd=ROOT,check=True)
    tracked=[s for s in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if s]
    imports=json.loads((ROOT/'provenance/imported_files.json').read_text())
    files=sorted((set(tracked)|set(imports)|{'integration_history.bundle'})-{'FILE_SHA256.json'})
    hashes={}
    for name in files:
        p=ROOT/name;assert p.is_file() and not p.is_symlink(),name;hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
        if name in imports:assert hashes[name]==imports[name],name
    manifest={'algorithm':'sha256','self_excluded':'FILE_SHA256.json','files':hashes}
    (ROOT/'FILE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    out=WORKSPACE/'output';out.mkdir(exist_ok=True);(out/'pdf').mkdir(exist_ok=True)
    archive=out/'Assignment_8_Integrated_Project.zip'
    if archive.exists():raise FileExistsError('Do not overwrite an exported deliverable')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in files+['FILE_SHA256.json']:z.write(ROOT/name,'assignment8_integrated/'+name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'assignment8_integrated/'+n for n in files+['FILE_SHA256.json']}
        for n,digest in hashes.items():assert hashlib.sha256(z.read('assignment8_integrated/'+n)).hexdigest()==digest,n
    destinations=[]
    for source,target in [(ROOT/'reports/Assignment_8_Integrated_Technical_Report.pdf',out/'pdf/Assignment_8_Integrated_Technical_Report.pdf'),(ROOT/'reports/Assignment_8_Captioned_Demo.mp4',out/'Assignment_8_Captioned_Demo.mp4')]:
        shutil.copyfile(source,target);assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest();destinations.append(str(target))
    check={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifest_files':len(hashes),'zip_entries':len(hashes)+1,'imported_files_verified':len(imports),'crc_ok':True,'manifest_ok':True,'separate_files':destinations,'integration_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    (WORKSPACE/'tmp/integration_archive_check.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check,indent=2))
if __name__=='__main__':main()
