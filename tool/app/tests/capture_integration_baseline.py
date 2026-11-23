"""Capture current upstream controls from parent's pinned blob-verified archive."""
from pathlib import Path
import hashlib,json,os,zipfile
R=Path(__file__).resolve().parents[1];E=R/'integration-evidence';E.mkdir(exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
if __name__=='__main__':
 meta_path=Path(os.environ['TMPDIR'])/'r08_upstream_base_preservation.json'
 meta=json.loads(meta_path.read_text('utf-8'));archive=Path(meta['backup'])
 assert sha(archive.read_bytes())==meta['zip_sha256']
 files={};controls={}
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name in z.namelist():
   if not name.startswith('tool/') or name.endswith('/'):continue
   data=z.read(name);blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
   assert meta['base_tree'][name]==blob,name
   files[name[5:]]={'sha256':sha(data),'git_blob_sha1':blob,'bytes':len(data)}
  for name,row in files.items():
   p=Path(name)
   if p.parent.as_posix()=='app' and (p.suffix in ['.js','.css'] or p.name in ['index.html','server.py','launch.py','launch.cmd','engine-issue-codes.json']):controls[p.name]=row
  for name in ['fonts/PretendardVariable.woff2','fonts/LICENSE.txt','help/walkthrough.mp4','help/walkthrough.ko.srt','help/walkthrough.timeline.json']:
   controls[name]=files['app/'+name]
 intentional=['app.js','server.py','launch.py','launch.cmd']
 preserved=[n for n in controls if n not in intentional]
 assert all(sha((R/n).read_bytes())==controls[n]['sha256'] for n in preserved)
 result={'base_commit':meta['base'],'previous_R08_base':'288d166f81f1a2872864bf2a7bd862fd309d4bc1','previous_R08_local_commit':'b62323bbf5e72b707bef596be3cccb24b86dfe3e','previous_proof':'Original verified R08 records archived outside worktree and in parent-owned local commit; not current combined proof.','upstream_archive_sha256':meta['zip_sha256'],'upstream_archive_verified_files':meta['verified_files'],'controls':controls,'preserved_controls':preserved,'intentional_R08_runtime_changes':intentional,'all_upstream_tool_files':files,'no_Git_operations_performed':True}
 (E/'BASELINE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('UPSTREAM_BASELINE',meta['base'],len(files),'tool files',len(preserved),'preserved controls')
