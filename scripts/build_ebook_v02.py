"""Build v0.2 visual field guide from verified outputs; preserve v0.1."""
import html
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import markdown
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports/v02'
OUT.mkdir(parents=True,exist_ok=True)
cards=json.loads((ROOT/'e-book/workflow/diagnostic_cards_v02.json').read_text(encoding='utf-8'))
analysis=json.loads((ROOT/'e-book/analysis/v02/verified_analysis.json').read_text(encoding='utf-8'))
metrics=analysis['metrics']; primary,booking,guard=metrics
E=html.escape

def ci_chart():
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 340" role="img" aria-label="B-A 차이와 지표별 미보정 95% 구간. 주지표 완료 구간은 0을 포함한다.">']
    def x(v):return 300+(v+1)/6*450
    parts.append('<rect width="800" height="340" fill="#FFFFFF"/>')
    for tick in [-1,0,1,2,3,4,5]:
        xx=x(tick);parts.append(f'<line x1="{xx}" y1="35" x2="{xx}" y2="245" stroke="#526168" stroke-width="{2 if tick==0 else .4}"/><text x="{xx}" y="280" text-anchor="middle" font-size="20" fill="#526168">{tick:+d}</text>')
    for r,label,y in zip(metrics,['시승 완료 · 주지표','예약 · 진단','수신 거부 · 위험'],[75,150,225]):
        color='#8B431D' if r['metric']=='opted_out' else '#125E59'
        parts.append(f'<text x="10" y="{y+6}" font-size="22" fill="#162B33">{label}</text><line x1="{x(r["ci95_low_pp"])}" x2="{x(r["ci95_high_pp"])}" y1="{y}" y2="{y}" stroke="{color}" stroke-width="5"/><circle cx="{x(r["diff_pp"])}" cy="{y}" r="7" fill="{color}"/>')
    parts.append('<text x="300" y="325" font-size="20" fill="#526168">B-A 차이 (퍼센트포인트) · 점: 추정 / 선: 95% 구간</text></svg>')
    return ''.join(parts)
chart=ci_chart();(OUT/'verified_effects.svg').write_text(chart,encoding='utf-8')

stage_data=[('G0','질문·안전','대상·동의·허용되는 개입'),('G1','비교·실행','배정 단위·대조 정책·간섭'),('G2','데이터 품질','배정 원본·누락·중복·측정'),('G3','기간·정보','성숙한 관측·표본·종료 규칙'),('G4','효과·불확실성','추정·구간·다중성·가정'),('G5','상충 패턴','관심→행동→가치·관계'),('G6','집단·전이','사전 집단·탐색·적용 범위'),('G7','가치·제약','비용·이익·수용량·장기'),('G8','승인·재평가','결정·책임·감시·롤백')]
flow=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 1050" role="img" aria-label="TRI-V 아홉 단계와 미해결 시 보류·재설계"><rect width="680" height="1050" fill="white"/>']
for i,(g,title,evidence) in enumerate(stage_data):
    y=20+i*105
    flow.append(f'<rect x="25" y="{y}" width="530" height="82" rx="3" fill="#F6F4EF" stroke="#125E59"/><text x="45" y="{y+31}" font-size="24" fill="#125E59">{g} · {title}</text><text x="45" y="{y+61}" font-size="22" fill="#162B33">{evidence}</text><path d="M555,{y+40} L610,{y+40}" stroke="#526168" stroke-dasharray="5 4"/>')
    if i<8:flow.append(f'<path d="M290,{y+82} L290,{y+103} m-5,-6 l5,6 l5,-6" stroke="#526168" fill="none"/>')
flow.append('<path d="M610,60 L610,990 L130,990" stroke="#526168" fill="none" stroke-dasharray="6 4"/><text x="25" y="1025" font-size="22" fill="#526168">미해결 문제는 보류·재설계 → 해당 단계로 재진입</text></svg>')
flow=''.join(flow);(OUT/'workflow_print_v02.svg').write_text(flow,encoding='utf-8')

# Assemble manuscript with table tokens generated from immutable verified outputs.
source=(ROOT/'e-book/manuscript/reading_draft_v01.md').read_text(encoding='utf-8')
source=source[source.index('# 프롤로그'):source.index('# 출처·표기와 다음 집필 범위')]
source=source.replace('본 시작 원고는 독립적인 주 효과 계산 검증을 아직 완료하지 않았으므로 출시 권고를 제시하지 않는다.','주 효과의 구현·집계 대조는 이 판에서 완료했고 다음 분석 장에 제시한다. 다만 사업적 채택과 안전을 입증한 것은 아니다.')
source=source.replace('주 효과의 추론, 가드레일, 비용, 최소 사업 효과, 운영 여력을 검토해야 한다.','주 효과의 추론, 가드레일, 비용, 최소 사업 효과, 운영 여력을 검토해야 한다.')
table='| 항목 | A | B |\n|---|---:|---:|\n'
for label,key in [('배정 고객','n'),('예약','booked'),('시승 완료','completed'),('수신 거부','opted_out')]:
    if key=='n':av,bv=primary['n_A'],primary['n_B']
    else:
        m=next(x for x in metrics if x['metric']==key);av,bv=m['events_A'],m['events_B']
    table+=f'| {label} | {av:,} | {bv:,} |\n'
source=source.replace('{{BASELINE_TABLE}}',table)
story=(ROOT/'e-book/manuscript/author_story_v02.md').read_text(encoding='utf-8')
evidence=(ROOT/'e-book/manuscript/winner_evidence_v02.md').read_text(encoding='utf-8')
t='| 指標 | A | B | B-A (pp) | 95% 구간 (pp) | 양측 p |\n|---|---:|---:|---:|---:|---:|\n'.replace('指標','지표')
for r,label in zip(metrics,['시승 완료 · 주지표','예약 · 진단','수신 거부 · 가드레일']):
    t+=f"| {label} | {r['rate_A']:.2%} | {r['rate_B']:.2%} | {r['diff_pp']:+.2f} | [{r['ci95_low_pp']:+.2f}, {r['ci95_high_pp']:+.2f}] | {r['p_two_sided_pooled_z']:.4f} |\n"
evidence=evidence.replace('{{VERIFIED_METRICS}}',t)
evidence=evidence.replace('{{PRIMARY_INTERPRETATION}}',f"완료율은 A {primary['rate_A']:.2%}, B {primary['rate_B']:.2%}였다. 차이는 {primary['diff_pp']:+.2f}pp, 상대 개선율은 {primary['relative_lift']:.2%}로 관측됐다. 그러나 95% 구간은 [{primary['ci95_low_pp']:+.2f}, {primary['ci95_high_pp']:+.2f}]pp이고 양측 p={primary['p_two_sided_pooled_z']:.4f}다. 통상적인 0.05 기준에서는 주지표의 우위를 선언하지 않는다. 그렇다고 무효과나 동등성이 입증된 것도 아니다. 상대 개선율만 강조하면 이 불확실성이 가려진다.")
evidence=evidence.replace('{{BOOKING_INTERPRETATION}}',f"예약률은 A {booking['rate_A']:.2%}, B {booking['rate_B']:.2%}, 차이는 {booking['diff_pp']:+.2f}pp이며 미보정 p={booking['p_two_sided_pooled_z']:.4f}다. 이 신호는 예약 단계의 개선을 탐색할 근거이지, 주지표를 예약으로 사후 교체하거나 차량 매출 증가를 선언할 근거가 아니다. 예약 후 시승 완료로 이어지는 과정과 운영 상태를 진단한다. 이항 검정의 p-value를 ‘B가 옳을 확률’로 읽지 않는다.")
evidence=evidence.replace('{{GUARDRAIL_INTERPRETATION}}',f"수신 거부율은 A {guard['rate_A']:.2%}, B {guard['rate_B']:.2%}로 관측됐다. 차이는 {guard['diff_pp']:+.2f}pp, 95% 구간은 [{guard['ci95_low_pp']:+.2f}, {guard['ci95_high_pp']:+.2f}]pp다. p={guard['p_two_sided_pooled_z']:.4f}라는 이유로 ‘안전하다’고 하지 않는다. 양의 차이는 이 지표에서는 위험의 증가 방향이다. 사전에 정한 비열등 한계가 없고 의미 있는 악화도 구간에 남아 있다.")
p=analysis['planning_example']
evidence=evidence.replace('{{PLANNING_EXAMPLE}}',f"별도의 교육용 계획 예로 기준 전환율 {p['baseline_rate']:.0%}에서 {p['target_rate']:.0%}로의 절대 개선을 구분하려고 한다고 하자. 양측 유의수준 {p['alpha_two_sided']:.0%}, 검정력 {p['power']:.0%}, 독립 개인·동일 배정·고정 종료·단일 주 비교의 정규근사 식에서는 군당 약 {p['approx_n_per_arm']:,}명이 계산된다. 손실·군집·운영상 이슈를 포함한 최종 설계 수가 아니며, 현재 표본에서 관측한 효과로 사후 검정력을 계산한 결과도 아니다.")
front='''# 독자 안내 · 이 책을 사용하는 방법

이 판은 읽기·실습·회의 준비에 사용할 수 있도록 묶은 저자 검토본 v0.2다. 최종 출간본으로 승인된 파일은 아니다. 현대자동차·기아의 내부 감사나 실제 캠페인 성과 보고가 아니며, 두 기업과의 제휴·검수도 의미하지 않는다.

처음 공부한다면 저자 서사와 본문을 순서대로 읽는다. 회의 직전이라면 ‘B가 이겼다는 말을 검증하는 법’과 반론 장을 먼저 읽고 카드 ID를 찾는다. 실습은 저장소의 합성 DB와 분석 JSON을 대조한다. 카드의 관측·원인 후보·증거·행동을 서로 바꿔 읽지 않는다.

표기 원칙은 네 가지다. **공개 사실**은 출처와 확인 범위를 붙인다. **저자 제안**은 기존 원칙을 조직한 관점으로 표시한다. **합성 실습**은 생성 규칙과 가정을 공개한다. **미확인**은 빈칸을 그럴듯한 숫자로 채우지 않는다.

판단 기록은 ‘B가 승리’보다 길어질 수 있다. 그래도 짧은 단정보다 범위가 명확한 문장이 좋은 결정을 만든다. 반론은 상대를 이기기 위한 질문이 아니라, 더 정확한 결론을 만들기 위한 증거 요청으로 사용한다.
'''
refs='''# 출처와 검증 상태

현대자동차 Sales Results: https://www.hyundai.com/worldwide/en/company/ir/ir-resources/sales-results — 공식 페이지와 모델별 판매 파일 확인. 집계 판매이며 CRM 인과 원자료 아님.

기아 Monthly Sales Results: https://worldwide.kia.com/en/company/investor-relations/library/performance-and-plans — 공개 자료 목록 확인. 개별 파일·내부 성과는 이 판에서 확인하지 않음.

Apple Mail Privacy Protection: https://www.apple.com/legal/privacy/data/en/mail-privacy-protection/ — 원격 콘텐츠 자동 로딩과 오픈 해석의 한계.

Toyota Sustainability Data Book 2025: https://global.toyota/pages/global_toyota/sustainability/report/sdb/sdb25_en.pdf — 고객 피드백·서비스 운영 공개자료. 개별 고객 실험 아님.

통계 방법 문서와 ASA 성명은 계산 방법 부록에 수록했다. URL의 존재나 도구 간 수치 일치가 연구 가정·출판 권리 검수까지 보증하지 않는다.

이 판에서 완료한 것은 원본 이벤트/집계 대조와 비율 검정·구간의 독립 라이브러리 구현 대조, 화면 상호작용·출력 검사다. 남은 것은 통계 전문가·OEM 실무자·실제 독자의 검토, 모든 카드의 실증·반례 검증, 기업별 상세 근거 장부, 최종 저자 서사 승인, 글꼴·인용·배포처 권리 및 규격 검수다. 모든 CRM 경우를 완전하게 다뤘다고 주장하지 않는다.
'''
text=front+'\n'+story+'\n'+source+'\n'+evidence+'\n'+refs
assert '{{' not in text
(OUT/'ebook_review_v02.md').write_text(text,encoding='utf-8')

css='''*{box-sizing:border-box}:root{--ink:#162B33;--muted:#526168;--teal:#125E59;--paper:#F6F4EF;--rust:#8B431D;--line:#b6c0bf}body{margin:0;color:var(--ink);background:var(--paper);font:16px/1.7 "Malgun Gothic","Apple SD Gothic Neo",sans-serif}a{color:var(--teal)}button,input,select{font:inherit;min-height:44px;color:var(--ink)}button{cursor:pointer;background:white;border:1px solid var(--muted);padding:8px 14px}button:hover,button[aria-pressed=true]{background:var(--teal);color:white}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--teal);outline-offset:3px}.shell{max-width:1440px;padding:32px;margin:auto}.kicker{font-size:12px;letter-spacing:.1em;color:var(--teal);font-weight:bold}h1{font-size:clamp(30px,4vw,46px);line-height:1.3;letter-spacing:-.04em}h2{font-size:25px;line-height:1.5}h3{line-height:1.5}.muted{color:var(--muted)}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0}.atlas{display:grid;grid-template-columns:320px minmax(0,1fr);gap:24px}.library{border-top:2px solid var(--ink);padding-top:16px}.library input,.library select{width:100%;padding:7px;margin-bottom:10px}.case-buttons{height:650px;overflow:auto;display:flex;flex-direction:column;gap:0}.case-buttons button{text-align:left;flex-shrink:0;border:0;border-bottom:1px solid var(--line);padding:12px}.case-buttons small{display:block}.card{background:white;padding:28px;border:1px solid var(--line)}.card-top{display:flex;flex-wrap:wrap;gap:10px;color:var(--teal);font-size:13px;font-weight:700}.challenge{color:var(--rust);font-size:21px;font-weight:bold;border-top:2px solid var(--rust);padding-top:18px;margin-top:20px}.evidence-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.evidence-grid section{border-top:1px solid var(--line);padding-top:4px}.label{font-size:12px;font-weight:bold;letter-spacing:.05em;color:var(--muted)}.sequence{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:20px 0}.sequence span{border:1px solid var(--muted);padding:6px 10px;font-size:14px}.response{border-top:2px solid var(--teal);padding-top:12px}.unsafe{color:var(--rust)}.card-footer{display:flex;gap:12px;justify-content:space-between;margin-top:22px}.note{font-size:14px;color:var(--muted)}.proof{max-width:1000px;background:white;padding:28px}.proof svg{width:100%}table{width:100%;border-collapse:collapse}th,td{padding:10px 6px;border-bottom:1px solid var(--line);text-align:left}thead{background:var(--paper)}.table-wrap{overflow:auto}.flow-screen{max-width:700px;background:white;padding:20px}.flow-screen svg{width:100%}[hidden]{display:none!important}.book{max-width:900px;background:white;margin:auto;padding:56px 64px}.book h1{font-size:30px;margin:48px 0 24px}.book h2{font-size:22px;margin-top:28px}.book p{word-break:keep-all;overflow-wrap:anywhere}.book table{font-size:14px}.book a{overflow-wrap:anywhere}.cover{height:1000px;display:flex;flex-direction:column;justify-content:space-between;border-top:10px solid var(--teal);padding-top:30px}.cover h1{font-size:59px;line-height:1.28;margin:0}.cover .byline{font-size:25px}.toc{background:var(--paper);padding:24px;margin-top:40px}.toc a{text-decoration:none}.proof-print{border:1px solid var(--line);padding:20px;margin:28px 0}.proof-print svg{width:100%}.map-page svg{height:920px;width:100%}.print-case{padding:24px 0}.worksheet-line{height:38px;border-bottom:1px solid var(--line)}.print-controls{position:fixed;bottom:18px;right:18px}.diagram-head{font-size:14px;color:var(--muted)}@media(max-width:850px){.shell{padding:20px 14px}.atlas{grid-template-columns:1fr}.case-buttons{height:240px}.card{padding:20px}.evidence-grid{grid-template-columns:1fr}.book{padding:26px 22px}.cover{height:780px}.cover h1{font-size:45px}}@media print{@page{size:A4;margin:17mm 16mm 18mm}body{font-size:12pt;background:white;line-height:1.6}.book{padding:0;max-width:none}.book h1{font-size:24pt;break-after:avoid;margin:30px 0 16px}.book h2{font-size:17pt;break-after:avoid}.book h3{font-size:14pt;break-after:avoid}.book p{orphans:3;widows:3}.book table{font-size:12pt}.book th,.book td{padding:8px 4px}.book tr{break-inside:avoid}.cover{height:251mm;break-after:page}.cover h1{font-size:36pt;margin:0}.toc{break-after:page;margin:0}.cover .note,.note{font-size:12pt}.card-top,.label,.diagram-head{font-size:12pt}.print-case{break-before:page;break-after:page;min-height:235mm;padding:0;display:flex;flex-direction:column;justify-content:flex-start}.print-case h2{font-size:20pt;margin:12px 0}.print-case .challenge{font-size:17pt;line-height:1.5}.print-case .evidence-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.print-case .sequence{margin:16px 0}.print-case .sequence span{font-size:12pt}.print-case .response{margin-top:12px}.print-case .reflection{margin-top:auto}.map-page{break-before:page;break-after:page}.map-page svg{height:230mm;width:100%}.proof-print{break-inside:avoid;padding:8px}.print-controls{display:none}.book .toc ul{padding-left:20px}.book a{color:var(--ink)}.print-case .card-footer{display:none}}'''

def card_body(c,printing=False):
    return f'''<div class="card-top"><span>{E(c['case_id'])}</span><span>{E(c['dimension'])}</span><span>{E(c['gate'])}</span></div><h2>{E(c['observation'])}</h2><p class="note">{E(c['risk'])} · 원인 미확정 · 자동 승리 판정 금지</p><div class="sequence" aria-label="관측에서 판단으로"><span>관측</span>→<span>반론</span>→<span>증거</span>→<span>다음 행동</span></div><div class="challenge">“{E(c['objection'])}”</div><div class="evidence-grid"><section><p class="label">가능한 설명 · 아직 원인 아님</p><p>{E(c['competing_explanations'])}</p></section><section><p class="label">확인해야 할 증거</p><p>{E(c['required_evidence'])}</p></section></div><p class="unsafe"><b>피할 답변</b> · {E(c['unsafe_reply'])}</p><div class="response"><p class="label">답변의 범위와 다음 단계</p><p>{E(c['defensible_boundary'])}</p><p><b>다음 행동:</b> {E(c['next_step'])}</p></div><p class="note"><b>실습 연결:</b> {E(c['dataset_link'])}. 원인이나 방법론 효과의 실증을 뜻하지 않습니다.</p>'''
proof_html='<h2>예약의 신호와 주지표의 승리는 다릅니다</h2><p>JH Motors 합성 데이터 · 사후 교육 분석 · 지표별 미보정 검정·구간</p>'+chart+'<div class="table-wrap">'+markdown.markdown(t,extensions=['tables'])+'</div><p>시승 완료의 95% 구간은 0을 포함합니다. 예약의 신호를 근거로 주지표를 사후 변경하지 않습니다. 수신 거부에서 양의 차이는 위험 증가 방향이며, 비유의성은 안전의 증거가 아닙니다.</p><p class="note">자체 수식과 statsmodels 구현 대조, 원본 이벤트 SQL 대조 완료. 계약·차량 매출·LTV·사업 최소 효과·관계 허용 한계는 이 자료로 입증되지 않았습니다.</p>'
app='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>B가 이겼다고요? · CRM 진단 카드 | 허재혁</title><style>__CSS__</style><body><main class="shell"><div class="kicker">JH / EVIDENCE BEFORE VERDICT / V0.2</div><h1>B가 이겼다고요?<br>어떤 근거로요?</h1><p>반론을 증거 요청으로 바꾸는 CRM 진단 카드. 관측만으로 원인이나 출시 결론을 확정하지 않습니다.</p><nav class="tabs" aria-label="보기"><button data-view="cards" aria-pressed="true">60개 진단 카드</button><button data-view="proof" aria-pressed="false">실제 계산 결과</button><button data-view="flow" aria-pressed="false">판단 워크플로우</button><a href="ebook_review_v02.html">전자책 읽기 →</a></nav><section id="view-cards" class="atlas"><aside class="library"><label>상황 검색<input id="q" type="search" placeholder="예: 매출, 동의, 예약"></label><label>분류<select id="category"><option value="">전체 범주</option></select></label><p id="count" class="note" aria-live="polite"></p><button id="reset">검색 초기화</button><div id="list" class="case-buttons" aria-label="진단 카드 목록"></div></aside><article id="selected" class="card" aria-live="polite"></article></section><section id="view-proof" class="proof" hidden>__PROOF__</section><section id="view-flow" class="flow-screen" hidden><h2>TRI-V · 판단 경로</h2><p>각 단계에서 증거가 부족하면 보류·재설계합니다. 지표별 오류 영향은 구분합니다.</p>__FLOW__</section><footer class="note"><p>허재혁 · 저자 제안·검토본 · 현대자동차·기아 내부 데이터나 실제 캠페인 실적을 사용한 화면이 아닙니다.</p></footer></main><script>
const data=__DATA__;let active=16,filtered=data;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function body(c){return `<div class="card-top"><span>${esc(c.case_id)}</span><span>${esc(c.dimension)}</span><span>${esc(c.gate)}</span></div><h2>${esc(c.observation)}</h2><p class="note">${esc(c.risk)} · 원인 미확정 · 자동 승리 판정 금지</p><div class="sequence"><span>관측</span>→<span>반론</span>→<span>증거</span>→<span>다음 행동</span></div><div class="challenge">“${esc(c.objection)}”</div><div class="evidence-grid"><section><p class="label">가능한 설명 · 아직 원인 아님</p><p>${esc(c.competing_explanations)}</p></section><section><p class="label">확인해야 할 증거</p><p>${esc(c.required_evidence)}</p></section></div><p class="unsafe"><b>피할 답변</b> · ${esc(c.unsafe_reply)}</p><div class="response"><p class="label">답변의 범위와 다음 단계</p><p>${esc(c.defensible_boundary)}</p><p><b>다음 행동:</b> ${esc(c.next_step)}</p></div><p class="note"><b>실습 연결:</b> ${esc(c.dataset_link)}. 실증된 원인·자동 처방이 아닙니다.</p>`}
function select(id){active=data.findIndex(c=>c.case_id===id);const c=data[active];document.getElementById('selected').innerHTML=body(c)+`<div class="card-footer"><button id="prev">← 이전</button><span>${esc(c.case_id)}</span><button id="next">다음 →</button></div>`;document.querySelectorAll('[data-id]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===id)));const i=filtered.findIndex(x=>x.case_id===id);document.getElementById('prev').disabled=i<=0;document.getElementById('next').disabled=i>=filtered.length-1;document.getElementById('prev').onclick=()=>select(filtered[i-1].case_id);document.getElementById('next').onclick=()=>select(filtered[i+1].case_id)}
function render(){const q=document.getElementById('q').value.trim().toLowerCase(),cat=document.getElementById('category').value;filtered=data.filter(c=>(!cat||c.dimension===cat)&&(!q||Object.values(c).join(' ').toLowerCase().includes(q)));document.getElementById('count').textContent=`${filtered.length} / ${data.length}개`;document.getElementById('list').innerHTML=filtered.map(c=>`<button data-id="${esc(c.case_id)}" aria-pressed="false"><small>${esc(c.case_id)} · ${esc(c.dimension)}</small>${esc(c.observation)}</button>`).join('');document.querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>select(b.dataset.id));if(filtered.length)select(filtered.some(c=>c.case_id===data[active].case_id)?data[active].case_id:filtered[0].case_id);else document.getElementById('selected').innerHTML='<h2>일치하는 상황이 없습니다</h2><p>분류를 전체로 바꾸거나 다른 검색어로 확인하세요. 미분류 상황을 억지로 기존 카드에 맞추지 않습니다.</p>';}
const cat=document.getElementById('category');[...new Set(data.map(c=>c.dimension))].forEach(d=>{let o=document.createElement('option');o.value=d;o.textContent=d;cat.append(o)});cat.onchange=render;document.getElementById('q').oninput=render;document.getElementById('reset').onclick=()=>{cat.value='';document.getElementById('q').value='';render()};document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-view]').forEach(x=>{const yes=x===b;x.setAttribute('aria-pressed',String(yes));document.getElementById('view-'+x.dataset.view).hidden=!yes})});render();
</script></body></html>'''
app=app.replace('__CSS__',css).replace('__DATA__',json.dumps(cards,ensure_ascii=False)).replace('__PROOF__',proof_html).replace('__FLOW__',flow)
(OUT/'diagnostic_atlas_v02.html').write_text(app,encoding='utf-8')

cover='''<section class="cover"><p class="kicker">CRM EXPERIMENT PLAYBOOK / AUTHOR REVIEW 0.2</p><div><h1>그래서,<br>이 캠페인<br>계속할까요?</h1><h2>“B가 이겼다”는 말에 답하는<br>CRM A/B 테스트 진단 플레이북</h2></div><div><p class="byline">허재혁</p><p>고객 여정 · 지표 근거 · 반론 검토 · 60개 상황 카드</p><p class="note">현대자동차·기아 적용 설계 제안 / JH Motors 합성 실습<br>저자 검토본 · 최종 출간 승인 전</p></div></section>'''
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'],output_format='html')
# Add actual-effect chart adjacent to the analysis section, with explicit context.
needle='<h1 id="_16">'
# Reliable insertion uses the first computed metric table rather than heading slug assumptions.
metric_table=markdown.markdown(t,extensions=['tables'])
body=body.replace(metric_table,metric_table+'<div class="proof-print">'+chart+'</div>')
# Build a compact linked content map from heading IDs.
import re
heads=re.findall(r'<h1 id="([^"]+)">(.*?)</h1>',body)
toc='<nav class="toc" aria-label="목차"><h2>목차</h2><ol>'+''.join(f'<li><a href="#{i}">{label}</a></li>' for i,label in heads)+'</ol><p>부록: 상황별 진단 카드 CRM-001~CRM-060. 카드 ID로 검색할 수 있습니다.</p></nav>'
appendix='<h1 id="diagnostic-cards">상황별 진단 카드 · 현장 참조편</h1><p>각 카드는 관측·반론·증거·행동의 경계를 구분합니다. 한 카드가 한 원인을 확정하지 않으며 모든 사례가 실증·시뮬레이션 검증된 것은 아닙니다. 회의 메모 칸에 실제 자료와 다음 확인 작업을 적으세요.</p>'
for c in cards:
    appendix+='<section class="print-case" id="'+c['case_id']+'">'+card_body(c,True)+'<div class="reflection"><p class="label">우리 회사 적용 메모 · 원본 근거 / 담당자 / 재검토 조건</p><div class="worksheet-line"></div><div class="worksheet-line"></div></div></section>'
book='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>그래서, 이 캠페인 계속할까요? | 허재혁 · 저자 검토본 v0.2</title><style>'+css+'</style><body><main class="book">'+cover+toc+body+'<section class="map-page"><h1>TRI-V · 판단 워크플로우</h1>'+flow+'</section>'+appendix+'</main><button class="print-controls" onclick="window.print()">인쇄 / PDF</button></body></html>'
(OUT/'ebook_review_v02.html').write_text(book,encoding='utf-8')
(ROOT/'e-book/design/v02').mkdir(parents=True,exist_ok=True)
(ROOT/'e-book/design/v02/palette_and_scope.json').write_text(json.dumps({'palette_proposal':['#162B33','#526168','#125E59','#8B431D','#F6F4EF','#FFFFFF'],'contrast_minimum':5.85,'font':'Local Malgun Gothic; final distribution rights pending','status':'author review, not publication-approved','author':'허재혁','built_at_seoul':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),'case_count':len(cards),'verified_metrics':len(metrics),'compiled_manuscript_characters':len(text)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'out':str(OUT),'cards':len(cards),'headings':len(heads),'manuscript_characters':len(text),'unresolved_template':bool(re.search(r'\{\{[A-Z_]+\}\}',text))},ensure_ascii=False,indent=2))
