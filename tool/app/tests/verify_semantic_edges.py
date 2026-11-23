"""Real UI regressions for lossless metadata/evidence and atomic invalid imports."""
from pathlib import Path
import argparse,json,copy
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'fix-evidence'/'semantic';E.mkdir(parents=True,exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);url=a.parse_args().url
checks=[];blocked=[];errors=[]
FIELDS={'purpose':'purpose','metric':'metric','window':'window','policyA':'policy-a','policyB':'policy-b','audience':'audience'}
IDS={'randomized':'randomized','independent':'independent','mature':'mature','fixedStop':'fixed-stop','segmentPrespecified':'segment-prespecified'}
RAW='arm,success,total\nA,10,100\nB,20,100'
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n,flush=True)
def restore(p,x,valid=True):
 p.set_input_files('#project-file',{'name':'SYNTHETIC.json','mimeType':'application/json','buffer':json.dumps(x,ensure_ascii=False).encode()})
 expect(p.locator('#toast')).to_contain_text('복원했습니다' if valid else '복원 실패')
def save(p,name):
 with p.expect_download() as d:p.click('#save-project')
 path=E/(name+'.json');d.value.save_as(str(path));return json.loads(path.read_text(encoding='utf-8'))
def prepare(p):
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
def snapshot(p):return p.evaluate('JSON.stringify({state,design,conditions:readConditions(),meta:experimentMeta(),raw:document.querySelector("#data-text").value,print:document.querySelector("#print-area").innerHTML})')
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 def page():
  p=b.new_page(accept_downloads=True)
  def guard(route):
   if route.request.method!='GET' or not route.request.url.startswith(url+'/'):blocked.append(route.request.url);route.abort()
   else:route.continue_()
  p.route('**/*',guard);p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url,wait_until='networkidle');return p
 p=page();p.click('nav [data-view=design]');p.click('#begin-design')
 text='첫째\n둘째 <img src=x onerror="window.S01=1"> & 😀'
 for k in FIELDS:p.fill('#design-'+k,text+' '+k)
 p.click('#design-to-input');x=save(p,'MULTILINE_PLAN')
 for k,id in FIELDS.items():check('S01 native multiline '+k,x['design']['fields'][k]['value']==text+' '+k==x['plan'][k] and p.locator('#'+id).input_value()==text+' '+k)
 p.close();p=page();restore(p,x);y=save(p,'MULTILINE_PLAN_FRESH');check('S01 native plan fresh exact',x['design']==y['design'] and x['plan']==y['plan'])
 p.click('#design-to-input');p.set_input_files('#csv-file',{'name':'SYNTHETIC.csv','mimeType':'text/csv','buffer':RAW.encode()});expect(p.locator('#data-text')).to_have_value(RAW);prepare(p);z=save(p,'MULTILINE_WITH_CSV')
 check('S01 CSV linked all metadata exact',all(z['plan'][k]==text+' '+k==z['design']['fields'][k]['value'] for k in FIELDS))
 p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible();check('S01 escaped output',not p.evaluate('Boolean(window.S01)') and p.locator('#experiment-context img').count()==0)
 baseline=copy.deepcopy(z)
 # Native textarea editing has the browser's LF contract; imported raw strings use a separate lossless shadow.
 for label,note in [('CRLF','첫째\r\n둘째'),('CR','첫째\r둘째'),('MIXED','첫째\r\n둘째\r셋째\n넷째')]:
  p.close();p=page();p.click('nav [data-view=design]');p.click('#begin-design')
  canonical=note.replace('\r\n','\n').replace('\r','\n')
  for k in FIELDS:p.fill('#design-'+k,note)
  p.click('#design-to-input');native=save(p,'NATIVE_'+label)
  check('S01 native '+label+' all duplicate fields',all(native['plan'][k]==native['design']['fields'][k]['value']==canonical for k in FIELDS))
 for label,note in [('LF','첫째\n둘째'),('CRLF','첫째\r\n둘째'),('CR','첫째\r둘째'),('MIXED','첫째\r\n둘째\r셋째\n넷째'),('NONBMP','😀'*500)]:
  p.close();p=page();x=copy.deepcopy(baseline)
  for k in FIELDS:
   value=note if label!='NONBMP' or k!='audience' else '😀'*150
   x['plan'][k]=value;x['design']['fields'][k]['value']=value
  for k in IDS:x['conditions'][k]['evidence']=note+'가'*(1000-len(note.encode('utf-16-le'))//2)
  restore(p,x);before=snapshot(p);p.click('nav [data-view=design]');p.click('#design-next');p.click('#design-back');p.click('nav [data-view=input]')
  check('raw DOM display and navigation not edits '+label,snapshot(p)==before)
  prepare(p);y=save(p,'RAW_'+label)
  for k in FIELDS:check('S01 imported '+label+' '+k,y['plan'][k]==x['plan'][k]==y['design']['fields'][k]['value'])
  for k in IDS:check('S02 imported '+label+' '+k,y['conditions'][k]==x['conditions'][k])
  p.close();p=page();restore(p,y);prepare(p);zz=save(p,'FRESH_'+label)
  check('S01 S02 second new page '+label,zz['conditions']==y['conditions'] and zz['plan']==y['plan'] and zz['design']==y['design'])
  if label=='MIXED':
   p.select_option('#mature','yes');y2=save(p,'STATUS_ONLY');check('S02 status-only retains raw',y2['conditions']['mature']['evidence']==x['conditions']['mature']['evidence'])
   p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible();p.click('nav [data-view=share]');p.check('#share-confirm');p.evaluate('preparePrint()');p.click('nav [data-view=input]');p.fill('#mature-evidence','EDITED_PRIVATE\nline')
   check('S02 actual edit invalidates result and confirmations',p.evaluate('state.result===null&&!document.querySelector("#confirm-input").checked&&!document.querySelector("#share-confirm").checked&&!document.querySelector("#llm-consent").checked&&document.querySelector("#print-area").textContent===""'))
   edited=save(p,'EDITED');check('S02 edit replaces only own raw evidence',edited['conditions']['mature']['evidence']=='EDITED_PRIVATE\nline' and edited['conditions']['randomized']['evidence']==x['conditions']['randomized']['evidence'])
   p.fill('#metric','EDITED\nmetric');edited=save(p,'META_EDITED');check('S01 input edit replaces both duplicate metadata',edited['plan']['metric']==edited['design']['fields']['metric']['value']=='EDITED\nmetric')
 # Crafted invalid imports are rejected before any current input or result mutation.
 p.close();p=page();restore(p,baseline);prepare(p);p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
 for version in range(2,8):
  for defect in ['collision']+(['dangling'] if version>=5 else []):
   bad=copy.deepcopy(baseline);bad['version']=version
   if defect=='collision':bad['cells']=[{'arm':'A','segment':None,'success':1,'total':10},{'arm':'A','segment':'','success':2,'total':10}]
   else:bad['source_digest']='A'*64;bad['lineage']={'version':1,'algorithm':'SHA-256','origin':{'kind':'unknown','digest':None},'previous':None,'current':None,'transformation':{'name':'none','version':'0.5.1'}}
   before=snapshot(p);restore(p,bad,False);check('atomic '+defect+' schema '+str(version),snapshot(p)==before)
 for note in ['가'*1001,'😀'*500+'x']:
  bad=copy.deepcopy(baseline);bad['conditions']['mature']['evidence']=note;before=snapshot(p);restore(p,bad,False);check('S02 UTF16 overflow atomic '+str(len(note)),snapshot(p)==before)
 for version in [2,3,4]:
  x=copy.deepcopy(baseline);x['version']=version;x['source_digest']='A'*64;restore(p,x);prepare(p);y=save(p,'LEGACY_HASH_'+str(version));check('S04 legacy hash retained '+str(version),y['lineage']['origin']=={'kind':'legacy_untyped','digest':'A'*64} and y['lineage']['current']['kind']=='restored_aggregate_csv_utf8')
 # Raw imported CR evidence remains private in real public HTML/PDF and minimum facts.
 x=copy.deepcopy(baseline);marker='RAW_PRIVATE_EVIDENCE';x['conditions']['mature']['evidence']=marker+'\r\n둘째\r셋째';restore(p,x);prepare(p);p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
 check('S02 raw private evidence excluded from facts',marker not in json.dumps(p.evaluate('explanationFacts()')))
 p.click('nav [data-view=share]');p.check('#share-confirm')
 with p.expect_download() as d:p.click('#export-report')
 d.value.save_as(str(E/'RAW_PRIVACY_REPORT.html'));check('S02 raw private evidence excluded from HTML',marker not in (E/'RAW_PRIVACY_REPORT.html').read_text(encoding='utf-8'))
 p.pdf(path=str(E/'RAW_PRIVACY_REPORT.pdf'),format='A4')
 import fitz
 with fitz.open(E/'RAW_PRIVACY_REPORT.pdf') as doc:check('S02 raw private evidence excluded from PDF',marker not in ''.join(pg.get_text() for pg in doc))
 p.evaluate('preparePrint()');p.click('nav [data-view=input]')
 p.evaluate('''() => {window.originalFileBuffer=File.prototype.arrayBuffer;File.prototype.arrayBuffer=async function(){const actual=await originalFileBuffer.call(this);await new Promise(resolve=>window.releaseRawRestore=resolve);return actual;};}''')
 p.set_input_files('#project-file',{'name':'DELAYED.json','mimeType':'application/json','buffer':json.dumps(baseline).encode()});expect(p.locator('#prepare')).to_be_disabled()
 p.fill('#mature-evidence','EDITED_DURING_RAW_RESTORE')
 check('S02 actual evidence edit cancels async restore ownership',p.evaluate('state.result===null&&inputTask===null&&!document.querySelector("#confirm-input").checked&&!document.querySelector("#share-confirm").checked&&!document.querySelector("#llm-consent").checked&&document.querySelector("#print-area").textContent===""'))
 p.evaluate('() => {releaseRawRestore();File.prototype.arrayBuffer=originalFileBuffer;}');p.wait_for_timeout(250)
 check('S02 released stale actual file cannot overwrite raw edit',p.evaluate('readConditions().mature.evidence==="EDITED_DURING_RAW_RESTORE"&&inputTask===null&&state.prepared!==null'))
 check('no model external requests or page errors',not blocked and not errors);b.close()
result={'status':'PASS','count':len(checks),'checks':checks,'blocked_requests':blocked,'page_errors':errors,'actual_model_calls':0,'human_observations':0,'scope':'synthetic actual Chrome; native edit, exact raw CR/LF import at UTF-16 cap, freshpage download, atomic invalid restore, raw-evidence HTML/PDF/minimum-facts exclusion, delayed actual file ownership; not human observation or experiment validity certification'}
(E/'BROWSER_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',len(checks),'semantic browser checks passed')
