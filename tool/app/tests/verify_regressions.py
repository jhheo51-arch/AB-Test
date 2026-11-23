"""Regression for W01-W04. Real APIs are delayed, not replaced with fake data/hash."""
from pathlib import Path
import argparse,json,time
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser();p.add_argument('--url',required=True);a=p.parse_args();ROOT=Path(__file__).resolve().parents[1];out=ROOT/'fix-evidence';out.mkdir(exist_ok=True);checks=[]
def check(name,ok):
    assert ok,name
    checks.append({'name':name,'pass':True});print('PASS',name,flush=True)
def wait(p,expr):
    until=time.monotonic()+15
    while time.monotonic()<until:
        if p.evaluate(expr):return
        p.wait_for_timeout(30)
    raise AssertionError(expr)
def open_page(b,init=None):
    p=b.new_page(viewport={'width':1440,'height':1060},accept_downloads=True)
    if init:p.add_init_script(init)
    p.goto(a.url,wait_until='networkidle');return p
def analyze(p):p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])')
def sample(p):p.click('#example-aggregate');p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');analyze(p)
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=open_page(b);sample(p);p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_OLD_PRINT_AUDIENCE');analyze(p);p.click('.result-heading>button[data-view=share]');p.check('#share-confirm');p.evaluate('window.print=()=>{}');p.click('#print-report');check('approved report prepares current print snapshot','SYNTHETIC_OLD_PRINT_AUDIENCE' in p.locator('#print-area').text_content())
    p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_NEW_UNAPPROVED_AUDIENCE');check('W02 input invalidation discards old print DOM',p.locator('#print-area').text_content()=='');p.emulate_media(media='print');p.pdf(path=str(out/'native_print_after_invalidation.pdf'),format='A4',print_background=True);p.emulate_media(media='screen');check('afterprint clears temporary print DOM',p.locator('#print-area').text_content()=='')
    analyze(p);p.click('.result-heading>button[data-view=share]');p.check('#share-confirm');p.click('#print-report');p.fill('#decision','SYNTHETIC_NEW_DECISION');check('decision change revokes print approval and DOM',not p.locator('#share-confirm').is_checked() and p.locator('#print-area').text_content()=='');p.check('#share-confirm');p.click('#print-report');p.check('#share-groups');check('group share change revokes print snapshot',p.locator('#print-area').text_content()=='' and p.locator('#print-report').is_disabled());p.check('#share-confirm');p.click('#print-report');p.emulate_media(media='print');p.pdf(path=str(out/'native_print_current_approved.pdf'),format='A4',print_background=True);p.close()
    init="const digest=crypto.subtle.digest.bind(crypto.subtle);window.auditDigestReleases=[];crypto.subtle.digest=(...args)=>digest(...args).then(hash=>new Promise(resolve=>{window.auditDigestReleases.push(()=>resolve(hash))}));"
    p=open_page(b,init);p.fill('#data-text','arm,success,total\nA,1,10\nB,2,10');p.click('#prepare');wait(p,'window.auditDigestReleases.length===1');p.fill('#data-text','arm,success,total\nA,10,100\nB,30,100');check('W03 editing during real hash allows retry',not p.locator('#prepare').is_disabled());p.click('#prepare');wait(p,'window.auditDigestReleases.length===2');p.evaluate('window.auditDigestReleases[0]()');p.wait_for_timeout(60);check('old hash finally cannot unlock newer job',p.locator('#prepare').is_disabled());p.evaluate('window.auditDigestReleases[1]()');p.wait_for_selector('#analysis-options:not([hidden])');check('new hash resolves with latest counts',p.evaluate("state.prepared.cells.find(c=>c.arm==='B').success===30") and not p.locator('#prepare').is_disabled());p.close()
    init="const read=Blob.prototype.arrayBuffer;Blob.prototype.arrayBuffer=function(...args){const slow=['AUDIT_SLOW.csv','AUDIT_SLOW.json'].includes(this.name);return read.apply(this,args).then(bytes=>slow?new Promise(resolve=>window.releaseAuditFile=()=>resolve(bytes)):bytes)};"
    p=open_page(b,init);slow='arm,success,total\nA,1,10\nB,2,10';latest='arm,success,total\nA,40,100\nB,50,100';p.set_input_files('#csv-file',{'name':'AUDIT_SLOW.csv','mimeType':'text/csv','buffer':slow.encode()});wait(p,"typeof window.releaseAuditFile==='function'");check('pending file immediately blocks analysis/save',p.locator('#analyze').is_disabled() and p.locator('#save-project').is_disabled());p.fill('#data-text',latest);p.evaluate('window.releaseAuditFile()');p.wait_for_timeout(100);check('W01 older file cannot overwrite latest typed table',p.locator('#data-text').input_value()==latest and '사용자 표' in p.locator('#source-badge').inner_text() and p.locator('#csv-file').input_value()=='');p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');check('latest typed table remains analyzable',p.evaluate("state.prepared.cells.find(c=>c.arm==='B').success===50"));p.close()
    p=open_page(b,init);p.set_input_files('#csv-file',{'name':'AUDIT_SLOW.csv','mimeType':'text/csv','buffer':slow.encode()});wait(p,"typeof window.releaseAuditFile==='function'");p.set_input_files('#csv-file',{'name':'NEWER.csv','mimeType':'text/csv','buffer':latest.encode()});expect(p.locator('#source-badge')).to_contain_text('사용자 CSV');p.evaluate('window.releaseAuditFile()');p.wait_for_timeout(100);check('newer file wins over earlier pending file',p.locator('#data-text').input_value()==latest);p.close()
    p=open_page(b,init);p.set_input_files('#csv-file',{'name':'AUDIT_SLOW.csv','mimeType':'text/csv','buffer':slow.encode()});wait(p,"typeof window.releaseAuditFile==='function'");p.select_option('#format','individual');p.evaluate('window.releaseAuditFile()');p.wait_for_timeout(60);check('format change cancels pending earlier file',p.locator('#format').input_value()=='individual' and p.locator('#data-text').input_value()=='');p.close()
    project={'format':'ab-local-project','version':3,'source_kind':'synthetic','synthetic':True,'source_digest':None,'plan':{'randomized':True,'independent':True,'mature':True,'fixedStop':True,'includeSegments':False,'segmentPrespecified':False,'alpha':.05,'purpose':'NEW_PROJECT_PURPOSE','metric':'success','window':'complete','policyA':'NEW_PROJECT_A','policyB':'NEW_PROJECT_B','audience':'NEW_PROJECT_AUDIENCE'},'cells':[{'arm':'A','segment':None,'success':70,'total':100},{'arm':'B','segment':None,'success':80,'total':100}],'decision':'','revisit':''}
    p=open_page(b,init);p.set_input_files('#project-file',{'name':'AUDIT_SLOW.json','mimeType':'application/json','buffer':json.dumps(project).encode()});wait(p,"typeof window.releaseAuditFile==='function'");p.fill('#data-text',latest);p.evaluate('window.releaseAuditFile()');p.wait_for_timeout(60);check('pending older restore cannot overwrite newer typed table',p.locator('#data-text').input_value()==latest and p.locator('#purpose').input_value()=='');p.close()
    p=open_page(b,init);p.set_input_files('#csv-file',{'name':'AUDIT_SLOW.csv','mimeType':'text/csv','buffer':slow.encode()});wait(p,"typeof window.releaseAuditFile==='function'");p.set_input_files('#project-file',{'name':'NEW_PROJECT.json','mimeType':'application/json','buffer':json.dumps(project).encode()});expect(p.locator('#audience')).to_have_value('NEW_PROJECT_AUDIENCE');restored=p.locator('#data-text').input_value();p.evaluate('window.releaseAuditFile()');p.wait_for_timeout(60);check('newer restore wins over earlier pending file',p.locator('#data-text').input_value()==restored and '70' in restored and '집계 복원' in p.locator('#source-badge').inner_text() and p.locator('#audience').input_value()=='NEW_PROJECT_AUDIENCE');p.close()
    groups='arm,success,total,segment\n'+'\n'.join(arm+','+str(1 if arm=='A' else 2)+',10,g'+str(i) for i in range(7) for arm in ['A','B'])
    long='X'*201;long_csv='arm,success,total,segment\nA,10,100,'+long+'\nB,20,100,'+long+'\nA,10,100,Y\nB,20,100,Y'
    for name,csv,unsupported in [('long_group',long_csv,False),('fourteen_cells',groups,True),('above_inference_cap','arm,success,total\nA,100,200001\nB,110,200001',True)]:
        p=open_page(b);p.fill('#data-text',csv);p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');expected=p.evaluate('state.prepared.cells')
        with p.expect_download() as d:p.click('#save-project')
        text=Path(d.value.path()).read_text(encoding='utf-8');p.goto(a.url,wait_until='networkidle');p.set_input_files('#project-file',{'name':name+'.json','mimeType':'application/json','buffer':text.encode()});expect(p.locator('#source-badge')).to_contain_text('집계 복원');p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');check('W04 '+name+' saved/restored counts preserved',p.evaluate('state.prepared.cells')==expected)
        for key in ['randomized','independent','mature','fixed-stop']:p.check('#'+key)
        if name!='above_inference_cap':p.check('#segment-prespecified')
        analyze(p)
        if unsupported:check(name+' restore does not relax inference gates',p.evaluate('state.result.inference_allowed===false && state.result.overall.p_raw===null'))
        p.close()
    p=open_page(b);sample(p);before=p.locator('#overall-results').inner_text();p.set_input_files('#project-file',{'name':'invalid.json','mimeType':'application/json','buffer':b'{invalid'});expect(p.locator('#toast')).to_contain_text('복원 실패');check('malformed restore preserves valid current result',p.locator('#overall-results').inner_text()==before and p.locator('#results-view').is_visible());p.close()
    p=b.new_page();hits=[]
    def worker_route(route):
        hits.append(route.request.url)
        if len(hits)==1:route.abort('failed')
        else:route.continue_()
    p.route('**/worker.js',worker_route);p.goto(a.url,wait_until='networkidle');p.fill('#data-text',latest);p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');check('worker load error permits a fresh successful retry',len(hits)>=2 and p.evaluate("state.prepared.cells.find(c=>c.arm==='B').success===50"));p.close();b.close()
result={'status':'PASS','count':len(checks),'checks':checks,'scope':'synthetic controlled timing; actual hashes/files; no model calls','original_audit':'AB_Test_Workspace_v04_Audit/AUDIT_REVIEW.md','pdf_proof':'validated separately with actual PDF extraction'}
(ROOT/'regression_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',len(checks),'fix regression checks passed',flush=True)
