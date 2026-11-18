"""Exercise the shared operating contract and printable companion forms."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,re,csv,hashlib
import markdown,pymupdf
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v09';REV=ROOT/'e-book/design/v09/review';REV.mkdir(parents=True,exist_ok=True)
text=(OUT/'ebook_review_v09.md').read_text(encoding='utf-8');record=(OUT/'tri_v_decision_record_v09.md').read_text(encoding='utf-8')
rows=json.loads((ROOT/'e-book/manuscript/tri_v_case_records_v09.json').read_text(encoding='utf-8'))['cases']
assert [r['id'] for r in rows]==list(range(1,7))
for r in rows:assert text.count(r['paragraph'])==1
for term in ['비교 명세','적용 범위 문장','결정문','최소 경로','심화 경로','변경 전 값과 변경 후 값','결과 열람 여부','확인 기한']:
 assert term in text,term
for term in ['실험 전 공통 기준','결과 후 세 축','변경 전','변경 후','결과 열람 여부','승인 역할','기한','복구']:
 assert term in record,term
with (OUT/'tri_v_criteria_change_log_v09.csv').open(encoding='utf-8-sig',newline='') as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;changes=list(reader)
assert changes==[]
for f in ['value_before','value_after','result_seen_at_proposal','reason','approver_role','new_data_confirmation_plan']:assert f in fields
style='''@font-face{font-family:ReaderSans;src:url("assets/reader-sans.woff2");font-weight:100 900}*{box-sizing:border-box}body{font:16px/1.65 ReaderSans,sans-serif;color:#142D32;background:white;max-width:950px;margin:auto;padding:30px}h1{font-size:28px}h2{font-size:23px;margin-top:28px}h3{font-size:19px}table{border-collapse:collapse;width:100%;font-size:16px}th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #9CAEA6}th{background:#F2F5F1}p,li{overflow-wrap:anywhere}h1,h2,h3{break-after:avoid}tr{break-inside:avoid}@page{size:A4;margin:17mm}@media print{body{max-width:none;margin:0;padding:0;font-size:12pt;line-height:1.6}h1{font-size:22pt}h2{font-size:17pt}h3{font-size:13pt}table{font-size:12pt}th,td{padding:2mm}p{orphans:3;widows:3}}'''
(OUT/'tri_v_decision_record_v09.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>TRI-V 결정 기록</title><style>'+style+'</style><main>'+markdown.markdown(record,extensions=['tables'])+'</main></html>',encoding='utf-8')
outputs={};errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 for stem in ['tri_v_operating_card_v09','tri_v_decision_record_v09']:
  page=browser.new_page(viewport={'width':1200,'height':900});page.on('pageerror',lambda e:errors.append(str(e)));page.goto((OUT/f'{stem}.html').as_uri());page.evaluate('document.fonts.ready')
  assert page.evaluate('document.fonts.check("16px ReaderSans")')
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  page.screenshot(path=str(REV/f'{stem}.png'),full_page=True)
  page.emulate_media(media='print');page.pdf(path=str(OUT/f'{stem}.pdf'),print_background=True,prefer_css_page_size=True)
  with pymupdf.open(OUT/f'{stem}.pdf') as d:
   texts='\n'.join(pg.get_text() for pg in d);outside=[];sizes=[]
   for idx,pg in enumerate(d):
    for word in pg.get_text('words'):
     if word[0]<-.5 or word[1]<-.5 or word[2]>pg.rect.width+.5 or word[3]>pg.rect.height+.5:outside.append([idx+1,word[4]])
    sizes.extend(s['size'] for b in pg.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans'] if s['text'].strip())
   assert not outside,outside
   assert min(sizes)>=11.9,(stem,min(sizes))
   assert not any(c in texts for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
   if stem=='tri_v_operating_card_v09':assert len(d)==1,('Operating card must fit one page',len(d))
   outputs[stem]={'pages':len(d),'min_text_pt':min(sizes),'outside_words':outside,'sha256':hashlib.sha256((OUT/f'{stem}.pdf').read_bytes()).hexdigest()}
  page.close()
 page=browser.new_page(viewport={'width':1200,'height':950});page.goto((OUT/'ebook_review_v09.html').as_uri());page.evaluate('document.fonts.ready')
 svg_overflow=page.evaluate('''[...document.querySelectorAll('.reading svg text')].filter(t=>{const b=t.getBoundingClientRect(),v=t.ownerSVGElement.getBoundingClientRect();return b.left<v.left-1||b.top<v.top-1||b.right>v.right+1||b.bottom>v.bottom+1}).map(t=>t.textContent)''')
 assert not svg_overflow,svg_overflow
 page.locator('#tri-v-operating-contract').scroll_into_view_if_needed();page.screenshot(path=str(REV/'operating_contract_desktop.png'))
 browser.close()
assert not errors,errors
with pymupdf.open(OUT/'ebook_review_v09.pdf') as d:
 hits=[entry[2] for entry in d.get_toc() if entry[1]=='TRI-V 공통 운용 기준'];assert len(hits)==1
 d[hits[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(REV/'operating_contract_print.png')
 for term in ['최소 경로','변경 전 값과 변경 후 값']:assert any(term in pg.get_text() for pg in d),term
report={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'operating_contract_page':hits[0],'book_three_repairs_present':True,'case_record_mappings':[{k:r[k] for k in ['id','record_status','route']} for r in rows],'mapping_scope':'Editorial integration checks, not an automated statistical or adoption classifier','companion_outputs':outputs,'criterion_change_rows':len(changes),'svg_text_overflow':svg_overflow,'browser_errors':errors,'real_reader_results_created':False,'name_finalized':False}
(OUT/'operations_validation_v09.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
