"""Post-package installed py -3 fallback HTTP check, separate from suite totals."""
from pathlib import Path
import hashlib,json,os,queue,shutil,socket,subprocess,tempfile,threading,time,urllib.request
R=Path(__file__).resolve().parents[1]

def run():
 package=json.loads((R.parent/'downloads/package_verification.json').read_text('utf-8'));assert package['status']=='PASS'
 actual=hashlib.sha256((R.parent/'downloads/AB_Test_Workspace.zip').read_bytes()).hexdigest();assert actual==package['sha256']
 rows=[];py=shutil.which('py');assert py
 with tempfile.TemporaryDirectory(prefix='한글 py 대체 경로 ',dir=os.environ['TMPDIR']) as tmp:
  temp=Path(tmp);isolated=temp/'PATH';isolated.mkdir();shutil.copy2(py,isolated/'py.exe')
  source=temp/'소스 앱';shutil.copytree(R,source,ignore=shutil.ignore_patterns('__pycache__','r08-evidence','evidence'))
  for label,app in [('source',source),('extracted',Path(package['extraction'])/'AB_Test_Workspace')]:
   environment={**os.environ,'PATH':str(isolated)};p=None;url=None
   try:
    p=subprocess.Popen([os.environ['COMSPEC'],'/d','/c','launch.cmd --no-browser'],cwd=app,env=environment,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    q=queue.Queue()
    def read(stream):
     for line in stream:q.put(line)
    threading.Thread(target=read,args=(p.stdout,),daemon=True).start();lines=[];deadline=time.monotonic()+15
    while time.monotonic()<deadline:
     try:line=q.get(timeout=.15);lines.append(line)
     except queue.Empty:
      if p.poll() is not None:break
      continue
     if line.startswith('AB_LOCAL_URL='):url=line.strip().split('=',1)[1];break
    assert url and url.startswith('http://127.0.0.1:'),lines
    with urllib.request.urlopen(url,timeout=5) as response:assert response.status==200 and b'<!doctype html>' in response.read().lower()
    row={'scope':label,'pass':True,'py_exe_only_in_PATH':True,'url':url,'stdout_until_ready':lines,'stdin':'DEVNULL','actual_model_calls':0};rows.append(row)
   finally:
    if p:
     if p.poll() is None:subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=10)
     p.wait(timeout=10)
     if url:
      with socket.socket() as s:s.settimeout(.3);closed=s.connect_ex(('127.0.0.1',int(url.rsplit(':',1)[1])))!=0
      assert closed
      rows[-1]['port_closed_after_stop']=closed
 result={'status':'PASS','checks':rows,'unique_additional_environment_cases':1,'source_runs':1,'extracted_runs':1,'not_added_to_integration_or_browser_totals':True,'tested_zip_sha256':actual,'scope':'actual installed py -3 launches HTTP through launch.cmd with python absent only from isolated PATH; not a real Python-uninstalled machine','human_observations':0,'actual_model_calls':0}
 (R/'r08-evidence/PY_FALLBACK_HTTP.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
