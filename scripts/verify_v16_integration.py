"""Close the v16 visual edit with frozen-source, chart and actual-footnote checks."""
from pathlib import Path
import re,json,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v16'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
checks=[]
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
old=(ROOT/'e-book/exports/v15/ebook_review_v15.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v16.md').read_text(encoding='utf-8');replay=old
for ch in load('e-book/exports/v16/MANUSCRIPT_CHANGES.json')['changes']:
 check('Registered change '+ch['before'][:50],replay.count(ch['before'])==ch['occurrences']);replay=replay.replace(ch['before'],ch['after'])
check('Only registered visual/source-call changes',replay==new)
for p,h in load('e-book/manuscript/visual_v16/BASELINE.json')['hashes'].items():check('Frozen '+p,sha(p)==h)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','PLANNING_EXAMPLE.json','REGRESSION_CHECK.json','counterexample_fixture.json']:
 check('Exact numerical/record companion '+name,sha('e-book/exports/v16/'+name)==sha('e-book/exports/v15/'+name))
check('No new prose microheadings',re.findall(r'^## .+',old,re.M)==re.findall(r'^## .+',new,re.M))
check('All chapter titles preserved',re.findall(r'^# \d+장 .+',old,re.M)==re.findall(r'^# \d+장 .+',new,re.M))
audit=load('e-book/review/visual_numeric_v16/AUDIT.json');check('Separate-code bounded numeric audit passes',not audit['failed'] and audit['passed']==audit['total_checks'])
figs=load('e-book/exports/v16/FIGURE_DATA.json');core=load('e-book/analysis/winner_v04/core_results.json');check('Five quantitative chart sources',figs['chart_count']==5)
for name,p in figs['frozen_source_hashes'].items():check('Chart ledger hash '+name,sha(name)==p)
for chart in figs['charts']:
 name=chart['file'];r=ET.fromstring((OUT/name).read_text(encoding='utf-8'))
 if name in ['winner_effect.svg','guardrail_effect.svg']:
  a=chart['source'];ref=next(x for x in audit['primary'] if x['comparison']=='B-A') if name=='winner_effect.svg' else audit['guardrail']
  for key in ['diff_pp','ci_low_pp','ci_high_pp']:check('Chart vs fresh audit '+name+' '+key,math.isclose(a[key],ref[key],abs_tol=1e-10))
  lo,hi=chart['axis_domain_pp'];x=lambda v:85+(v-lo)/(hi-lo)*540
  points=[e for e in r.iter() if e.tag.endswith('circle')];check('Point position '+name,len(points)==1 and math.isclose(float(points[0].get('cx')),x(a['diff_pp']),abs_tol=1e-8))
  intervals=[e for e in r.iter() if e.tag.endswith('line') and e.get('stroke-width')=='7'];check('CI endpoints '+name,len(intervals)==1 and math.isclose(float(intervals[0].get('x1')),x(a['ci_low_pp']),abs_tol=1e-8) and math.isclose(float(intervals[0].get('x2')),x(a['ci_high_pp']),abs_tol=1e-8))
 if name=='guardrail_effect.svg':
  ticks=chart['axis_ticks_pp'];check('Unambiguous guardrail ticks',all(math.isclose(ticks[i+1]-ticks[i],.1,abs_tol=1e-12) for i in range(len(ticks)-1)))
 if name=='capacity_v06.svg':
  labels=' '.join(''.join(e.itertext()) for e in r.iter() if e.tag.endswith('text'))
  for row in chart['source_rows']:
   check('Capacity value '+row['policy'],f"{row['completed']:,}건" in labels and f"{row['net_value_krw']/10000:,.1f}만원" in labels)
v=load('e-book/exports/v16/validation_v16.json');check('Four conceptual diagrams inserted',len(v['new_concept_figures'])==4);check('Actual labels at least12pt within tolerance',all(f['minimum_label_pt']>=11.9 for f in v['figure_layout']));check('Footnotes all on caller page',v['footnote_count']==8 and all(n['page']==n['callerPage'] and n['y']>=n['body']*.75-1 for n in v['footnotes']))
check('Three restrained emphasis spans',new.count('<u class="reader-emphasis">')==3)
before=load('e-book/design/v16/WHITESPACE_BEFORE.json');after=load('e-book/design/v16/WHITESPACE_AFTER.json');check('Median bottom leftover reduced',after['median_remaining_bottom_mm']<before['median_remaining_bottom_mm']);check('High-percentile bottom leftover reduced',after['p90_remaining_bottom_mm']<before['p90_remaining_bottom_mm']);check('Fewer pages with30mm bottom leftovers',len(after['pages_with_at_least_30mm_unused'])<len(before['pages_with_at_least_30mm_unused']))
with pymupdf.open(OUT/'ebook_review_v16.pdf') as d:
 check('Exact final PDF hash',sha('e-book/exports/v16/ebook_review_v16.pdf')==v['pdf_sha256']);text=''.join(re.sub(r'\s+','',p.get_text()) for p in d)
 for phrase in ['관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며','Variable Control','Vector Segmentation','Value-Linked Decision','51.7%','59.9%','67.4%','1.17pp']:check('Final PDF retained '+phrase,re.sub(r'\s+','',phrase) in text)
 check('No forbidden separator',not any(c in text for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
 for page in d:
  for link in page.get_links():
   if link['kind']==pymupdf.LINK_GOTO:assert 0<=link['page']<len(d)
 check('All PDF internal links valid',True)
 check('At least two entries on final glossary page',sum(level==2 and page==len(d) for level,name,page in d.get_toc())>=2)
 headings=d.get_toc();pages={}
 for key,title in {'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','scope':'11장 TRI-V의 기여와 적용 범위','chapter6':'6장 고객 수보다 필요한 정보량부터','chapter12':'12장 한 건의 캠페인을 설계에서 결정까지'}.items():
  hits=[p for _,name,p in headings if name==title];check('Exact PDF destination '+key,len(hits)==1);pages[key]=hits[0]
 report={'status':'passed','edition':'v0.16 visual publication review','full_book_pages':len(d),'chapter_pages':pages,'checks_passed':len(checks),'checks':checks,'source_v15_preserved':True,'historical_statistics_unchanged':True,'new_concept_figures':v['new_concept_figures'],'footnote_count':v['footnote_count'],'bounded_numeric_audit_checks':audit['total_checks'],'numeric_audit_not_full_book':True,'cover_proposal':'A','cover_approved':False,'human_review_approved':False,'real_reader_test_conducted':False,'whitespace_before':{k:before[k] for k in ['median_remaining_bottom_mm','p90_remaining_bottom_mm','pages_with_at_least_30mm_unused']},'whitespace_after':{k:after[k] for k in ['median_remaining_bottom_mm','p90_remaining_bottom_mm','pages_with_at_least_30mm_unused']}}
(OUT/'integration_validation_v16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','new_concept_figures']},ensure_ascii=False,indent=2))
