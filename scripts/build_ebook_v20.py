"""Build v20 by replaying three registered stages against v19."""
from pathlib import Path
from collections import OrderedDict,Counter
import re,json,html,shutil,ast,hashlib
import markdown
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v20';D=R/'e-book/manuscript/development_v20'
s=(R/'e-book/exports/v19/ebook_review_v19.md').read_text(encoding='utf-8');sections={};order=[]
for block in re.split(r'(?=^# )',s,flags=re.M):
 if not block.strip():continue
 title=block.splitlines()[0][2:];sections[title]=block;order.append(title)
cut=order.index('찾아보기');main=''.join(sections[k] for k in order[:cut]);original_main=main
stages=[];numeric=lambda t:Counter(re.findall(r'(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?',t))
for name in ['01_COMPRESSION','02_GUIDED_RECORD','03_TRANSFER']:
 entries=json.loads((D/(name+'.json')).read_text(encoding='utf-8'));assert entries
 before=main
 for e in entries:
  assert main.count(e['before'])==1,(name,e['id']);assert e['before']!=e['after'];assert not any(c in e['after'] for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb');main=main.replace(e['before'],e['after'])
 if name=='01_COMPRESSION':assert sum(len(e['after']) for e in entries)<sum(len(e['before']) for e in entries)
 if name=='03_TRANSFER':assert numeric(before)==numeric(main),'Transfer must preserve the numerical multiset while moving design details ahead of answers'
 stages.append({'name':name,'edits':entries,'before_characters':len(before),'after_characters':len(main)})
assert re.findall(r'data-note-id="(fn-\d+)"',main)==re.findall(r'data-note-id="(fn-\d+)"',original_main)
main=re.sub(r'<a id="b-[^"]+"></a>\s*','',main)
main=re.sub(r'\[사례 자료 길잡이\]\([^\n]+\)\s*','',main)
terms=[]
terms=json.loads((R/'e-book/exports/v19/LOOKUP.json').read_text(encoding='utf-8'))['terms']
assert len(terms)==36
aliases={'randomization':['무작위 배정','무작위배정'],'counterfactual':['반사실'],'estimand':['추정 대상'],'itt':['ITT','배정 기준','원래 배정군'],'units':['배정 단위','분석 단위'],'denominator':['분모'],'maturity':['관측 성숙','관측 창'],'srm':['SRM','표본 비율'],'aa':['A/A'],'oec':['OEC','전체 평가 기준'],'primary':['주지표'],'diagnostic':['진단 지표','퍼널을 진단'],'guardrail':['보호 지표','가드레일'],'pvalue':['p값','p-value'],'alpha':['유의수준','제1종'],'power':['검정력','제2종'],'ci':['신뢰구간'],'effect':['pp','상대 효과'],'mde':['MDE','최소 검출'],'business-threshold':['최소 사업 효과','사업 문턱'],'multiplicity':['다중 비교','Bonferroni'],'peeking':['피킹','고정 시점','매일 고정 표본'],'sequential':['순차'],'segments':['세그먼트'],'interaction':['상호작용'],'post-treatment':['처치 후','발송 후 클릭','발송 뒤 클릭'],'holdout':['홀드아웃','미발송'],'incrementality':['증분'],'ltv':['LTV','고객생애가치'],'sensitivity':['민감도'],'interference':['간섭'],'cluster':['군집','지점별'],'did':['이중차분'],'factorial':['요인 설계','다변량'],'bandit':['밴딧'],'twyman':['트와이먼']}
preferred={'randomization':2,'counterfactual':5,'estimand':2,'itt':2,'units':2,'denominator':2,'maturity':6,'srm':2,'aa':9,'oec':9,'primary':2,'diagnostic':9,'guardrail':4,'pvalue':5,'alpha':5,'power':6,'ci':5,'effect':5,'mde':6,'business-threshold':6,'multiplicity':5,'peeking':6,'sequential':6,'segments':3,'interaction':3,'post-treatment':3,'holdout':7,'incrementality':4,'ltv':4,'sensitivity':4,'interference':7,'cluster':2,'did':9,'factorial':9,'bandit':9,'twyman':9}
# Index points to a concrete narrative paragraph, not a guessed page or every occurrence.
paragraphs=main.split('\n\n');body_targets={}
for term in terms:
 key=term['id'][2:];candidates=[];chapter=0
 for n,para in enumerate(paragraphs):
  m=re.match(r'# (\d+)장 ',para.lstrip())
  if m:chapter=int(m[1])
  if chapter and not para.startswith(('#','|','```','![','<a ')) and any(a in re.sub('<[^>]+>','',para) for a in aliases[key]):candidates.append((chapter!=preferred[key],n,chapter))
 if not candidates:
  term['body_id']=None;term['body_chapter']=None;continue
 _,n,chapter=min(candidates);anchor='b-'+key;body_targets.setdefault(n,[]).append(anchor);term['body_id']=anchor;term['body_chapter']=chapter
for n,ids in body_targets.items():paragraphs[n]='\n'.join(f'<a id="{i}"></a>' for i in ids)+'\n\n'+paragraphs[n]
main='\n\n'.join(paragraphs).rstrip()+'\n\n'
short={'g-guardrail':'가드레일','g-srm':'표본 비율 불일치','g-itt':'배정 기준 분석','g-power':'검정력과 제2종 오류','g-effect':'절대 효과와 상대 효과','g-interaction':'상호작용','g-alpha':'유의수준과 제1종 오류','g-factorial':'요인 설계와 다변량 테스트','g-bandit':'다중 팔 밴딧'}
for term in terms:term['display']=short.get(term['id'],term['label'])
terms.sort(key=lambda t:(not bool(re.match('[가-힣]',t['display'])),t['display']))
def folio(ident):return f'<span class="folio" data-id="{ident}">00</span>'
def body_link(t,label=''):
 return '<a href="#'+t['body_id']+'">'+label+folio(t['body_id'])+'</a>' if t['body_id'] else '—'
def index_table(rows):
 lines=[]
 for t in rows:
  lines.append('<tr data-search="'+html.escape(t['label']+' '+t['english']+' '+t['display'])+'"><td><a href="#'+t['id']+'">'+html.escape(t['display'])+'</a></td><td>'+body_link(t)+'</td><td><a href="#'+t['id']+'">'+folio(t['id'])+'</a></td></tr>')
 return '<table class="index-table"><thead><tr><th>용어</th><th>본문</th><th>해설</th></tr></thead><tbody>'+''.join(lines)+'</tbody></table>'
eng={'A/A':'aa','CI':'ci','DID':'did','ITT':'itt','LTV':'ltv','MAB':'bandit','MDE':'mde','MVT':'factorial','OEC':'oec','p-value':'pvalue','Power':'power','SRM':'srm','Guardrail':'guardrail','Holdout':'holdout','Peeking':'peeking'}
index='# 찾아보기\n\n용어 이름을 알면 가나다순에서, 영문 약어만 기억나면 아래 약어에서 찾는다. 본문은 대표 설명으로, 해설은 용어 풀이로 이동한다. 모든 등장 쪽을 나열한 색인은 아니다. 본문 쪽수가 없는 항목은 용어 해설에서 확인한다.\n\n<a id="term-index"></a>\n<div class="lookup-tools"><label>용어 또는 영문 약어 <input id="term-search" type="search" placeholder="예: 검정력, MDE, SRM" /></label><button type="button" id="term-clear">지우기</button><span id="term-result" aria-live="polite"></span></div>\n<div class="index-pair">'+index_table(terms[:18])+index_table(terms[18:])+'</div>\n<div class="english-index"><strong>영문과 약어</strong><p>'+ ' / '.join(f'<a href="#g-{key}">{label}</a>' for label,key in sorted(eng.items()))+'</p></div>\n\n'
glossary='# 용어 해설\n\n용어는 가나다순이며 영문으로 시작하는 항목은 뒤에 둔다. 각 항목의 본문 링크로 돌아가 사례 속 뜻을 확인할 수 있다.\n\n'
for t in terms:
 for_body=body_link(t,'본문 ') if t['body_id'] else '용어 해설에서 확인'
 glossary+=f'<a id="{t["id"]}"></a>\n## {t["display"]}\n\n<div class="term-meta">{html.escape(t["english"])}<span>{for_body} / <a href="#term-index">찾아보기</a></span></div>\n\n{t["definition"]}\n\n'
refs=sections['참고자료와 계산 범위'].replace('# 참고 자료와 계산의 범위','# 참고자료와 계산 범위').replace('앞의 계산 부록','뒤의 계산 부록')
calc=sections['부록 A 계산과 자료'].replace('# 부록 계산과 자료','# 부록 A 계산과 자료')
calc=calc.replace('_v19','_v20').replace('v19_integration','v20_integration')
calc=calc.replace('uv run --with scipy --with statsmodels python scripts/develop_planning_v15.py\n','')
for a,b in [('build_ebook_v16','build_ebook_v20'),('prepare_fonts_v16','prepare_fonts_v20'),('verify_ebook_v16_numbers','verify_ebook_v20_numbers'),('render_verify_v16','render_verify_v20'),('verify_v16_integration','verify_v20_integration')]:calc=calc.replace(a,b)
guide=sections['부록 B 사례와 자료 길잡이'].replace('# 부록 사례와 자료를 찾아가는 길','# 부록 B 사례와 자료 길잡이')
guide=re.sub(r'<a id="materials-case-[1-6]"></a>\[([^\]]+)\]\(#case-[1-6]\) <span class="folio" data-id="case-[1-6]">\d+</span>쪽',r'\1',guide)
for i,label in enumerate(['1 예약과 완료','2 완료와 채택','3 문구와 캠페인 가치','4 측정 역전','5 고객군 효과','6 공유 용량'],1):
 guide=guide.replace('| '+label+' |','| <a id="materials-case-'+str(i)+'"></a>['+label+'](#case-'+str(i)+') '+folio('case-'+str(i))+'쪽 |')
 main=re.sub(r'(## 사례 '+str(i)+r' [^\n]+)',lambda m:m[1]+'\n\n[사례 자료 길잡이](#materials-case-'+str(i)+')',main,count=1)
text=main+index+glossary+refs+'\n\n'+calc+'\n\n'+guide
note_old='실제 발송 효과나 이번 org 재실행의 증거는 아니다.';note_new='실제 발송 효과를 입증하거나 이번 책 작업에서 Salesforce 환경을 다시 검증했다는 뜻은 아니다.'
assert note_old not in text
for stem in ['tri_v_workflow','three_judgments','observation_maturity','decision_record']:text=text.replace(stem+'_v19.svg',stem+'_v20.svg')
assert not any(c in text for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
text=text.rstrip()+'\n'
(O/'ebook_review_v20.md').write_text(text,encoding='utf-8',newline='\n')
shutil.copytree(R/'e-book/exports/v19/assets',O/'assets',dirs_exist_ok=True)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','counterexample_fixture.json','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json','READ_SCOPE.json','CONCEPT_CHECKS.json','PLANNING_EXAMPLE.json','SELF_CHECK.md','FOOTNOTES.json','FIGURE_DATA.json']:shutil.copyfile(R/'e-book/exports/v19'/name,O/name)
figmeta=json.loads((O/'FIGURE_DATA_V20.json').read_text(encoding='utf-8'))
(O/'FIGURE_DATA.json').write_text(json.dumps(figmeta,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
fn=json.loads((O/'FOOTNOTES.json').read_text(encoding='utf-8'))
for n in fn['notes']:n['text']=n['text'].replace(note_old,note_new)
(O/'FOOTNOTES.json').write_text(json.dumps(fn,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'])
oldhtml=(R/'e-book/exports/v19/ebook_review_v19.html').read_text(encoding='utf-8')
# Preserve exact figure captions, including statistical methods and conditions.
caps={m[1]:m[2] for m in re.finditer(r'<figure[^>]*data-figure="([^"]+)".*?<figcaption>(.*?)</figcaption></figure>',oldhtml,re.S)}
def embed(m):
 name=m[2];svg=(O/name).read_text(encoding='utf-8');svg=re.sub(r'<style>.*?</style>','',svg,flags=re.S);old=name.replace('_v20','_v19');cls='concept' if '_v20' in name else 'data' if name in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg'] else 'intro'
 return f'<figure class="book-figure {cls}" data-figure="{name}">'+svg+'<figcaption>'+caps.get(old,html.escape(m[1]))+'</figcaption></figure>'
caps.update({
'winner_effect.svg':'상단은 합성 실험의 배정 고객 전체를 분모로 한 완료율, 하단은 B-A의 개별 98.33% Wilson–Newcombe 구간이다. 완료 세 대비는 Bonferroni 보정했다. 1,000명 환산은 표준화한 비교이지 추가 완료의 실제 관측 건수가 아니다. +0.5pp는 사후 교육용 사업 기준이다.',
'guardrail_effect.svg':'개별 95% Wilson–Newcombe 양측 탐색 구간이다. 철회 증가가 악화다. +0.2pp는 사후 허용 악화 예시이며 이 그림은 사전 비열등성 설계에 따른 안전 판정이 아니다.',
'measurement_v06.svg':'A와 B의 배정 분모는 각각 4,000명이다. B 완료 341건을 누락시킨 별도 합성 실습으로, 전체 고객이나 실제 현장의 복구 성과가 아니다. 구간은 개별 95% Newcombe다.',
'segments_v06.svg':'전체는 0.5/0.5 고정 구성의 95% 층화 Wald, 두 고객 상태는 각각 97.5% Newcombe 구간이다. 상태별 군당 3,000명, 전체 군당 6,000명이다. 고객군별 결과가 새 표적 정책의 효과를 자동 검증하지 않는다.',
'capacity_v06.svg':'같은 28일, 12,000명 수요 세계에서 일 60슬롯의 세 정책을 비교했다. 모든 막대는 0에서 시작하고 단위는 서로 다르다. 미수용률의 분모는 요청 건수다. 고정 조건의 모형값이며 실제 이익이나 신뢰구간이 아니다.'})
body=re.sub(r'<img[^>]*alt="([^"]*)"[^>]*src="([^"]+\.svg)"[^>]*/?>',embed,body)
body=re.sub(r'<p>(\s*<figure.*?</figure>\s*)</p>',r'\1',body,flags=re.S)
body=re.sub(r'<p>((?:<a id="[gb]-[^"]+"></a>\s*)+)</p>',r'\1',body)
body=re.sub(r'<h1 id="([^"]+)">(\d+)장 (.*?)</h1>',lambda m:f'<h1 class="chapter" id="{m[1]}"><span class="chapter-no">CHAPTER {int(m[2]):02d}</span>{m[2]}장 {m[3]}</h1>',body)
for title,cls in [('찾아보기','lookup-start'),('용어 해설','glossary-start'),('참고자료와 계산 범위','references-start'),('부록 A 계산과 자료','appendix-start'),('부록 B 사례와 자료 길잡이','appendix-start')]:body=re.sub(r'<h1 id="([^"]+)">'+re.escape(title)+r'</h1>',lambda m:f'<h1 class="{cls}" id="{m[1]}">{title}</h1>',body)
a=body.index('<h1 class="glossary-start"');b=body.index('<h1 class="references-start"');body=body[:a]+re.sub('<h2 ', '<h2 class="glossary-term" ',body[a:b])+body[b:]
a=body.index('<h1 class="glossary-start"');b=body.index('<h1 class="references-start"')
parts=re.split(r'(?=<a id="g-)',body[a:b]);body=body[:a]+parts[0]+''.join('<section class="term-entry'+(' term-entry-final' if i>=len(parts)-3 else '')+'">'+part+'</section>' for i,part in enumerate(parts[1:]))+body[b:]
def regroup_table(m):
 header,rows_html=m.groups();rows=re.findall(r'<tr>.*?</tr>',rows_html,re.S)
 if '하루 슬롯' in header and len(rows)==9:
  return ''.join('<table class="keep-table policy-table"><caption>하루 '+str(cap)+'슬롯</caption>'+header+'<tbody>'+''.join(rows[i:i+3])+'</tbody></table>' for i,cap in [(0,40),(3,60),(6,90)])
 return '<table'+(' class="keep-table reuse-table"' if '이미 있는 근거와 참조할 것' in header else ' class="keep-table"' if len(rows)<=8 else '')+'>'+header+'<tbody>'+rows_html+'</tbody></table>'
body=re.sub(r'<table>\s*(<thead>.*?</thead>)\s*<tbody>(.*?)</tbody>\s*</table>',regroup_table,body,flags=re.S)
body=re.sub(r'(<p><strong>완성된 한 장 결정문 예시</strong></p>)(.*?)(?=<h1)',r'<section class="worked-record">\1\2</section>',body,flags=re.S)
body=body.replace('<p>결정문을 쓴 뒤','<p><strong>내 사례로 옮길 때.</strong> 결정문을 쓴 뒤')
body=body.replace('<p>이번에는 같은 회사의 후속 실험을 새로 계획한다고 가정해 보자.','<p class="section-kicker">별도 후속 설계: 가용 고객20,000명</p><p>이번에는 같은 회사의 후속 실험을 새로 계획한다고 가정해 보자.')
body=re.sub(r'<h2 id="([^"]+)">(사례 ([1-6]) .*?)</h2>',lambda m:'<a id="case-'+m[3]+'"></a><h2 id="'+m[1]+'">'+m[2]+'</h2>',body)
body=re.sub(r'<p>(https?://[^<\s]+)</p>',lambda m:'<p class="source-url"><a href="'+html.escape(m[1])+'">'+html.escape(m[1])+'</a></p>',body)
body=re.sub(r'<p>\[(\d+)\] (.*?)</p>',r'<p class="reference-title"><strong>[\1]</strong> \2</p>',body,flags=re.S)
body=re.sub(r'(<p[^>]*>(?:(?!</p>).)*</p>\s*<p class="source-url">.*?</p>)',r'<div class="reference-entry">\1</div>',body,flags=re.S)
unit_count=0
def unit_tag(m):
 global unit_count
 tag,attrs=m.groups()
 if tag=='pre' or any(k in attrs for k in ['keep-table','worked-record','term-entry-final']):
  unit_count+=1;return '<'+tag+' data-layout-unit="unit-'+str(unit_count)+'"'+attrs+'>'
 return m[0]
body=re.sub(r'<(pre|table|section)([^>]*)>',unit_tag,body)
heads=[(m[1],re.sub(r'<[^>]*>','',re.sub(r'<span class="chapter-no">.*?</span>','',m[2]))) for m in re.finditer(r'<h1[^>]*id="([^"]+)"[^>]*>(.*?)</h1>',body,re.S)]
contents='<nav class="contents" aria-label="목차"><h1>목차</h1>'+''.join(f'<a href="#{ident}"><span>{label}</span>'+folio(ident)+'</a>' for ident,label in heads)+'</nav>'
font='@font-face{font-family:ReaderSans;src:url("assets/reader-sans.woff2");font-weight:100 900}@font-face{font-family:ReaderSerif;src:url("assets/reader-serif.woff2");font-weight:100 900}'
tree=ast.parse((R/'scripts/build_ebook_v16.py').read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='basecss' for t in n.targets));css=font+ast.literal_eval(node.value.right)
css=css.replace('::footnote-marker{content:counter(footnote)', '::footnote-marker{content:counter(footnote-marker)')
css+='''.book-figure{max-width:150mm;margin:4mm auto 5mm}.book-figure.concept{max-width:150mm}.book-figure.data{max-width:160mm}.book-figure figcaption{text-align:left}.lookup-start,.glossary-start{break-before:page}.index-pair{display:flex;gap:6mm;align-items:flex-start}.index-table{width:calc(50% - 3mm);font:12pt/1.4 ReaderSans;margin:2mm 0;table-layout:fixed}.index-table th,.index-table td{padding:1.1mm .5mm}.index-table th:first-child{width:72%}.index-table th:not(:first-child),.index-table td:not(:first-child){width:14%;text-align:right}.index-table .folio{min-width:0}.english-index{font:12pt/1.6 ReaderSans;margin:3mm 0}.english-index p{text-indent:0}.term-meta{display:flex;gap:4mm;justify-content:space-between;font:12pt/1.35 ReaderSans;color:#4F625F;margin:0 0 2mm}.term-meta>span{white-space:nowrap}.term-meta .folio{min-width:0}.glossary-term{margin:3mm 0 1mm}a[id^="b-"],a[id^="g-"]{display:block;height:0;line-height:0;break-after:avoid}.reference-title{font-family:ReaderSans;margin-top:4mm;text-indent:0}.source-url{font:12pt/1.4 ReaderSans;text-indent:0;overflow-wrap:anywhere;margin:1mm 0 4mm}.lookup-tools{display:none}.keep-table{break-inside:avoid}.policy-table caption{text-align:left;font:600 12pt ReaderSans;padding:2mm 0}.worked-record{break-inside:avoid;border-top:1px solid #BAC9C1;border-bottom:1px solid #BAC9C1;padding:3mm 0;margin:4mm 0;font:12pt/1.45 ReaderSans}.worked-record p{text-indent:0}.reference-entry{break-inside:avoid}.term-entry{font-size:12pt;line-height:1.5}.term-entry-final{break-inside:avoid;page-break-inside:avoid}.term-meta{break-after:avoid}.term-entry p{margin:.3em 0}.term-meta{margin-bottom:1mm}pre{display:inline-block;width:100%;page-break-inside:avoid;vertical-align:top}.section-kicker{font:650 12pt ReaderSans;color:#125E59;text-indent:0;margin-top:4mm;break-after:avoid}'''
css+='''.reuse-table{table-layout:fixed}.reuse-table th:nth-child(1){width:16%}.reuse-table th:nth-child(2){width:45%}.reuse-table th:nth-child(3){width:39%}.reuse-table code{overflow-wrap:anywhere}.analysis-group{font:650 12pt ReaderSans;break-after:avoid;text-indent:0;margin:3mm 0 1mm}'''
pagecss='''@page{size:190mm 270mm;margin:14mm 15mm 16mm;@bottom-right{content:counter(page);font:10pt ReaderSans;color:#4F625F}@footnote{float:bottom;border-top:1px solid #9CAEA6;padding-top:1.8mm}}@page cover{margin:0;@bottom-right{content:none}}'''
cover=(O/'cover_A.svg').read_text(encoding='utf-8');imprint='<section class="imprint"><p>그래서, 이 캠페인 계속할까요? / CRM A/B 테스트 실무 / 허재혁 / 저자 검토본0.20</p><p>제목 구성은 저자의 진행 승인에 따라 적용했다. 표지의 최종 시각과 출간 승인은 별도다. JH Motors는 교육용 가상 회사다.</p></section>'
content='<section class="cover">'+cover+'</section><main class="reading">'+imprint+contents+body+'</main>'
head='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>그래서, 이 캠페인 계속할까요? | 허재혁 | v0.20</title><style>'
(O/'ebook_review_v20_print.html').write_text(head+css+pagecss+'</style></head><body>'+content+'<script>window.PagedConfig={auto:false};</script><script src="assets/paged.polyfill.min.js"></script></body></html>',encoding='utf-8',newline='\n')
reader_css='''html{background:#E3EEE8}.reading{max-width:900px;margin:auto;padding:35px 38px;background:white}.cover{max-width:900px;width:100%;height:auto;aspect-ratio:900/1280;margin:auto}.footnote{float:none;display:inline;color:#4F625F}.footnote:before{content:"（주）"}.lookup-tools{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0;font:16px ReaderSans}.lookup-tools input,.lookup-tools button{min-height:44px;font:inherit;border:1px solid #4F625F;border-radius:4px;padding:8px;background:white;color:#142D32}.lookup-tools button{cursor:pointer}.lookup-tools :focus-visible{outline:3px solid #125E59;outline-offset:3px}@media(max-width:600px){.reading{padding:24px 18px}.index-pair{display:block}.index-table{width:100%}.term-meta{display:block}.term-meta>span{display:block}.book-figure{max-width:100%}.lookup-tools input{max-width:100%}}'''
script='''<script>const input=document.getElementById('term-search');function filterTerms(){const q=input.value.trim().toLocaleLowerCase();let n=0;document.querySelectorAll('.index-table tbody tr').forEach(r=>{r.hidden=!!q&&!r.dataset.search.toLocaleLowerCase().includes(q);if(!r.hidden)n++});document.getElementById('term-result').textContent=n+'개 용어';}input.addEventListener('input',filterTerms);document.getElementById('term-clear').addEventListener('click',()=>{input.value='';filterTerms();input.focus()});filterTerms();</script>'''
(O/'ebook_review_v20.html').write_text(head+css+reader_css+'</style></head><body>'+content+script+'</body></html>',encoding='utf-8',newline='\n')
(O/'LOOKUP.json').write_text(json.dumps({'terms':terms,'aliases':eng,'body_target_policy':'One representative narrative paragraph per term, not every mention','glossary_definitions_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(O/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.19','stages':stages,'stage_order':[p['name'] for p in stages],'prototype':False,'original_main_sha256':hashlib.sha256(original_main.encode()).hexdigest(),'definition_count':36,'numerical_inference_changed':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(O/'build_manifest_v20.json').write_text(json.dumps({'version':'0.20 compression, guided-record and transfer development','source_characters':len(text),'body_pt':12,'note_pt':12,'notes':8,'figure_count':13,'cover':'Previously approved title structure retained; final visual and publication approval pending','prototype':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('Full v20 built in the authorized three-stage order')
