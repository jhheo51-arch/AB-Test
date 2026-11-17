"""Expanded reading edition with a new cover and editorial typesetting."""
from pathlib import Path
import re,json,hashlib,html
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v07';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v06/ebook_review_v06.md')
start,rest=base.split('# 5장 숫자를 읽을 때 필요한 통계',1)
_,rest=rest.split('# 7장 결과가 엇갈리는 여섯 상황',1)
text=start+'\n\n'+read('e-book/manuscript/statistical_foundations_v07.md')+'\n\n# 7장 결과가 엇갈리는 여섯 상황'+rest
text=text.replace('# 부록 계산과 자료',read('e-book/manuscript/end_to_end_v07.md')+'\n\n# 부록 계산과 자료',1)
# Keep source provenance in the audit, replace production chatter with reader-facing bibliography.
a=text.index('# 이번 판의 학습 자료와 반영 범위');b=text.index('# 키워드 찾아보기와 설명',a)
refs='''# 참고 자료와 계산의 범위

이 책은 기존 실험 원칙을 정화, 해체와 입체화, 언어의 전환이라는 순서로 연결하는 저자의 제안이다. 다음 자료는 각 원칙의 근거와 더 공부할 경로이며, 이 방법론의 성과를 인증한 자료가 아니다. 공개 학습 노트는 질문의 출발점으로 사용하되 영상의 검증된 전사본으로 간주하지 않았다.

[1] Widad Machmouchi, Somit Gupta, Ruhan Zhang. Patterns of Trustworthy Experimentation: During-Experiment Stage. Microsoft Experimentation Platform, 2021. 지표 분류와 안정적인 집단, 시간별 효과와 중간 모니터링을 참고했다.

https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-during-experiment-stage/

[2] Widad Machmouchi, Somit Gupta. Patterns of Trustworthy Experimentation: Post-Experiment Stage. Microsoft Experimentation Platform, 2021. 측정과 분모, 지표 간 상충, 재실험과 결과 보관을 참고했다.

https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/

[3] NIST/SEMATECH. e-Handbook of Statistical Methods, Randomized block designs. 방해 요인과 블록 및 무작위화의 역할을 참고했다.

https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm

[4] ICH. E9(R1) Addendum on Estimands and Sensitivity Analysis in Clinical Trials, 2019. 질문과 추정 대상, 분석의 정렬 원칙을 참고했다. 임상 규정을 CRM의 규정으로 옮긴 것은 아니다.

https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf

Ron Kohavi, Diane Tang, Ya Xu. Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing. Cambridge University Press, 2020. 공식 공개 1장 샘플과 목차의 열람 범위에서 비교했다. 전체 책을 완독하거나 내용을 재현한 것은 아니다.

https://experimentguide.com/

Georgi Z. Georgiev. Statistical Methods in Online A/B Testing. 저자의 학습 출발 자료다. 이 책의 초기 구상은 제공된 목차와 학습 요약을 참고했으며 원서 전체의 독립적인 대조를 완료한 것은 아니다. 단측 검정 선호나 다른 추론 체계에 대한 특정 저자의 입장을 전체 통계학의 합의로 취급하지 않는다.

양승화. 그로스 해킹: 데이터와 실험을 통해 성장하는 서비스를 만드는 방법. 위키북스, 2021. 출판사 공개 소개와 독자 범위 및 목차를 편집 비교에 참고했다. 본문을 인용하거나 책 전체를 읽었다는 뜻은 아니다.

https://wikibook.co.kr/growthhacking/

구현과 수치의 확인 범위는 앞의 계산 부록에 적었다. 자료의 열람과 계산 재현은 실제 고객을 대상으로 한 방법론 검증을 대신하지 않는다. 저자 검토본의 제목과 서사, 인용과 배포 권리 및 판매 규격의 최종 검토는 별도로 필요하다.

'''
text=text[:a]+refs+text[b:]
text=read('e-book/manuscript/reader_route_v07.md')+'\n\n'+text
text=re.sub(r'나는 이런 결과를 다루는 관점을 트리아타시스\(Tri-Ataxis\)라고 불러왔다\..*?이를 실제 순서로 풀어 쓴 것이 TRI-V다\.', '나는 이런 결과를 다루는 관점을 트리아타시스(Tri-Ataxis)라고 부른다. 비교를 믿을 수 있는지 확인하고, 누구에게 적용할지 살피며, 실행할 조건을 정하는 일이다. 이를 실제 순서로 풀어 쓴 것이 TRI-V다.',text,count=1)
text=text.replace('이 책의 상위 관점은 기존 이름인 트리아타시스이고 실행 절차는 TRI-V다. ‘맥락항법’은 둘을 새 독자에게 설명할 방법론 제목의 제안이다. 맥락항법: 비교의 근거에서 실행의 결론까지라는 표현을 시험해 보려 한다. 별개의 네 번째 단계나 새로운 검정법을 추가한 것은 아니다.','트리아타시스는 질문을 바라보는 관점이고 TRI-V는 그 질문을 순서대로 실행하는 절차다. 새로운 검정법을 추가하는 것은 아니다. 통계적으로 이미 알려진 방법을 어느 판단에 사용하고, 근거가 부족하면 어디로 되돌아갈지 정리한다.')
first_report='''이 표를 바탕으로 쓸 수 있는 첫 판단문은 다음과 같다. 기존 A보다 편의 안내 B에서 예약 증가의 신호가 관측됐다. 그러나 이번 주지표인 완료의 B-A 차이는 약 +0.99pp이고 개별 95% 구간은 약 [-0.44,+2.42]pp이므로, 현재 자료에서 완료 우위를 확인했다고 보고하지 않는다. 그렇다고 효과가 없다고 확정한 것도 아니다. 예약 증가가 완료로 이어지지 않은 이유는 이 집계만으로 고르지 않는다. 예약 이후 취소와 일정 변경, 실제 방문 기록과 수용 가능 시간을 같은 배정 고객 기준으로 연결해 다음 판단의 근거를 마련한다.

원장 접근 권한이 없다면 자료 요청도 구체적으로 쓸 수 있다. 분석 담당자에게는 배정 식별자와 고객 식별자, 원래 군, 배정 시각, 관측 종료 기준이 있는 명부를 요청한다. 예약 운영 담당자에게는 같은 식별자에 연결되는 예약 생성과 취소 및 변경 시각, 방문 담당자에게는 실제 완료 시각과 누락 정정 기록을 요청한다. 필요한 것은 고객 연락처를 보고서에 복사하는 일이 아니라, 권한이 통제된 환경에서 동일 고객의 경로와 개인별 관측 창을 대조하는 일이다. 자료가 도착하면 배정 분모를 유지한 완료 결과와 예약 이후의 진단을 분리해 다시 검토한다. 요청을 했다는 사실은 원인의 확인이나 전면 적용의 승인이 아니다.

'''
text=text.replace('## 사례 2 완료에서 이겼어도 남는 질문',first_report+'## 사례 2 완료에서 이겼어도 남는 질문',1)
evidence='''# 부록 사례와 자료를 찾아가는 길

여섯 사례는 하나의 원장을 잘라 만든 같은 실험이 아니다. 다음 표는 어떤 자료에서 어떤 주장을 읽는지 구분하는 길잡이다. 앞의 정화와 입체화, 언어의 전환을 사용했다는 사실이 각 분석의 설계 한계를 없애지는 않는다.

| 사례 | 자료와 비교 단위 | 추론과 계획의 범위 | 재사용할 때의 경계 |
|---|---|---|---|
| 1 예약과 완료 | v01 기본 A/B, 배정 고객 | 사후 교육 분석, 개별 95% Newcombe와 미보정 양측 검정 | 예약을 완료 성공으로 바꾸지 않음 |
| 2 완료와 채택 | v03 A/B/H, 배정 고객 | 생성 전 로컬 계획, 세 완료 대비 Bonferroni, 개별 약 98.33% 구간 | 사후 사업 기준과 보호 한계를 사전 성공 조건으로 바꾸지 않음 |
| 3 문구와 캠페인 가치 | v03와 고정 비용 가정, 배정 고객당 손익 | 개별 탐색 Welch 구간, 계약과 비용에 조건부 | 완료 가족 보정이 손익 주장까지 보호하지 않음 |
| 4 측정 역전 | 별도 원장과 결함 로그, 군당 4,000명 | 주입한 누락의 합성 실습, 개별 95% Newcombe | 원장의 정답이 알려진 교육 환경과 현장 복구를 구분 |
| 5 고객군 효과 | 별도 사전 상태별 고정 배정 | 전체 0.5/0.5 층화 Wald 95%, 상태별 Newcombe 97.5%, 상호작용 명목 95% | 상호작용까지 공동 가족 확증으로 바꾸지 않음 |
| 6 공유 용량 | 별도 고정 수요와 운영 정책 | 같은 수요 세계의 조건부 모형 비교, 신뢰구간 없음 | 독립 개인 p값이나 실제 기대 이익으로 해석하지 않음 |

기본과 큰 실험을 잇는 계산은 `scripts/analyze_winner_v04.py`, 별도 세 실습은 `scripts/build_winner_scenarios_v04.py`와 그 결과 장부를 따른다. 읽기 패키지에 PDF와 HTML, 편집 원고와 그림 및 글꼴은 포함하지만 기존 고객 DB와 전체 개발 환경까지 들어 있다고 가정하지 않는다. 데이터와 코드에 접근할 권한이 있는 독자는 저장소의 명세와 경로를 확인한 별도 작업 사본에서 재현한다. 생성 명령과 읽기 전용 확인을 구분하고, 원본 데이터에 새 오류를 주입하거나 덮어쓰지 않는다.

검증 상태도 나누어 읽는다. 저자의 논리 구성과 합성 사례의 구현 대조는 수행했지만 독립된 사람의 통계 검토와 OEM 실무 검토, 실제 독자의 과제 수행 시험은 완료하지 않았다. 외부 사람이 같은 패키지로 결과를 복원하는 일, 실제 조직에서 판단 누락이 줄어드는지를 확인하는 일은 각각 별도의 검증이다. 이 책을 조직의 자동 승인 규칙이나 새로운 통계 분석 엔진으로 사용해서는 안 된다.

'''
text=text.replace('# 부록 계산과 자료',evidence+'# 부록 계산과 자료',1)
# Reader-facing editing: retain caveats where needed, remove conversational production language.
text=text.replace('이 장의 출발 자료인 Notion의 Studying 페이지는 영상 추천, 개념 요약, 질문과 답변, 개인적인 관심이 함께 담긴 학습 노트다. 연결된 영상의 검증된 녹취록은 아니며, 노트 속 설명을 발표자의 발언으로 그대로 돌릴 수 없다. 같은 내용이 반복되거나 서로 다른 설명이 섞인 곳도 있다. 따라서 여기서는 노트의 문제의식을 이어받되, 정의와 가정은 바로잡아 설계의 언어로 옮긴다. 원문을 충실히 공부한다는 것은 오해까지 보존한다는 뜻이 아니다.','개념을 배웠다는 것과 그 개념으로 설계를 바꿀 수 있다는 것은 다르다. 같은 용어도 가정을 생략하면 반대의 판단에 쓰일 수 있다. 이 장에서는 앞서 익힌 원칙을 하나의 계획에 옮기며 어느 조건을 사전에 정하고 무엇을 실행 중에 감시할지 연결한다.')
text=text.replace('scripts/build_ebook_v06.py','scripts/build_ebook_v07.py').replace('scripts/render_verify_v06.py','scripts/render_verify_v07.py')
text=text.replace('uv run --with playwright --with pymupdf --with pillow scripts/render_verify_v07.py','uv run --with markdown --with playwright --with pymupdf --with pillow scripts/render_verify_v07.py')
for name in ['winner_effect.svg','guardrail_effect.svg','tri_v_method.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']:
 (OUT/name).write_text(read('e-book/exports/v06/'+name),encoding='utf-8')
# A concept map, not fabricated operational data.
flow='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 370" role="img" aria-label="가상 캠페인의 설계에서 결정까지"><rect width="720" height="370" fill="white"/><g font-family="ReaderSans,sans-serif" fill="#142D32"><text x="12" y="34" font-size="25" font-weight="700">한 캠페인을 끝까지 읽는 순서</text><text x="18" y="95" font-size="23">정화</text><text x="220" y="95" font-size="22">동의와 대상 → 비교 정책 → 배정과 측정</text><text x="18" y="170" font-size="23">해체와 입체화</text><text x="220" y="170" font-size="22">전체 효과 → 사전 고객군 → 적용 범위</text><text x="18" y="245" font-size="23">언어의 전환</text><text x="220" y="245" font-size="22">사업 기준 → 보호와 용량 → 조건부 결정</text><text x="18" y="337" font-size="21" fill="#4F625F">근거가 비어 있으면 앞선 단계로 돌아가 다음 자료를 정한다.</text></g><path d="M18 115H700M18 190H700M18 265H700" stroke="#9CAEA6"/></svg>'''
(OUT/'campaign_path_v07.svg').write_text(flow,encoding='utf-8')
text=text.replace('# 12장 한 건의 캠페인을 설계에서 결정까지','# 12장 한 건의 캠페인을 설계에서 결정까지\n\n![캠페인의 설계와 해석 및 결정 순서](campaign_path_v07.svg)',1)
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden)
assert '{{' not in text
assert len(re.findall(r'^## 사례 [1-6] ',text,re.M))==6
assert not re.search(r'^### ',text,re.M)
(OUT/'ebook_review_v07.md').write_text(text,encoding='utf-8')
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'],output_format='html')
for name in [p.name for p in OUT.glob('*.svg')]:body=re.sub(r'<img[^>]+src="'+re.escape(name)+'"[^>]*/?>',lambda m:read('e-book/exports/v07/'+name),body)
body=re.sub(r'<table>(.*?)</table>',lambda m:'<table'+(' class="compact"' if m[1].count('<tr>')<=5 else '')+'>'+m[1]+'</table>',body,flags=re.S)
# Sans labels accompany a deliberate serif reading face.
body=re.sub(r'<h1 id="([^"]+)">(\d+)장 (.*?)</h1>',lambda m:f'<h1 class="chapter" id="{m[1]}"><span class="chapter-no">CHAPTER {int(m[2]):02d}</span><span>{m[2]}장 {m[3]}</span></h1>',body)
body=re.sub(r'<h2 id="([^"]+)">(사례 [1-6] .*?)</h2>',r'<h2 class="case-opening" id="\1">\2</h2>',body)
glossary_marker=re.search(r'<h1 id="[^"]+">키워드 찾아보기와 설명</h1>',body)
assert glossary_marker
body=body[:glossary_marker.start()]+'<section class="glossary">'+body[glossary_marker.start():]+'</section>'
heads=[]
for match in re.finditer(r'<h1[^>]*id="([^"]+)"[^>]*>(.*?)</h1>',body,re.S):
 label=re.sub(r'<span class="chapter-no">.*?</span>','',match[2]);label=re.sub('<[^>]*>','',label);heads.append((match[1],label))
cover=read('e-book/design/v07/covers/selected_cover.html')
covercss=read('e-book/design/v07/covers/cover_styles.css');covercss=covercss[covercss.index('*{'):]
# Scope cover selectors to avoid overriding book headings and page geometry.
covercss=covercss.replace('html,body{margin:0}','').replace('body{font-family:ReaderSans,sans-serif}','')
font='''@font-face{font-family:ReaderSans;src:url("assets/reader-sans.woff2");font-weight:100 900}@font-face{font-family:ReaderSerif;src:url("assets/reader-serif.woff2");font-weight:100 900}'''
css=font+covercss+'''
:root{--ink:#142D32;--muted:#4F625F;--paper:#F5F1E8;--accent:#125E59}html{background:#DFE3DE}body{margin:0;color:var(--ink);font-family:ReaderSerif,serif;word-break:keep-all;overflow-wrap:anywhere}.cover-frame{position:relative;width:min(900px,100%);aspect-ratio:900/1280;margin:0 auto;overflow:hidden}.cover-frame .book-cover{font-family:ReaderSans,sans-serif;position:absolute;top:0;left:0;transform:scale(var(--cover-scale,1));transform-origin:top left}.reading{max-width:900px;margin:auto;background:white;padding:50px 62px;font-size:18px;line-height:1.9}.imprint{font:15px/1.8 ReaderSans,sans-serif;border-top:1px solid #9CAEA6;padding-top:18px;color:var(--muted)}.imprint p{margin:.3em 0;text-indent:0}.contents{font-family:ReaderSans,sans-serif;margin:45px 0 65px}.contents ol{list-style:none;padding:0}.contents li{margin:.55em 0}.contents a{display:flex;justify-content:space-between;gap:20px;text-decoration:none;border-bottom:1px solid #DCE3DE;padding:6px 0}.contents .folio{font-variant-numeric:tabular-nums;min-width:28px;text-align:right}h1,h2{font-family:ReaderSans,sans-serif;letter-spacing:-.035em;line-height:1.45}h1{font-size:30px;margin:2.5em 0 1em}h2{font-size:24px;margin:1.7em 0 .8em}.chapter-no{display:block;font-size:14px;letter-spacing:.13em;color:var(--accent);margin-bottom:12px;font-weight:600}.chapter>span:last-child{display:block}p{margin:.65em 0;text-indent:1em}a{color:var(--accent);text-underline-offset:3px}a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}table{font-family:ReaderSans,sans-serif;font-size:16px;line-height:1.6;width:100%;border-collapse:collapse;margin:24px 0}th,td{vertical-align:top;text-align:left;padding:10px 6px;border-bottom:1px solid #BAC9C1}th{background:#F2F5F1;font-weight:600}pre,code{font-family:Consolas,ReaderSans,monospace;font-size:.9em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#F2F5F1;padding:16px;line-height:1.65}svg{width:100%;height:auto;display:block;margin:24px 0}svg text{font-family:ReaderSans,sans-serif}ul{list-style:none;padding-left:0}li{margin:.5em 0}.contents p{text-indent:0}.case-opening{margin-top:2em}strong{font-family:ReaderSans,sans-serif;font-weight:600}@media(max-width:650px){.reading{padding:26px 20px;font-size:17px}table{font-size:15px}th,td{padding:8px 4px}h1{font-size:27px}h2{font-size:22px}.contents{margin-bottom:45px}}
@page{size:190mm 270mm;margin:17mm 16mm 18mm}@page cover{size:190mm 270mm;margin:0}@media print{html,body{background:white}.cover-frame{page:cover;width:190mm;height:270mm;aspect-ratio:auto;--cover-scale:.7979002625!important;break-after:page;margin:0}.reading{max-width:none;margin:0;padding:0;font-size:12pt;line-height:1.8}.imprint{font-size:12pt;line-height:1.65;margin:0 0 7mm;padding-top:3mm}.contents{break-after:page;margin:0}.contents h1{margin:4mm 0}.contents li{margin:.1em 0}.contents a{padding:1.3mm 0;line-height:1.4}.contents .folio{font-size:12pt}h1{font-size:22pt;margin:9mm 0 5mm;break-after:avoid;break-before:auto;break-inside:avoid;page-break-inside:avoid}h2{font-size:16pt;line-height:1.5;margin:7mm 0 4mm;break-after:avoid}.chapter-no{font-size:12pt;margin-bottom:3mm}p{orphans:3;widows:3;margin:.5em 0}table{font-size:12pt;line-height:1.45;margin:5mm 0;table-layout:auto}th,td{padding:1.8mm .8mm}thead{display:table-header-group}tr{break-inside:avoid}pre{font-size:12pt;line-height:1.5;break-inside:avoid;padding:3mm}table.compact{break-inside:avoid}.glossary h2{font-size:15pt;margin:5mm 0 3mm}code{font-size:12pt}svg{margin:6mm 0;max-height:180mm;break-inside:avoid}ul{padding:0}.case-opening{margin-top:8mm}a{overflow-wrap:anywhere}.cover-frame .book-cover{transform:none;zoom:.7979002625}.cover-frame .title{margin:0;font-size:90px;line-height:1.2}.cover-frame p{line-height:inherit;text-indent:0}.cover-frame .book-cover svg{margin:0;max-height:none}.cover-frame .byline{font-size:24px}.cover-frame .promise{font-size:28px}.cover-frame .strap{font-size:23px}.cover-frame .method{font-size:18px}.cover-frame .edition{font-size:18px}}
'''
toc='<nav class="contents" aria-label="목차"><h1>목차</h1><ol>'+''.join(f'<li><a href="#{i}"><span>{html.escape(label)}</span><span class="folio" data-id="{i}"></span></a></li>' for i,label in heads)+'</ol></nav>'
imprint='<section class="imprint"><p>허재혁의 CRM A/B 테스트 실무서 / 저자 검토본 0.7</p><p>작업 가제: 그래서, 이 캠페인 계속할까요?</p><p>JH Motors는 교육용 가상 회사다. 사례의 합성 자료와 실제 기업 자료를 구분한다.</p><p>맥락항법은 제목 제안이며 저자 승인, 사람의 기술 검수와 출간 검토 전이다.</p></section>'
script='''<script>function fitCover(){let f=document.querySelector('.cover-frame');f.style.setProperty('--cover-scale',f.clientWidth/900)}addEventListener('resize',fitCover);fitCover();</script>'''
full='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>그래서, 이 캠페인 계속할까요? | 허재혁 | 검토본0.7</title><style>'+css+'</style></head><body><div class="cover-frame">'+cover+'</div><main class="reading">'+imprint+toc+body+'</main>'+script+'</body></html>'
assert not any(c in full for c in forbidden)
(OUT/'ebook_review_v07.html').write_text(full,encoding='utf-8')
# A same-layout A4 control separates added text from new book geometry.
oldcss=re.search('<style>(.*?)</style>',read('e-book/exports/v06/ebook_review_v06.html'),re.S)[1]
control=markdown.markdown(text,extensions=['tables','toc','fenced_code'])
for name in [p.name for p in OUT.glob('*.svg')]:control=re.sub(r'<img[^>]+src="'+re.escape(name)+'"[^>]*/?>',lambda m:read('e-book/exports/v07/'+name),control)
(OUT/'content_control_A4_v07.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><style>'+oldcss+'</style><main>'+control+'</main></html>',encoding='utf-8')
manifest={'version':'0.7 author review','author':'허재혁','selected_cover':'A, recommendation pending author approval','page_geometry_mm':[190,270],'body_pt':12,'font_families':['Noto Serif KR reading face','Noto Sans KR headings, tables and labels'],'source_characters':len(text),'source_nonspace_characters':len(''.join(text.split())),'previous_v06_characters':len(base),'six_cases_preserved':True,'new_content':['Reader route','Rewritten and expanded chapters5-6','Complete campaign chapter12, decision memo and worked answers'],'new_layout_is_not_evidence_of_depth':True,'old_numeric_ledgers':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']},'limits':['Simulated persona review, not real reader research','Author title and voice approval pending','No claims of actual OEM success, new statistical theory or publication readiness']}
(OUT/'build_manifest_v07.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False,indent=2))
