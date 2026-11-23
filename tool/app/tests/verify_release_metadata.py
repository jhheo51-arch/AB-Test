"""Check release aggregate metadata against exact runtime files and real logs."""
from pathlib import Path
import json,hashlib,re,argparse

def verify(root):
 root=Path(root)
 def load(n):return json.loads((root/n).read_text(encoding='utf-8'))
 def sha(n):return hashlib.sha256((root/n).read_bytes()).hexdigest()
 s=load('verification.json');run=load('integration_verification.json');baseline=load('conditions-evidence/BASELINE_CONTROLS.json')
 assert s['status']==run['status']=='PASS' and all(r['exit_code']==0 for r in run['checks'])
 assert s['integration_suite']['scripts']==len(run['checks']) and s['timestamp_utc']==run['timestamp_utc']
 expected=({p.name for pattern in ['*.js','*.css'] for p in root.glob(pattern)}|{'index.html','server.py','launch.py','launch.cmd','engine-issue-codes.json'})
 assert set(s['source_sha256'])==expected,'runtime manifest omits files'
 assert all(sha(n)==h for n,h in s['source_sha256'].items()),'stale runtime SHA-256'
 assert s['baseline']==baseline,'historical baseline changed/rewritten in aggregate'
 changed=s['intentional_baseline_control_changes'];preserved=s['preserved_baseline_bytes']
 assert set(changed)=={'design-ui.js'} and set(preserved)==set(baseline['controls'])-set(changed)
 assert all(v and sha(n)==baseline['controls'][n]['sha256'] for n,v in preserved.items())
 assert all(v['current_sha256']==sha(n) and v['historical_sha256']==baseline['controls'][n]['sha256'] and v['reason'] for n,v in changed.items())
 units=[]
 for r in run['checks']:
  if r['test'].endswith('_smoke'):units.append(len(re.findall(r'^PASS ',(root/r['log']).read_text(encoding='utf-8'),re.M)))
 assert sum(units)==s['unit_group_total']==sum(r['groups'] for r in s['unit_groups'])
 for n,count in s['browser_checks'].items():assert load(n)['count']==count and load(n)['status']=='PASS'
 assert s['browser_check_total']==sum(s['browser_checks'].values())
 semantic=s['semantic_regressions'];text=(root/semantic['log']).read_text(encoding='utf-8')
 match=re.search(r'^RESULT (\d+) semantic assertions passed \((\d+) engine gate cases;',text,re.M);assert match
 assert tuple(map(int,match.groups()))==(semantic['cases'],semantic['engine_gate_cases_included'])
 assert len(re.findall(r'^PASS ',text,re.M))==semantic['cases']
 return {'status':'PASS','runtime_hashes_checked':len(s['source_sha256']),'historical_baseline_sha256':sha('conditions-evidence/BASELINE_CONTROLS.json'),'scripts':len(run['checks']),'unit_groups':s['unit_group_total'],'separate_semantic_cases':semantic['cases'],'engine_gate_cases_included':semantic['engine_gate_cases_included'],'browser_checks':s['browser_check_total'],'preserved_control_count':len(preserved),'intentional_changed_controls':list(changed),'scope':'actual metadata/file hashes and retained execution logs; no invented execution or remote readback'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--output');args=a.parse_args();result=verify(args.root)
 if args.output:Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
