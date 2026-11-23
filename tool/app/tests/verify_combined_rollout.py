"""Combined R08/rollout state ownership and supplied example regression."""
from pathlib import Path
import argparse,json,traceback
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'startscreen-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);a.add_argument('--baseline',action='store_true');args=a.parse_args();checks=[]
def check(n,v):
 checks.append({'name':n,'pass':bool(v)});print('PASS' if v else 'FAIL',n,flush=True)
 if not v and not args.baseline:raise AssertionError(n)
def snapshot(p):return p.evaluate('JSON.stringify({state,rollout:rollout.current(),conditions:readConditions(),meta:experimentMeta(),design,forms:[...document.querySelectorAll("input,textarea,select")].filter(e=>e.type!=="file").map(e=>[e.id,e.name,e.value,e.checked,e.disabled]),print:$("#print-area").innerHTML})')
def load(p,x):
 p.set_input_files('#project-file',{'name':'PROVIDED.json','mimeType':'application/json','buffer':json.dumps(x).encode()});expect(p.locator('#rollout > summary')).to_be_visible()
result={'status':'FAIL','checks':checks,'actual_model_calls':0,'human_observations':0,'scope':'supplied synthetic release JSON, real Chrome file automation (not native picker); existing rollout math unchanged'}
try:
 with sync_playwright() as w:
  b=w.chromium.launch(channel='chrome');p=b.new_page(accept_downloads=True);p.set_default_timeout(12000);p.route('**/api/explain',lambda r:r.abort());p.goto(args.url,wait_until='networkidle')
  # Exact published inputs: normalize/recalculate, never fabricate operational approvals.
  names=['routine-service-original-hold.json','routine-service-metrics-met-hold.json','routine-service-edited-review.json']
  for name,decision in zip(names,['hold','hold','review']):
   data=(R/'examples/projects'/name).read_bytes();project=json.loads(data);load(p,project);expect(p.locator('#rollout-decision')).to_have_text('확대 보류' if decision=='hold' else '확대 검토 가능')
   check('provided input recalculates expected decision '+name,p.evaluate('rollout.current().decision')==decision)
   with p.expect_download() as d:p.click('#save-project')
   saved=json.loads(Path(d.value.path()).read_text('utf-8'));check('provided schema8 exact input roundtrip '+name,saved['version']==8 and saved['rollout']['input']==project['rollout']['input'])
   if name==names[1]:check('metrics met does not invent operational approval',saved['rollout']['input']['capacity']==saved['rollout']['input']['cost']=='unknown' and saved['rollout']['decision']=='hold')
  # A valid schema7 project resets rollout, invalid schema8 is atomic.
  good=json.loads((R/'examples/projects'/names[2]).read_text('utf-8'));p.fill('#purpose','COMBINED_RAW_NOTE');p.fill('#policy-a','REVIEW_ONLY_NOT_APPROVAL');p.click('nav [data-view=share]');p.check('#share-confirm');p.evaluate('preparePrint()');p.click('nav [data-view=input]');before=snapshot(p)
  for label,buffer in [('size',b'X'*(2097152+1)),('utf8',b'\xc3\x28'),('syntax',b'arm,success,total\nA,"unterminated')]:
   p.set_input_files('#csv-file',{'name':'INVALID.csv','mimeType':'text/csv','buffer':buffer});expect(p.locator('#toast')).to_contain_text('파일 읽기 실패');expect(p.locator('#prepare')).to_be_enabled();check('invalid CSV preserves rollout decision operational statements notes sharing print '+label,snapshot(p)==before)
  bad=json.loads(json.dumps(good));bad['rollout']['input']['visit-b']=999999
  load(p,bad);expect(p.locator('#toast')).to_contain_text('복원 실패');check('invalid schema8 cannot replace current rollout state',snapshot(p)==before)
  p.set_input_files('#csv-file',{'name':'VALID.csv','mimeType':'text/csv','buffer':b'arm,success,total\nA,1,10\nB,2,10'});expect(p.locator('#data-text')).to_have_value('arm,success,total\nA,1,10\nB,2,10');expect(p.locator('#prepare')).to_be_enabled()
  check('valid new CSV clears old rollout operational approval and derived decision',p.evaluate('rollout.current()===null') and p.locator('[name=capacity]').input_value()=='unknown' and p.locator('[name=cost]').input_value()=='unknown')
  check('valid new CSV discards sharing and print confirmation',p.evaluate('!$("#share-confirm").checked&&$("#print-area").textContent===""'))
  # Pending real file bytes cannot wipe a newer rollout edit after completion.
  load(p,good);expect(p.locator('#rollout-decision')).to_have_text('확대 검토 가능')
  p.evaluate('''()=>{window.realBuffer=File.prototype.arrayBuffer;File.prototype.arrayBuffer=async function(){const bytes=await realBuffer.call(this);return await new Promise(r=>window.releaseCombinedRead=()=>r(bytes));};}''')
  p.set_input_files('#csv-file',{'name':'DELAYED.csv','mimeType':'text/csv','buffer':b'arm,success,total\nA,3,10\nB,4,10'});expect(p.locator('#prepare')).to_be_disabled();p.fill('[name=visit-b]','1700');edited=snapshot(p);p.evaluate('()=>{releaseCombinedRead();File.prototype.arrayBuffer=realBuffer;}');p.wait_for_timeout(100)
  check('new rollout edit cancels old CSV ownership without stale overwrite',snapshot(p)==edited and p.locator('[name=visit-b]').input_value()=='1700' and p.locator('#prepare').is_enabled())
  # Schema7 remains a supported CSV/plan save, not misreported as a lost migration.
  legacy=json.loads(json.dumps(good));legacy['version']=7;legacy.pop('rollout');load(p,legacy);expect(p.locator('[name=visit-b]')).to_have_value('');check('schema7 restore explicitly clears prior rollout and accepts legacy conditions',p.evaluate('rollout.current()===null') and p.locator('nav [data-view=share]').is_disabled())
  b.close()
 result['status']='PASS' if all(c['pass'] for c in checks) else 'FAIL'
except Exception as exc:result['error']=str(exc);result['traceback']=traceback.format_exc()
result['count']=len(checks);(E/('COMBINED_BASELINE.json' if args.baseline else 'COMBINED_VERIFICATION.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'count':len(checks),'error':result.get('error')},ensure_ascii=False));raise SystemExit(0 if args.baseline or result['status']=='PASS' else 1)
