"""Summarize real subprocess logs; do not run or invent checks."""
from pathlib import Path
import json,re,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
run=load('integration_verification.json');assert run['status']=='PASS' and all(x['exit_code']==0 for x in run['checks'])
unit=[]
for row in run['checks']:
 if row['test'].endswith('_smoke'):
  log=(R/row['log']).read_text(encoding='utf-8');n=len(re.findall(r'^PASS ',log,re.M))
  unit.append({'script':row['test']+'.cjs','groups':n,'exit_code':row['exit_code'],'log':row['log']})
semantic_row=next(x for x in run['checks'] if x['test']=='semantic_edges')
semantic_log=(R/semantic_row['log']).read_text(encoding='utf-8')
semantic_match=re.search(r'^RESULT (\d+) semantic assertions passed \((\d+) engine gate cases;',semantic_log,re.M);assert semantic_match
semantic_cases,gates=map(int,semantic_match.groups())
assert len(re.findall(r'^PASS ',semantic_log,re.M))==semantic_cases
semantic={'script':'semantic_edges.cjs','cases':semantic_cases,'engine_gate_cases_included':gates,'exit_code':semantic_row['exit_code'],'log':semantic_row['log'],'counting':'Separate from smoke unit groups; engine gate cases are included, not additional. A case may contain several assertions.'}
files=sorted({p.name for pattern in ['*.js','*.css'] for p in R.glob(pattern)}|{'index.html','server.py','launch.py','launch.cmd','engine-issue-codes.json'})
# Initial clean-worktree SHA controls captured before R06 edits; no unavailable backup dependency.
baseline=load('conditions-evidence/BASELINE_CONTROLS.json')
intentional={'column-mapping.js':'Intentional bounded CRM alias additions and stricter observation-alias no-drop guard; statistical engine unchanged.','workflow.js':'Intentional optional local profile initialization and current raw-arm guidance; existing confirm/apply and tutorial behavior retained.','help/walkthrough.mp4':'Intentional actual-Chrome R05/R06 tutorial replacement; old video bytes are NOT preserved.', 'design-ui.js':'S01 shared lossless metadata getter/setter and unedited question navigation; intentionally modified, not a preserved control.'}
unchanged=[n for n in baseline['controls'] if n not in intentional]
checks={n:sha(R/n)==baseline['controls'][n]['sha256'] for n in unchanged};assert all(checks.values())
counts={n:load(n)['count'] for n in ['column_profile_verification.json','conditions_verification.json','browser_verification.json','context_verification.json','interface_verification.json','workflow_verification.json','regression_verification.json','R03_browser_verification.json','design-evidence/BROWSER_VERIFICATION.json','design-evidence/BOUNDARY_VERIFICATION.json','fix-evidence/semantic/BROWSER_VERIFICATION.json']}
summary={'status':'PASS','timestamp_utc':run['timestamp_utc'],'deployment':'single canonical current app; latest-only; no visible product version labels','integration_suite':{'scripts':len(run['checks']),'all_exit_zero':True,'record':'integration_verification.json','server_stopped':run['server_stopped']},'browser_checks':counts,'unit_groups':unit,'unit_group_total':sum(x['groups'] for x in unit),'numeric_reference':{'record':'tests/reference_verification.json','status':load('tests/reference_verification.json')['status'],'summary':load('tests/reference_verification.json')['summary']},'current_pdf_records':['conditions_verification.json','pdf_verification.json','design-evidence/PDF_TEXT_VERIFICATION.json','workflow_evidence/GUIDED_PDF_PROOF.json','lineage_evidence/LINEAGE_PDF_PROOF.json'],'source_sha256':{n:sha(R/n) for n in files},'preserved_baseline_bytes':checks,'intentional_baseline_control_changes':{n:{'reason':reason,'historical_sha256':baseline['controls'][n]['sha256'],'current_sha256':sha(R/n)} for n,reason in intentional.items()},'baseline':baseline,'baseline_role':'Historical pre-R06 record unchanged; preserved subset is explicit above. No current remote readback claimed.','video':{'sha256':sha(R/'help/walkthrough.mp4'),'asset_sha256':{n:sha(R/n) for n in ['help/walkthrough.mp4','help/walkthrough.ko.srt','help/walkthrough.timeline.json']},'current_metadata':load('interface_verification.json')['video_metadata'],'design_feature_tutorial_added':True,'conditions_tutorial_added':True,'full_decode':load('evidence/tutorial_media_validation.json'),'capture_source_note':'Original capture hashes describe the fixed pre-help-copy snapshot, not the current index/server hashes; current runtime hashes above and actual Chrome checks are rerun.'},'storage':{'schema':7,'legacy_imports':[2,3,4,5,6],'same_save_parse_normalization':True,'audience_guided_maxlength':300},'actual_model_calls_this_integration':0,'human_observations':0,'historical_baselines_not_rerun':['narrative_verification.json (original summary; current smoke rerun recorded separately)','prior actual model connection; no model called in current integration','prior video baseline superseded by explicit replacement; historical file unchanged'],'initial_run':'evidence/r06-initial/result.json','initial_issues':'R06 initial failures are preserved; test-only adaptation from checkbox actions and schema6 expectations to visible selects/schema7; see conditions-evidence/IMPLEMENTATION_NOTES.md; previous R05 initial failures are historical and not rerun','limits':['Synthetic automation, not participant study','No actual AI semantic design; local fixed questions and proposals','No new statistical support or automatic application approval','Actual-app design and conditions tutorial replaces prior analysis-only video; synthetic assumptions are not experiment certification']}
save('tests/unit_verification.json',{'status':'PASS','runs':unit,'unit_group_total':sum(x['groups'] for x in unit),'semantic_regressions':semantic,'timestamp_utc':run['timestamp_utc'],'scope':'real smoke groups and semantic cases counted separately'})
summary['metadata_generated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
summary['browser_check_total']=sum(counts.values())
summary['semantic_regressions']=semantic
summary['historical_initial_run']=summary.pop('initial_run')
summary['historical_initial_issues']=summary.pop('initial_issues')
summary['limits'] += ['Actual-app synthetic R05/R06 tutorial preserved byte-for-byte; optional local column-profile slice added, not yet covered by the tutorial; no human study or live LLM','Smoke groups, semantic cases and browser checks are separate counts; source/extracted repetitions are not additional unique coverage.']
summary['current_pdf_records'].append('fix-evidence/semantic/BROWSER_VERIFICATION.json')
profile_baseline=load('profile-evidence/BASELINE.json')
profile_controls=['engine.js','worker.js','project-schema.js','design.js','design-ui.js','conditions.js','help/walkthrough.mp4','help/walkthrough.ko.srt','help/walkthrough.timeline.json','tests/semantic_edges.cjs']
profile_preserved={n:sha(R/n) for n in profile_controls}
assert all(h==profile_baseline['files']['app/'+n]['sha256'] for n,h in profile_preserved.items())
summary['column_profile']={'format':'ab-column-profile','version':1,'max_bytes':8192,'raw_headers_stored':False,'raw_rows_stored':False,'arm_values_stored':False,'automatic_persistence':False,'conditions_inherited':False,'project_schema':7,'tutorial_covers_profiles':False,'browser_record':'column_profile_verification.json','node_log':'evidence/integration/column_profile_smoke.log','fixture_sha256':sha(R/'examples/SYNTHETIC_CRM_MAPPING.csv'),'baseline_commit':profile_baseline['commit'],'preserved_sha256':profile_preserved}
save('verification.json',summary)
print('PASS summary:',len(run['checks']),'executed scripts;',summary['unit_group_total'],'unit groups;',semantic_cases,'separate semantic cases;',sum(counts.values()),'browser checks')
