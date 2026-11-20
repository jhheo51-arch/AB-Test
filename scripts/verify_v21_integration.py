"""Verify the authorized v21 edits against the frozen reader and its final PDF."""
from pathlib import Path
from collections import Counter
import json,re,hashlib
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v21';D=R/'e-book/manuscript/development_v21';checks=[]
def ok(name,condition,detail=None):
 assert condition,(name,detail);checks.append({'name':name,'status':'passed','detail':detail})
baseline=json.loads((D/'BASELINE.json').read_text(encoding='utf-8'))
for p,h in baseline['hashes'].items():ok('baseline '+p,hashlib.sha256((R/p).read_bytes()).hexdigest()==h)
s=(R/'e-book/exports/v20/ebook_review_v20.md').read_text(encoding='utf-8');out=(O/'ebook_review_v21.md').read_text(encoding='utf-8');original=s.split('# 찾아보기')[0];expected=original
for e in json.loads((D/'EDITORIAL_EDITS.json').read_text(encoding='utf-8')):
 ok('unique source '+e['id'],expected.count(e['before'])==1);expected=expected.replace(e['before'],e['after'])
def normalize(t):
 t=re.sub(r'<a id="b-[^"]+"></a>','',t);t=re.sub(r'\[사례 자료 길잡이\]\([^\n]+\)','',t);t=re.sub(r'(<span class="folio"[^>]*>)\d+(</span>)',r'\g<1>00\2',t);return re.sub(r'\s+','',t.replace('_v21.svg','_v20.svg'))
ok('exact editorial replay apart from regenerated navigation',normalize(expected)==normalize(out.split('# 찾아보기')[0]))
nums=lambda t:Counter(re.findall(r'\d+(?:[,.]\d+)*',t))
ok('only question markers removed, no changed numerical values',nums(original)-nums(expected)==Counter({'1':1,'2':1,'3':1}) and not nums(expected)-nums(original))
ok('fenced code unchanged',re.findall(r'```.*?```',original,re.S)==re.findall(r'```.*?```',expected,re.S))
for chapter in [6]:
 old=re.search(r'# '+str(chapter)+r'장 .*?(?=# '+str(chapter+1)+r'장 )',original,re.S)[0];new=re.search(r'# '+str(chapter)+r'장 .*?(?=# '+str(chapter+1)+r'장 )',expected,re.S)[0]
 tables=lambda t:Counter(re.findall(r'(?m)^\|[^\n]*\n(?:\|[^\n]*(?:\n|$))+',t))
 ok('chapter6 table content preserved across reordering',tables(old)==tables(new))
start='**완성된 한 장 결정문 예시**';record=s.split(start,1)[1].split('# 찾아보기',1)[0];newrecord=out.split(start,1)[1].split('# 찾아보기',1)[0];ok('decision wording unchanged',record==newrecord)
ok('footnote identities unchanged',Counter(re.findall('data-note-id="(fn-\\d+)"',s))==Counter(re.findall('data-note-id="(fn-\\d+)"',out)))
v=json.loads((O/'validation_v21.json').read_text(encoding='utf-8'));ok('final PDF hash',hashlib.sha256((O/'ebook_review_v21.pdf').read_bytes()).hexdigest()==v['pdf_sha256']);ok('eight same-page footnotes',v['footnote_count']==8 and v['footnotes_on_caller_page']);ok('all figure print labels >=12pt',all(f['minimum_label_pt']>=11.9 for f in v['figure_layout']))
units=[u for u in v['atomic_layout_units'] if 'worked-record' in u['cls']];ok('complete decision stays one face on physical page 79',len(units)==1 and units[0]['page']==79,units)
compact=lambda x:re.sub(r'\s+','',x)
with pymupdf.open(O/'ebook_review_v21.pdf') as pdf:
 page=compact(pdf[78].get_text());ok('unchanged decision paragraphs physically on page79',all(compact(p) in page for p in record.strip().split('\n\n')))
 pdf[78].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(R/'e-book/design/v21/decision_page_079.png')
ok('six-axis terms retained',all(t in out for t in ['Variable Control','Vector Segmentation','Value-Linked Decision']))
ui=json.loads((R/'e-book/design/v21/ui_validation_v21.json').read_text(encoding='utf-8'));ok('UI exercised against final edition, not fixture',ui['status']=='passed' and not ui['fixture_only']);ok('no new statistical inference',json.loads((O/'MANUSCRIPT_CHANGES.json').read_text(encoding='utf-8'))['numerical_inference_changed'] is False)
ok('numeric text and read-only SQL results exist',all((O/n).exists() for n in ['numeric_text_validation_v21.json','chapter12_sql_validation_v21.json']))
report={'status':'passed','check_count':len(checks),'checks':checks,'pdf_pages':v['pdf_pages'],'decision_page':79,'new_statistical_inference':False,'actual_reader_test':False,'human_approval':False}
(O/'integration_validation_v21.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
