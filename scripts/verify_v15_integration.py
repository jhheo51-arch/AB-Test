"""Verify the developed v15 design exercises and unchanged historical analysis."""
from pathlib import Path
from bisect import bisect_right
import json,re,hashlib,math
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v15';REVIEW=ROOT/'e-book/design/v15/review';REVIEW.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def compact(s):return re.sub(r'\s+','',s)
checks=[]
def check(name,value):checks.append({'check':name,'pass':bool(value)});assert value,name
old=(ROOT/'e-book/exports/v14/ebook_review_v14.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v15.md').read_text(encoding='utf-8');record=load('e-book/exports/v15/MANUSCRIPT_CHANGES.json');replay=old
for change in record['changes']:
 check('Unique registered change '+change['before'][:40],replay.count(change['before'])==change['occurrences']);replay=replay.replace(change['before'],change['after'])
check('Only registered design and reproduction development',replay==new)
for p,h in load('e-book/manuscript/development_v15/BASELINE.json')['hashes'].items():check('Frozen '+p,sha(p)==h)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','counterexample_fixture.json','REGRESSION_CHECK.json','PROVENANCE.json']:
 check('Byte-identical companion '+name,sha('e-book/exports/v15/'+name)==sha('e-book/exports/v14/'+name))
def chapter(s,n):
 m=re.search(r'^# '+str(n)+r'장[^\n]*\n.*?(?=^# |\Z)',s,re.M|re.S);assert m;return m[0]
for n in [1,3,4,5,7,8,10,11,12]:check('Unedited chapter '+str(n),chapter(new,n)==chapter(old,n))
check('Chapter and case headings unchanged',re.findall(r'^#{1,2} .+',old,re.M)==re.findall(r'^#{1,2} .+',new,re.M))
check('Forbidden middle dots absent',not any(c in new for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
plan=load('e-book/analysis/development_v15/PLANNING_EXAMPLE.json');p=plan['available_plan'];n=plan['assumptions']['available_n_total'];check('New illustration is explicitly hypothetical','별도 교육용 조건' in new);check('New illustration is not the old A/B/H design','앞의 A/B/H 실험을 다시 해석하거나' in new)
for value in [f"{p['power_display_percent']:.1f}%",f"{p['required_n_each']:,}",f"{p['required_n_total']:,}",f"{p['additional_eligible_customers']:,}",f"{p['mde_display_pp']:.2f}pp"]:check('Planning display '+value,value in new)
check('Power has separate calculation agreement',math.isclose(p['power_direct'],p['power_library'],abs_tol=1e-12));check('MDE has separate calculation agreement',math.isclose(p['mde_at_available_n'],p['mde_library'],abs_tol=1e-12));check('Budget deficit reconciles',p['required_n_total']-n==p['additional_eligible_customers'])
toy=load('e-book/exports/v15/CONCEPT_CHECKS.json')['independent_true_null_tests'];check('Prior toy probability still correct',math.isclose(toy['probability_at_least_one'],1-(1-toy['alpha'])**toy['trials'],abs_tol=1e-14))
for phrase in ['관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며','목표 80%','보호 기준과 필요한 수를 별도로','Variable Control','Vector Segmentation','Value-Linked Decision']:check('Preserved safeguard '+phrase,phrase in new)
with pymupdf.open(OUT/'ebook_review_v15.pdf') as pdf:
 texts=[]
 for i,page in enumerate(pdf,1):
  lines=page.get_text().splitlines()
  if lines and lines[-1].strip()==str(i):lines.pop()
  texts.append(compact('\n'.join(lines)))
 starts=[];end=0
 for text in texts:starts.append(end);end+=len(text)
 joined=''.join(texts)
 def find_pages(q):
  q=compact(q);pos=joined.find(q);assert pos>=0,q[:100];return list(range(bisect_right(starts,pos),bisect_right(starts,pos+len(q)-1)+1))
 developed=[]
 for d in record['developments']:
  pages=[]
  for part in d['text'].split('\n\n'):
   if part.startswith('|'):
    for line in part.splitlines():
     if re.fullmatch(r'[| :\-]+',line):continue
     for cell in line.strip('|').split('|'):
      if cell.strip():pages+=find_pages(cell.strip());check('PDF table cell '+d['id']+' '+cell.strip()[:20],True)
   else:pages+=find_pages(part);check('PDF complete paragraph '+d['id'],True)
  developed.append({**d,'pdf_pages':sorted(set(pages))});pdf[min(pages)-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/(d['id']+'.png'))
 for term in [f"{p['power_display_percent']:.1f}%",f"{p['mde_display_pp']:.2f}pp",'관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며']:check('Final PDF value and guard '+term,bool(find_pages(term)))
 check('No stranded last glossary entry',sum(level==2 and page==len(pdf) for level,name,page in pdf.get_toc())>=2)
 pages={}
 for key,title in {'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','scope':'11장 TRI-V의 기여와 적용 범위','chapter6':'6장 고객 수보다 필요한 정보량부터','chapter12':'12장 한 건의 캠페인을 설계에서 결정까지'}.items():
  hits=[p for _,name,p in pdf.get_toc() if name==title];assert len(hits)==1;pages[key]=hits[0]
 report={'status':'passed','edition':'v0.15 developed design decisions','full_book_pages':len(pdf),'chapter_pages':pages,'checks_passed':len(checks),'checks':checks,'developments':developed,'source_v14_preserved':True,'historical_statistics_unchanged':True,'new_planning_illustration_only':True,'human_review_approved':False,'actual_reader_test_conducted':False,'new_sequential_engine_implemented':False}
(OUT/'integration_validation_v15.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','developments']},ensure_ascii=False,indent=2));print(json.dumps([{'id':d['id'],'pages':d['pdf_pages']} for d in developed],ensure_ascii=False))
