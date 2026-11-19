"""Verify page-review coverage, semantic preservation, navigation and v17 layout."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v17';REV=R/'e-book/review/page_personas_v17'
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def compact(s):return re.sub(r'\s+','',s)
checks=[]
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
old=(R/'e-book/exports/v16/ebook_review_v16.md').read_text(encoding='utf-8');new=(O/'ebook_review_v17.md').read_text(encoding='utf-8')
for p,h in load('e-book/manuscript/editorial_v17/BASELINE.json')['hashes'].items():check('Frozen '+p,hashlib.sha256((R/p).read_bytes()).hexdigest()==h)
a=old.split('# 부록 사례와 자료를 찾아가는 길')[0];b=new.split('# 찾아보기')[0]
a=a.replace('실제 발송 효과나 이번 org 재실행의 증거는 아니다.','실제 발송 효과를 입증하거나 이번 책 작업에서 Salesforce 환경을 다시 검증했다는 뜻은 아니다.')
for fix in load('e-book/manuscript/editorial_v17/PROSE_FIXES.json'):a=a.replace(fix['before'],fix['after'])
a=a.replace('_v16.svg','_v17.svg')
b=re.sub(r'<a id="[gb]-[^"]+"></a>\s*','',b);b=re.sub(r'\[사례 자료 길잡이\]\([^\n]+\)\s*','',b)
paras=lambda s:Counter(p.strip() for p in s.split('\n\n') if p.strip())
check('Registered repeated-advice compression; other narrative paragraphs and quantitative explanations retained',paras(a)==paras(b))
lookup=load('e-book/exports/v17/LOOKUP.json');terms=lookup['terms'];check('36 unique glossary terms',len(terms)==len({t['id'] for t in terms})==36)
olddefs={m[1]:m[3].strip() for m in re.finditer(r'<a id="(g-[^"]+)"></a>\s*\n## ([^\n]+)\n\n(.*?)(?=\n<a id="g-|\Z)',old.split('# 키워드 찾아보기와 설명')[1],re.S)}
for t in terms:check('Exact definition '+t['id'],olddefs[t['id']]==t['definition'])
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.md','MINIMUM_RECORD.html','analysis_report_v13.json','COUNTEREXAMPLE_RESULTS.json','PLANNING_EXAMPLE.json','REGRESSION_CHECK.json']:
 check('Preserved numerical companion '+name,(O/name).read_bytes()==(R/'e-book/exports/v16'/name).read_bytes())
v=load('e-book/exports/v17/validation_v17.json');geom=load('e-book/exports/v17/visual_geometry_v17.json');check('Thirteen centered figures without text collisions or panel overflow',len(geom['figures'])==13 and not geom['issues']);check('Printed labels remain at least12pt within tolerance',all(f['minimum_label_pt']>=11.9 for f in v['figure_layout']))
for t in terms:
 check('Actual glossary destination '+t['id'],t['id'] in v['lookup_pages'])
 if t['body_id']:check('Actual representative body destination '+t['id'],t['body_id'] in v['lookup_pages'])
back=v['backmatter_pages'];check('Tail section order',list(back.values())==sorted(back.values()))
for n in v['footnotes']:check('Correct caller and note number '+str(n['number']),n['page']==n['callerPage'] and n['marker_content'].strip('"')==str(n['number'])+'. ' and n['caller_content'].strip('"')==str(n['number']))
units=v['atomic_layout_units'];worked=[u for u in units if 'worked-record' in u['cls']];check('Complete one-page worked decision',len(worked)==1)
check('Three whole capacity-policy groups',sum('policy-table' in u['cls'] for u in units)==3)
for u in {u['unit'] for u in units}:check('Intact table/code/report unit '+u,len({r['page'] for r in units if r['unit']==u})==1)
# The plotting coordinates change, not the frozen displayed estimates and intervals.
for f in load('e-book/exports/v17/GRAPH_LAYOUT_V17.json'):
 root=ET.fromstring((O/f['file']).read_text(encoding='utf-8'));dots=[e for e in root.iter() if e.tag.endswith('circle')]
 for d,s in zip(dots,f['series']):
  low,high=f['domain_pp'];value=low+(float(d.get('cx'))-435)/415*(high-low);check('Frozen vector estimate '+f['file']+' '+s['label'],math.isclose(value,s['point_pp_from_vector'],abs_tol=1e-10))
rows=[]
for filename in ['batch_001_028.json','batch_029_056.json','batch_057_083.json']:rows.extend(json.loads((REV/filename).read_text(encoding='utf-8')))
check('Every v16 page reviewed exactly once',len(rows)==83 and Counter(r['page'] for r in rows)==Counter(range(1,84)))
with pymupdf.open(R/'e-book/exports/v16/ebook_review_v16.pdf') as d:
 oldtexts=[p.get_text() for p in d]
 for row in rows:
  quotes=row['evidence'] if isinstance(row['evidence'],list) else [row['evidence']]
  for quote in quotes:check('Actual v16 page evidence '+str(row['page']),compact(quote) in compact(oldtexts[row['page']-1]))
repairs={1:['COVER_DIFFERENCE'],2:['LOOKUP_AND_TAIL'],3:['LOOKUP_AND_TAIL'],5:['NOTE_WORDING'],6:['FIGURE_ALIGNMENT'],7:['FIGURE_ALIGNMENT'],9:['WORKFLOW_REDRAW'],10:['INTACT_TABLES'],11:['INTACT_TABLES'],18:['TWO_COLUMN_VALUES'],19:['TWO_COLUMN_VALUES'],20:['TWO_COLUMN_VALUES'],21:['DIRECTION_AND_SCOPE'],22:['WORKFLOW_REDRAW'],24:['DESIGN_BOUNDARY'],25:['DESIGN_BOUNDARY'],27:['INTACT_TABLES','WORKFLOW_REDRAW'],28:['INTACT_TABLES'],33:['TWO_COLUMN_VALUES','DIRECTION_AND_SCOPE'],36:['TWO_COLUMN_VALUES'],39:['TWO_COLUMN_VALUES','DIRECTION_AND_SCOPE'],42:['CAPACITY_PROTECTION'],43:['POLICY_GROUPS'],44:['POLICY_GROUPS'],46:['EXACT_SIX_FIELDS'],58:['NOTE_NUMBER_IDENTITY'],59:['NOTE_NUMBER_IDENTITY'],61:['FIGURE_ALIGNMENT'],63:['LOOKUP_AND_TAIL'],64:['INTACT_CODE'],68:['ONE_PAGE_DECISION'],69:['ONE_PAGE_DECISION']}
for page in range(70,84):repairs[page]=['LOOKUP_AND_TAIL','INTACT_CODE_AND_SOURCES']
for row in rows:
 row['applied_repairs']=repairs.get(row['page'],['PRESERVE_PROSE_AND_RECHECK_FLOW'])
 row['disposition']='부분 반영' if '소제목' in row['concrete_fix'] else ('반영' if row['page'] in repairs else '설명 유지 및 재조판 확인')
 row['decision_reason']='문단마다 소제목이나 경고 상자를 늘리는 제안은 기존 저자 문체 방침에 따라 그대로 채택하지 않았다. 필요한 탐색, 표, 도형 및 실제 오류를 우선 수정했다.' if '소제목' in row['concrete_fix'] else '기존 설명과 수치를 보존하고 실제 탐색 및 조판 문제를 수정했다. 모든 모의 제안이 관측된 사용성 문제라는 뜻은 아니다.'
(REV/'PAGE_REVIEW_DISPOSITIONS.json').write_text(json.dumps({'scope':'v16 physical83 pages, persona-based simulated editorial review, not interviews','source_pdf_sha256':hashlib.sha256((R/'e-book/exports/v16/ebook_review_v16.pdf').read_bytes()).hexdigest(),'pages':rows},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
# Map source review to the final pagination; final visual contact sheets are inspected separately.
def grams(s):
 s=compact(s);return {s[i:i+8] for i in range(max(0,len(s)-7))}
oldgrams=[grams(s) for s in oldtexts]
with pymupdf.open(O/'ebook_review_v17.pdf') as d:
 check('Final PDF hash',hashlib.sha256((O/'ebook_review_v17.pdf').read_bytes()).hexdigest()==v['pdf_sha256']);final=[]
 for i,page in enumerate(d,1):
  text=page.get_text();g=grams(text);scores=[len(g&a)/max(1,min(len(g),len(a))) for a in oldgrams];best=max(range(83),key=lambda n:scores[n]);sourcepages=[j+1 for j in sorted(range(83),key=lambda n:scores[n],reverse=True)[:4] if scores[j]>=.12] or [best+1]
  r=rows[best];final.append({'page':i,'primary_persona':r['primary_persona'],'secondary_persona':r['secondary_persona'],'source_v16_pages':sourcepages,'reader_task':r['reader_task'],'actual_final_excerpt':re.sub(r'^\d+\s*','',text.strip())[:100],'review_scope':'Source-persona findings mapped by text overlap, plus final PDF layout and navigation checks; not a new reader experiment','applied_repairs':sorted({a for n in sourcepages for a in rows[n-1]['applied_repairs']}),'page_bounds':'passed'})
  for link in page.get_links():
   if link['kind']==pymupdf.LINK_GOTO:assert 0<=link['page']<len(d)
 check('Every final page has mapped persona recheck',len(final)==v['pdf_pages'])
 finaltext=''.join(p.get_text() for p in d);check('No forbidden separators',not any(c in finaltext for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
(REV/'FINAL_PAGE_RECHECK.json').write_text(json.dumps({'scope':'Final-page mapping and technical/visual recheck, not independently observed reader performance','pages':final},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
lines=['# 쪽별 모의 편집 평가와 보완','',f'v16의83쪽 모두에 주독자와 보조독자를 배정해 평가했다. 최종본은{v["pdf_pages"]}쪽이며 원문 겹침으로 평가 위치를 연결하고 재조판을 확인했다. 실제 독자시험이나 인터뷰가 아니며 예상 영향을 관측 성과로 제시하지 않는다.','', '문단마다 소제목을 늘리거나 새로운 표로 모든 설명을 쪼개는 제안은 그대로 채택하지 않았다. 연속 서술을 유지하면서 탐색과 실제 조판 오류를 우선 수정했다.','', '| v16쪽 | 주독자 | 관찰과 제안 | 처리 | 반영한 보완 |','|---:|---|---|---|---|']
for row in rows:lines.append('| '+str(row['page'])+' | '+row['primary_persona']+' | '+row['observation'].replace('|','/').replace('\n',' ')+' | '+row['disposition']+' | '+', '.join(row['applied_repairs'])+' |')
lines+=['','## 최종본 쪽별 연결','','| 최종쪽 | 주독자 | 대조한 v16쪽 | 실제 쪽의 시작 문구 |','|---:|---|---|---|']
for row in final:lines.append('| '+str(row['page'])+' | '+row['primary_persona']+' | '+', '.join(map(str,row['source_v16_pages']))+' | '+row['actual_final_excerpt'].replace('|','/').replace('\n',' ')+' |')
(REV/'PAGE_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
report={'status':'passed','version':'v0.17','checks_passed':len(checks),'checks':checks,'reviewed_source_pages':83,'final_pages':v['pdf_pages'],'glossary_entries':36,'print_aliases':len(lookup['aliases']),'representative_body_links':sum(bool(t['body_id']) for t in terms),'worked_decision_page':worked[0]['page'],'backmatter_pages':back,'old_inputs_preserved':True,'numeric_recalculation_scope':'Existing103 text checks and read-only SQL; frozen estimate/interval graphics preserved; not a fresh full statistical review','actual_reader_test':False,'human_approved':False}
(O/'integration_validation_v17.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
