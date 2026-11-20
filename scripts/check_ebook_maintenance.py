"""Check the private reader repository without rebuilding frozen editions."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from zipfile import ZipFile
from urllib.parse import urlsplit,unquote
import argparse,csv,hashlib,json,os,re,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[1];M=R/'e-book/maintenance';C=M/'checks';C.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
args=argparse.ArgumentParser();args.add_argument('--regressions',action='store_true');args=args.parse_args()
source=read(R/'e-book/review/publication_v22/TECHNICAL_RIGHTS_CHECK.json')['baseline_hashes']
assert all(sha(R/n)==h for n,h in source.items()),'Frozen v22 file changed'
tasks=read(M/'TASKS.json');assert tasks['goal']=='private_github_learning_reference' and tasks['publication_intent'] is False
if args.regressions:
 uv=shutil.which('uv');assert uv,'uv is required for browser regressions'
 scratch=os.environ.get('TMPDIR') or os.environ.get('BH_AGENT_WORKSPACE');assert scratch and Path(scratch).is_dir(),'Set TMPDIR to an existing scratch directory'
 with tempfile.TemporaryDirectory(prefix='reader_maintenance_',dir=scratch) as td:
  for stem,folder in [('verify_reader_features_v22','ui'),('verify_record_print_v22','print')]:
   original=R/'scripts'/(stem+'.py');text=original.read_text(encoding='utf-8');needle="R/'e-book/design/v22'";assert needle in text;text=text.replace(needle,"R/'e-book/maintenance/checks/"+folder+"'")
   out=C/folder;out.mkdir(exist_ok=True)
   if folder=='print':text=re.sub(r"T=Path\('[^']*'\)","T=Path(os.environ['BH_MAINT_SCRATCH'])",text);text='import os\n'+text
   runner="source="+repr(text)+"\nexec(compile(source,"+repr(str(original))+",'exec'),{'__file__':"+repr(str(original)) +",'__name__':'__main__'})"
   env=os.environ.copy();env['BH_MAINT_SCRATCH']=td
   result=subprocess.run([uv,'run','--with','playwright','--with','pymupdf','python','-c',runner],cwd=R,env=env,text=True,capture_output=True,encoding='utf-8')
   (C/(folder+'_run.log')).write_text((result.stdout+'\n'+result.stderr).rstrip()+'\n',encoding='utf-8',newline='\n');assert result.returncode==0,(stem,result.returncode,'See maintenance/checks/'+folder+'_run.log')
 ui=read(C/'ui/ui_validation_v22.json');printing=read(C/'print/print_validation_v22.json');assert ui['status']==printing['status']=='passed' and not ui['fixture_only']
 save(C/'regression_check.json',{'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'kind':'Re-executed existing v22 regression logic; output directory redirected only','zoom_return_cases':len(ui['zoom_cases']),'copy':ui['copy'],'copy_denial_fallback':ui['copy_denial_fallback'],'download_exact_values_and_six_fields':ui['download_exact_values_and_six_fields'],'automatic_storage':ui['automatic_storage'],'remote_requests':ui['remote_requests'],'print_cases':printing['cases'],'original_artifacts_changed':False,'actual_reader_test':False})
 for t in tasks['tasks']:
  if t['id']=='R2':t['status']='completed'
regression=read(C/'regression_check.json');assert regression['status']=='passed'
preserved=0
for edition in ['v20','v21','v22']:
 d=R/('e-book/manuscript/development_'+edition);mapping={}
 if (d/'BASELINE_RELOCATION.json').exists():mapping={x['original_path']:x['current_path'] for x in read(d/'BASELINE_RELOCATION.json')['paths']}
 for name,h in read(d/'BASELINE.json')['hashes'].items():assert sha(R/mapping.get(name,name))==h,name;preserved+=1
O=R/'e-book/exports/v22';V=R/'e-book/design/v22';D=R/'e-book/manuscript/development_v22';package=read(O/'package_smoke_v22.json');assert sha(R/package['archive'])==package['sha256']
extra={'DEVELOPMENT.md':V/'DEVELOPMENT.md','REVIEW.md':V/'REVIEW.md','UI_VALIDATION.json':V/'ui_validation_v22.json','PRINT_VALIDATION.json':V/'print_validation_v22.json'}
with ZipFile(R/package['archive']) as z:
 assert z.testzip() is None and len(z.namelist())==package['file_count']
 for n in z.namelist():
  if n=='START_HERE.md':continue
  p=extra.get(n,D/n.split('/',1)[1] if n.startswith('development/') else O/n);assert z.read(n)==p.read_bytes(),n
P=R/'e-book/review/publication_v22';H=P/'history/before_repository_only'
with ZipFile(P/'PUBLICATION_REVIEW_v22.zip') as z:
 assert z.testzip() is None
 for n in z.namelist():assert z.read(n)==(H/n).read_bytes(),n
links=0;target=C/'repository_check.json'
for p in [R/'README.md',R/'PROJECT_SUMMARY.md',R/'e-book/README.md',R/'scripts/README.md']+list(M.rglob('*.md'))+list(P.glob('*.md')):
 for name in re.findall(r'\]\(([^)\n]+)\)',p.read_text(encoding='utf-8')):
  if urlsplit(name).scheme or name.startswith('#'):continue
  dest=p.parent/unquote(name.split('#')[0]);assert dest.exists() or dest.resolve()==target.resolve(),(p.name,name);links+=1
counts={}
for name in ['AUTHOR_OBSERVATIONS.csv','ISSUES.csv']:
 with (M/name).open(encoding='utf-8-sig',newline='') as f:counts[name]=len(list(csv.DictReader(f)))
assert all(sha(R/n)==h for n,h in source.items()),'Frozen artifacts changed during checking'
report={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'goal':tasks['goal'],'publication_intent':False,'protected_v22_files':len(source),'preserved_input_checks':preserved,'local_links_checked':links,'reader_zip_entries':package['file_count'],'original_review_zip_preserved':True,'record_rows':counts,'frozen_v22_unchanged':True,'limits':['No independent statistical re-audit','No human reader test or external recruitment','No PDF all-citation audit or contact sheet']};save(target,report)
for t in tasks['tasks']:
 if t['id']=='R1':t['status']='completed'
save(M/'TASKS.json',tasks);print(json.dumps({'repository':report,'regression':regression},ensure_ascii=False,indent=2))
