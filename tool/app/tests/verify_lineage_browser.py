from condition_controls import set_checked, is_checked
"""R03: typed hash roundtrips, legacy uncertainty, output and stale-await checks."""
from pathlib import Path
import argparse,json,hashlib,time
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--url',required=True);u=a.parse_args().url;checks=[]
sha=lambda s:hashlib.sha256(s.encode('utf-8')).hexdigest()
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n,flush=True)
def prepare(p):p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])')
def analyze(p):
 for k in ['randomized','independent','mature','fixed-stop']:set_checked(p, '#' + k)
 set_checked(p, '#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])')
def save(p):
 with p.expect_download() as d:p.click('#save-project')
 return json.loads(Path(d.value.path()).read_text(encoding='utf-8'))
def restore(p,x):
 p.goto(u,wait_until='networkidle');p.set_input_files('#project-file',{'name':'synthetic.json','mimeType':'application/json','buffer':json.dumps(x).encode()});expect(p.locator('#source-badge')).to_contain_text('집계 복원')
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page(accept_downloads=True);errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(u,wait_until='networkidle')
 raw='variant,converted,participants\nA,1,10\nB,2,10';canonical='arm,success,total\nA,1,10\nB,2,10';p.fill('#data-text',raw);p.click('#prepare');p.wait_for_selector('#mapping-panel:not([hidden])');set_checked(p, '#mapping-confirm');p.click('#apply-mapping');p.wait_for_selector('#analysis-options:not([hidden])');analyze(p);l=p.evaluate('state.lineage')
 check('original digest hashes actual input text',l['origin']=={'kind':'input_text_utf8','digest':sha(raw)})
 check('analysis digest hashes actual converted CSV',l['current']=={'kind':'analysis_csv_utf8','digest':sha(canonical)} and l['origin']['digest']!=l['current']['digest'])
 x=save(p);check('current schema stores typed lineage and matching compatibility alias',x['version']==7 and x['lineage']==l and x['source_digest']==l['current']['digest'])
 restore(p,x);prepare(p);analyze(p);l2=p.evaluate('state.lineage');check('restore preserves origin and immediate prior calculation record',l2['origin']==l['origin'] and l2['previous']==l['current']);check('restored input gets actual aggregate kind not original claim',l2['current']['kind']=='restored_aggregate_csv_utf8' and l2['current']['digest']==sha(canonical) and l2['transformation']['name']=='aggregate_restore')
 x2=save(p);restore(p,x2);prepare(p);analyze(p);l3=p.evaluate('state.lineage');check('second restore retains origin and labels latest parent',l3['origin']==l['origin'] and l3['previous']==l2['current'])
 p.click('nav [data-view=share]');text=p.locator('#report-preview').inner_text();check('report labels origin previous current and limits',all(s in text for s in ['최초 입력의 기록','복원 전 직전 계산 기록','이번 계산 입력','원자료를 다시 검증하지 않았습니다']))
 set_checked(p, '#share-confirm');p.emulate_media(media='print');(R/'lineage_evidence').mkdir(exist_ok=True);p.pdf(path=str(R/'lineage_evidence/LINEAGE_REPORT.pdf'),format='A4',print_background=True);p.emulate_media(media='screen')
 check('typed lineage is excluded from explanation payload',all(h not in p.evaluate('JSON.stringify(explanationFacts())') for h in [sha(raw),sha(canonical)]))
 legacy=json.loads(json.dumps(x));legacy['version']=4;legacy.pop('lineage');legacy['source_digest']='A'*64;restore(p,legacy);prepare(p);analyze(p);ll=p.evaluate('state.lineage');check('legacy hash is retained literally with unknown target type',ll['origin']=={'kind':'legacy_untyped','digest':'A'*64} and ll['previous'] is None)
 p.click('nav [data-view=input]');fresh='arm,success,total\nA,3,10\nB,4,10';p.fill('#data-text',fresh);prepare(p);analyze(p);nl=p.evaluate('state.lineage');check('edited source starts fresh lineage instead of false inherited origin',nl['origin']['digest']==sha(fresh) and nl['previous'] is None)
 before=p.evaluate('JSON.stringify(state.lineage)');p.set_input_files('#project-file',{'name':'bad.json','mimeType':'application/json','buffer':b'{}'});expect(p.locator('#toast')).to_contain_text('복원 실패');check('invalid restore preserves previous valid lineage',p.evaluate('JSON.stringify(state.lineage)')==before)
 p.close()
 p=b.new_page();p.add_init_script("const old=crypto.subtle.digest.bind(crypto.subtle);crypto.subtle.digest=(...args)=>old(...args).then(h=>new TextDecoder().decode(args[1])==='arm,success,total\\nA,1,10\\nB,2,10'?new Promise(resolve=>window.releaseCanonicalHash=()=>resolve(h)):h)");p.goto(u,wait_until='networkidle');p.fill('#data-text',raw);p.click('#prepare');p.wait_for_selector('#mapping-panel:not([hidden])');set_checked(p, '#mapping-confirm');p.click('#apply-mapping');deadline=time.monotonic()+15
 while time.monotonic()<deadline and not p.evaluate("typeof window.releaseCanonicalHash==='function'"):p.wait_for_timeout(30)
 check('canonical hash delay is real pending work',p.evaluate("typeof window.releaseCanonicalHash==='function'&&state.prepared===null"));p.fill('#data-text',fresh);p.evaluate('window.releaseCanonicalHash()');prepare(p);analyze(p);check('older canonical hash cannot attach stale lineage',p.evaluate('state.lineage.origin.digest')==sha(fresh) and p.evaluate('state.prepared.cells[0].success')==3);p.close();check('no uncaught primary page errors',not errors);b.close()
(R/'R03_browser_verification.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'scope':'synthetic controlled timing; real SHA-256, file downloads and PDF; no model requests'},ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',len(checks),'R03 browser checks passed')
