"""Cross-check AI reviewers; disclose rather than erase provenance failures."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,math,sqlite3
A=Path(__file__).resolve().parent;R=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=read(A/'numeric/RESULTS.json');p=read(A/'parent/RESULTS.json');power=read(A/'parent/POWER_RESULTS.json');scenarios=read(A/'parent/SCENARIO_RESULTS.json');method=read(A/'method/FINDINGS.json');source=(R/'e-book/exports/v22/ebook_review_v22.md').read_text(encoding='utf-8').splitlines()
failed=[x for x in n['checks'] if not x['passed']];assert {x['name'] for x in failed}=={'plan.sha256_vs_ledger','plan.sha256_vs_database_manifest'}
assert n['check_summary']=={'total':len(n['checks']),'passed':sum(x['passed'] for x in n['checks']),'failed':len(failed)}
raw=(R/'e-book/virtual-data/v03/experiment_plan.json').read_bytes();current=hashlib.sha256(raw).hexdigest();crlf=hashlib.sha256(raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest();historical=read(R/'e-book/analysis/winner_v04/core_results.json')['source_plan_sha256']
with sqlite3.connect((R/'e-book/virtual-data/v13/data/jh_motors_v13.sqlite').as_uri()+'?mode=ro',uri=True) as db:
 db.execute('PRAGMA query_only=ON');manifest=json.loads(db.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])
assert current!=historical and crlf==historical==manifest
assert 'LF' in source[1399] and 'CRLF' in source[1399]
assert p['status']==power['status']==scenarios['status']=='passed' and all(x['passed'] for x in p['checks']) and all(x['passed'] for x in scenarios['checks']);assert not n['raw_outcome_comparison']['mismatches'];assert not n['findings']['confirmed_numeric_errors'];assert not method['confirmed_errors'] and not method['new_actionable_conditional_defects']
peer_checks=[]
for x in p['checks']:
 name=x['label'];value=None
 if name.startswith('completion.'):
  _,contrast,key=name.split('.');value=next(y for y in n['primary_family'] if y['comparison']==contrast)[key]
 elif name.startswith('withdrawal.'):
  _,contrast,key=name.split('.');value=n['guardrail_exploratory'][key]
 elif name.startswith('financial.'):
  _,contrast,key=name.split('.');value=next(y for y in n['financial_exploratory'] if y['comparison']==contrast)[key]
 elif name.split('.')[0] in ['A','B','H'] and not name.endswith('net_mean'):
  arm,key=name.split('.');value=n['groups'][arm][key]
 if value is not None:
  assert math.isclose(x['actual'],value,rel_tol=1e-7,abs_tol=0 if 'p_raw' in name or 'p_family' in name else 1e-7),name;peer_checks.append(name)
for item in method['reservations_not_manuscript_defects']:assert item['quote'] in source[item['line']-1]
baseline=read(R/'e-book/review/publication_v22/TECHNICAL_RIGHTS_CHECK.json')['baseline_hashes'];assert all(sha(R/path)==h for path,h in baseline.items())
inputs=[path for path in A.rglob('*') if path.is_file() and path.name not in ['VERIFICATION.json','AI_STAT_REVIEW_v22.zip']]
report={'status':'completed_with_disclosed_historical_byte_mismatch','verified_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'review_mode':'AI and bots; separate implementations, not independent humans','numeric_check_summary':n['check_summary'],'all_strict_numeric_review_checks_passed':False,'all_nonprovenance_numeric_checks_passed':True,'provenance_issue_count':len(n['findings']['confirmed_provenance_discrepancies']),'known_provenance_issue':{'current_plan_sha256':current,'historical_plan_sha256':historical,'crlf_representation_sha256':crlf,'database_manifest_matches_crlf':True,'already_disclosed_at_manuscript_line':1400,'source_not_rewritten':True},'assigned_customers':p['assigned_records'],'parent_scalar_checks':p['comparison_count'],'peer_scalar_cross_checks':len(peer_checks),'sample_plan_grid_rows':power['plan_grid_rows'],'scenario_scalar_checks':scenarios['scalar_comparisons'],'scenario_operations_rows':scenarios['case6_operations_rows_matched'],'new_confirmed_manuscript_errors':len(method['confirmed_errors']),'new_actionable_conditional_defects':len(method['new_actionable_conditional_defects']),'nondefect_reservations':len(method['reservations_not_manuscript_defects']),'human_review_completed':False,'human_reviewer_required_to_continue':False,'manuscript_edits':False,'baseline_unchanged':True,'input_hashes':{x.relative_to(A).as_posix():sha(x) for x in inputs},'limits':['No independent human certification or human reading test','No proof of external historical preregistration time','No real OEM accounting or field-performance validation','Approximation calculations are not a global exact coverage/FWER proof','No full PDF citation sweep or contact sheet']}
(A/'VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'},ensure_ascii=False,indent=2))
