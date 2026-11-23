"""Real fetched sample bytes gated after text decode; cross-input ownership."""
from pathlib import Path
import argparse,json,time,traceback
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'startscreen-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);a.add_argument('--baseline',action='store_true');args=a.parse_args();checks=[]
RAW='arm,success,total\nA,1,10\nB,2,10';NEW='arm,success,total\nA,3,10\nB,4,10'
def check(n,v):
 checks.append({'name':n,'pass':bool(v)});print('PASS' if v else 'FAIL',n,flush=True)
 if not v and not args.baseline:raise AssertionError(n)
def snap(p):return p.evaluate('JSON.stringify({state,rollout:rollout.current(),conditions:readConditions(),raw:$("#data-text").value,meta:experimentMeta(),forms:[...document.querySelectorAll("input,textarea,select")].filter(e=>e.type!=="file").map(e=>[e.id,e.name,e.value,e.checked,e.disabled])})')
def wait(p,expr):
 end=time.monotonic()+10
 while time.monotonic()<end:
  if p.evaluate(expr):return
  p.wait_for_timeout(20)
 raise AssertionError('bounded gate wait '+expr)
result={'status':'FAIL','checks':checks,'actual_model_calls':0,'human_observations':0,'scope':'actual Chrome and actual local GET sample bytes; delayed real response.text completion, no synthetic successful response; file picker automated'}
try:
 with sync_playwright() as w:
  b=w.chromium.launch(channel='chrome')
  def page():
   p=b.new_page();p.set_default_timeout(12000);p.route('**/api/explain',lambda r:r.abort());p.goto(args.url,wait_until='networkidle');p.fill('#data-text',RAW);p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
   p.evaluate('''()=>{window.actualFetch=fetch;window.sampleGates=[];window.fetch=async(...args)=>{const response=await actualFetch(...args);if(String(args[0]).includes('examples/projects/')){const original=response.text.bind(response);response.text=async()=>{const real=await original();return await new Promise(resolve=>sampleGates.push(()=>resolve(real)));};}return response;};}''');return p
  selector='[data-rollout-example="routine-service-original-hold.json"]'
  for action in ['CSV','condition','project']:
   p=page();p.click(selector);wait(p,'sampleGates.length===1')
   if action=='CSV':
    p.set_input_files('#csv-file',{'name':'NEW.csv','mimeType':'text/csv','buffer':NEW.encode()});expect(p.locator('#data-text')).to_have_value(NEW);expect(p.locator('#prepare')).to_be_enabled()
   elif action=='condition':p.select_option('#mature','yes')
   else:
    data=(R/'examples/projects/routine-service-edited-review.json').read_bytes();p.set_input_files('#project-file',{'name':'PROJECT.json','mimeType':'application/json','buffer':data});expect(p.locator('#rollout-decision')).to_have_text('확대 검토 가능');expect(p.locator('#prepare')).to_be_enabled()
   before=snap(p);p.evaluate('()=>{sampleGates[0]();}');p.wait_for_timeout(100);check('late fetched sample cannot overwrite newer '+action,snap(p)==before);p.close()
  p=page();p.click(selector);wait(p,'sampleGates.length===1')
  p.evaluate('''()=>{window.realRead=File.prototype.arrayBuffer;File.prototype.arrayBuffer=async function(){const bytes=await realRead.call(this);return await new Promise(r=>window.releaseCSV=()=>r(bytes));};}''')
  p.set_input_files('#csv-file',{'name':'PENDING.csv','mimeType':'text/csv','buffer':NEW.encode()});wait(p,'typeof releaseCSV==="function"');p.evaluate('()=>{sampleGates[0]();}');p.wait_for_timeout(100)
  check('old sample finally cannot unlock newer CSV read',p.evaluate('inputTask?.kind==="file"&&$("#prepare").disabled'))
  check('old sample cannot inject rollout while newer CSV owns input',p.evaluate('rollout.current()===null'))
  p.evaluate('()=>{releaseCSV();File.prototype.arrayBuffer=realRead;}');expect(p.locator('#prepare')).to_be_enabled();p.close()
  p=page();p.evaluate('''()=>{window.realRead=File.prototype.arrayBuffer;File.prototype.arrayBuffer=async function(){const bytes=await realRead.call(this);return await new Promise(r=>window.releaseCSV=()=>r(bytes));};}''')
  p.set_input_files('#csv-file',{'name':'OLD.csv','mimeType':'text/csv','buffer':NEW.encode()});wait(p,'typeof releaseCSV==="function"');p.click(selector);wait(p,'sampleGates.length===1');p.evaluate('()=>{sampleGates[0]();}');expect(p.locator('#rollout-example-status')).to_contain_text('원래 사례 / 확대 보류');before=snap(p);p.evaluate('()=>{releaseCSV();File.prototype.arrayBuffer=realRead;}');p.wait_for_timeout(100)
  check('new sample cancels older file read and preserves newer result',snap(p)==before and p.locator('#data-text').input_value()==RAW);p.close()
  p=page();p.click(selector);wait(p,'sampleGates.length===1');p.click('[data-rollout-example="routine-service-edited-review.json"]');wait(p,'sampleGates.length===2');p.evaluate('()=>{sampleGates[0]();}');p.wait_for_timeout(100)
  check('old sample cannot apply or unlock newer sample',p.evaluate('rollout.current()===null&&rolloutExampleRequest!==null'))
  p.evaluate('()=>{sampleGates[1]();}');expect(p.locator('#rollout-decision')).to_have_text('확대 검토 가능');check('new sample actual bytes applied with controls released',p.locator('#prepare').is_enabled() and p.locator('#data-text').input_value()==RAW);p.close();b.close()
 result['status']='PASS' if all(x['pass'] for x in checks) else 'FAIL'
except Exception as exc:result['error']=str(exc);result['traceback']=traceback.format_exc()
result['count']=len(checks);(E/('ASYNC_BASELINE.json' if args.baseline else 'BROWSER_VERIFICATION.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'count':len(checks),'error':result.get('error')},ensure_ascii=False));raise SystemExit(0 if args.baseline or result['status']=='PASS' else 1)
