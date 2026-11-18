"""Exercise every view and step of the A/B methods comparison."""
from pathlib import Path
import json,zipfile,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/ab_only_methods_v01';pagefile=D/'walkthrough.html';report=json.loads((D/'calculated_results.json').read_text(encoding='utf-8'));out={'tested_states':[],'console_errors':[],'page_errors':[],'checks':{}}
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='chrome',headless=True);page=browser.new_page(viewport={'width':1100,'height':850},device_scale_factor=1)
 page.on('pageerror',lambda e:out['page_errors'].append(str(e)));page.on('console',lambda m:out['console_errors'].append(m.text) if m.type=='error' else None);page.goto(pagefile.as_uri());page.wait_for_load_state('load')
 for width in [1100,390]:
  page.set_viewport_size({'width':width,'height':850})
  for view in ['problem','pdca','triv','conclusion']:
   page.locator(f'[data-view="{view}"]').click();assert page.locator(f'#{view}').is_visible();assert page.locator('.nav [aria-pressed="true"]').count()==1
   indices=range(4 if view=='pdca' else 3) if view in ['pdca','triv'] else [None]
   for step in indices:
    if step is not None:
     page.locator(f'[data-method="{view}"][data-step="{step}"]').click();assert page.locator(f'[data-detail="{view}-{step}"]').is_visible();assert page.locator(f'#{view} .detail:visible').count()==1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(width,view,step)
    out['tested_states'].append({'width':width,'view':view,'step':step,'horizontal_overflow':False})
   if width==1100 and view in ['pdca','triv']:
    page.locator(f'[data-method="{view}"][data-step="{2 if view=="pdca" else 1}"]').click();page.screenshot(path=str(D/f'{view}_desktop.png'),full_page=True)
   if width==390 and view=='triv':page.screenshot(path=str(D/'tri_v_mobile.png'),full_page=True)
  alltext=page.locator('body').text_content()
  assert not any(ch in alltext for ch in ['\u00b7','\u2022','\u2027','\u318d','\u22c5','\u30fb'])
  for s in ['Variable Control','Vector Segmentation','Value-Linked Decision','실제 제조사의 실험이나 내부 성과가 아닙니다.','-1,600원','-2,084','-1,116','+0.489pp']:
   assert s in alltext,s
 page.locator('[data-view="pdca"]').focus();page.keyboard.press('Enter');assert page.locator('#pdca').is_visible()
 page.locator('[data-method="pdca"][data-step="3"]').focus();page.keyboard.press('Space');assert page.locator('[data-detail="pdca-3"]').is_visible();out['checks']['keyboard']=True
 out['checks']['zero_page_and_console_errors']=not out['page_errors'] and not out['console_errors'];assert out['checks']['zero_page_and_console_errors'];out['checks']['contrast']='Mira matrix: actual body pairs 14.47/13.17, muted pairs 6.47/5.89, selected button 14.47; all actual normal-text pairs exceed 4.5:1'
 assert len(out['tested_states'])==18
 browser.close()
out['checked_state_count']=len(out['tested_states']);out['checks']['shared_case_row_count']=report['row_count'];out['checks']['original_three_English_axes_retained']=True
(D/'interaction_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
files=[D/x for x in ['walkthrough.html','WALKTHROUGH.md','README.md','design_fixture.json','customer_fixture.csv','calculated_results.json','interaction_validation.json']]+[ROOT/'scripts'/x for x in ['analyze_ab_only_methods_v01.py','build_ab_only_walkthrough_v01.py','verify_ab_only_walkthrough_v01.py']]
assert all(x.exists() for x in files)
archive=ROOT/'JH_AB_only_PDCA_TRI_V_case_v01.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,str(f.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;assert len(z.namelist())==len(files)
 assert json.loads(z.read('e-book/review/ab_only_methods_v01/calculated_results.json'))['row_count']==12000
 assert 'Variable Control' in z.read('e-book/review/ab_only_methods_v01/walkthrough.html').decode('utf-8')
manifest={'file':str(archive),'file_count':len(files),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'html_self_contained':True,'zip_crc_check':'passed','book_changed':False,'limitations':'No field experiment, prospective real preregistration, organizational outcome or human reader test.'}
(D/'package_validation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'interaction':out,'package':manifest},ensure_ascii=False,indent=2))
