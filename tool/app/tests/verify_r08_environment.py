"""Bounded Windows launcher audit; no model requests or credentials."""
from pathlib import Path
import argparse,contextlib,ctypes,datetime,hashlib,json,os,platform,queue,shutil,socket,subprocess,sys,tempfile,threading,time,urllib.request,zipfile
R=Path(__file__).resolve().parents[1]

def run(root, baseline=False):
 root=Path(root); evidence=root/'r08-evidence';evidence.mkdir(exist_ok=True)
 rows=[];processes=[];ports=[]
 def check(name,value,detail=None):
  rows.append({'name':name,'pass':bool(value),'detail':detail});print('PASS' if value else 'FAIL',name,flush=True)
  # Keep diagnostics and complete cleanup even when an assertion fails.
 def closed(port):
  with socket.socket() as s:s.settimeout(.3);return s.connect_ex(('127.0.0.1',port))!=0
 def start(app,extra=None,cmd=False):
  args=[sys.executable,'launch.py','--no-browser']+(extra or [])
  if cmd:args=[os.environ['COMSPEC'],'/d','/c','launch.cmd --no-browser'+(' '+' '.join(extra) if extra else '')]
  p=subprocess.Popen(args,cwd=app,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace');processes.append(p)
  q=queue.Queue()
  def reader():
   for line in p.stdout:q.put(line)
  threading.Thread(target=reader,daemon=True).start();lines=[];end=time.monotonic()+12
  while time.monotonic()<end:
   try:line=q.get(timeout=.2);lines.append(line)
   except queue.Empty:
    if p.poll() is not None:break
    continue
   if line.startswith('AB_LOCAL_URL='):
    url=line.strip().split('=',1)[1];port=int(url.rsplit(':',1)[1]);ports.append(port)
    return p,url,lines
  return p,None,lines
 def stop(p):
  if p.poll() is None:
   # Windows task tree is needed when launch.cmd owns python.exe.
   if os.name=='nt':subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=10)
   else:p.terminate()
  p.wait(timeout=10)
 try:
  with contextlib.nullcontext(tempfile.mkdtemp(prefix='한글 경로 공백 ',dir=os.environ['TMPDIR'])) as tmp:
   app=Path(tmp)/'작업실 앱';shutil.copytree(root,app,ignore=shutil.ignore_patterns('__pycache__','r08-evidence'))
   p,u,lines=start(app);check('Python launcher Korean spaces no-browser loopback HTTP',bool(u) and urllib.request.urlopen(u,timeout=5).status==200,lines)
   if u:
    probe=subprocess.run([sys.executable,'-c',"from server import AppServer,Handler; import json; s=AppServer(('127.0.0.1',0),Handler,None,'mira'); print(json.dumps(s.socket.getsockname())); s.server_close()"],cwd=app,capture_output=True,text=True,timeout=10)
    address=json.loads(probe.stdout) if probe.returncode==0 else None
    check('actual AppServer socket API bind address is IPv4 loopback',address and address[0]=='127.0.0.1',address)
    p2,u2,l2=start(app);check('two simultaneous instances unique loopback ports',u2 and u2!=u,l2)
    if u2:stop(p2)
    port=int(u.rsplit(':',1)[1]);p3,u3,l3=start(app,['--port',str(port)]);check('explicit occupied port exits usefully without alternate server',u3 is None and p3.poll() is not None and any('port' in x.lower() and ('use' in x.lower() or '사용' in x) for x in l3),l3);stop(p3)
    stop(p);check('closed server port actually refuses connection',closed(port));p4,u4,l4=start(app,['--port',str(port)]);check('restart same explicit port succeeds',u4==u,l4);stop(p4)
   # Missing critical asset must fail startup rather than advertise a broken URL.
   for asset in ['conditions.js','design.js','design-ui.js','column-profile.js','profile-ui.js','rollout.js']:
    (app/asset).unlink();pm,um,lm=start(app);check('incomplete extraction missing '+asset+' blocked at startup',um is None and pm.poll() is not None and any(asset in x for x in lm),lm);stop(pm);shutil.copy2(root/asset,app/asset)
   # Stub discovers argument forwarding without opening a real browser in the baseline.
   stubs=Path(tmp)/'isolated PATH';stubs.mkdir();(stubs/'python.cmd').write_text('@echo off\necho STUB_PYTHON %*\nexit /b 0\n',encoding='ascii')
   env={**os.environ,'PATH':str(stubs)}
   c=subprocess.run([os.environ['COMSPEC'],'/d','/c','launch.cmd --no-browser --port 12345'],cwd=app,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors='replace',timeout=10)
   check('CMD forwards no-browser and explicit port arguments','--no-browser --port 12345' in c.stdout,c.stdout+c.stderr)
   # No Python installed is only simulated in isolated PATH, not this actual system.
   (stubs/'python.cmd').unlink()
   c=subprocess.run([os.environ['COMSPEC'],'/d','/c','launch.cmd --no-browser'],cwd=app,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors='replace',timeout=10)
   check('isolated PATH Python missing actionable instruction',c.returncode!=0 and 'https://www.python.org/downloads/' in c.stdout,c.stdout+c.stderr)
   if not baseline:
    pc,uc,lc=start(app,cmd=True);check('actual launch.cmd starts Korean path HTTP with no-browser',uc and urllib.request.urlopen(uc,timeout=5).status==200,lc);stop(pc)
    # Real installed py -3 executes Python; isolated path exposes only that launcher.
    py=shutil.which('py');check('real installed Python launcher available',bool(py))
    if py:
     shutil.copy2(py,stubs/'py.exe')
     c=subprocess.run([os.environ['COMSPEC'],'/d','/c','launch.cmd --no-browser --help'],cwd=app,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors='replace',timeout=15)
     check('real py -3 fallback help no server',c.returncode==0 and '--no-browser' in c.stdout,c.stdout+c.stderr)
 finally:
  for p in processes:stop(p)
  check('all owned server ports closed',all(closed(p) for p in ports),ports)
  if 'tmp' in locals():shutil.rmtree(tmp)
 mem=ctypes.create_string_buffer(64);ctypes.c_ulong.from_buffer(mem).value=64
 memory=None;cpu=platform.processor()
 if os.name=='nt':
  import winreg
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:cpu=winreg.QueryValueEx(key,'ProcessorNameString')[0]
 if os.name=='nt' and ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):memory={'memory_load_percent':ctypes.c_ulong.from_buffer(mem,4).value,'physical_total_bytes':ctypes.c_ulonglong.from_buffer(mem,8).value,'physical_available_bytes':ctypes.c_ulonglong.from_buffer(mem,16).value}
 result={'status':'PASS' if all(x['pass'] for x in rows) else 'FAIL','checks':rows,'count':len(rows),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'os':platform.platform(),'python':sys.version,'cpu_logical':os.cpu_count(),'processor':cpu,'memory_snapshot':memory},'scope':'automated actual Windows launcher subprocesses; isolated PATH simulates missing Python, not a real uninstalled system; no live models or humans','actual_model_calls':0,'human_observations':0}
 (evidence/('ENVIRONMENT_BASELINE.json' if baseline else 'ENVIRONMENT_VERIFICATION.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',action='store_true');a.add_argument('--root',type=Path,default=R);args=a.parse_args();r=run(args.root,args.baseline);sys.exit(0 if args.baseline or r['status']=='PASS' else 1)
