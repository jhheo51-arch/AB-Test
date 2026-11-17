"""Build a source-grounded v0.6 without modifying frozen numeric ledgers."""
import json,re,html,hashlib
from pathlib import Path
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v06';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def load(p):return json.loads(read(p))
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb'
base=read('e-book/exports/v05/ebook_review_v05.md')
main,appendix=base.split('# 부록 계산과 자료',1)
main=main.replace('나는 이런 결과를 다루는 관점을 트리아타시스(Tri-Ataxis)라고 부른다.','나는 이런 결과를 다루는 관점을 트리아타시스(Tri-Ataxis)라고 불러왔다. 이번 판에서는 이 관점을 더 쉽게 전달할 이름으로 ‘맥락항법’을 제안한다. 측정의 조건과 고객의 차이, 실행의 제약이라는 맥락을 읽으며 판단의 경로를 찾는다는 뜻으로 만든 이름이다. 새로운 인과 추론 기법을 뜻하지는 않는다. 이름은 저자 검토를 위한 제안이며 기존의 TRI-V 세 단계는 유지한다.')
main=main.replace('초기 구상에서는 이러한 연결을 밸류-벡터 내비게이션(Value-Vector Navigation)이라고도 표현했다. 이 책에서는 이름을 더 늘리기보다 상위 관점을 트리아타시스, 실행 절차를 TRI-V로 통일한다.','이 책의 상위 관점은 기존 이름인 트리아타시스이고 실행 절차는 TRI-V다. ‘맥락항법’은 둘을 새 독자에게 설명할 방법론 제목의 제안이다. 맥락항법: 비교의 근거에서 실행의 결론까지라는 표현을 시험해 보려 한다. 별개의 네 번째 단계나 새로운 검정법을 추가한 것은 아니다.')
# Autobiographical detail explicitly supplied in the Notion notes, with exposure uncertainty retained.
para='나는 근 1년 동안 토스와 카카오뱅크, 신한은행, 우리은행, 카카오페이 같은 금융 앱과 T-멤버십의 화면을 살펴보는 일이 취미가 됐다. 처음에는 리워드를 모으려는 목적이 컸지만, 점차 같은 행동을 요구하는 화면이 어떻게 다르게 설계되는지 관심이 옮겨갔다. 어떤 안내는 다음 행동을 쉽게 만들었고 어떤 안내는 보상을 확인하는 데 더 많은 탐색을 요구했다. 다만 서로 다른 화면을 봤다는 경험만으로 내가 특정 무작위 실험의 대상이었다고 확인할 수는 없다. 앱 버전이나 개인화 정책의 차이일 수도 있다. 이 경험은 실험 결과의 증거가 아니라 가설의 출발점이다. 편리하게 느낀 화면이 실제 고객의 행동도 개선하는지, 누구에게 편리한지, 그 개선이 회사와 고객에게 어떤 가치로 이어지는지를 묻게 됐다.'
main=main.replace('\nCRM에서도 비슷한 질문이 생긴다.', '\n'+para+'\n\nCRM에서도 비슷한 질문이 생긴다.',1)
review=read('e-book/manuscript/method_review_v06.md')
review=review.replace('# 방법론을 어디까지 믿을 수 있을까','# 11장 맥락항법이라는 제안, 어디까지 유효한가')
review=review.replace('CONSORT 2025는 집단별 효과의 차이를 상호작용으로 직접 살피고, 사전 계획과 사후 분석을 구분하라고 요구한다.','집단별 효과의 차이는 상호작용으로 직접 살피고, 사전 계획과 사후 분석을 구분해야 한다.')
review=review.replace('[5]','')
review=review.split('\n출처 [1]')[0]
review += '\n\n| 방법론의 축 | 이미 확립된 원칙과 겹치는 부분 | 이 책이 제안하는 실무적 연결 |\n|---|---|---|\n| 정화 / Variable Control | 무작위 배정, 블록, 추정 대상, 측정 품질 | 배정 원장과 사건 원장을 CRM 여정에서 함께 대조한다 |\n| 해체와 입체화 / Vector Segmentation | 사전 집단, 효과 이질성, 상호작용과 다중성 | 고객별로 적용 정책을 바꿀 근거와 후속 가설을 구분한다 |\n| 언어의 전환 / Value-Linked Decision | 보호 지표, 실질적 효과, 비용과 채택 판단 | 운영 용량과 관계 위험, 승인 책임을 한 결정에 연결한다 |\n\n이 비교에서 내리는 판단은 명확하다. 현재 관점은 기존 실험 원칙과 어긋나지 않으며 CRM 의사결정을 구조화하는 방법론으로 발전시킬 만하다. 다만 기존에 없던 통계 원리라고 주장할 수 없고, 실제 조직에서 기존 방식보다 낫다는 효과는 아직 검증하지 않았다. ‘충분히 유효하다’는 표현은 사전 명세와 데이터 검증, 다중성 관리, 비용 가정의 공개를 지키는 조건에서 실무 검토 틀로 사용할 수 있다는 범위로 한정한다. 이 조건을 생략하면 세 단계의 이름만 남고 사후 설득 도구가 될 위험이 있다.\n\n제안한 제목 ‘맥락항법’은 비교의 근거와 실행의 결론을 잇는다는 의도를 담는다. 이름의 간결함을 위해 원래 세 축의 의미를 바꾸지는 않는다. 공개 웹에서 맥락항법과 Causeweave의 정확 표현을 검색했지만 같은 A/B 방법론의 선행 사용을 확인하지 못했다. 검색이 유사 단어를 돌려준 경우도 있어 사용 흔적을 충분히 배제한 조사라고 할 수 없다. 학술적 최초성이나 상표 등록 가능성을 확인한 것도 아니다. 따라서 영어 이름을 새로 확정하지 않고 한국어 제목을 저자 검토용 제안으로 남긴다.\n'
# Source URLs are in the book rather than pointing to an absent research file.
sources='''
# 이번 판의 학습 자료와 반영 범위

사용자가 제공한 Notion Studying 페이지를 공개 브라우저에서 마지막 스크롤 위치까지 확인하고 블록별로 수집했다. 중첩 블록의 반복을 포함한 원문 스냅샷은 학습 메모의 기록이며 영상의 검증된 전사본은 아니다. 연결된 강의를 모두 시청했거나 연결 문서를 모두 읽었다는 뜻도 아니다. 메모 속 잘못된 설명을 그대로 인용하는 대신 9장과 10장의 설계와 운영 논의, 용어 설명에 고쳐 반영했다. 앱 관찰 경험은 들어가며에 저자 서사 초안으로 반영하되 실험 노출이 확인된 사례와 구분했다.

학습 메모: https://app.notion.com/p/Studying-41b629822d0b802c9b26e955044690eb?source=copy_link

[1] Microsoft Experimentation Platform, Patterns of Trustworthy Experimentation: During-Experiment Stage, 2021. 본문에서 지표 분류, 안정적인 집단, 날짜별 효과와 중간 모니터링을 확인했다. 정화와 입체화가 기존 원칙과 겹치는 근거로 사용했다.

https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-during-experiment-stage/

[2] Microsoft Experimentation Platform, Patterns of Trustworthy Experimentation: Post-Experiment Stage, 2021. 본문의 측정 변경, 분모, 지표 간 교환, 재실험과 결과 보관 절을 확인했다. 놀라운 결과의 재확인과 조직의 기록, 채택 판단을 확장하는 데 사용했다.

https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/

[3] NIST/SEMATECH, e-Handbook of Statistical Methods, Randomized block designs. 주요 방해 요인을 블록으로 다루고 나머지를 무작위화하는 설명을 확인했다. 모든 노이즈를 제거한다는 해석을 제한하는 근거다.

https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm

[4] ICH E9(R1), Addendum on Estimands and Sensitivity Analysis in Clinical Trials, 2019. 목표 질문과 추정 대상의 속성, 분석 정렬에 관한 A.1과 A.3을 확인했다. 임상시험 규정을 CRM 규정으로 옮기는 것이 아니라 질문과 추정량을 맞추는 원칙으로 참고했다.

https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf

새 이름의 사용 흔적 검색은 공개 웹의 제한된 확인이다. 별도의 학술 체계적 문헌고찰과 상표 조사는 하지 않았다. 본문은 출간 확정본이 아닌 저자 검토본이며 원고와 새 제목의 최종 승인은 저자에게 남아 있다.
'''
# Place added chapters before technical appendix; glossary is genuinely last.
text='\n\n'.join([main,read('e-book/manuscript/study_development_v06.md'),review,'# 부록 계산과 자료'+appendix,sources,read('e-book/manuscript/glossary_v06.md').split('\n---\n')[0]])
text=text.replace('scripts/build_ebook_v05.py','scripts/build_ebook_v06.py').replace('scripts/render_verify_v05.py','scripts/render_verify_v06.py')
# Figures inserted beside the cases they explain.
for n,name,caption in [(4,'measurement_v06.svg','같은 배정 분모에서도 기록 누락은 결론의 방향을 바꾼다. 사례 4의 별도 합성 실습이며 95% Newcombe 구간이다.'),(5,'segments_v06.svg','전체는 고정 구성 0.5/0.5의 층화 Wald 95% 구간, 상태별 값은 두 후속 비교의 Bonferroni 97.5% Newcombe 구간이다. 구간의 수준과 추정법이 같지 않다.'),(6,'capacity_v06.svg','일 60슬롯에서 완료와 순가치가 반대 방향으로 움직인다. 단일 고정 수요 조건의 모형 비교이며 불확실성 구간이나 실제 OEM 이익이 아니다.')]:
 pattern=rf'(^## 사례 {n} .*?$)'
 text=re.sub(pattern,lambda m:m[0]+f'\n\n![{caption}]({name})\n\n'+caption,text,flags=re.M)
assert not any(c in text for c in forbidden)
assert '{{' not in text
(OUT/'ebook_review_v06.md').write_text(text,encoding='utf-8')
s=load('e-book/analysis/winner_v04/scenario_results.json');figdata=[]
def svg(title,rows,xmin,xmax,footer,name):
 W=720;H=150+len(rows)*72;left=225;right=620
 def x(v):return left+(v-xmin)/(xmax-xmin)*(right-left)
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}"><rect width="720" height="{H}" fill="white"/><g font-family="Malgun Gothic,sans-serif" fill="#162B33"><text x="12" y="30" font-size="23">{title}</text>']
 for tick in range(int(xmin),int(xmax)+1,2):
  parts.append(f'<path d="M{x(tick):.2f} 50V{H-65}" stroke="#D1D8D6"/><text x="{x(tick):.2f}" y="{H-40}" font-size="18" text-anchor="middle">{tick:+g}</text>')
 parts.append(f'<path d="M{x(0):.2f} 48V{H-65}" stroke="#526168" stroke-width="2"/>')
 for i,(label,v,lo,hi) in enumerate(rows):
  y=78+i*72
  parts.append(f'<text x="12" y="{y}" font-size="20">{label}</text><path d="M{x(lo):.2f} {y-6}H{x(hi):.2f}" stroke="#125E59" stroke-width="4"/><circle cx="{x(v):.2f}" cy="{y-6}" r="6" fill="#125E59"/><text x="225" y="{y+24}" font-size="18">{v:+.2f} [{lo:+.2f}, {hi:+.2f}] pp</text>')
 parts.append(f'<text x="12" y="{H-9}" font-size="18" fill="#526168">{footer}</text></g></svg>')
 (OUT/name).write_text(''.join(parts),encoding='utf-8');figdata.append({'figure':name,'rows':rows,'source':'scenario_results.json'})
rows=[]
for k,label in [('log','누락된 로그'),('truth','원장 대조 후')]:
 z=s['case4'][k];rows.append((label,z['difference_B_minus_A']*100,*[v*100 for v in z['newcombe_ci']]))
svg('정화: 기록을 고치자 방향이 바뀌었다',rows,-8,6,'B-A 완료율 차이, 개별 95% Newcombe 구간','measurement_v06.svg')
z=s['case5']['overall']['stratified_primary'];rows=[('전체, 사전 구성',100*z['estimate'],*[v*100 for v in z['wald_ci']])]
for k,label in [('new','신규 고객'),('existing','기존 고객')]:
 z=s['case5']['segments'][k];rows.append((label,z['difference_B_minus_A']*100,*[v*100 for v in z['newcombe_ci']]))
svg('입체화: 전체의 개선이 모두의 개선은 아니다',rows,-6,10,'전체 95% 층화 Wald / 상태별 97.5% Newcombe','segments_v06.svg')
rows=[z for z in s['case6']['summaries'] if z['capacity_per_day']==60]
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 370" role="img" aria-label="완료와 순가치의 정책 비교"><rect width="720" height="370" fill="white"/><g font-family="Malgun Gothic,sans-serif" fill="#162B33"><text x="12" y="30" font-size="23">언어의 전환: 더 많은 완료, 더 낮은 순가치</text><text x="220" y="70" font-size="20">완료, 건</text><text x="470" y="70" font-size="20">모형 순가치, 만원</text>']
for i,(z,label) in enumerate(zip(rows,['A 전면','B 10% 파일럿','B 전면'])):
 y=120+i*78;v=z['completed'];profit=z['net_value_krw']/10000
 parts.extend([f'<text x="12" y="{y}" font-size="20">{label}</text>',f'<rect x="220" y="{y-23}" width="{v/1600*180:.2f}" height="24" fill="#125E59"/><text x="220" y="{y+24}" font-size="18">{v:,}건</text>',f'<rect x="470" y="{y-23}" width="{profit/2200*180:.2f}" height="24" fill="#526168"/><text x="470" y="{y+24}" font-size="18">{profit:,.1f}만원</text>'])
parts.append('<text x="12" y="361" font-size="18" fill="#526168">일 60슬롯, 고정 수요 모형 / 실제 관측 이익이나 신뢰구간 아님</text></g></svg>')
(OUT/'capacity_v06.svg').write_text(''.join(parts),encoding='utf-8');figdata.append({'figure':'capacity_v06.svg','rows':rows})
oldhtml=read('e-book/exports/v05/ebook_review_v05.html');css=re.search(r'<style>(.*?)</style>',oldhtml,re.S)[1]
css+='\n.glossary-index{line-height:2} @media print{h2{margin-top:7mm} svg{break-inside:avoid} .contents li{margin:.25em 0} .contents{font-size:11pt}}'
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'],output_format='html')
for name in ['winner_effect.svg','guardrail_effect.svg','tri_v_method.svg']:(OUT/name).write_text(read('e-book/exports/v05/'+name),encoding='utf-8')
for p in OUT.glob('*.svg'):
 body=re.sub(r'<img[^>]+src="'+re.escape(p.name)+r'"[^>]*/?>',lambda m:p.read_text(encoding='utf-8'),body)
body=re.sub(r'<h2 id="([^"]+)">(사례\s*([1-6])\s.*?)</h2>',lambda m:f'<h2 class="case-opening" id="{m[1]}">{m[2]}</h2>',body)
heads=re.findall(r'<h1 id="([^"]+)">(.*?)</h1>',body)
cover='''<section class="cover"><p>허재혁의 CRM A/B 테스트</p><div><h1>그래서,<br>이 캠페인<br>계속할까요?</h1><p class="subtitle">맥락항법: 비교의 근거에서 실행의 결론까지<br>트리아타시스와 TRI-V의 확장</p></div><div><p class="author">허재혁</p><p class="note">저자 검토본 0.6 / 맥락항법은 방법론 제목 제안</p></div></section>'''
toc='<nav class="contents" aria-label="목차"><h1>목차</h1><ol>'+''.join(f'<li><a href="#{i}">{label}</a></li>' for i,label in heads)+'</ol></nav>'
full='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>그래서, 이 캠페인 계속할까요? | 허재혁 | 검토본0.6</title><style>'+css+'</style></head><body><main>'+cover+toc+body+'</main></body></html>'
assert not any(c in full for c in forbidden)
(OUT/'ebook_review_v06.html').write_text(full,encoding='utf-8')
(OUT/'figure_data_v06.json').write_text(json.dumps(figdata,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'version':'0.6 author review','author':'허재혁','proposed_title':'맥락항법: 비교의 근거에서 실행의 결론까지','title_approval':'pending','chapter_headings':len(heads),'case_count':len(re.findall(r'^## 사례 [1-6] ',text,re.M)),'glossary_entries':len(re.findall(r'<a id="g-',text)),'characters':len(text),'numeric_ledger_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']},'source_scope':'Public Notion page scrolled to end; external videos not watched; primary sources checked separately','contrast':{'ink_white':14.71,'teal_white':7.58,'muted_white':6.42,'minimum_paper':5.85},'limits':['Name proposal not author-approved','No novel statistical theory or field-validation claim','Prior workbook and card companions unchanged','Author, human technical, rights and publication review pending']}
(OUT/'build_manifest_v06.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False,indent=2))
