"""Execute current synthetic checks, own a temporary loopback server, stop it on exit."""
from pathlib import Path
import subprocess,sys,json,urllib.request,concurrent.futures,hashlib,datetime
R=Path(__file__).resolve().parents[1];E=R/'evidence'/'integration';E.mkdir(parents=True,exist_ok=True)
rows=[]
def run(name,cmd):
 p=subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
 (E/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
 row={'test':name,'command':cmd,'exit_code':p.returncode,'log':'evidence/integration/'+name+'.log'}
 print(name,'PASS' if p.returncode==0 else 'FAIL',flush=True)
 if p.returncode:print((p.stdout+p.stderr)[-2800:],flush=True)
 return row
if __name__=='__main__':
 server=subprocess.Popen([sys.executable,'server.py','--port','0'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 try:
  url=server.stdout.readline().strip().split('=',1)[1];print(url,flush=True)
  assert urllib.request.urlopen(url).status==200
  jobs=[(f.stem,['node',str(f)]) for f in sorted((R/'tests').glob('*.cjs'))]
  jobs += [(n,[sys.executable,str(R/'tests'/(n+'.py')),'--url',url]+(['--browser-path','C:/Program Files/Google/Chrome/Application/chrome.exe'] if n=='verify_current_interface' else [])) for n in ['verify_semantic_edges','verify_conditions','verify_design','verify_design_boundaries','verify_browser','verify_regressions','verify_current_interface','verify_design_style','verify_lineage_browser','verify_workflow','verify_context']]
  jobs += [(n,[sys.executable,str(R/'tests'/(n+'.py'))]) for n in ['verify_issue_allowlist','verify_design_pdf','verify_pdf','verify_guided_pdf','verify_lineage_pdf']]
  # Run serially for bounded worker-start timing; each owns separate browser state.
  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:rows=list(pool.map(lambda j:run(*j),jobs))
 finally:
  server.terminate();server.wait(timeout=15)
 result={'status':'PASS' if all(r['exit_code']==0 for r in rows) else 'FAIL','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':rows,'human_observations':0,'actual_llm_calls':0,'server_stopped':server.poll() is not None,'url_during_tests':url,'scope':'current canonical app; synthetic automated Node and actual Chrome; logs are exact subprocess output'}
 (R/'integration_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 if result['status']=='PASS':subprocess.run([sys.executable,str(R/'tests/finalize_verification.py')],cwd=R,check=True)
 sys.exit(0 if result['status']=='PASS' else 1)
