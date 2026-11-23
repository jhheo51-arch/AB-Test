"""Pin ff current upstream via exact GitHub compare blobs, without Git operations."""
from pathlib import Path
import hashlib,json,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'startscreen-evidence';E.mkdir(exist_ok=True)
OLD='a0b506c2e9e199a3d00832b0411a49da35c3302d';NEW='ff6d463adbafa5b5525204ab9bc3adb6a8f10465'
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'local-release-verification'}),timeout=40).read()
if __name__=='__main__':
 old=json.loads((R/'integration-evidence/BASELINE.json').read_text('utf-8'));assert old['base_commit']==OLD
 comparison=json.loads(get('https://api.github.com/repos/jhheo51-arch/AB-Test/compare/'+OLD+'...'+NEW));assert comparison['commits'][-1]['sha']==NEW and comparison['base_commit']['sha']==OLD
 files=dict(old['all_upstream_tool_files']);changes=[]
 for row in comparison['files']:
  name=row['filename']
  if not name.startswith('tool/'):continue
  relative=name[5:]
  if row['status']=='removed':files.pop(relative);continue
  data=get('https://raw.githubusercontent.com/jhheo51-arch/AB-Test/'+NEW+'/'+name)
  blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blob==row['sha'],name
  files[relative]={'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':blob,'bytes':len(data)};changes.append({'path':name,**files[relative]})
 controls={n:files['app/'+n] for n in old['controls']};preserved=old['preserved_controls']
 assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==controls[n]['sha256'] for n in preserved)
 result={**old,'base_commit':NEW,'previous_R08_base':OLD,'previous_R08_local_commit':'99736c9','previous_baseline_sha256':hashlib.sha256((R/'integration-evidence/BASELINE.json').read_bytes()).hexdigest(),'controls':controls,'all_upstream_tool_files':files,'current_delta_blobs':changes,'provenance':'Pinned ff GitHub compare SHA-1 blobs layered on parent-verified a0 archive; no Git commands; older a0/288 records unchanged.'}
 (E/'BASELINE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PINNED',NEW,'preserved',len(preserved),'delta',len(changes))
