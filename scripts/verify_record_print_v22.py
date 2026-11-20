"""Regression-test actual long-input print rendering and restoration."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import pymupdf,json,re
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v22';V=R/'e-book/design/v22';T=Path('C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch');cases=[]
compact=lambda s:re.sub(r'\s+','',s)
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);q=b.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
 for name,counts in [('same_failure_case',[12]*6),('single_field_spans_pages',[140,2,2,2,2,2]),('blank',[0]*6)]:
  q.goto((O/'MINIMUM_RECORD.html').as_uri());expected=[]
  for i,n in enumerate(counts,1):
   lines=[f'R{i}-LINE-{j:04d} 검수용 문장입니다.' for j in range(1,n+1)]+([f'END-R{i}'] if n else []);value='\n'.join(lines);q.locator('#r'+str(i)).fill(value);expected+=lines
  values=q.locator('.field textarea').evaluate_all('(es)=>es.map(e=>e.value)');q.pdf(path=str(T/(name+'_v22.pdf')),format='A4',print_background=True,prefer_css_page_size=True)
  assert q.locator('.record-print-value').count()==0;assert q.locator('.record-print-source').count()==0;assert q.locator('.field textarea').evaluate_all('(es)=>es.map(e=>e.value)')==values
  with pymupdf.open(T/(name+'_v22.pdf')) as d:
   text=compact('\n'.join(pg.get_text() for pg in d));missing=[line for line in expected if compact(line) not in text];assert not missing,missing;pages=len(d)
   if name=='blank':assert pages==1,pages
   else:assert pages>1;d[0].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1)).save(V/(name+'_print.png'))
  if expected:
   with q.expect_download() as info:q.locator('#record-export').click()
   exported=compact(Path(info.value.path()).read_text(encoding='utf-8-sig'));assert all(compact(line) in exported for line in expected)
  cases.append({'case':name,'pages':pages,'expected_lines':len(expected),'missing_lines':missing,'input_restored':True,'print_dom_removed':True})
 b.close()
assert not errors,errors
report={'status':'passed','cases':cases,'browser_errors':errors,'test_data_only':True};(V/'print_validation_v22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
