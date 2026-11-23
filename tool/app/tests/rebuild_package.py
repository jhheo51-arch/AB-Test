"""Build an exact-allowlist ZIP and test a separate extraction with real Chrome."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,urllib.request,tempfile,datetime,os
R=Path(__file__).resolve().parents[1];TOOL=R.parent;D=TOOL/'downloads';E=R/'evidence/package';E.mkdir(parents=True,exist_ok=True)
APP_FILES='''conditions.js app.js column-mapping.js context.css CONTEXT_CONTRACT.md design.js design-ui.js design.css engine-issue-codes.json engine.js index.html INPUT_CONTRACT.md launch.cmd launch.py lineage.js narrative.js project-schema.js README.md server.py styles.css theme.css worker.js workflow.css workflow.js examples/SYNTHETIC_aggregate.csv fonts/LICENSE.txt fonts/PretendardVariable.woff2 help/walkthrough.mp4'''.split()
TESTS='''semantic_edges.cjs verify_semantic_edges.py verify_document_links.py verify_release_metadata.py finalize_verification.py conditions_smoke.cjs condition_controls.py verify_conditions.py column_mapping_smoke.cjs compare_reference.cjs design_smoke.cjs engine_smoke.cjs generate_reference.py golden_reference.json lineage_smoke.cjs narrative_smoke.cjs project_schema_smoke.cjs REFERENCE_NOTES.md reference_verification.json unit_verification.json verify_browser.py verify_context.py verify_current_interface.py verify_design.py verify_design_boundaries.py verify_design_style.py verify_design_pdf.py verify_guided_pdf.py verify_issue_allowlist.py verify_lineage_browser.py verify_lineage_pdf.py verify_pdf.py verify_regressions.py verify_workflow.py run_integration.py'''.split()
REPORTS='''fix-evidence/semantic/BROWSER_VERIFICATION.json conditions-evidence/BASELINE_CONTROLS.json conditions-evidence/STYLE_CONTRAST.json conditions-evidence/IMPLEMENTATION_NOTES.md conditions-evidence/ENGINE_GATE_CASES.json conditions-evidence/CONDITIONS_MIXED.json conditions-evidence/CONDITIONS_MIXED_RESTORED.json conditions-evidence/CONDITIONS_SAVED.json conditions-evidence/CONDITIONS_RESTORED.json conditions-evidence/CONDITIONS_REPORT.html conditions-evidence/CONDITIONS_REPORT.pdf conditions-evidence/EVIDENCE_CAP.json conditions-evidence/LEGACY_2.json conditions-evidence/LEGACY_3.json conditions-evidence/LEGACY_4.json conditions-evidence/LEGACY_5.json conditions-evidence/LEGACY_6.json conditions-evidence/conditions-desktop.png conditions-evidence/conditions-mobile.png conditions_verification.json browser_verification.json context_verification.json interface_verification.json issue_allowlist_verification.json narrative_verification.json pdf_verification.json R03_browser_verification.json regression_verification.json verification.json workflow_verification.json integration_verification.json design-evidence/BOUNDARY_VERIFICATION.json design-evidence/BROWSER_VERIFICATION.json design-evidence/BROWSER_STYLE_NETWORK.json design-evidence/PDF_TEXT_VERIFICATION.json design-evidence/PLAN_ONLY.json design-evidence/PLAN_RESTORED.json design-evidence/PLAN_WITH_AGGREGATES.json design-evidence/POST_RESULT_EDIT.json design-evidence/RESULT_REPORT.html design-evidence/RESULT_REPORT.pdf design-evidence/INVALIDATED_REPORT.pdf design-evidence/plan-desktop.png design-evidence/plan-mobile.png workflow_evidence/GUIDED_PDF_PROOF.json lineage_evidence/LINEAGE_PDF_PROOF.json'''.split()
REVIEW='''README.md REVIEW_STATUS.md OBSERVER_GUIDE.md PARTICIPANT_TASKS.md SESSION_TEMPLATE.json observer/ENGINE_GROUND_TRUTH.json fixtures/SYNTHETIC_CRM_CUSTOM.csv fixtures/SYNTHETIC_CRM_STANDARD.csv fixtures/SYNTHETIC_IMMATURE.csv'''.split()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
 from verify_document_links import check_links
 from verify_release_metadata import verify as verify_metadata
 write(E/'SOURCE_RELEASE_METADATA.json',verify_metadata(R))
 source_links=check_links(TOOL);write(E/'SOURCE_DOCUMENT_LINKS.json',source_links);assert source_links['status']=='PASS',source_links['broken_links']
 sources={n:R/n for n in APP_FILES+REPORTS}
 sources.update({'tests/'+n:R/'tests'/n for n in TESTS})
 sources.update({'review/'+n:TOOL/'review'/n for n in REVIEW})
 # Exact log paths from the successful current run, never arbitrary directory inclusion.
 run=json.loads((R/'integration_verification.json').read_text(encoding='utf-8'));assert run['status']=='PASS'
 for row in run['checks']:
  n=row['log'];assert n.startswith('evidence/integration/') and '..' not in n;sources[n]=R/n
 members={'AB_Test_Workspace/'+n:p for n,p in sources.items()};assert len(members)==len(sources)
 assert all(p.is_file() and not any(s in n.lower() for s in ['__pycache__','.env','token','secret','credential']) for n,p in members.items())
 allow=[{'member':n,'source':p.relative_to(TOOL).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for n,p in sorted(members.items())]
 write(D/'PACKAGE_ALLOWLIST.json',{'policy':'explicit files only; no caches, original data, secrets or prior deployment archives','members':allow})
 zpath=D/'AB_Test_Workspace.zip'
 with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,p in sorted(members.items()):z.write(p,n)
 with zipfile.ZipFile(zpath) as z:
  assert z.testzip() is None;assert sorted(z.namelist())==sorted(members)
  assert all(z.read(n)==p.read_bytes() for n,p in members.items())
  extract=Path(tempfile.mkdtemp(prefix='ab_current_package_',dir=os.environ['TMPDIR']));z.extractall(extract)
 app=extract/'AB_Test_Workspace';rows=[];url=None
 write(E/'ZIP_PACKAGED_RELEASE_METADATA.json',verify_metadata(app))
 zip_links=check_links(app);write(E/'ZIP_DOCUMENT_LINKS.json',zip_links);assert zip_links['status']=='PASS',zip_links['broken_links']
 server=subprocess.Popen([sys.executable,'server.py','--port','0'],cwd=app,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 try:
  url=server.stdout.readline().strip().split('=',1)[1];assert urllib.request.urlopen(url).status==200
  assert urllib.request.urlopen(url+'/help/walkthrough.mp4').read()==(R/'help/walkthrough.mp4').read_bytes()
  for n in ['run_integration']:
   cmd=[sys.executable,str(app/'tests'/(n+'.py'))]
   p=subprocess.run(cmd,cwd=app,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1800)
   (E/'FULL_EXTRACTED_INTEGRATION.log').write_text(p.stdout+p.stderr,encoding='utf-8');rows.append({'script':'run_integration.py','exit_code':p.returncode,'output':p.stdout,'stderr':p.stderr})
   print('EXTRACTED FULL INTEGRATION',p.returncode,flush=True)
   write(E/'EXTRACTED_RELEASE_METADATA.json',verify_metadata(app))
   write(E/'EXTRACTED_VERIFICATION.json',json.loads((app/'verification.json').read_text(encoding='utf-8')))
   write(E/'EXTRACTED_INTEGRATION.json',json.loads((app/'integration_verification.json').read_text(encoding='utf-8')))
   write(E/'EXTRACTED_SEMANTIC_BROWSER.json',json.loads((app/'fix-evidence/semantic/BROWSER_VERIFICATION.json').read_text(encoding='utf-8')))
   write(E/'EXTRACTED_INTERFACE.json',json.loads((app/'interface_verification.json').read_text(encoding='utf-8')))
   # Preserve all exact extracted subprocess logs, not only their exit status.
   for log in (app/'evidence/integration').glob('*.log'):(E/('extracted_'+log.name)).write_bytes(log.read_bytes())
 finally:server.terminate();server.wait(timeout=15)
 result={'status':'PASS' if rows and all(x['exit_code']==0 for x in rows) else 'FAIL','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file':zpath.name,'sha256':sha(zpath.read_bytes()),'bytes':zpath.stat().st_size,'members':len(members),'duplicate_members':False,'CRC':'PASS','all_member_bytes_match_source':True,'allowlist':'PACKAGE_ALLOWLIST.json','separate_extracted_server':url,'extraction':str(extract),'server_stopped':server.poll() is not None,'unpacked_browser':rows,'actual_model_calls':0,'human_observations':0,'scope':'current ZIP; synthetic real Chrome design, saved plans, legacy migration, mapped analysis and actual help playback/state preservation'}
 write(D/'package_verification.json',result);print('PACKAGE',result['status'],len(members),'members',result['sha256'])
 sys.exit(0 if result['status']=='PASS' else 1)
