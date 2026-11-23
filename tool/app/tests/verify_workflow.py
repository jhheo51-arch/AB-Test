"""Synthetic v0.5 feature UI checks; no actual model requests."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--url',required=True);u=a.parse_args().url;checks=[]
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n,flush=True)
def fresh(b):
 p=b.new_page(viewport={'width':1440,'height':1100},accept_downloads=True);p.goto(u,wait_until='networkidle');return p
def prepare(p):p.click('#prepare');p.wait_for_selector('#analysis-options:not([hidden])')
def analyze(p,confirmed=True):
 if confirmed:
  for k in ['randomized','independent','mature','fixed-stop']:p.check('#'+k)
 p.check('#confirm-input');p.click('#analyze');p.wait_for_selector('#results-view:not([hidden])')
def mapped(p,raw):
 p.fill('#data-text',raw);p.click('#prepare');p.wait_for_selector('#mapping-panel:not([hidden])')
def apply(p):p.check('#mapping-confirm');p.click('#apply-mapping')
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);errs=[]
 p=fresh(b);p.on('pageerror',lambda e:errs.append(str(e)));raw='variant,converted,participants,cohort,PRIVATE_UNUSED\nA,50,500,new,PRIVATE_VALUE_A\nB,75,500,new,PRIVATE_VALUE_B';mapped(p,raw)
 check('custom headers propose mapping but do not analyze',not p.locator('#mapping-confirm').is_checked() and p.locator('#analysis-options').is_hidden())
 p.click('#apply-mapping');check('unconfirmed mapping cannot be applied',p.locator('#analysis-options').is_hidden())
 apply(p);p.wait_for_selector('#analysis-options:not([hidden])');check('confirmed mapping preserves counts and raw input',p.evaluate("state.prepared.cells[0].success===50&&state.prepared.cells[1].success===75") and p.locator('#data-text').input_value()==raw)
 p.select_option('#map-success','participants');check('editing mapping revokes prior prepared input',p.evaluate('state.prepared===null') and not p.locator('#mapping-confirm').is_checked());apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('duplicate source columns rejected',p.locator('#analysis-options').is_hidden());p.select_option('#map-success','converted');apply(p);p.wait_for_selector('#analysis-options:not([hidden])');analyze(p)
 check('result excludes ignored raw column and values','PRIVATE_' not in p.locator('#results-view').inner_text())
 p.click('nav [data-view=share]');p.select_option('#decision-direction','defer');p.fill('#decision','SYNTHETIC_REASON');p.fill('#decision-checks','SYNTHETIC_CHECKS');p.fill('#revisit','SYNTHETIC_REVISIT')
 check('guided judgment appears in share preview',all(s in p.locator('#report-preview').inner_text() for s in ['판단 유보','SYNTHETIC_REASON','SYNTHETIC_CHECKS','SYNTHETIC_REVISIT']))
 p.check('#share-confirm');p.evaluate('window.print=()=>{}');p.click('#print-report');p.fill('#decision-checks','SYNTHETIC_NEW_CHECKS');check('judgment checks edit revokes approval and print DOM',not p.locator('#share-confirm').is_checked() and p.locator('#print-area').inner_text()=='')
 with p.expect_download() as d:p.click('#save-project')
 saved=Path(d.value.path()).read_text(encoding='utf-8');obj=json.loads(saved);check('v5 stores judgment but no original headers/rows',obj['version']==5 and obj['judgment']=={'direction':'defer','checks':'SYNTHETIC_NEW_CHECKS'} and 'PRIVATE_' not in saved and 'variant' not in saved)
 p.check('#share-confirm')
 with p.expect_download() as d:p.click('#export-report')
 html=Path(d.value.path()).read_text(encoding='utf-8');check('HTML includes judgment and expanded calculation, no raw data','SYNTHETIC_NEW_CHECKS' in html and 'PRIVATE_' not in html and '<script' not in html and 'calc-details' in html)
 ev=R/'workflow_evidence';ev.mkdir(exist_ok=True);p.emulate_media(media='print');p.pdf(path=str(ev/'GUIDED_JUDGMENT.pdf'),format='A4',print_background=True);p.emulate_media(media='screen')
 check('new judgment is excluded from LLM payload','SYNTHETIC_' not in p.evaluate('JSON.stringify(explanationFacts())'))
 p.goto(u,wait_until='networkidle');p.set_input_files('#project-file',{'name':'saved.json','mimeType':'application/json','buffer':saved.encode()});expect(p.locator('#decision-direction')).to_have_value('defer');check('v5 restores judgment and canonical aggregates',p.locator('#decision-checks').input_value()=='SYNTHETIC_NEW_CHECKS' and 'PRIVATE_' not in p.locator('#data-text').input_value());prepare(p);analyze(p);p.click('nav [data-view=share]');check('restored judgment survives reanalysis','SYNTHETIC_NEW_CHECKS' in p.locator('#report-preview').inner_text());p.close()
 p=fresh(b);mapped(p,'variant,converted,participants\ncontrol,1,10\ntreatment,2,10');apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);p.wait_for_selector('#analysis-options:not([hidden])');check('explicit arm values map control/treatment without changing counts',p.evaluate("state.prepared.cells[0].arm==='A'&&state.prepared.cells[1].arm==='B'&&state.prepared.cells[1].success===2"));p.close()
 p=fresh(b);mapped(p,'variant,converted,participants\nA,1,10\nB,2,10\nC,3,10');apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('unknown arm is rejected, no rows silently dropped',p.evaluate('state.prepared===null'));p.close()
 p=fresh(b);p.select_option('#format','individual');mapped(p,'id,variant,result,observed\ns1,A,1,0\ns2,B,0,1');p.select_option('#map-subject_id','id');p.select_option('#map-outcome','result');p.select_option('#map-observed','');apply(p);expect(p.locator('#mapping-error')).not_to_be_empty();check('known observed column cannot be dropped',p.locator('#analysis-options').is_hidden());p.select_option('#map-observed','observed');apply(p);expect(p.locator('#issues')).not_to_be_empty();check('mapped immature observation remains blocked',p.locator('#analysis-options').is_hidden() and 'IMMATURE_OBSERVATION' in p.locator('#issues').inner_text());p.close()
 p=fresh(b);p.fill('#data-text','arm,success,total\ncontrol,1,10\ntreatment,2,10');p.click('#open-mapping');p.wait_for_selector('#mapping-panel:not([hidden])');p.fill('#arm-value-a','control');p.fill('#arm-value-b','treatment');apply(p);p.wait_for_selector('#analysis-options:not([hidden])');check('canonical headers also permit explicit arm conversion',p.evaluate("state.prepared.cells[1].success===2"));p.fill('#arm-value-b','new_label');check('arm label edit discards prior prepared counts',p.evaluate('state.prepared===null') and not p.locator('#mapping-confirm').is_checked());p.fill('#data-text','arm,success,total\nA,1,10\nB,2,10');check('raw input replacement discards old mapping panel',p.locator('#mapping-panel').is_hidden());p.close()
 p=fresh(b);p.set_input_files('#csv-file',{'name':'SYNTHETIC_CUSTOM.csv','mimeType':'text/csv','buffer':raw.encode()});expect(p.locator('#source-badge')).to_contain_text('사용자 CSV');p.click('#prepare');p.wait_for_selector('#mapping-panel:not([hidden])');apply(p);p.wait_for_selector('#analysis-options:not([hidden])');check('actual uploaded file supports confirmed custom mapping',p.evaluate("state.prepared.cells[0].success===50&&state.prepared.cells[1].success===75"));p.close()
 p=fresh(b);mapped(p,'variant,converted,participants,<img src=x onerror=window.BAD=1>\nA,1,10,unused\nB,2,10,unused');check('untrusted source header is escaped in mapping UI',p.locator('#mapping-panel img').count()==0 and p.evaluate('window.BAD===undefined'));p.close()
 for name,a1,b1,confirmed,title in [('A',80,20,True,'A 우세 근거'),('B',20,80,True,'B 우세 근거'),('hold',1,1,True,'승패 보류'),('unconfirmed',80,20,False,'판정 미실행')]:
  p=fresh(b);p.fill('#data-text',f'arm,success,total\nA,{a1},100\nB,{b1},100');prepare(p);analyze(p,confirmed);check(name+' result state uses engine verdict',p.locator('#result-title').inner_text()==title);check(name+' cards neutral and summary first',p.evaluate("(()=>{const c=[...document.querySelectorAll('#overall-results .rate-grid>div')];return getComputedStyle(c[0]).backgroundColor===getComputedStyle(c[1]).backgroundColor&&document.querySelector('#result-summary').getBoundingClientRect().top<document.querySelector('#overall-results').getBoundingClientRect().top})()"));check(name+' details are progressive disclosure',not p.locator('#overall-results .calc-details').evaluate('e=>e.open') and not p.locator('.context-panel').evaluate('e=>e.open'))
  if name=='A':
   p.click('nav [data-view=share]');p.select_option('#decision-direction','review_b');check('contrary direction gets warning not automatic approval','달라요' in p.locator('#judgment-guide').inner_text())
  if name=='B':
   p.screenshot(path=str(ev/'result_desktop.png'),full_page=True);p.set_viewport_size({'width':390,'height':844});check('390px summary has no page overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.screenshot(path=str(ev/'result_mobile.png'),full_page=True)
  p.close()
 check('no page JavaScript errors in primary mapping flow',not errs);b.close()
(R/'workflow_verification.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'scope':'synthetic browser tasks; no actual LLM calls'},ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',len(checks),'workflow checks passed')
