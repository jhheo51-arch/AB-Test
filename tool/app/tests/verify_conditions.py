"""R06 visible controls, real engine, local files, native help and PDF. No model calls."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'conditions-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);url=a.parse_args().url
checks=[];posts=[];errors=[]
IDS=['randomized','independent','mature','fixed-stop','segment-prespecified']
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n,flush=True)
def save(p,name):
 with p.expect_download() as d:p.click('#save-project')
 path=E/name;d.value.save_as(str(path));return json.loads(path.read_text(encoding='utf-8'))
def analyze(p):
 p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
def input_view(p):p.click('nav [data-view=input]')
def restore(p,x):
 p.set_input_files('#project-file',{'name':'conditions.json','mimeType':'application/json','buffer':json.dumps(x,ensure_ascii=False).encode()})
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
 p.goto(url,wait_until='networkidle')
 check('five selects only; no checkbox aliases',all(p.locator('#'+id).evaluate('(e)=>e.tagName')=='SELECT' for id in IDS) and p.locator('input#randomized,input#independent,input#mature,input#fixed-stop,input#segment-prespecified').count()==0)
 check('fresh page unknown and empty evidence',all(p.locator('#'+id).input_value()=='unknown' and p.locator('#'+id+'-evidence').input_value()=='' for id in IDS))
 p.click('#example-aggregate');p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
 check('demo assumptions honestly identified not proof',p.evaluate("Object.values(readConditions()).every(v=>v.origin==='synthetic_assumption'&&v.evidence==='')"))
 # Actual new file must not inherit any of the demo assertions.
 raw='arm,success,total,segment\nA,50,500,new\nB,75,500,new\nA,80,500,old\nB,75,500,old'
 p.set_input_files('#csv-file',{'name':'SYNTHETIC_R06.csv','mimeType':'text/csv','buffer':raw.encode()});expect(p.locator('#source-badge')).to_contain_text('사용자 CSV')
 check('actual CSV resets all conditions and evidence',all(p.locator('#'+id).input_value()=='unknown' and p.locator('#'+id+'-evidence').input_value()=='' for id in IDS))
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible();analyze(p)
 check('all unknown actual engine descriptive null inference',p.evaluate('!state.result.inference_allowed&&state.result.overall.p_raw===null&&state.result.overall.ci===null'))
 input_view(p)
 for id in IDS:p.select_option('#'+id,'no')
 analyze(p)
 check('all no actual engine descriptive null inference',p.evaluate('!state.result.inference_allowed&&state.result.overall.p_raw===null'))
 input_view(p)
 for id in IDS:p.select_option('#'+id,'yes')
 analyze(p)
 check('all yes actual engine p and counts',p.evaluate('state.result.inference_allowed&&Number.isFinite(state.result.overall.p_raw)&&state.result.overall.A.total===1000&&state.result.overall.B.success===150'))
 for id in IDS[:4]:
  for status in ['no','unknown']:
   input_view(p);p.select_option('#'+id,status);analyze(p)
   check(id+' '+status+' blocks actual engine',p.evaluate('!state.result.inference_allowed&&state.result.overall.p_raw===null'))
   input_view(p);p.select_option('#'+id,'yes');analyze(p)
 for status in ['unknown','no']:
  input_view(p);p.select_option('#segment-prespecified',status);analyze(p)
  check('segment '+status+' keeps overall valid, segments exploratory',p.evaluate('state.result.inference_allowed&&Number.isFinite(state.result.overall.p_raw)&&state.result.segments.every(g=>g.p_raw===null)'))
 input_view(p);p.select_option('#segment-prespecified','yes')
 text='<img src=x onerror="window.R06_XSS=1"> 사용자 메모 & 기록\nEVIDENCE_PRIVATE_R06'
 for i,id in enumerate(IDS):p.fill('#'+id+'-evidence',text+' '+str(i))
 check('free text never changes state to independent validation',p.evaluate("Object.values(readConditions()).every(v=>v.origin==='user_statement')"))
 x=save(p,'CONDITIONS_SAVED.json')
 check('schema7 exact evidence and canonical projection saved',x['version']==7 and all(x['conditions'][k]['status']=='yes' and x['plan'][k] for k in x['conditions']) and x['conditions']['randomized']['evidence']==text+' 0')
 p.close();p=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
 p.goto(url,wait_until='networkidle');restore(p,x);expect(p.locator('#data-text')).to_have_value(raw)
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
 y=save(p,'CONDITIONS_RESTORED.json');check('fresh page save restore exact all status evidence origin',x['conditions']==y['conditions'])
 p.set_viewport_size({'width':390,'height':844});expect(p.locator('#toast')).to_have_text('',timeout=8000);check('mobile no horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.locator('#randomized').scroll_into_view_if_needed();p.screenshot(path=str(E/'conditions-mobile.png'),full_page=True);p.set_viewport_size({'width':1440,'height':1000});p.locator('#randomized').scroll_into_view_if_needed();p.screenshot(path=str(E/'conditions-desktop.png'),full_page=True)
 analyze(p)
 check('user text escaped in local method details',p.evaluate('!window.R06_XSS') and p.locator('#method-details img').count()==0 and text+' 0' in p.locator('#method-details').text_content())
 check('minimal model facts exclude evidence and all free text',all(t not in p.evaluate('JSON.stringify(explanationFacts())') for t in ['EVIDENCE_PRIVATE_R06','사용자 메모','<img']))
 p.click('nav [data-view=share]');p.check('#share-confirm')
 with p.expect_download() as d:p.click('#export-report')
 d.value.save_as(str(E/'CONDITIONS_REPORT.html'));html=(E/'CONDITIONS_REPORT.html').read_text(encoding='utf-8')
 check('public HTML states included evidence excluded', '실험 조건 기록' in html and '확인됨' in html and 'EVIDENCE_PRIVATE_R06' not in html and '<img src=x' not in html)
 p.pdf(path=str(E/'CONDITIONS_REPORT.pdf'),format='A4');
 import fitz
 pdf=fitz.open(E/'CONDITIONS_REPORT.pdf');pdftext=''.join(page.get_text() for page in pdf);pdf.close()
 check('actual PDF states included evidence excluded','실험 조건 기록' in pdftext and 'EVIDENCE_PRIVATE_R06' not in pdftext)
 # Help preserves every new field exactly while playing, button close and Escape.
 input_view(p);p.select_option('#randomized','unknown');p.select_option('#independent','no')
 mixed=save(p,'CONDITIONS_MIXED.json');p.close();p=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
 p.goto(url,wait_until='networkidle');restore(p,mixed);expect(p.locator('#data-text')).to_have_value(raw);p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
 mixed_restored=save(p,'CONDITIONS_MIXED_RESTORED.json');check('fresh page mixed yes no unknown and all evidence exact',mixed['conditions']==mixed_restored['conditions'] and p.locator('#randomized').input_value()=='unknown' and p.locator('#independent').input_value()=='no' and not p.evaluate('plan().randomized||plan().independent'))
 p.check('#confirm-input')
 snapshot="() => ({conditions:readConditions(),forms:[...document.querySelectorAll('input,select,textarea')].filter(e=>e.type!=='file').map(e=>({id:e.id,value:e.value,checked:e.checked})),state:JSON.stringify(state),url:location.href,timeOrigin:performance.timeOrigin})"
 for method in ['button','Escape']:
  before=p.evaluate(snapshot);p.click('#demo-help');expect(p.locator('#demo-dialog')).to_be_visible();p.locator('#demo-video').evaluate('(e)=>e.play()');expect(p.locator('#demo-video')).to_have_js_property('paused',False)
  if method=='button':p.click('#close-demo')
  else:p.keyboard.press('Escape')
  expect(p.locator('#demo-dialog')).not_to_be_visible();check('help '+method+' immediate pause',p.locator('#demo-video').evaluate('(e)=>e.paused'));check('help '+method+' exact tri-state evidence state URL preserved',p.evaluate(snapshot)==before)
 # Results / confirmations / print are revoked by both state and evidence edits.
 for id in IDS:p.select_option('#'+id,'yes')
 for suffix in ['-evidence','']:
  analyze(p);p.click('nav [data-view=share]');p.check('#share-confirm');p.evaluate('preparePrint()');check('approved print populated '+suffix,p.locator('#print-area').inner_text()!='')
  input_view(p)
  if suffix:p.fill('#mature-evidence','EDITED_PRIVATE_R06')
  else:p.select_option('#mature','no')
  check('condition edit revokes result share input LLM print '+suffix,p.evaluate('state.result===null&&!document.querySelector("#share-confirm").checked&&!document.querySelector("#confirm-input").checked&&!document.querySelector("#llm-consent").checked&&document.querySelector("#print-area").textContent===""'))
  p.select_option('#mature','yes')
 analyze(p);before=p.evaluate('JSON.stringify({state,conditions:readConditions(),data:document.querySelector("#data-text").value})')
 for kind in ['conflict','oversize','invalid']:
  bad=json.loads(json.dumps(x))
  if kind=='conflict':bad['plan']['randomized']=False
  elif kind=='oversize':bad['conditions']['mature']['evidence']='x'*1001
  else:bad['conditions']['fixedStop']['status']=''
  restore(p,bad);expect(p.locator('#toast')).to_contain_text('복원 실패');check('invalid '+kind+' restore preserves current result and records',p.evaluate('JSON.stringify({state,conditions:readConditions(),data:document.querySelector("#data-text").value})')==before)
 input_view(p);p.fill('#mature-evidence','가'*1000);cap=save(p,'EVIDENCE_CAP.json');check('visible evidence cap matches schema',p.locator('#mature-evidence').get_attribute('maxlength')=='1000' and len(cap['conditions']['mature']['evidence'])==1000)
 # Legacy migration is asserted in browser as well as Node, including schema6.
 for version in [2,3,4,5,6]:
  old=json.loads(json.dumps(x));old['version']=version;old.pop('conditions');old['plan']['randomized']=False
  restore(p,old);expect(p.locator('#randomized')).to_have_value('unknown');p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible();m=save(p,'LEGACY_'+str(version)+'.json')
  check('legacy '+str(version)+' honest false unknown true assertion empty evidence',m['conditions']['randomized']=={'status':'unknown','evidence':'','origin':'legacy_unconfirmed'} and m['conditions']['mature']=={'status':'yes','evidence':'','origin':'legacy_user_confirmation'})
 check('no model POST or page errors',posts==[] and errors==[]);b.close()
result={'status':'PASS','count':len(checks),'checks':checks,'posts':posts,'page_errors':errors,'human_observations':0,'actual_model_calls':0,'scope':'synthetic actual Chrome; visible controls, engine gates, JSON freshpage migration, PDF and actual video; not independent experiment verification'}
(R/'conditions_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',len(checks),'R06 browser checks passed')
