"""Inspect only the newly edited page states, not a whole-book contact sheet."""
from pathlib import Path
import json,re
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v20';V=R/'e-book/design/v20';D=V/'review';D.mkdir(parents=True,exist_ok=True)
probes={'guided_comparison':'여기서부터 4장까지는 같은 JH Motors 설계 기록','guided_scope':'앞 장에서 고친 비교 명세는 그대로 참조한다.','guided_action':'현재는 정한 대상의 비교 설계와 보호 평가를 준비한다.','transfer_problem':'두 표를 모두 읽은 뒤 해설로 넘어가기 전에','reuse_question':'해설을 읽기 전에 이전 기록에서 그대로 참조할 문장','reuse_feedback':'자신의 답에서 정책과 고객 및 사건의 정의를','compressed_application':'p값을 성공 확률로 바꾸어 적은 문장','standalone_decision':'완성된 한 장 결정문 예시'}
compact=lambda s:re.sub(r'\s+','',s)
rows={}
with pymupdf.open(O/'ebook_review_v20.pdf') as doc:
 texts=[compact(p.get_text()) for p in doc]
 for name,probe in probes.items():
  pages=[i+1 for i,t in enumerate(texts) if compact(probe) in t];assert len(pages)==1,(name,pages);rows[name]=pages[0]
  doc[pages[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(D/(name+'.png'))
report={'scope':'Targeted new-page text locators and individual page renders; no prior blocked full citation audit or whole-book contact regeneration','pages':rows,'actual_reader_test':False}
(V/'TARGETED_PAGE_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
