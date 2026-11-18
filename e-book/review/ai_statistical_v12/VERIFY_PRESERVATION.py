"""Freeze and check the source boundary for this audit only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'e-book/review/statistical_v12/INPUT_MANIFEST.json').read_text(encoding='utf-8'))
prior=[]
for f in manifest['files']:
 actual=hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest();prior.append({'path':f['path'],'expected':f['sha256'],'actual':actual,'status':'passed' if actual==f['sha256'] else 'mismatch'})
assert all(x['status']=='passed' for x in prior)
paths=set(f['path'] for f in manifest['files'])
for folder in ['e-book/exports/v12','e-book/virtual-data','e-book/analysis/winner_v04','e-book/analysis/v02']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:paths.add(p.relative_to(ROOT).as_posix())
current={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)}
baseline=OUT/'BASELINE.json'
if not baseline.exists():
 report={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'baseline_commit':'eefdd4ee9ea026c06d65a760706a742e02407bce','source_hashes':current,'prior_inventory_checks':prior,'scope':'AI and separate code audit only; do not edit the book or advance publication gates','human_review_completed':False}
 baseline.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
else:
 old=json.loads(baseline.read_text(encoding='utf-8'))['source_hashes'];changed=[name for name,sha in old.items() if current.get(name)!=sha];assert not changed,changed
 report={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'protected_source_files':len(old),'changed_files':changed,'prior_inventory_files':len(prior),'status':'passed','human_review_completed':False}
 (OUT/'PRESERVATION_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'source_files':len(current),'prior_inventory_passed':len(prior),'source_boundary':'unchanged','human_review_completed':False}));
