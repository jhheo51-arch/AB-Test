"""Optional local profile vertical slice in actual Chrome. Synthetic inputs only."""
from pathlib import Path
import argparse,json,hashlib,urllib.request,urllib.error,time
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--url',required=True);u=a.parse_args().url;checks=[]
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n,flush=True)
def fresh(b):
 p=b.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
 p.route('**/api/explain',lambda r:r.abort())
 p.goto(u,wait_until='networkidle');p.locator('details').filter(has=p.locator('#profile-file')).evaluate('(e)=>{e.open=true}')
 return p
def upload(p,raw):
 p.set_input_files('#csv-file',{'name':'SYNTHETIC.csv','mimeType':'text/csv','buffer':raw.encode()});expect(p.locator('#source-badge')).to_contain_text('사용자 CSV');expect(p.locator('#prepare')).to_be_enabled()
def imp(p,data):p.set_input_files('#profile-file',{'name':'AB_COLUMN_PROFILE.json','mimeType':'application/json','buffer':data if isinstance(data,bytes) else data.encode()})
def loaded(p):expect(p.locator('#profile-status')).to_contain_text('역할 후보를 채웠습니다')
def opened(p,raw):
 upload(p,raw);p.click('#open-mapping');expect(p.locator('#mapping-panel')).to_be_visible()
def apply(p):
 p.check('#mapping-confirm');p.click('#apply-mapping')
def analyze(p,yes=True):
 if yes:
  for k in ['randomized','independent','mature','fixed-stop','segment-prespecified']:p.select_option('#'+k,'yes')
 p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
def snapshot(p):return p.evaluate("JSON.stringify({raw:$('#data-text').value,mode:$('#format').value,draft:mappingDraft,mapping:currentMapping(),a:$('#arm-value-a').value,b:$('#arm-value-b').value,confirmed:$('#mapping-confirm').checked,state,conditions,share:$('#share-confirm').checked,print:$('#print-area').innerHTML,lineageSeed})")
def gate(p):p.evaluate("""()=>{window.realDigest=crypto.subtle.digest.bind(crypto.subtle);window.gates=[];crypto.subtle.digest=async(...args)=>{const real=await realDigest(...args);return await new Promise(resolve=>gates.push(()=>resolve(real)));};} """)
def release(p,start=0,end=None):p.evaluate('([s,e])=>{gates.slice(s,e===null?undefined:e).forEach(f=>f());}',[start,end])
def gatecount(p,n):
 end=time.monotonic()+10
 while p.evaluate('gates.length')<n and time.monotonic()<end:p.wait_for_timeout(25)
 check('pending real digest gates '+str(n),p.evaluate('gates.length')==n)
raw=(R/'examples/SYNTHETIC_CRM_MAPPING.csv').read_text('utf-8');hs=raw.splitlines()[0].split(',')
reordered='cohort,recipient_count,test_group,conversion_count\nSYNTHETIC_new,500,control,50\nSYNTHETIC_new,500,treatment,75\nSYNTHETIC_existing,500,control,80\nSYNTHETIC_existing,500,treatment,75\n'
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=fresh(b);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 check('actual secure localhost WebCrypto',p.evaluate('isSecureContext&&!!crypto.subtle'))
 opened(p,raw);p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);expect(p.locator('#analysis-options')).to_be_visible()
 p.click('#profile-export');expect(p.locator('#profile-status')).to_contain_text('동의해 주세요');check('no template export without explicit metadata consent',not p.locator('#profile-consent').is_checked())
 p.check('#profile-consent')
 with p.expect_download() as d:p.click('#profile-export')
 profile=Path(d.value.path()).read_text('utf-8');obj=json.loads(profile)
 check('actual local download only role fingerprints exact SHA256',obj=={'format':'ab-column-profile','version':1,'mode':'aggregate','roles':{k:'sha256:'+hashlib.sha256(h.encode()).hexdigest() for k,h in zip(['arm','success','total','segment'],hs)}})
 check('profile excludes headers arm values cohorts raw rows filename',all(s not in profile for s in hs+['control','treatment','SYNTHETIC_new','SYNTHETIC.csv']))
 check('download consent consumed; no local/session persistence',not p.locator('#profile-consent').is_checked() and p.evaluate('localStorage.length===0&&sessionStorage.length===0'))
 p.close();p=fresh(b);upload(p,reordered);imp(p,profile);loaded(p)
 check('fresh page reordered CSV candidate roles matched by current names',p.evaluate('currentMapping()')==dict(zip(['arm','success','total','segment'],hs)))
 check('fresh raw arm confirmation required no inferred defaults',p.locator('#arm-value-a').input_value()==p.locator('#arm-value-b').input_value()=='' and not p.locator('#mapping-confirm').is_checked() and p.evaluate('state.prepared===null&&state.result===null'))
 check('profile does not inherit conditions or evidence',p.evaluate("ABConditions.KEYS.every(k=>conditions[k].status==='unknown'&&conditions[k].evidence==='')"))
 p.click('#apply-mapping');check('candidate without confirmation never prepares',p.evaluate('state.prepared===null'))
 apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('confirmed candidate with no arm values still blocked',p.evaluate('state.prepared===null'))
 p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);expect(p.locator('#analysis-options')).to_be_visible()
 check('all rows retained counts 2000 and 280 source 4',p.evaluate('state.prepared.sourceRowCount===4&&state.prepared.cells.reduce((s,v)=>s+v.total,0)===2000&&state.prepared.cells.reduce((s,v)=>s+v.success,0)===280') and p.locator('#data-text').input_value()==reordered)
 analyze(p,False);check('unknown source conditions continue to restrict inference',not p.evaluate('state.result.inference_allowed'))
 p.click('nav [data-view=input]');analyze(p,True)
 check('actual engine result not hardcoded winner',p.evaluate("state.result.overall.A.success===130&&state.result.overall.B.success===150&&state.result.overall.winner==='hold'&&Math.abs(state.result.overall.p_raw-0.2207487698031054)<1e-14"))
 p.click('nav [data-view=share]');p.check('#share-confirm');p.evaluate('preparePrint()')
 check('profile hashes not data hash lineage',not any(v in p.evaluate('JSON.stringify(state.lineage)') for v in obj['roles'].values()))
 with p.expect_download() as d:p.click('#save-project')
 project=Path(d.value.path()).read_text('utf-8')
 with p.expect_download() as d:p.click('#export-report')
 report=Path(d.value.path()).read_text('utf-8')
 check('project7 report and LLM payload exclude profile and selected headers',all(s not in project+report+p.evaluate('JSON.stringify(explanationFacts())') for s in hs+list(obj['roles'].values())+['ab-column-profile']))
 p.click('nav [data-view=input]');before=snapshot(p)
 invalids=[b'',b'\xc3\x28',b' '*8193,b'{}',json.dumps({**obj,'format':'bad'}).encode(),json.dumps({**obj,'mode':'individual'}).encode(),json.dumps({**obj,'headerNames':hs}).encode(),json.dumps({**obj,'roles':{**obj['roles'],'arm':'sha256:'+'G'*64}}).encode(),json.dumps({**obj,'roles':{**obj['roles'],'total':obj['roles']['arm']}}).encode(),json.dumps({**obj,'roles':{**obj['roles'],'arm':'sha256:'+'0'*64}}).encode()]
 for n,data in enumerate(invalids):
  imp(p,data);expect(p.locator('#profile-status')).to_contain_text('가져오기 실패');check('invalid template '+str(n)+' atomic unchanged state',snapshot(p)==before)
 imp(p,profile+' '*(8192-len(profile.encode())));loaded(p)
 check('browser exact 8KiB valid template accepted',p.locator('#arm-value-a').input_value()=='')
 check('successful candidate invalidates prepared result input sharing print',p.evaluate("state.prepared===null&&state.result===null&&!$('#confirm-input').checked&&!$('#share-confirm').checked&&!$('#llm-consent').checked&&$('#print-area').innerHTML===''"))
 check('successful reuse resets all conditions no inherited evidence',p.evaluate("ABConditions.KEYS.every(k=>conditions[k].status==='unknown'&&conditions[k].evidence==='')"))
 for kind,badraw in [('missing','test_group,conversion_count,recipient_count\ncontrol,1,10\ntreatment,2,10'),('duplicate','test_group,conversion_count,recipient_count,cohort,cohort\ncontrol,1,10,g,g\ntreatment,2,10,g,g')]:
  upload(p,badraw);before=snapshot(p);imp(p,profile);expect(p.locator('#profile-status')).to_contain_text('가져오기 실패');check(kind+' header template fails with existing state intact',snapshot(p)==before)
 for arm in ['H','C','control ']:
  opened(p,raw+f'{arm},1,10,SYNTHETIC_new\n');imp(p,profile);loaded(p);p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('extra arm '+repr(arm)+' rejected no rows filtered',p.evaluate('state.prepared===null'))
 # Known static fixture download cannot use current customer input or alter it.
 p.fill('#data-text','PRIVATE_SENTINEL');before=snapshot(p)
 with p.expect_download() as d:p.click('a[href="examples/SYNTHETIC_CRM_MAPPING.csv"]')
 check('static synthetic file exact bytes and does not modify current input',Path(d.value.path()).read_bytes()==(R/'examples/SYNTHETIC_CRM_MAPPING.csv').read_bytes() and snapshot(p)==before)
 # All user-provided headers/values displayed as text; exported profile contains only hashes.
 xss='variant,converted,participants,<img src=x onerror=window.BAD=1>\nA,1,10,<svg/onload=window.BAD=2>\nB,2,10,unused'
 opened(p,xss);p.select_option('#map-segment','<img src=x onerror=window.BAD=1>');apply(p);expect(p.locator('#analysis-options')).to_be_visible();p.check('#profile-consent')
 with p.expect_download() as d:p.click('#profile-export')
 xp=Path(d.value.path()).read_text('utf-8');imp(p,xp);loaded(p)
 check('XSS selected headers come from current CSV safely escaped',p.locator('#mapping-panel img,#mapping-panel svg').count()==0 and p.evaluate('window.BAD===undefined') and '<img' not in xp)
 p.set_viewport_size({'width':390,'height':844});check('new controls mobile no page overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.set_viewport_size({'width':1440,'height':1100})
 # Individual profile with actual observations and noncanonical aliases.
 p.select_option('#format','individual');ind='subscriber_key,variant,outcome,관측 여부\nSYNTHETIC_ID_A,A,1,1\nSYNTHETIC_ID_B,B,0,1';opened(p,ind);apply(p);expect(p.locator('#analysis-options')).to_be_visible();p.check('#profile-consent')
 with p.expect_download() as d:p.click('#profile-export')
 ip=Path(d.value.path()).read_text('utf-8');check('individual profile no IDs/rows exported','SYNTHETIC_ID' not in ip and 'subscriber_key' not in ip)
 upload(p,ind.replace('A,1,1','A,1,0'));imp(p,ip);loaded(p);p.fill('#arm-value-a','A');p.fill('#arm-value-b','B');apply(p);expect(p.locator('#issues')).to_contain_text('IMMATURE_OBSERVATION');check('profile cannot bypass immature observation or switch format',p.locator('#format').input_value()=='individual' and p.locator('#analysis-options').is_hidden())
 p.select_option('#map-observed','');apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('observed alias cannot be dropped',p.evaluate('state.prepared===null'))
 bad=json.loads(ip);bad['roles']['observed']=None;before=snapshot(p);imp(p,json.dumps(bad));expect(p.locator('#profile-status')).to_contain_text('가져오기 실패');check('profile null observation cannot omit current observation',snapshot(p)==before)
 p.close()
 # Pending real hashes vs edits/new file/mode/re-import: operation ownership, not fake digests.
 for action in ['edit','newfile','mode','reimport']:
  p=fresh(b);opened(p,raw);gate(p);imp(p,profile);gatecount(p,4)
  if action=='edit':p.fill('#data-text','arm,success,total\nA,1,10\nB,2,10')
  elif action=='newfile':upload(p,'arm,success,total\nA,3,10\nB,4,10')
  elif action=='mode':p.select_option('#format','individual')
  else:
   imp(p,profile);gatecount(p,8);release(p,0,4);p.wait_for_timeout(100)
   check('old finally cannot unlock newer import',p.evaluate("inputTask?.kind==='profile-import'&&$('#prepare').disabled"));release(p,4,8);loaded(p)
  if action!='reimport':
   before=snapshot(p);release(p);p.wait_for_timeout(100);check('stale profile digest '+action+' cannot apply',snapshot(p)==before and p.locator('#prepare').is_enabled())
  p.close()
 # Pending read and export have the same input epoch. No old completion can download.
 p=fresh(b);opened(p,raw)
 p.evaluate("()=>{window.realBuffer=File.prototype.arrayBuffer;window.reads=[];File.prototype.arrayBuffer=async function(){const bytes=await realBuffer.call(this);return await new Promise(r=>reads.push(()=>r(bytes)));};}")
 imp(p,profile);p.wait_for_timeout(50);p.fill('#data-text','arm,success,total\nA,1,10\nB,1,10');before=snapshot(p);p.evaluate('()=>{reads.forEach(f=>f());}');p.wait_for_timeout(100);check('stale profile file read cannot replace edited input',snapshot(p)==before);p.close()
 for action in ['edit','consent']:
  p=fresh(b);opened(p,raw);p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);expect(p.locator('#analysis-options')).to_be_visible();p.check('#profile-consent');downloads=[];p.on('download',lambda d:downloads.append(d.suggested_filename));gate(p);p.click('#profile-export');gatecount(p,4)
  if action=='edit':p.fill('#arm-value-a','other')
  else:p.uncheck('#profile-consent')
  release(p);p.wait_for_timeout(100);check('pending export '+action+' prevents stale download',not downloads and p.locator('#prepare').is_enabled());p.close()
 p=fresh(b);opened(p,raw);p.evaluate("()=>{crypto.subtle.digest=async()=>{throw Error('SYNTHETIC_CRYPTO_UNAVAILABLE');};}");before=snapshot(p);imp(p,profile);expect(p.locator('#profile-status')).to_contain_text('가져오기 실패');check('WebCrypto failure preserves current state and unlocks',snapshot(p)==before and p.locator('#prepare').is_enabled());p.close()
 # Narrow local GET surface: known fixture works, arbitrary CSV and profile evidence do not.
 for path in ['/examples/not-shipped.csv','/profile-evidence/BASELINE.json','/column_profile_verification.json']:
  try:urllib.request.urlopen(u+path);ok=False
  except urllib.error.HTTPError as e:ok=e.code==404
  check('GET denied '+path,ok)
 check('no JS errors in original actual download flow',not errors);b.close()
(R/'column_profile_verification.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'actual_llm_calls':0,'human_observations':0,'scope':'Synthetic actual Chrome download/new-page/reordered import/engine/privacy/XSS/strict metadata/stale real SHA256 and file read timing; not a human usability or security certification'},ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULT',len(checks),'column profile browser checks passed')
