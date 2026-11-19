"""Validate editorial citations against the exact source editions and PDFs."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,re,hashlib
import pymupdf
R=Path(__file__).resolve().parents[1];D=R/'e-book/review/editorial_quality_v18'
compact=lambda s:re.sub(r'\s+','',s)
review=json.loads((D/'WHOLE_BOOK_QUALITY_BASELINE.json').read_text(encoding='utf-8'))
def evidence(obj):
 if isinstance(obj,dict):
  if 'quote' in obj:yield obj
  for value in obj.values():yield from evidence(value)
 elif isinstance(obj,list):
  for value in obj:yield from evidence(value)
with pymupdf.open(R/'e-book/exports/v17/ebook_review_v17.pdf') as doc:oldpdf=[p.get_text() for p in doc]
oldlines=(R/'e-book/exports/v17/ebook_review_v17.md').read_text(encoding='utf-8').splitlines();checked=[]
for e in evidence(review):
 assert compact(e['quote']) in compact('\n'.join(oldlines[n-1] for n in e['markdown_lines'])),e
 assert compact(e['quote']) in compact(''.join(oldpdf[n-1] for n in e['pdf_pages'])),e
 checked.append(e)
assert len(review['chapter_coverage'])==12 and {r['chapter'] for r in review['chapter_coverage']}==set(range(1,13))
new=(R/'e-book/exports/v18/ebook_review_v18.md').read_text(encoding='utf-8');newlines=new.splitlines()
quotes={
'learning_route':'직접 계산하거나 평가 설계를 정하기 어려운 부분은 분석 담당자에게 확인할 질문으로 남긴다.',
'sampling_not_external_validity':'그렇다면 이번에 얻은 +0.93pp는 배정이 달라져도 비슷했을까.',
'p_value_definition':'효과가 없다는 귀무가설과 분석 가정 아래에서, 관측한 검정통계량만큼 또는 그보다 더 극단적인 값을 얻을 확률이다.',
'design_revision_task':'해설을 읽기 전에 비교할 고객의 분모, 주지표, 확대 판단 시점을 각각 한 문장으로 다시 써 보자.',
'reuse_task':'재사용할 수 있는 근거와 다시 확인할 조건을 각각 한 문장으로 적어 보자.',
'questions_first':'이 장의 자료를 읽으며 다음 질문에 먼저 답해 보자.',
'answers_later':'장 앞에서 적은 답을 다음 해설과 대조해 보자.',
'withdrawal_point_not_proven_harm':'완료 증가와 철회 증가의 점추정을 한 방향의 성과로 묶을 수 없다는 점이 드러난다.',
'no_universal_sample_growth':'표본 확대가 필요한지는 목표 정밀도에 따라 판단한다.',
'review_not_approval':'실제로 조건을 확인하기 전에는 재검토 요청일 뿐 실행 승인이 아니다.',
'case4_action':'TRI-V의 정화, Variable Control에서 먼저 할 일은 승자 판정을 멈추고 기록 경로를 확인하는 것이다.'}
with pymupdf.open(R/'e-book/exports/v18/ebook_review_v18.pdf') as doc:
 pages=[p.get_text() for p in doc];final=[];toc=doc.get_toc()
 for key,quote in quotes.items():
  assert new.count(quote)==1,(key,'source match')
  hits=[[i+1] for i,p in enumerate(pages) if compact(quote) in compact(p)]
  if not hits:hits=[[i+1,i+2] for i in range(len(pages)-1) if compact(quote) in compact(pages[i]+pages[i+1])]
  assert hits,(key,'PDF match');final.append({'id':key,'quote':quote,'markdown_lines':[i+1 for i,l in enumerate(newlines) if quote in l],'pdf_pages':hits[0]})
 loc={e['id']:e['pdf_pages'][0] for e in final};assert loc['questions_first']<loc['answers_later']
 for e in json.loads((D/'SEMANTIC_AUDIT_DISPOSITIONS.json').read_text(encoding='utf-8'))['resolutions']:
  assert e['original_flagged_phrase'] not in new,e
  assert e['corrected_phrase'] in new,e
result={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'source_review_edition':'v0.17','baseline_evidence_count':len(checked),'baseline_evidence':checked,'all12_chapters_recorded':True,'final_edition':'v0.18','final_pdf_sha256':hashlib.sha256((R/'e-book/exports/v18/ebook_review_v18.pdf').read_bytes()).hexdigest(),'final_evidence':final,'four_semantic_flags_resolved_in_final_text':True,'scope':'Verbatim source/PDF citation checking, not a new full-book quality or statistical judgment and not reader testing.'}
(D/'EVIDENCE_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['baseline_evidence','final_evidence']},ensure_ascii=False,indent=2));print('Final quote locations:',loc)
