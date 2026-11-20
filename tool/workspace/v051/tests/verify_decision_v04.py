"""v0.4 context/reason regression using synthetic data. No actual LLM call here."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--url',required=True);args=a.parse_args();checks=[];requests=[];errors=[]
def check(name,condition):
    assert condition,name
    checks.append({'name':name,'pass':True});print('PASS',name,flush=True)
def analyze(p):
    p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])');p.locator('.context-panel > summary').click() if not p.locator('.context-panel').evaluate('e=>e.open') else None
def fresh(p):p.goto(args.url,wait_until='networkidle')
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    p=b.new_page(viewport={'width':1440,'height':1060},accept_downloads=True)
    p.on('request',lambda r:requests.append({'method':r.method,'url':r.url,'body':r.post_data}));p.on('pageerror',lambda e:errors.append(str(e)))
    fresh(p);p.click('#example-aggregate')
    metadata={'policy-a':'A: 가치 안내_POLICY_A','policy-b':'B: 예약 안내_POLICY_B','audience':'SYNTHETIC_AUDIENCE 배정 대상','metric':'SYNTHETIC_SUCCESS 시승 완료','window':'SYNTHETIC_WINDOW 관측 완료','purpose':'SYNTHETIC_PURPOSE 고객군 차이 확인'}
    for key,value in metadata.items():p.fill('#'+key,value)
    p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');analyze(p)
    context=p.locator('#experiment-context').inner_text()
    check('all context fields appear in result',all(v in context for v in metadata.values()))
    check('policy names tied to actual A and B rate cards',metadata['policy-a'] in p.locator('#overall-results .rate-grid>div').nth(0).inner_text() and metadata['policy-b'] in p.locator('#overall-results .rate-grid>div').nth(1).inner_text())
    check('overall hold has specific local explanation',p.locator('#overall-results [data-reason=HOLD]').count()==1)
    check('segment Holm hold differs from ordinary hold',p.locator('#segment-results [data-reason=HOLM_HOLD]').count()==1)
    check('direct difference is not inferred from one significant group',p.locator('#segment-results [data-reason=INTERACTION_HOLD]').count()==1)
    p.click('.result-heading>button[data-view=share]')
    body=p.locator('#report-preview').inner_text();check('all context fields transfer to default report',all(v in body for v in metadata.values()))
    check('excluded group explanation absent from actual report DOM',p.locator('#report-preview [data-reason=HOLM_HOLD]').count()==0 and p.locator('#report-preview [data-reason=INTERACTION_HOLD]').count()==0)
    p.check('#share-confirm')
    with p.expect_download() as d:p.click('#export-report')
    html=Path(d.value.path()).read_text(encoding='utf-8')
    check('downloaded HTML has policy audience and embedded reason style',all(v in html for v in metadata.values()) and '.decision-reason' in html)
    p.evaluate('window.print=()=>{}');p.click('#print-report');p.emulate_media(media='print');p.pdf(path=str(ROOT/'screenshots/V04_CONTEXT_REPORT.pdf'),format='A4',print_background=True);p.emulate_media(media='screen')
    p.check('#share-groups');check('explicit group inclusion adds group and direct explanations',p.locator('#report-preview [data-reason=HOLM_HOLD]').count()==1 and p.locator('#report-preview [data-reason=INTERACTION_HOLD]').count()==1)
    with p.expect_download() as d:p.click('#save-project')
    saved=json.loads(Path(d.value.path()).read_text(encoding='utf-8'));check('v5 project preserves audience',saved['version']==5 and saved['plan']['audience']==metadata['audience'])
    fresh(p);p.set_input_files('#project-file',{'name':'saved-v5.json','mimeType':'application/json','buffer':json.dumps(saved).encode()});expect(p.locator('#audience')).to_have_value(metadata['audience']);p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');analyze(p)
    check('v5 restore reanalysis preserves policy and audience',all(v in p.locator('#experiment-context').inner_text() for v in metadata.values()))
    p.click('nav [data-view=input]');p.fill('#audience','SYNTHETIC_CHANGED_AUDIENCE');check('audience edits invalidate previous result',p.locator('nav [data-view=results]').is_disabled());analyze(p)
    check('reanalyzed context no longer shows stale audience','SYNTHETIC_CHANGED_AUDIENCE' in p.locator('#experiment-context').inner_text() and metadata['audience'] not in p.locator('#experiment-context').inner_text())
    p.route('**/api/explain',lambda route:route.fulfill(status=503,content_type='application/json',body='{"error":"SIMULATED_TEST_FAILURE","message":"test failure"}'))
    p.check('#llm-consent');p.click('#explain');expect(p.locator('#llm-status')).to_have_text('호출·검증 실패')
    posts=[json.loads(r['body']) for r in requests if r['method']=='POST']
    check('new metadata and local explanation never enter model payload',len(posts)==1 and not any(v in json.dumps(posts,ensure_ascii=False) for v in [*metadata.values(),'SYNTHETIC_CHANGED_AUDIENCE','policyA','audience']))
    p.unroute('**/api/explain')
    p.click('nav [data-view=input]');p.fill('#policy-a','<img src=x onerror=window.__unsafe=1>');analyze(p);p.click('.result-heading>button[data-view=share]')
    check('policy text remains escaped in result and report',p.locator('#experiment-context img,#overall-results img,#report-preview img').count()==0 and p.evaluate('window.__unsafe===undefined'))
    legacy=json.loads(json.dumps(saved));legacy['version']=2;legacy['plan'].pop('audience');fresh(p);p.set_input_files('#project-file',{'name':'legacy-v2.json','mimeType':'application/json','buffer':json.dumps(legacy).encode()});expect(p.locator('#policy-a')).to_have_value(metadata['policy-a']);check('legacy v2 restores with empty audience not guessed',p.locator('#audience').input_value()=='')
    p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])');analyze(p);check('missing audience is explicitly recorded','대상 미기록' in p.locator('#experiment-context').inner_text())
    p.set_viewport_size({'width':390,'height':844});check('context and reasons fit 390px',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no page JavaScript errors',not errors);b.close()
result={'status':'PASS','count':len(checks),'checks':checks,'javascript_errors':errors,'llm_failure':'explicit simulated failure, not an actual model outcome','no_actual_llm_call':True,'scope':'synthetic regression; context PDF text checked separately'}
(ROOT/'DECISION_VERIFICATION_v04.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULT',len(checks),'v04 checks passed',flush=True)
