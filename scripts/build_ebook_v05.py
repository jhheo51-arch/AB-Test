"""Build v0.5 around the author's Tri-Ataxis / TRI-V method.
uv run --with markdown scripts/build_ebook_v05.py
"""
import html,json,re,hashlib
from pathlib import Path
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v05';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def load(p):return json.loads(read(p))
r=load('e-book/analysis/winner_v04/core_results.json');plan=load('e-book/virtual-data/v03/experiment_plan.json');sim=load('e-book/virtual-data/v03/repeated_sampling_check.json')
methods=read('e-book/manuscript/methodology_v05.md');numbers=read('e-book/manuscript/numbers_and_cases_v05.md');end=read('e-book/manuscript/decision_and_sources_v05.md');extra=read('e-book/manuscript/winner_cases_456_v05.md')
for n in [4,5,6]:assert re.search(rf'^## 사례\s*{n}\s',extra,re.M)
assert not re.search(r'^###',extra,re.M)
forbidden='\u00b7\u2022\u2027\u318d'
def no_dots(s):
    # Historical figure labels are editorial prose, not source identifiers or numerical values.
    for char in forbidden:s=s.replace(char,', ')
    return s
methods=methods.replace('{{METHOD_MAP}}','![트리아타시스와 TRI-V의 세 단계](tri_v_method.svg)')
labels={'click_large':'클릭','drive_primary':'시승','contract_rare':'계약','optout_risk':'철회','complaint_rare':'희귀 불만','drive_tiny':'작은 시승 변화'}
t='| 구분할 변화 | 군당 고객 | 두 군 합계 | 관측 기간 |\n|---|---:|---:|---:|\n'
for key in labels:
    x=next(a for a in plan['sample_size_grid'] if a['scenario']==key and a['family_comparisons']==1)
    t+=f"| {labels[key]} {100*x['baseline']:g}%에서 {100*x['target']:g}% | {x['n_each_numeric_power']:,} | {x['two_arm_total']:,} | {x['observation_days']}일 |\n"
numbers=numbers.replace('{{SAMPLE_TABLE}}',t)
t='| 군 | 배정 고객 | 28일 완료 | 180일 계약 |\n|---|---:|---:|---:|\n'
for x in r['groups']:t+=f"| {x['arm']} | {x['n']:,} | {x['completed']:,} | {x['contracted']:,} |\n"
numbers=numbers.replace('{{GROUP_TABLE}}',t)
t='| 군당 고객 | 5,000회 중 계획 효과 발견률 |\n|---|---:|\n'
for x in sim['results']:
    if x['scenario']=='planned_effect':t+=f"| {x['n_per_arm']:,} | {x['observed_rejection_rate']:.2%} |\n"
numbers=numbers.replace('{{REPEAT_TABLE}}',t)
t='| 지표 | A 사건/배정 | B 사건/배정 | 차이pp | 개별95% 구간pp | 미보정 p |\n|---|---:|---:|---:|---:|---:|\n'
for key,label in [('completed','완료, 주지표'),('booked','예약, 진단'),('opted_out','철회, 보호')]:
    x=r['case1'][key];t+=f"| {label} | {x['events_A']:,}/{x['n_A']:,} | {x['events_B']:,}/{x['n_B']:,} | {x['diff_pp']:+.2f} | [{x['ci_low_pp']:+.2f}, {x['ci_high_pp']:+.2f}] | {x['p_raw']:.4f} |\n"
numbers=numbers.replace('{{CASE1_TABLE}}',t)
t='| 완료 대비 | 차이pp | 개별 약98.33% 구간pp | 가족 보정 p |\n|---|---:|---:|---:|\n'
for x in r['primary_family']:t+=f"| {x['comparison']} | {x['diff_pp']:+.2f} | [{x['ci_low_pp']:+.2f}, {x['ci_high_pp']:+.2f}] | {x['p_family']:.6g} |\n"
numbers=numbers.replace('{{PRIMARY_TABLE}}',t)
t='| 군 | 배정 고객당 합성 순기여액 |\n|---|---:|\n'+''.join(f'| {arm} | {val:,.0f}원 |\n' for arm,val in r['financial_means'].items());numbers=numbers.replace('{{ECON_MEANS}}',t)
t='| 손익 대비 | 고객당 차이 | 개별 탐색95% Welch 구간 |\n|---|---:|---:|\n'
for x in r['financial_exploratory']:t+=f"| {x['comparison']} | {x['diff_krw']:+,.0f}원 | [{x['ci95_low_krw']:+,.0f}, {x['ci95_high_krw']:+,.0f}]원 |\n"
numbers=numbers.replace('{{ECON_CI}}',t)
t='| 계약 기여액 가정 | A 고객당 | B 고객당 | H 고객당 | B-H |\n|---|---:|---:|---:|---:|\n'
for x in r['financial_sensitivity']:
    m=x['means_krw'];t+=f"| {x['assumed_contribution_per_contract']:,.0f}원 | {m['A']:,.0f}원 | {m['B']:,.0f}원 | {m['H']:,.0f}원 | {x['B_minus_H_krw']:+,.0f}원 |\n"
numbers=numbers.replace('{{ECON_SENSITIVITY}}',t)
sources='| 내용 | 저장소에서 확인할 자료 |\n|---|---|\n'
for a,b in [('기본 A/B','e-book/virtual-data/v01/data/oem_crm.sqlite'),('큰 A/B/H','e-book/virtual-data/v03/data/jh_motors_v03.sqlite'),('생성 전 계획','e-book/virtual-data/v03/experiment_plan.json'),('사례1에서3 계산','e-book/analysis/winner_v04/core_results.json'),('사례4에서6 계산','e-book/analysis/winner_v04/scenario_results.json'),('새 합성 CSV','e-book/analysis/winner_v04/scenarios/'),('기본 계산 코드','scripts/analyze_winner_v04.py'),('추가 실습 코드','scripts/build_winner_scenarios_v04.py')]:sources+=f'| {a} | `{b}` |\n'
end=end.replace('{{SOURCE_TABLE}}',sources)
text='\n\n'.join([methods,numbers,extra,end]);text=no_dots(text)
assert '{{' not in text
assert not re.search(r'^###',text,re.M)
assert len(re.findall(r'^## 사례\s*[1-6]\s',text,re.M))==6
assert len(re.findall(r'^## ',text,re.M))==6,'Only the six substantial case headings remain below chapter level'
assert not any(x in text for x in forbidden)
(OUT/'ebook_review_v05.md').write_text(text,encoding='utf-8')
# Reuse exact numerically verified interval drawings, changing only punctuation in their labels.
for name in ['winner_effect.svg','guardrail_effect.svg']:(OUT/name).write_text(no_dots(read('e-book/exports/v04/'+name)),encoding='utf-8')
model='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 336" role="img" aria-label="트리아타시스를 실행하는 TRI-V: 정화, 해체와 입체화, 언어의 전환. 필요하면 앞선 단계로 돌아간다."><rect width="720" height="336" fill="white"/><g fill="#162B33" font-family="Malgun Gothic,sans-serif"><text x="22" y="32" font-size="24">트리아타시스를 실행하는 세 단계</text><text x="22" y="84" font-size="22">정화</text><text x="260" y="84" font-size="20" fill="#125E59">Variable Control</text><text x="22" y="116" font-size="19">무엇을 비교했고, 같은 방식으로 관측했는가</text><text x="22" y="166" font-size="22">해체와 입체화</text><text x="260" y="166" font-size="20" fill="#125E59">Vector Segmentation</text><text x="22" y="198" font-size="19">전체와 고객별 차이는 어디에서 생겼는가</text><text x="22" y="248" font-size="22">언어의 전환</text><text x="260" y="248" font-size="20" fill="#125E59">Value-Linked Decision</text><text x="22" y="280" font-size="19">비용과 위험을 고려하면 무엇을 선택할 것인가</text><text x="22" y="326" font-size="18" fill="#526168">비교나 운영의 문제가 드러나면 앞선 단계로 돌아가 다시 설계한다.</text></g><path d="M22 132 H680 M22 214 H680" stroke="#526168" stroke-width=".6"/></svg>'''
(OUT/'tri_v_method.svg').write_text(model,encoding='utf-8')
css='''*{box-sizing:border-box}body{margin:0;background:#F6F4EF;color:#162B33;font:18px/1.9 "Malgun Gothic","Apple SD Gothic Neo",sans-serif;word-break:keep-all;overflow-wrap:anywhere}main{max-width:900px;margin:auto;padding:42px}h1,h2{line-height:1.5;letter-spacing:-.025em}h1{font-size:31px;margin:2em 0 1em}h2{font-size:25px;margin:1.8em 0 1em}p{margin:.55em 0;text-indent:1em}a{color:#125E59;text-underline-offset:3px}a:focus-visible{outline:3px solid #125E59;outline-offset:3px}table{width:100%;border-collapse:collapse;font-size:16px;line-height:1.65;margin:1.3em 0}th,td{border-bottom:1px solid #b6c0bf;padding:8px 6px;text-align:left;vertical-align:top}thead{display:table-header-group}tr{break-inside:avoid}th{color:#162B33;background:#F6F4EF}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#F6F4EF;padding:15px;font-size:16px;line-height:1.6}code{font-family:Consolas,"Malgun Gothic",monospace;font-size:.95em}img,svg{width:100%;height:auto;display:block;margin:1.3em auto;max-width:720px}.cover{min-height:880px;display:flex;flex-direction:column;justify-content:space-between;padding:40px 0}.cover p{text-indent:0}.cover h1{font-size:60px;line-height:1.3;margin:0}.subtitle{font-size:24px;line-height:1.6}.author{font-size:23px}.note{color:#526168;font-size:16px}.contents p{text-indent:0}.contents ol{list-style:none;padding:0}.contents li{margin:.7em 0}.contents a{text-decoration:none}.case-opening{margin-top:2em}ul{list-style:none}@media(max-width:650px){main{padding:22px}.cover{min-height:650px}.cover h1{font-size:44px}table{font-size:14px}td,th{padding:6px 4px}}@page{size:A4;margin:18mm 18mm 20mm}@media print{body{background:white;font-size:12pt;line-height:1.75}main{max-width:none;margin:0;padding:0}h1{font-size:22pt;break-before:auto;page-break-before:auto;break-after:avoid;margin:9mm 0 5mm}h2{font-size:17pt;margin:0 0 5mm;break-after:avoid}p{margin:.45em 0;orphans:3;widows:3}table{font-size:12pt;line-height:1.55;margin:5mm 0}th,td{padding:2mm 1.1mm}pre,code{font-size:12pt}.cover{height:250mm;min-height:0;padding:12mm 0;break-after:page}.cover h1{font-size:36pt;break-before:auto;page-break-before:auto}.subtitle{font-size:18pt}.author{font-size:18pt}.note{font-size:12pt}.contents{break-after:page}.contents h1{break-before:auto;page-break-before:auto}.contents li{margin:3mm 0}.case-opening{break-before:auto;page-break-before:auto;margin-top:8mm}.case-first{break-before:auto;page-break-before:auto}svg,img{break-inside:avoid;max-height:98mm;object-fit:contain}a[href^=http]{overflow-wrap:anywhere}}
'''
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'],output_format='html')
for name in ['winner_effect.svg','guardrail_effect.svg','tri_v_method.svg']:
    body=re.sub(r'<img[^>]+src="'+re.escape(name)+r'"[^>]*/?>',lambda m:(OUT/name).read_text(encoding='utf-8'),body)
body=re.sub(r'<h2 id="([^"]+)">(사례\s*([1-6])\s.*?)</h2>',lambda m:f'<h2 class="case-opening'+(' case-first' if m[3]=='1' else '')+f'" id="{m[1]}">{m[2]}</h2>',body)
heads=re.findall(r'<h1 id="([^"]+)">(.*?)</h1>',body)
cover='''<section class="cover"><p>허재혁의 CRM A/B 테스트</p><div><h1>그래서,<br>이 캠페인<br>계속할까요?</h1><p class="subtitle">트리아타시스와 TRI-V로<br>실험의 결과를 판단으로 연결하기</p></div><div><p class="author">허재혁</p><p class="note">저자 검토본 0.5</p></div></section>'''
toc='<nav class="contents" aria-label="목차"><h1>목차</h1><ol>'+''.join(f'<li><a href="#{id}">{label}</a></li>' for id,label in heads)+'</ol></nav>'
full='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>그래서, 이 캠페인 계속할까요? — 트리아타시스와 TRI-V | 허재혁</title><style>'+css+'</style></head><body><main>'+cover+toc+body+'</main></body></html>'
assert not any(x in full for x in forbidden)
assert '<h3' not in full and '<ul' not in full
(OUT/'ebook_review_v05.html').write_text(full,encoding='utf-8')
manifest={'version':'0.5 author review','author':'허재혁','methodology':{'perspective':'트리아타시스 (Tri-Ataxis)','procedure':'TRI-V','phases':['정화 / Variable Control','해체와 입체화 / Vector Segmentation','언어의 전환 / Value-Linked Decision'],'role':'Main argument in chapters1-4, applied throughout all six cases and chapter8; not a newly validated statistical test'},'manuscript_characters':len(text),'chapter_headings':len(heads),'case_headings':6,'other_subheadings':0,'forbidden_middle_dots':0,'source_numeric_analysis_unchanged':True,'source_analysis_sha256':hashlib.sha256((ROOT/'e-book/analysis/winner_v04/core_results.json').read_bytes()).hexdigest(),'editorial_changes':['Method-led complete rewrite, not just a name added in one section','No paragraph-level microheadings or repeated case template headings','No middle dots in new manuscript, HTML or graphic labels','Continuous book prose, tables retained for evidence','All six worked cases retained with numerical and statistical boundaries'],'limits':['Author voice and title still need approval','Human technical/domain review and real reader/rights review pending','This edition revises the main book, not the historical v0.4 companion workbook/card content']}
(OUT/'build_manifest_v05.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
