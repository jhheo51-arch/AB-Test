"""Compile the complete v0.4 reading book; cards/workbook remain separate.
uv run --with markdown scripts/build_ebook_v04.py
Requires actual core/scenario analysis outputs, never fabricates missing results.
"""
import html,json,re
from pathlib import Path
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v04';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def data(p):return json.loads(read(p))
r=data('e-book/analysis/winner_v04/core_results.json');s=data('e-book/analysis/winner_v04/scenario_results.json')
extra=read('e-book/manuscript/winner_cases_456_v04.md')
for i in [4,5,6]:assert re.search(rf'^## 사례\s*{i}',extra,re.M),f'Missing actual worked case {i}'
core=read('e-book/manuscript/winner_core_v04.md')
metrics=r['case1'];prim=r['primary_family'][0];guard=r['guardrail_exploratory']
t='| 지표·역할 | A 사건/배정 | B 사건/배정 | 차이pp | 개별95% 구간pp | 미보정 p |\n|---|---:|---:|---:|---:|---:|\n'
for key,label in [('completed','완료·주지표'),('booked','예약·진단'),('opted_out','철회·가드레일')]:
    x=metrics[key];t+=f"| {label} | {x['events_A']:,}/{x['n_A']:,} | {x['events_B']:,}/{x['n_B']:,} | {x['diff_pp']:+.2f} | [{x['ci_low_pp']:+.2f}, {x['ci_high_pp']:+.2f}] | {x['p_raw']:.4f} |\n"
core=core.replace('{{CASE1_TABLE}}',t)
t='| 완료 정책 대비 | 차이pp | 개별 약98.33% 구간pp | 가족 보정 p |\n|---|---:|---:|---:|\n'
for x in r['primary_family']:t+=f"| {x['comparison']} | {x['diff_pp']:+.2f} | [{x['ci_low_pp']:+.2f}, {x['ci_high_pp']:+.2f}] | {x['p_family']:.6g} |\n"
core=core.replace('{{PRIMARY_TABLE}}',t+'\n\n![시승 완료의 효과 구간과 사후 예시 최소 효과 기준](winner_effect.svg)\n')
core=core.replace('{{PRIMARY_PARAGRAPH}}',f"B-A의 완료는 A {prim['events_A']:,}/{prim['n_A']:,}({prim['rate_A']:.2%}), B {prim['events_B']:,}/{prim['n_B']:,}({prim['rate_B']:.2%})였다. 절대 차이{prim['diff_pp']:+.2f}pp와 상대 차이{prim['relative_lift']:+.2%}는 같은 관측을 다른 단위로 표현한다. 세 완료 대비 보정 p={prim['p_family']:.5f}, 약98.33% 구간[{prim['ci_low_pp']:+.2f},{prim['ci_high_pp']:+.2f}]pp다. 합성 설계와 가정 아래 완료의 개선 근거가 있지만, 이 p는 B가 최선일 확률이 아니다.")
core=core.replace('{{GUARD_PARAGRAPH}}',f"철회는 A {guard['events_A']:,}/{guard['n_A']:,}({guard['rate_A']:.3%}), B {guard['events_B']:,}/{guard['n_B']:,}({guard['rate_B']:.3%})였다. B-A는 {guard['diff_pp']:+.3f}pp이며, 개별 미보정95% 구간은 [{guard['ci_low_pp']:+.3f},{guard['ci_high_pp']:+.3f}]pp다. p={guard['p_raw']:.4f}가 크다는 사실로 악화가 없다고 결론내리지 않는다. 이 구간은 주지표 가족의 약98.33% 구간과 수준·역할이 다르다.\n\n![철회 차이의 탐색 구간과 사후 가상 허용 악화](guardrail_effect.svg)")
t='| 군 | 배정 고객당 합성 순기여액 |\n|---|---:|\n'+''.join(f'| {a} | {v:,.0f}원 |\n' for a,v in r['financial_means'].items())
core=core.replace('{{ECON_MEANS}}',t)
t='| 손익 대비 | 고객당 차이 | 개별 탐색95% Welch 구간 |\n|---|---:|---:|\n'
for x in r['financial_exploratory']:t+=f"| {x['comparison']} | {x['diff_krw']:+,.0f}원 | [{x['ci95_low_krw']:+,.0f}, {x['ci95_high_krw']:+,.0f}]원 |\n"
core=core.replace('{{ECON_CI}}',t)
t='| 계약1건 기여액 가정 | A 고객당 | B 고객당 | H 고객당 | B-H 차이 |\n|---|---:|---:|---:|---:|\n'
for x in r['financial_sensitivity']:
    m=x['means_krw'];t+=f"| {x['assumed_contribution_per_contract']:,.0f}원 | {m['A']:,.0f}원 | {m['B']:,.0f}원 | {m['H']:,.0f}원 | {x['B_minus_H_krw']:+,.0f}원 |\n"
core=core.replace('{{ECON_SENSITIVITY}}',t)
assert '{{' not in core
(OUT/'winner_chapters_v04.md').write_text(core+'\n\n'+extra,encoding='utf-8')
old=read('e-book/exports/v02/ebook_review_v02.md')
foundations=old[old.index('# 프롤로그'):old.index('# 5장')]
foundations=foundations.replace('선택은 실행과 중단만이 아니다. 제한적 확대, 운영 보완, 새 가설의 실험, 추가 관측, 판단 보류가 있다. 보류에는 재개 조건이 있어야 한다. 누가 어떤 자료를 확보하면 어떤 결정을 다시 볼지 적는다. 법·동의·중대한 안전 문제는 이익으로 상쇄하지 않으며 최종 승인은 사람에게 남긴다.','선택에는 실행·중단 외에 제한 확대·운영 보완·후속 실험·추가 관측·보류가 있다. 보류에는 담당자·필요 자료·재개 조건을 적는다. 법·동의·중대한 안전은 이익으로 상쇄하지 않으며 최종 승인은 사람이 한다.')
# Historical combined reader no longer governs new completed checks.
foundations=foundations.replace('이 교육용 데이터는 사전에 등록된 실제 기업 실험이 아니라 이미 생성된 학습 자료이므로 그 사실도 명시한다.','실제 기업의 사전등록과 로컬 합성 계획을 구분한다. 기본 v0.1은 사후 교육 분석이며, v0.3은 생성 전에 로컬 계획을 동결한 별도 합성 설계다.')
v03=read('e-book/exports/v03/sample_and_data_chapter_v03.md')
v03=v03.replace('# 우리 CRM은 실험할 수 있는 규모인가?','# 5장 · 우리 CRM은 실험할 수 있는 규모인가?').replace('**허재혁 · 개정 장 v0.3 · 저자 검토용**\n','')
# Scope the original model omissions rather than falsely implying the new standalone exercises do not exist.
v03=v03.replace('동일 모형의 표본 효과를 검증하려면 같은 생성 가정 아래 별도 반복 시뮬레이션이 필요하다.','동일 모형의 표본 효과는 이 장의 별도 반복 시뮬레이션으로 구분한다.')
v03=v03.replace('향후 권한 있는 CRM 자료가 확보되면','뒤의 새 집단·용량 사례도 별도 합성 가정이지 원래 v0.3 모형의 현장 검증은 아니다. 향후 권한 있는 CRM 자료가 확보되면')
oem=old[old.index('# 6장 · 현대자동차'):old.index('# 워크북')].replace('# 6장','# 10장',1)
objections=old[old.index('# 반론을 증거 요청'):old.index('# 방법 부록')].replace('# 반론을 증거 요청으로 바꾸기','# 11장 · 반론을 증거 요청으로 바꾸기',1)
decision=read('e-book/manuscript/winner_decision_v04.md');appendix=decision.index('# 재현 부록');ch9=decision[:appendix];tail=decision[appendix:]
refs=old[old.index('# 출처와 검증 상태'):]
refs=refs.replace('이 판에서 완료한 것은 원본 이벤트/집계 대조와 비율 검정·구간의 독립 라이브러리 구현 대조, 화면 상호작용·출력 검사다.','v0.2에서 원본 이벤트/집계·비율 계산·카드 화면 검사를 수행했고, v0.4에서는 새 여섯 완결 사례와 고객별 탐색 손익, 측정·집단·용량 시나리오를 실제 계산해 본문에 통합했다. PDF의 실제 제작 검사 결과는 별도 validation_v04.json을 따른다.')
intro='''# 독자 안내 · 이 책에서 완성할 것

허재혁의 저자 검토본 v0.4다. 승리의 층위·통계와 최소 사업 효과·관계 가드레일·여섯 완결 사례를 본문에 통합했다. 읽고 나면 실험 계약과 한 장의 판단 보고서를 작성하는 것이 목표다. 최종 판매·출간 승인본은 아니며 외부 통계·OEM 실무자·실독자·권리 검토는 남아 있다.

주 독자는 CRM A/B 테스트를 공부하는 마케터와 기획자다. 처음에는 고객 상태와 비교의 정의를 읽고, 표본·Winner 장과 사례1~6을 순서대로 따라간다. 회의 직전에는9장의 판단 기록과11장의 반론을 참고한다. 수식보다 어떤 주장을 어디까지 할 수 있는지에 집중하되 계산 파일로 직접 재현할 수 있게 했다.

본문을 읽는 책과 회의용 카드는 다른 자료다. 기존60개 진단 카드는 별도 참조 PDF와 검색 HTML로 보존했다. 워크북 역시 별도 파일로 제공해 읽는 흐름을 빈칸과 카드가 끊지 않게 했다. 여섯 사례는 모든 CRM 조건을 망라한다는 뜻이 아니다. 각 사례는 서로 다른 오류·질문을 설명하는 대표 합성 실습이다.

**근거 표기.** 기존 통계 원칙, 저자 제안, 합성 생성 가정, 실제 공개 사실, 아직 미확인을 구분한다. 현대자동차·기아의 내부 원자료나 검수를 사용한 책이 아니며 제휴도 의미하지 않는다. 합성 원가·전환율·효과는 실제 제조사의 평균이나 성과가 아니다.

**버전 구분.** 기본 v0.1 데이터는 v0.2 읽기본의 작은 A/B 사례에 사용했다. v0.3은120,000명 모집단과 A/B/H,180일 계약을 포함한 별도 합성 설계다. v0.4는 이 자료를 보존하고 Winner 심화·새 측정/집단/용량 실습을 통합한 책의 버전이다. 다른 시나리오 고객을 합쳐 표본 수를 늘리지 않는다.
'''
text='\n\n'.join([intro,read('e-book/manuscript/author_story_v02.md'),foundations,v03,core,extra,ch9,oem,objections,tail,refs])
assert '{{' not in text
assert len(re.findall(r'^## 사례\s*[1-6]',text,re.M))==6
(OUT/'ebook_review_v04.md').write_text(text,encoding='utf-8')
# Interval graphics: exact output values; palette retained as a proposal, not company branding.
def interval_svg(row,lo,hi,threshold,title,caption,threshold_label):
    def x(v):return 85+(v-lo)/(hi-lo)*540
    ticks=[lo+(hi-lo)*i/4 for i in range(5)]
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 260" role="img" aria-label="'+html.escape(caption)+'"><rect width="720" height="260" fill="white"/>',f'<text x="20" y="32" font-size="22" fill="#162B33">{title}</text>']
    for v in ticks:out.append(f'<line x1="{x(v)}" x2="{x(v)}" y1="55" y2="150" stroke="#526168" stroke-width=".5"/><text x="{x(v)}" y="179" text-anchor="middle" font-size="18" fill="#526168">{v:+.2f}</text>')
    out.append(f'<line x1="{x(0)}" x2="{x(0)}" y1="55" y2="150" stroke="#162B33" stroke-width="2"/><line x1="{x(threshold)}" x2="{x(threshold)}" y1="55" y2="150" stroke="#8B431D" stroke-width="2" stroke-dasharray="7 5"/><line x1="{x(row["ci_low_pp"])}" x2="{x(row["ci_high_pp"])}" y1="110" y2="110" stroke="#125E59" stroke-width="6"/><circle cx="{x(row["diff_pp"])}" cy="110" r="7" fill="#125E59"/><text x="20" y="215" font-size="18" fill="#162B33">点=推定</text>')
    # Korean labels, never ornamental simulated data.
    out[-1]=out[-1].replace('点=推定','점: 추정 · 선: 효과 구간 · 단위: 퍼센트포인트')
    out.append(f'<text x="20" y="244" font-size="18" fill="#8B431D">점선: {threshold_label} · 사후 학습 예시, 사전 성공 기준 아님</text></svg>')
    return ''.join(out)
(OUT/'winner_effect.svg').write_text(interval_svg(prim,-.2,1.8,.5,'완료 B-A · 개별 약98.33% 구간','완료 효과는0 위지만 사후 예시 최소효과0.5pp를 걸친다','최소 효과 +0.5pp'),encoding='utf-8')
(OUT/'guardrail_effect.svg').write_text(interval_svg(guard,-.15,.35,.2,'철회 B-A · 탐색용 개별95% 구간','철회 효과 구간은 가상의 허용 악화0.2pp를 넘는다','가상 허용 악화 +0.2pp'),encoding='utf-8')
css='''*{box-sizing:border-box}body{margin:0;background:#F6F4EF;color:#162B33;font:18px/1.85 "Malgun Gothic","Apple SD Gothic Neo",sans-serif;word-break:keep-all;overflow-wrap:anywhere}main{max-width:920px;margin:auto;padding:46px}h1,h2,h3{line-height:1.45;letter-spacing:-.025em}h1{font-size:32px;margin:2em 0 .9em;border-bottom:2px solid #162B33;padding-bottom:.5em}h2{font-size:25px;color:#125E59;margin:1.7em 0 .7em}h3{font-size:21px;margin:1.4em 0 .5em}p{margin:.7em 0}a{color:#125E59;text-decoration:underline;text-underline-offset:3px}a:focus-visible{outline:3px solid #125E59;outline-offset:3px}table{width:100%;border-collapse:collapse;margin:1.3em 0;font-size:16px;line-height:1.6;table-layout:auto}th,td{border-bottom:1px solid #b6c0bf;padding:9px 7px;vertical-align:top}th{text-align:left;background:#F6F4EF;color:#162B33}tr{break-inside:avoid}thead{display:table-header-group}blockquote{margin:1em 0;padding:.7em 1em;background:white;color:#526168}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#F6F4EF;padding:16px;line-height:1.6;font-size:16px}code{font-family:Consolas,"Malgun Gothic",monospace;font-size:.95em}img,svg{display:block;width:100%;height:auto;max-width:720px;margin:1em auto}li{margin:.35em 0}.cover{min-height:920px;display:flex;flex-direction:column;justify-content:space-between;padding:50px 0}.cover h1{font-size:64px;line-height:1.25;border:0;margin:0}.cover h2{color:#162B33}.kicker{color:#125E59;font-size:16px;letter-spacing:.08em}.byline{font-size:25px}.muted{color:#526168}.contents{break-after:page}.contents ol{padding-left:1.3em}.contents li{margin:.65em 0}.case-opening{border-top:2px solid #125E59;padding-top:16px}.reading-note{font-size:16px;color:#526168}section{scroll-margin-top:20px}@media(max-width:650px){main{padding:20px}.cover{min-height:680px}.cover h1{font-size:46px}table{font-size:14px}th,td{padding:6px 4px}}@page{size:A4;margin:18mm 18mm 20mm}@media print{body{background:white;font-size:12pt;line-height:1.7}main{max-width:none;padding:0;margin:0}h1{font-size:22pt;break-before:page;page-break-before:always;margin:0 0 7mm;padding-bottom:3mm}h2{font-size:17pt;margin:7mm 0 3mm}h3{font-size:13pt;margin:5mm 0 2mm}h1,h2,h3{break-after:avoid}p{orphans:3;widows:3}table{font-size:12pt;line-height:1.55;margin:5mm 0}th,td{padding:2mm 1.3mm}pre,code{font-size:12pt}.cover{height:251mm;min-height:0;padding:10mm 0;break-after:page}.cover h1{font-size:38pt;page-break-before:auto;break-before:auto}.cover h2{font-size:18pt}.kicker,.reading-note{font-size:12pt}.byline{font-size:18pt}.contents{break-after:page}.contents h1{break-before:auto;page-break-before:auto}.contents li{margin:2mm 0;font-size:12pt}.case-opening{break-before:page;page-break-before:always;margin-top:0}img,svg{break-inside:avoid;max-height:92mm;object-fit:contain}blockquote{background:#F6F4EF}a{color:#125E59}a[href^=http]{overflow-wrap:anywhere}section{break-inside:auto}}
'''
cover='''<section class="cover"><p class="kicker">CRM / EVIDENCE BEFORE VERDICT / 0.4</p><div><h1>그래서,<br>이 캠페인<br>계속할까요?</h1><h2>‘B가 이겼다’는 말에 답하는<br>CRM A/B 테스트와 의사결정</h2></div><div><p class="byline">허재혁</p><p>실험 계약 · 통계와 사업 가치 · 관계 위험<br>JH Motors 여섯 완결 합성 사례</p><p class="reading-note">저자 검토본 · 실제 OEM 성과 아님<br>최종 제목·서사·통계·업무·권리·출간 승인 전</p></div></section>'''
def render(md,title,coverhtml):
    body=markdown.markdown(md,extensions=['tables','toc','fenced_code'],output_format='html')
    for name in ['winner_effect.svg','guardrail_effect.svg']:
        body=re.sub(r'<img[^>]+src="'+re.escape(name)+r'"[^>]*/?>',lambda m:(OUT/name).read_text(encoding='utf-8'),body)
    body=re.sub(r'<h2 id="([^"]+)">(사례\s*[1-6]\s*[·.].*?)</h2>',r'<h2 class="case-opening" id="\1">\2</h2>',body)
    body=re.sub(r'<h2 class="case-opening" id="([^"]+)">(사례\s*1\s*[·.].*?)</h2>',r'<h2 class="case-opening case-first" style="break-before:auto;page-break-before:auto" id="\1">\2</h2>',body)
    heads=re.findall(r'<h1 id="([^"]+)">(.*?)</h1>',body)
    toc='<nav class="contents" aria-label="목차"><h1>목차</h1><ol>'+''.join(f'<li><a href="#{id}">{label}</a></li>' for id,label in heads)+'</ol><p class="reading-note">여섯 사례는8장에 있습니다. PDF 책갈피에서 하위 제목으로 이동할 수 있습니다. 카드60개는 별도 참조편, 작성 양식은 별도 워크북입니다.</p></nav>'
    full='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+css+'</style></head><body><main>'+coverhtml+toc+body+'</main></body></html>'
    return full,len(heads)
book,n=render(text,'그래서, 이 캠페인 계속할까요? | 허재혁 · 저자 검토본 v0.4',cover)
(OUT/'ebook_review_v04.html').write_text(book,encoding='utf-8')
# Print-friendly workbook has actual answers, not a collection of unexplained empty cards.
work='''# Winner 워크북 · 실험 계약과 판단 기록

허재혁 · 저자 검토본 v0.4. 본책과 별도로 작성하는 자료다. 모든 답안은 합성 학습 예시이며 회사의 승인·위험 기준을 대신하지 않는다.

# 양식 1 · 결과 전 Winner 계약

| 작성 항목 | 우리 실험의 답 |
|---|---|
| 고객 상태·장벽·결정 질문 | ______________________________ |
| 대상 자격·동의·금지 대상 | ______________________________ |
| 처치·비교·무발송 대비 여부 | ______________________________ |
| 배정·분석 단위와 간섭 | ______________________________ |
| 주지표 분자·분모·기간·원장 | ______________________________ |
| 비교 가족·지표 위계 | ______________________________ |
| 계획 효과·표본·검정력·종료 | ______________________________ |
| 최소 사업 효과·기준을 정한 때 | ______________________________ |
| 관계·안전 허용 조건·정한 때 | ______________________________ |
| 비용·추적·적용 범위·승인자 | ______________________________ |

기준을 결과 뒤에 정했다면 그 사실을 기록한다. MDE를 최소 사업 가치와 자동으로 같게 두지 않는다.

# 양식 2 · 증거 상태표

| 판단 항목 | 지지/불확실/비교불가/미확인/해당없음 | 근거 파일·한계 |
|---|---|---|
| 비교 타당성 | __________ | __________ |
| 주지표 우위 | __________ | __________ |
| 최소 사업 효과 | __________ | __________ |
| 관계·안전 | __________ | __________ |
| 경제성·장기 가치 | __________ | __________ |
| 대상·규모 적용 | __________ | __________ |

# 양식 3 · 한 장 판단 보고서

결정 질문: __________________________________________________

대상·정책 대비·단위·관측 기간: _________________________________

주지표 효과·구간·方法·다중성·종료: _____________________________

관측과 경쟁 설명·대조한 원장: _________________________________

사업 가치·가드레일·운영의 확인/미확인: _________________________

권고·승인자·적용 범위: ________________________________________

중단·롤백·재평가 조건과 담당자: ________________________________

# 여섯 사례 · 직접 써 보는 판단

## 사례 1

예약의 미보정 신호와 완료 주지표의 불확실성을 한 문장씩 구분한다. 예약자 중 완료율을 전체 정책 효과로 바꾸면 왜 안 되는지도 적는다.

## 사례 2

0보다 나음, 사후 예시0.5pp보다 충분히 나음, 철회 가드레일 통과를 각각 다른 근거로 설명한다. 결과를 보고0.25pp로 기준을 바꾸는 문제를 적는다.

## 사례 3

고객당 합성 순기여액의 식을 적는다. B-A와 B-H의 탐색 구간이 다른데도 ‘B 재무 승리’ 하나로 묶으면 무엇이 사라지는가?

## 사례 4

앱 로그와 독립 원장 중 어떤 차이가 있었는가? 원장도 없다면 어느 주장까지 보류해야 하는가? 분모와 이벤트 누락을 나누어 적는다.

## 사례 5

각 집단의 효과와 집단 간 효과 차이는 어떻게 다른가? 실제 결과 JSON의 상호작용 값과 구간을 찾아 적고, 사후로 집단을 골랐다면 어떤 한계를 추가할지 쓴다.

## 사례 6

수요가 늘어도 완료가 그대로일 수 있는 용량 규칙을 적는다. 기본·낮은·높은 용량의 결과를 대조하고, 공유 자원이 있을 때 개인 독립 검정을 재사용하면 왜 안 되는지 적는다.

# 합성 답안 · 기준은 주장의 경계다

## 사례 1 답안

완료 차이는 약+0.99pp, 개별95% 구간[-0.44,+2.42]pp로0을 포함한다. 예약 신호는 주지표를 사후 바꾸거나 매출을 확정하는 근거가 아니다. 예약 여부가 처치 이후 변수이므로 예약자 조건부 비교를 ITT 전체 효과로 대체하지 않는다.

## 사례 2 답안

완료 B-A는 약+0.93pp, 세 대비 보정 p≈0.00274, 개별 약98.33% 구간[+0.26,+1.61]pp다. 합성 조건의 완료 우위는 지지하지만 최소0.5pp 이상 개선과 관계 안전은 다른 질문이다. 사후 임계값을 사전 성공 기준으로 쓰지 않는다.

## 사례 3 답안

고정 기여액·비용에서 B-H 손익의 탐색용95% Welch 구간은0을 포함한다. A-H의 음의 점추정도 확정 손실은 아니다. 이 모형 값은 실제 출고 매출·순이익·LTV가 아니며 원가 가정 오차·선택·다중성까지 검증한 구간이 아니다.

## 사례 4~6 답안과 계산

다음은 본책에 통합한 실제 실행 결과를 옮긴 완결 설명이다. 숫자만 외우기보다 원본·규칙·가정·결정의 연결을 확인한다.

'''.replace('方法','방법')+extra
(OUT/'workbook_v04.md').write_text(work,encoding='utf-8')
wh,_=render(work,'Winner 워크북 | 허재혁 · v0.4','')
(OUT/'workbook_v04.html').write_text(wh,encoding='utf-8')
manifest={'version':'0.4 author review','author':'허재혁','format':'full reading manuscript, six worked cases; diagnostic cards and workbook separate','headings':n,'worked_case_count':6,'manuscript_characters':len(text),'requests_covered':{'1_winner_layers':'chapter6','2_primary_vs_minimum_benefit':'chapter7 + case2','3_guardrail_safety':'chapter7 + case2 + chapter9','4_six_worked_cases':'chapter8 cases1-6'},'source_data_unchanged':['v01','v03'],'palette':'Existing proposal, not company brand; mira_contrast_matrix passed all8 combinations; minimum normal-text contrast5.85:1','human_review':'pending; not publication-ready'}
(OUT/'build_manifest_v04.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
