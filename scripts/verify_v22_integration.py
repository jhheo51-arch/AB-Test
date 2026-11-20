"""Verify the five minimal text fixes and worksheet print repair, not new content."""
from pathlib import Path
from collections import Counter
import json,hashlib,re
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v22';D=R/'e-book/manuscript/development_v22';V=R/'e-book/design/v22';checks=[]
def ok(name,value):assert value,name;checks.append({'name':name,'status':'passed'})
for n,h in json.loads((D/'BASELINE.json').read_text(encoding='utf-8'))['hashes'].items():ok('preserved '+n,hashlib.sha256((R/n).read_bytes()).hexdigest()==h)
s=(R/'e-book/exports/v21/ebook_review_v21.md').read_text(encoding='utf-8');expected=s
for e in json.loads((D/'PROOF_CORRECTIONS.json').read_text(encoding='utf-8')):
 ok('single source '+e['id'],expected.count(e['before'])==1);expected=expected.replace(e['before'],e['after'])
out=(O/'ebook_review_v22.md').read_text(encoding='utf-8')
def norm(t):
 t=re.sub(r'<a id="b-[^"]+"></a>','',t);t=re.sub(r'(<span class="folio"[^>]*>)\d+(</span>)',r'\g<1>00\2',t);return re.sub(r'\s+','',t.replace('v22','v21').replace('v0.22','v0.21'))
ok('entire manuscript matches only approved five corrections and regenerated navigation',norm(expected)==norm(out))
start='**완성된 한 장 결정문 예시**';record=s.split(start,1)[1].split('# 찾아보기',1)[0];ok('decision words unchanged',record==out.split(start,1)[1].split('# 찾아보기',1)[0])
for e in json.loads((D/'PROOF_CORRECTIONS.json').read_text(encoding='utf-8')):ok('corrected text present '+e['id'],e['after'] in out)
v=json.loads((O/'validation_v22.json').read_text(encoding='utf-8'));ok('97 pages',v['pdf_pages']==97);ok('PDF bytes match rendered validation',hashlib.sha256((O/'ebook_review_v22.pdf').read_bytes()).hexdigest()==v['pdf_sha256']);ok('decision atomic on page79',[u['page'] for u in v['atomic_layout_units'] if 'worked-record' in u['cls']]==[79]);ok('eight same-page footnotes',v['footnote_count']==8 and v['footnotes_on_caller_page']);ok('all 13 figure labels >=12pt',len(v['figure_layout'])==13 and all(f['minimum_label_pt']>=11.9 for f in v['figure_layout']))
compact=lambda t:re.sub(r'\s+','',t)
with pymupdf.open(O/'ebook_review_v22.pdf') as d:
 ok('record physically complete on79',all(compact(p) in compact(d[78].get_text()) for p in record.strip().split('\n\n')));d[78].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1)).save(V/'decision_page_079.png')
 # Only corrected passages, not an all-citation audit.
 for e in json.loads((D/'PROOF_CORRECTIONS.json').read_text(encoding='utf-8')):ok('corrected passage in final PDF '+e['id'],any(compact(e['after']) in compact(p.get_text()) for p in d))
for n in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']:ok('quantitative figure bytes preserved '+n,(O/n).read_bytes()==(R/'e-book/exports/v21'/n).read_bytes())
for name,path in [('UI',V/'ui_validation_v22.json'),('printing',V/'print_validation_v22.json')]:ok(name+' executed',json.loads(path.read_text(encoding='utf-8'))['status']=='passed')
ok('numeric and read-only SQL results exist',all((O/n).exists() for n in ['numeric_text_validation_v22.json','chapter12_sql_validation_v22.json']))
report={'status':'passed','check_count':len(checks),'checks':checks,'pdf_pages':v['pdf_pages'],'decision_page':79,'statistical_results_changed':False,'actual_reader_test':False,'human_approval':False};(O/'integration_validation_v22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
