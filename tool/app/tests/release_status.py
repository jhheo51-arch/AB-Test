"""Share count derivation between release generation and verification.
Only source tool/STATUS.json or ZIP-owned app-root STATUS.json is eligible.
Never traverse to an arbitrary extraction parent or create a missing target.
"""
from pathlib import Path
import json

def counts(summary):
 return {'scripts':summary['integration_suite']['scripts'],'smoke_unit_groups':summary['unit_group_total'],'separate_semantic_cases':summary['semantic_regressions']['cases'],'engine_gate_cases_included_in_semantic':summary['semantic_regressions']['engine_gate_cases_included'],'browser_checks':summary['browser_check_total']}

def storage(summary):
 s=summary['storage'];return {'storage_schema':s['schema'],'csv_plan_storage_schema':s['csv_plan_schema'],'rollout_storage_schema':s['rollout_schema'],'legacy_storage_versions':s['legacy_imports']}

def target(root):
 root=Path(root).resolve()
 if root.name=='app' and root.parent.name=='tool':candidate=root.parent/'STATUS.json'
 else:candidate=root/'STATUS.json'
 if not candidate.is_file():return None
 data=json.loads(candidate.read_text(encoding='utf-8'))
 assert data.get('app')=='tool/app' and data.get('release_metadata')=='tool/app/verification.json','unexpected STATUS contract'
 return candidate

def sync(root,summary):
 path=target(root)
 if path is None:return {'status':'ABSENT','written':False}
 data=json.loads(path.read_text(encoding='utf-8'));data['current_verified_counts']=counts(summary);data.setdefault('conditions',{}).update(storage(summary));data['current_base_commit']=summary['upstream_integration']['base_commit'];data['metadata_policy']='Current runtime SHA-256 and actual log-derived counts; immutable current-upstream controls checked separately from unchanged historical baselines; schema 8 rollout and schema 7 CSV/plan saves are explicit.'
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'status':'SYNCED','written':True,'counts':data['current_verified_counts']}

def verify(root,summary):
 path=target(root)
 if path is None:return {'status':'ABSENT','written':False}
 data=json.loads(path.read_text(encoding='utf-8'))
 assert data.get('current_verified_counts')==counts(summary),'stale STATUS current_verified_counts'
 assert data.get('current_base_commit')==summary['upstream_integration']['base_commit'],'stale STATUS current base'
 assert all(data.get('conditions',{}).get(k)==v for k,v in storage(summary).items()),'stale STATUS storage contract'
 return {'status':'PASS','counts':data['current_verified_counts'],'storage':storage(summary)}
