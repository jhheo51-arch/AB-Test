"""Validate the new persona evidence in Markdown and present disagreements.
This does not run the previously unapproved PDF-citation/contact-sheet job.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone,timedelta
import json,hashlib,html,re
D=Path(__file__).resolve().parent;R=D.parents[2];source=R/'e-book/exports/v18/ebook_review_v18.md';raw=source.read_bytes();text=raw.decode('utf-8');lines=text.splitlines();h=hashlib.sha256(raw).hexdigest()
previous=json.loads((R/'e-book/review/editorial_quality_v18/STRUCTURAL_SEMANTIC_RECHECK.json').read_text(encoding='utf-8'));assert previous['source_sha256']==h,'Source changed since the v18 review'
required={'persona','scope','findings','top3','strengths','verdict'};reviews=[];records=[];counts={}
for name in ['PERSONA_MARKETER','PERSONA_ANALYST','PERSONA_LEAD']:
 d=json.loads((D/(name+'.json')).read_text(encoding='utf-8'));assert required<=set(d)
 for i,f in enumerate(d['findings'],1):
  assert {'quote','chapter','source_line','problem','impact','fix'}<=set(f)
  n=f['source_line'];assert isinstance(n,int) and 1<=n<=len(lines)
  assert f['quote'] in lines[n-1],(name,i,n)
  records.append({'persona_file':name,'finding':i,'chapter':f['chapter'],'source_line':n,'quote':f['quote'],'exact_source_line_match':True})
 counts[name]=len(d['findings']);reviews.append((name,d))
assert counts=={'PERSONA_MARKETER':10,'PERSONA_ANALYST':11,'PERSONA_LEAD':12}
report={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'source_manuscript':str(source.relative_to(R)),'source_sha256':h,'review_file_count':len(reviews),'findings_by_persona':counts,'quote_records':len(records),'unique_quote_strings':len({r['quote'] for r in records}),'records':records,'scope':'New persona review Markdown quotation and schema checks only. Not a PDF citation audit, contact-sheet regeneration, statistical recomputation or real-reader study.','book_modified':False}
(D/'PERSONA_EVIDENCE_VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
E=html.escape
old=(D/'BENCHMARK.html').read_text(encoding='utf-8');oldhash=hashlib.sha256((D/'BENCHMARK.html').read_bytes()).hexdigest()

newjudgment='''<section class="judgment"><p><strong>제목을 폐기할 필요는 없다. 다만 현재 표지 그대로 확정하는 것은 권하지 않는다.</strong> 표지 축소 비교에서는 A/B 테스트라는 주제 단서가 약했다. 그러나 전권을 읽은 마케터와 CRM 책임자 역할은 현재 질문형 제목을 유지할 수 있다고 판단했다. 제목 교체가 유일한 해결책이라는 제 앞선 권고는 조정한다.</p><p>권장 구성은 큰 <strong>CRM A/B 테스트 실무</strong> 장르 표기, 기존 질문형 제목, 독자가 할 일을 말하는 TRI-V 부제다. “혼자 모든 분석과 승인을 끝내는 책”이 아니라 결과를 읽고 명세와 판단 기록을 고치며 필요한 확인을 담당자에게 요청하는 책이라는 약속을 분명히 한다.</p><p>TRI-V는 여전히 책 내용의 중심이다. 낯선 약어만 큰 메인 제목으로 내세우지 말자는 의견을 방법론을 빼거나 부록으로 내리자는 뜻으로 해석하지 않는다. 세 역할의 의견은 실제 시장 반응이나 독자 실험이 아니다.</p></section>'''
page=re.sub(r'<section class="judgment">.*?</section>',lambda m:newjudgment,old,count=1,flags=re.S)
page=page.replace('현 가제에 대한 판단','전권 비평을 반영해 조정한 제목 권고')
page=page.replace('<small>권장 / 범위와 주제 우선</small>','<small>대안 / 주제어를 제목에 넣기</small>')
keep='''<article class="title-option"><small>우선 권장 / 질문형 제목 유지안</small><p class="label">CRM A/B 테스트 실무</p><h3>그래서, 이 캠페인<br>계속할까요?</h3><p>TRI-V로 근거를 점검하고 적용 범위와 다음 행동을 정하는 법</p><p class="tradeoff">주제 표기는 크게, 제목은 두 줄 안팎으로 정리하는 제안이다. 최종 표지를 새로 렌더하거나 승인한 것은 아니다. 자동차 CRM 사례 중심이며 분석과 보호 평가 및 실제 승인은 담당자와 협업한다는 범위를 소개문에 밝힌다.</p></article>'''
page=page.replace('<section class="title-options">','<section class="title-options">'+keep,1)
page=page.replace('상단 작은 A/B 분류 → 큰 제목에 CRM A/B 테스트','작은 A/B 분류 → 크게 읽히는 CRM A/B 테스트 표기 또는 제목 편입')
page=page.replace('페르소나별 전권 비평은 별도 파일로 정리한다.','페르소나별 전권 비평의 근거는 위 펼치기에서 확인한다. 본책의 제목과 표지는 아직 바꾸지 않았다.')
summary='''<h2>세 페르소나의 가장 강한 반론</h2><p class="scope">최신 v0.18에 대한 AI 모의 편집 판단이다. 인터뷰, 구매 의사 조사나 실제 독자시험이 아니다. 기존 연습과 실행 후보 및 완성 결정문이 있다는 사실을 인정한 뒤 남은 부족을 평가했다.</p><table><thead><tr><th>가상 독자와 작업</th><th>가장 강한 반론</th><th>조건부 판단</th></tr></thead><tbody><tr><td>비전공 CRM 마케터<br>자기 캠페인 명세와 보고문 교정</td><td>무엇을 질문할지는 알겠지만, 불충분한 회신을 어떻게 판별하고 다시 고치는가?</td><td>전문 담당자와 협업하는 판단 학습서로 적합. 혼자 설계와 평가 및 승인까지 끝내는 안내서로는 부족.</td></tr><tr><td>A/B 분석 담당자<br>기존 명세와 판단 경계 공유</td><td>정상적인 표준 절차도 이 일을 한다. TRI-V를 추가해 늘어나는 작업보다 어떤 이득이 있는가?</td><td>공동 검토와 근거 추적의 교육적 가치는 가능. 성숙한 표준 절차의 대체나 검증된 우월성은 미확인.</td></tr><tr><td>CRM 책임자<br>현재 행동과 확인의 우선순위 결정</td><td>보류 결정은 완결돼 있다. 하지만 다음 담당자에게 넘겨 실제 업무를 진행시키는 연결은 충분한가?</td><td>제목은 유지 가능. 실행 후보와 보류를 함께 노출하고, 허용 행동과 승인 경계 및 인수인계를 먼저 보여 줄 것.</td></tr></tbody></table><h2>더 비판적으로 보면, 남은 핵심은 세 가지다</h2><ol><li><strong>쉬운 문장과 독립 수행은 다르다.</strong> 개념을 읽는 난도, 전문 분석 역할, 실제 자료와 권한 부족을 분리해야 한다. 계산을 못 하는 것을 모두 학습 실패로 취급하지 않는다.</li><li><strong>TRI-V의 추가 가치를 보여 줘야 한다.</strong> 잘 작성된 기존 명세를 재사용하면서 무엇만 새로 기록하고 어떤 확인을 생략하는지 비교할 필요가 있다. 새로운 통계 이론이나 이미 입증된 효율로 판매하지 않는다.</li><li><strong>새 이론보다 요청·회신·재수정 장면이 필요하다.</strong> 기존 9장과 10장 연습을 없애거나 없다고 비판하지 말고 담당자에게 넘기는 문서와 충분한 회신의 기준까지 연결한다. 12장의 보류 결정문도 현재 증거 아래의 완결된 결정이지 단순 미완성이 아니다.</li></ol><h2>실제 원고 근거 펼쳐 보기</h2>'''
labels={'PERSONA_MARKETER':'비전공 CRM 마케터','PERSONA_ANALYST':'A/B 분석 담당자','PERSONA_LEAD':'CRM 책임자와 기획 편집 관점'}
for name,d in reviews:
 summary+=f'<details><summary>{E(labels[name])} / 근거 {len(d["findings"])}개</summary><div class="evidence">'
 for f in d['findings']:
  summary+=f'<article><h3>{E(str(f["chapter"]))} / 원고 {f["source_line"]}줄</h3><blockquote>{E(f["quote"])}</blockquote><p><strong>문제:</strong> {E(f["problem"])}</p><p><strong>영향:</strong> {E(f["impact"])}</p><p><strong>수정:</strong> {E(f["fix"])}</p></article>'
 summary+='</div></details>'
summary+='<p class="scope">인용 기록은 모두 현재 Markdown의 지정 행과 대조했다. PDF 쪽수 검증이나 실제 독자의 수행 확인은 아니다. 서적 표지 출처와 전자책 형식의 확인 범위는 아래에 따로 표시한다.</p><details><summary>비교 서적의 열람 및 형식 확인 범위</summary>'
for b in json.loads((D/'SOURCES.json').read_text(encoding='utf-8'))['sources']:summary+=f'<p><strong>{E(b["title"])}</strong>: {E(b["format_evidence"])}</p>'
summary+='</details>'
page=page.replace('<footer>',summary+'<footer>',1)
page=page.replace('.title-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}', '.title-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}')
page=page.replace('</style>','details{margin:16px 0;background:white;border:1px solid #BAC9C1;padding:16px}summary{cursor:pointer;min-height:44px;display:list-item;font-weight:bold}.evidence article{padding:14px 0;border-bottom:1px solid #BAC9C1}blockquote{margin:12px 0;padding:12px 16px;background:#E3EEE8}td,blockquote,p{overflow-wrap:anywhere}a,summary{scroll-margin-top:20px}</style>',1)
(D/'POSITIONING_REVIEW.html').write_text(page,encoding='utf-8',newline='\n')
assert hashlib.sha256(source.read_bytes()).hexdigest()==h
assert hashlib.sha256((D/'BENCHMARK.html').read_bytes()).hexdigest()==oldhash
print(json.dumps({'status':'passed','findings_by_persona':counts,'quote_records_verified':len(records),'unique_quote_strings':report['unique_quote_strings'],'source_sha256':h,'final_review':str(D/'POSITIONING_REVIEW.html'),'original_book_and_initial_benchmark_unchanged':True},ensure_ascii=False))
