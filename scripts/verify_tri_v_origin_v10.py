"""Audit supplied naming provenance and locate new explanatory content in the exact PDF."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v10';REV=ROOT/'e-book/design/v10/review';REV.mkdir(parents=True,exist_ok=True)
source=Path('C:/Users/Administrator/AppData/Local/hermes/composer-pastes/pasted_content_2026-11-16_08-46-55-414_0f762e.txt')
draft=source.read_text(encoding='utf-8')
for name in ['TRI-V','Variable Control','Vector Segmentation','Value-Linked Decision','앞서 완성한']:assert name in draft,name
text=(OUT/'ebook_review_v10.md').read_text(encoding='utf-8');v=json.loads((OUT/'validation_v10.json').read_text(encoding='utf-8'))
images=['tri_v_easy_comparison.svg','tri_v_easy_population.svg','tri_v_easy_decision.svg']
assert all(text.count(']('+name+')')==1 and (OUT/name).is_file() for name in images)
for term in ['저자의 방법론이 TRI-V','별개의 방법론을 추가한 것이 아니다','모든 상황에서 같은 절차로 같은 수준의 답을 얻는 것도 아니다','이 조합 전체가 역사상 처음인지 판단할 정도의 선행 문헌 조사는 완료하지 않았다']:
 assert term in text,term
with pymupdf.open(OUT/'ebook_review_v10.pdf') as d:
 toc=d.get_toc();pages={}
 for heading in ['TRI-V를 시승 안내로 먼저 이해하기','TRI-V 공통 운용 기준','TRI-V의 출발점과 적용 범위']:
  hit=[t[2] for t in toc if t[1]==heading];assert len(hit)==1,(heading,hit);pages[heading]=hit[0]
  d[hit[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).save(REV/('easy_start.png' if heading.startswith('TRI-V를') else 'operating_criteria.png' if heading.endswith('운용 기준') else 'origin_scope.png'))
 assert hashlib.sha256((OUT/'ebook_review_v10.pdf').read_bytes()).hexdigest()==v['pdf_sha256']
ref=json.loads((ROOT/'e-book/references/METHOD_REVIEW_v06.json').read_text(encoding='utf-8'))
report={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'supplied_draft':{'file_name':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'observed':'TRI-V and all three V expansions are already present; the draft itself says the framework had been completed earlier','limits':'This excerpt does not establish the first coiner, the full earlier dialogue, historical novelty, career achievements or validated effectiveness. Earlier praise is not a literature review.'},'principle_sources':[{'id':s['id'],'title':s['title'],'url':s['url'],'scope':'Use the exact read ranges and cautions in METHOD_REVIEW_v06.json; these sources do not endorse TRI-V.'} for s in ref['sources']],'current_browser_recheck':{'NIST_S3':'Read opening blocking/randomization discussion and example excerpt, not the whole handbook','Microsoft_S2':'Read telemetry, observation-unit imbalance and tradeoff excerpts; predetermined tradeoff criteria, not endorsement of TRI-V'},'new_pdf_section_pages':pages,'new_illustrations':images,'primary_name':'TRI-V, author-proposed method','Contextvia_status':'Optional brand not approved or imposed','universal_applicability_established':False,'historical_priority_established':False,'human_learning_or_field_superiority_established':False,'previous_reading_editions_and_data_modified':False}
(OUT/'origin_scope_validation_v10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
