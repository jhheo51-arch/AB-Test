"""Read-only application audit. Delays real browser APIs, never fakes hashes/data/model results."""
from pathlib import Path
import argparse,json,time
from playwright.sync_api import sync_playwright,expect
args=argparse.ArgumentParser();args.add_argument('--url',required=True);args.add_argument('--out',required=True);a=args.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
results=[];posts=[]
def save(row):
    results.append(row);(out/'E2E_AUDIT.json').write_text(json.dumps({'scope':'synthetic adversarial audit; no app source edits; timing controlled only where stated','cases':results,'post_requests':posts},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(row,ensure_ascii=False),flush=True)
def wait_js(p,expr):
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if p.evaluate(expr):return
        p.wait_for_timeout(30)
    raise AssertionError('condition not reached: '+expr)
def page(browser,init=None):
    p=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    p.on('request',lambda req:posts.append({'url':req.url,'method':req.method}) if req.method=='POST' else None)
    if init:p.add_init_script(init)
    p.goto(a.url,wait_until='networkidle');return p
def sample_result(p):
    p.click('#example-aggregate');p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])')
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=page(browser);sample_result(p);p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_OLD_PRINT_AUDIENCE');p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])');p.click('.result-heading>button[data-view=share]');p.fill('#decision','SYNTHETIC_OLD_APPROVED_DECISION');p.check('#share-confirm');p.evaluate('window.print=()=>{}');p.click('#print-report')
    old_print=p.locator('#print-area').text_content();p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_NEW_UNANALYZED_AUDIENCE')
    residual=p.locator('#print-area').text_content();p.emulate_media(media='print');p.pdf(path=str(out/'stale_print_after_edit.pdf'),format='A4',print_background=True);p.emulate_media(media='screen')
    save({'id':'E01','scenario':'print approved old report, edit audience, use browser print pipeline without app print button','finding_reproduced':bool(residual) and 'SYNTHETIC_OLD_PRINT_AUDIENCE' in residual,'results_disabled':p.locator('nav [data-view=results]').is_disabled(),'share_confirmation_cleared':not p.locator('#share-confirm').is_checked(),'old_print_retained':residual==old_print,'new_audience_in_print':'SYNTHETIC_NEW_UNANALYZED_AUDIENCE' in residual,'evidence':'stale_print_after_edit.pdf','timing_controlled':False});p.close()
    init="""const realDigest=crypto.subtle.digest.bind(crypto.subtle);crypto.subtle.digest=(...args)=>realDigest(...args).then(hash=>new Promise(resolve=>{window.releaseAuditDigest=()=>resolve(hash)}));"""
    p=page(browser,init);p.click('#example-aggregate');p.click('#prepare');wait_js(p,"typeof window.releaseAuditDigest==='function'");busy_before=p.evaluate('state.busy');p.fill('#data-text','arm,success,total\nA,10,100\nB,30,100');p.evaluate('window.releaseAuditDigest()');p.wait_for_timeout(100)
    save({'id':'E02','scenario':'edit data while actual SHA-256 promise completion is delayed','finding_reproduced':p.locator('#prepare').is_disabled(),'worker_busy_during_hash':busy_before,'prepare_button_disabled_after_cancel':p.locator('#prepare').is_disabled(),'data_still_editable':p.locator('#data-text').is_editable(),'timing_controlled':'real crypto digest result delayed; bytes/hash not modified'});p.screenshot(path=str(out/'hash_cancel_disabled.png'));p.close()
    init="""const read=Blob.prototype.arrayBuffer;Blob.prototype.arrayBuffer=function(...args){const name=this.name;return read.apply(this,args).then(bytes=>name==='AUDIT_SLOW.csv'?new Promise(resolve=>{window.releaseAuditFile=()=>resolve(bytes)}):bytes)};"""
    p=page(browser,init);slow='arm,success,total\nA,1,10\nB,2,10';typed='arm,success,total\nA,40,100\nB,50,100';p.set_input_files('#csv-file',{'name':'AUDIT_SLOW.csv','mimeType':'text/csv','buffer':slow.encode()});wait_js(p,"typeof window.releaseAuditFile==='function'");p.fill('#data-text',typed);p.evaluate('window.releaseAuditFile()');expect(p.locator('#source-badge')).to_contain_text('사용자 CSV')
    save({'id':'E03','scenario':'type new table while earlier file read is pending','finding_reproduced':p.locator('#data-text').input_value()==slow,'latest_typed_table_preserved':p.locator('#data-text').input_value()==typed,'source_after':p.locator('#source-badge').inner_text(),'timing_controlled':'actual file bytes delayed; not modified'});p.close()
    p=page(browser);p.fill('#data-text','arm,success,total\nA,100,200001\nB,110,200001');p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])')
    with p.expect_download() as d:p.click('#save-project')
    text=Path(d.value.path()).read_text(encoding='utf-8');p.goto(a.url,wait_until='networkidle');p.set_input_files('#project-file',{'name':'saved-outside-inference-cap.json','mimeType':'application/json','buffer':text.encode()});expect(p.locator('#toast')).to_contain_text('복원 실패')
    save({'id':'E04','scenario':'save valid integer input above inference cap then restore generated project','finding_reproduced':'복원 실패' in p.locator('#toast').inner_text(),'save_succeeded':True,'restore_message':p.locator('#toast').inner_text(),'scope':'outside supported inference cap; parser/save permit it; round-trip inconsistency not evidence of wrong statistics','timing_controlled':False});p.close()
    p=page(browser);sample_result(p);before=p.locator('#overall-results').inner_text();p.set_input_files('#project-file',{'name':'broken.json','mimeType':'application/json','buffer':b'{broken json'});expect(p.locator('#toast')).to_contain_text('복원 실패')
    save({'id':'E05','scenario':'malformed project must not destroy current result','pass':p.locator('#overall-results').inner_text()==before and p.locator('#results-view').is_visible(),'timing_controlled':False});p.close()
    p=page(browser);sample_result(p);held=[];p.route('**/api/explain',lambda route:held.append(route));p.check('#llm-consent');p.click('#explain');wait_js(p,"document.querySelector('#llm-status').textContent==='실제 요청 중'")
    p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_CHANGED_WHILE_MODEL_PENDING');p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])');held[0].fulfill(status=503,content_type='application/json',body='{"error":"AUDIT_INJECTED_OLD_FAILURE","message":"SYNTHETIC_OLD_REQUEST_FAILURE"}');p.wait_for_timeout(100)
    save({'id':'E06','scenario':'late old explanation failure after reanalysis must not overwrite new result','pass':'SYNTHETIC_OLD_REQUEST_FAILURE' not in p.locator('#llm-answer').inner_text() and p.locator('#llm-status').inner_text()=='미요청','timing_controlled':'explicit simulated HTTP 503, not actual model failure'});p.close()
    p=page(browser);long_name='X'*201;csv='arm,success,total,segment\nA,10,100,'+long_name+'\nB,20,100,'+long_name+'\nA,10,100,Y\nB,20,100,Y';p.fill('#data-text',csv);p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])')
    with p.expect_download() as d:p.click('#save-project')
    text=Path(d.value.path()).read_text(encoding='utf-8');saved=json.loads(text);p.goto(a.url,wait_until='networkidle');p.set_input_files('#project-file',{'name':'saved-long-group.json','mimeType':'application/json','buffer':text.encode()});expect(p.locator('#toast')).to_contain_text('복원 실패')
    save({'id':'E07','scenario':'two groups and 200 participants per arm with 201-character group name save successfully but fail restore','finding_reproduced':'복원 실패' in p.locator('#toast').inner_text(),'max_segment_length':max(len(c['segment']) for c in saved['cells']),'saved_cells':len(saved['cells']),'scope':'within count and group-number support bounds; input parser declares no segment name length error','timing_controlled':False});p.close()
    browser.close()
assert all(x['url'].endswith('/api/explain') for x in posts)
print('AUDIT_COMPLETED',len(results),'cases; POST was intercepted, no actual LLM calls',flush=True)
