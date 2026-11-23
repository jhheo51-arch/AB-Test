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
save('tests/unit_verification.json',{'status':'PASS','runs':unit,'timestamp_utc':run['timestamp_utc'],'scope':'current subprocess output; not historical test count'})
files=['app.js','index.html','server.py','project-schema.js','design.js','design-ui.js','design.css','workflow.js','engine.js','worker.js','narrative.js','lineage.js','column-mapping.js','theme.css','context.css','workflow.css','styles.css']
# Checked-in current-remote snapshot is outside the worktree and never rewritten.
before=R.parents[2]/'ab_tool_before_integration'/'tool/app'
unchanged=['engine.js','worker.js','narrative.js','lineage.js','column-mapping.js','workflow.js','theme.css','context.css','workflow.css','styles.css','help/walkthrough.mp4']
checks={n:sha(R/n)==sha(before/n) for n in unchanged};assert all(checks.values())
counts={n:load(n)['count'] for n in ['browser_verification.json','context_verification.json','interface_verification.json','workflow_verification.json','regression_verification.json','R03_browser_verification.json','design-evidence/BROWSER_VERIFICATION.json','design-evidence/BOUNDARY_VERIFICATION.json']}
summary={'status':'PASS','timestamp_utc':run['timestamp_utc'],'deployment':'single canonical current app; latest-only; no visible product version labels','integration_suite':{'scripts':len(run['checks']),'all_exit_zero':True,'record':'integration_verification.json','server_stopped':run['server_stopped']},'browser_checks':counts,'unit_groups':unit,'unit_group_total':sum(x['groups'] for x in unit),'numeric_reference':{'record':'tests/reference_verification.json','status':load('tests/reference_verification.json')['status'],'summary':load('tests/reference_verification.json')['summary']},'current_pdf_records':['pdf_verification.json','design-evidence/PDF_TEXT_VERIFICATION.json','workflow_evidence/GUIDED_PDF_PROOF.json','lineage_evidence/LINEAGE_PDF_PROOF.json'],'source_sha256':{n:sha(R/n) for n in files},'preserved_current_remote_bytes':checks,'video':{'sha256':sha(R/'help/walkthrough.mp4'),'current_metadata':load('interface_verification.json')['video_metadata'],'design_feature_tutorial_added':False,'full_decode':'historical baseline; not rerun in this integration; actual Chrome playback rerun'},'storage':{'schema':6,'legacy_imports':[2,3,4,5],'same_save_parse_normalization':True,'audience_guided_maxlength':300},'actual_model_calls_this_integration':0,'human_observations':0,'historical_baselines_not_rerun':['narrative_verification.json (original summary; current smoke rerun recorded separately)','prior actual model connection; no model called in current integration','prior video full-decode certification; exact bytes preserved'],'initial_run':'evidence/integration-initial/result.json','initial_issues':'design navigation wiring and old-schema test expectations corrected; initial parallel worker readiness timeout not reproduced serially; general cause not established','limits':['Synthetic automation, not participant study','No actual AI semantic design; local fixed questions and proposals','No new statistical support or automatic application approval','No design tutorial added to existing analysis video']}
save('verification.json',summary)
print('PASS summary:',len(run['checks']),'executed scripts;',summary['unit_group_total'],'unit groups;',sum(counts.values()),'browser checks')
