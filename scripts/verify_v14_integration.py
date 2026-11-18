"""Verify scoped study integration, preserved inputs, and final PDF coverage."""
from pathlib import Path
from collections import Counter
from bisect import bisect_right
import json,re,hashlib,math
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v14';REVIEW=ROOT/'e-book/design/v14/review';REVIEW.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def compact(s):return re.sub(r'\s+','',s)
checks=[]
def check(label,ok):checks.append({'check':label,'pass':bool(ok)});assert ok,label
old=(ROOT/'e-book/exports/v13/ebook_review_v13.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v14.md').read_text(encoding='utf-8');changes=load('e-book/exports/v14/MANUSCRIPT_CHANGES.json');replay=old
for r in changes['changes']:
 check('Unique registered replacement '+r['before'][:45],replay.count(r['before'])==r['occurrences']);replay=replay.replace(r['before'],r['after'])
check('Only registered study and reproduction-reference changes',replay==new)
for p,h in load('e-book/manuscript/study_integration_v14/BASELINE.json')['hashes'].items():check('Frozen input '+p,sha(p)==h)
for p in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json']:
 check('Exact v13 companion preserved '+p,sha('e-book/exports/v14/'+p)==sha('e-book/exports/v13/'+p))
check('Twelve chapter titles unchanged',re.findall(r'^# \d+장 .+',new,re.M)==re.findall(r'^# \d+장 .+',old,re.M))
check('No new paragraph headings',re.findall(r'^## .+',new,re.M)==re.findall(r'^## .+',old,re.M))
check('No forbidden separators',not any(c in new for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
for term in ['Variable Control','Vector Segmentation','Value-Linked Decision','관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며','51.7%','59.9%']:check('Author method and corrected boundary '+term,term in new)
concept=load('e-book/analysis/study_integration_v14/CONCEPT_CHECKS.json')['independent_true_null_tests'];check('Analytic toy probability recomputed',math.isclose(concept['probability_at_least_one'],1-(1-concept['alpha'])**concept['trials'],abs_tol=1e-14));check('Toy display matches manuscript',f"{concept['display_percent']:.1f}%" in new)
coverage=load('e-book/review/study_integration_v14/PASTE_V13_CONCEPT_MAP.json');counts=dict(Counter(r['status'] for r in coverage['concepts']));check('All selected concepts distinct',len({r['id'] for r in coverage['concepts']})==16)
with pymupdf.open(OUT/'ebook_review_v14.pdf') as pdf:
 texts=[]
 for index,page in enumerate(pdf,1):
  lines=page.get_text().splitlines()
  if lines and lines[-1].strip()==str(index):lines=lines[:-1]
  texts.append(compact('\n'.join(lines)))
 joined=''.join(texts);starts=[];end=0
 for text in texts:starts.append(end);end+=len(text)
 def pages_for(phrase):
  q=compact(phrase);pages=[];pos=joined.find(q)
  while pos>=0:
   pages.extend(range(bisect_right(starts,pos),bisect_right(starts,pos+len(q)-1)+1));pos=joined.find(q,pos+1)
  return sorted(set(pages))
 additions=[]
 for p in changes['adopted_paragraphs']:
  found=pages_for(p['text']);check('Full adopted paragraph in final PDF '+p['id'],bool(found));additions.append({**p,'pdf_pages':found});pdf[found[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/(p['id']+'.png'))
 mapped=[]
 for row in coverage['concepts']:
  pages=pages_for(row['evidence']);check('Existing concept evidence remains '+row['id'],bool(pages));mapped.append({**row,'v13_pdf_pages':row['pdf_pages'],'v14_existing_evidence_pages':pages,'v14_added_pages':sorted({page for p in additions if row['id'] in p['concept_ids'] for page in p['pdf_pages']}),'disposition':'보완 반영' if row['status']=='부분적으로 있었음' else '기존 설명 유지'})
 check('No isolated final glossary entry',sum(level==2 and page==len(pdf) for level,name,page in pdf.get_toc())>=2)
 for phrase in ['관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며','51.7%','59.9%']:check('Final PDF retained '+phrase,bool(pages_for(phrase)))
 chapter_pages={}
 for key,title in {'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','scope':'11장 TRI-V의 기여와 적용 범위','chapter6':'6장 고객 수보다 필요한 정보량부터','chapter12':'12장 한 건의 캠페인을 설계에서 결정까지'}.items():
  hits=[p for _,name,p in pdf.get_toc() if name==title];assert len(hits)==1;chapter_pages[key]=hits[0]
 report={'chapter_pages':chapter_pages,'status':'passed','edition':'v0.14 scoped study-note integration','full_book_pages':len(pdf),'checks_passed':len(checks),'checks':checks,'coverage_counts_before':counts,'concept_count':len(mapped),'paragraphs_added':len(additions),'source_v13_preserved':True,'original_statistics_unchanged':True,'notion_direct_body_read':False,'human_review_approved':False,'actual_reader_test_conducted':False,'new_sequential_engine_implemented':False,'additions':additions}
(OUT/'integration_validation_v14.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'COVERAGE_AFTER.json').write_text(json.dumps({'counts_before':counts,'items':mapped,'scope':'Supplied pasted passage, Notion login blocked; chapter numbering of Georgiev not verified'},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','additions']},ensure_ascii=False,indent=2));print(json.dumps([{'id':p['id'],'pages':p['pdf_pages']} for p in additions],ensure_ascii=False))
