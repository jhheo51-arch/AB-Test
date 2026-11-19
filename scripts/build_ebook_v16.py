"""Visual v16 reader: friendly figures, restrained emphasis and real print footnotes."""
from pathlib import Path
import re,json,html,hashlib,shutil,xml.etree.ElementTree as ET
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v16';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v15/ebook_review_v15.md');text=base;changes=[]
def replace(old,new):
 global text
 assert text.count(old)==1,(old[:70],text.count(old));text=text.replace(old,new);changes.append({'before':old,'after':new,'occurrences':1})
# Existing numerical diagrams are regenerated separately from frozen results.
for p in (ROOT/'e-book/exports/v15').glob('*.svg'):
 if p.name not in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']:shutil.copyfile(p,OUT/p.name)
ET.register_namespace('','http://www.w3.org/2000/svg')
for p in (ROOT/'e-book/design/v16/illustrations').glob('*.svg'):
 r=ET.fromstring(p.read_text(encoding='utf-8'))
 for parent in r.iter():
  for child in list(parent):
   if child.tag.endswith('style'):parent.remove(child)
 (OUT/p.name).write_text(ET.tostring(r,encoding='unicode'),encoding='utf-8',newline='\n')
# A compact reading-page workflow complements the full standalone workflow proposal.
def tt(x,y,s,size=28,weight=500,color='#142D32'):return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(s)}</text>'
s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 670" role="img" aria-label="현재 선택에서 세 축과 되돌림 및 승인 구분까지" font-family="ReaderSans,sans-serif"><rect width="900" height="670" fill="white"/><defs><marker id="wf-arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9" fill="#125E59"/></marker></defs>'
s+='<rect x="28" y="20" width="844" height="76" rx="25" fill="#F5F1E8" stroke="#125E59"/>'+tt(51,67,'먼저 정할 것: 무엇을 비교하고 어디까지 선택할까?',31,700)
for x,lines,bg in [(28,['V1 정화','비교와 측정','해석 가능','일부 지표 제한','비교 보류'],'#E3EEE8'),(326,['V2','해체와 입체화','적용 범위','전체부터 확인','필요할 때만 세분화'],'#E3EEE8'),(624,['V3 언어의 전환','성과 / 사업 / 보호','현재 선택','승인과 책임','다음 확인'],'#FAE9DD')]:
 s+=f'<rect x="{x}" y="132" width="248" height="264" rx="23" fill="{bg}" stroke="#125E59"/>'
 for i,line in enumerate(lines):s+=tt(x+13,174+i*44,line,28,700 if i==0 else 500)
for x in [280,578]:s+=f'<path d="M{x} 262H{x+36}" stroke="#125E59" stroke-width="3" marker-end="url(#wf-arrow)"/>'
s+='<path d="M748 401V436H150V402 M450 436V402" fill="none" stroke="#125E59" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#wf-arrow)"/>'+tt(155,480,'선택을 바꾸는 근거가 비면 해당 질문으로 돌아간다',28)
for x,label in [(28,'실행 후보'),(246,'추가 확인'),(464,'미확대'),(682,'보호 대응')]:s+=f'<rect x="{x}" y="506" width="190" height="48" rx="22" fill="#F5F1E8" stroke="#125E59"/>'+tt(x+18,539,label,28,650)
s+=tt(29,598,'실행 후보 ≠ 실제 승인',28,700,'#8D4029')+tt(29,637,'추가 분석 종료, 통계적 실험 종료, 보호 운영 중단은 다르다',28,600,'#8D4029')+'</svg>'
(OUT/'tri_v_workflow_v16.svg').write_text(s,encoding='utf-8',newline='\n')
replace('![TRI-V 공통 기준과 세 산출물](tri_v_method.svg)','![TRI-V의 선택과 세 축, 되돌림과 승인 구분을 연결한 개념 워크플로우](tri_v_workflow_v16.svg)')
def after(prefix,addition):
 found=[p.strip() for p in text.split('\n\n') if p.strip().startswith(prefix)];assert len(found)==1,prefix;replace(found[0],found[0]+'\n\n'+addition)
after('등록 종료일과 최종 결과 확정일을 따로 적는다.','![모집을 멈춘 시점과 개인별 관측 창의 성숙은 다르다. 날짜와 고객 수를 나타내는 실측 자료가 아닌 개념도다.](observation_maturity_v16.svg)')
# The judgment picture belongs beside the first statistical/business boundary, not every case.
after('회의에는 완료율에서 B가 높았고 정한 완료 가족에서 개선 근거가 있다는 문장을 남긴다.','![관측, 통계적 해석, 사업과 보호 선택은 서로 다른 문장이다. TRI-V에 새 축을 추가한 것이 아닌 개념도다.](three_judgments_v16.svg)')
replace('# 8장 다시 한 건의 결정으로','# 8장 다시 한 건의 결정으로\n\n![기존 여섯 칸은 계획과 결과를 다시 쓰는 서류가 아니라 근거와 선택 및 재검토를 연결하는 기록이다.](decision_record_v16.svg)')
# Let each case introduce its question before an atomic chart; avoid a stranded heading.
for case in [4,5,6]:
 m=re.search(r'(## 사례 '+str(case)+r' [^\n]+\n\n)(!\[[^\n]+\]\([^\n]+\)\n\n)([^\n].*?)(?=\n\n)',text,re.S)
 assert m,case;replace(m[0],m[1]+m[3]+'\n\n'+m[2].strip())
# Typography additions preserve the exact underlying wording.
for phrase in ['B를 채택하지 않더라도 A가 모든 대안 중 최선이라는 답이 나온 것은 아니다.','추가 분석을 멈추는 것, 실험을 종료하는 것, 운영을 중단하는 것은 서로 다르다.','차이를 발견하지 못했다는 결론을 안전 확인으로 바꾸지 않는다.']:
 assert text.count(phrase)==1,phrase;replace(phrase,'<u class="reader-emphasis">'+phrase+'</u>')
# Convert source calls in narrative, not bibliography, into page-bottom notes.
marker='# 참고 자료와 계산의 범위';bodypart,refs=text.split(marker,1)
note_map={'[5][6]':'저자 프로젝트 문서의 기록을 참고했다. 실제 발송 효과나 이번 org 재실행의 증거는 아니다. 서지 [5], [6].','[3]':'블록 설계의 선택 원칙은 NIST 공개 문서를 참고했다. 단순 무작위배정의 보편적 열등을 뜻하지 않는다. 서지 [3].','[8]':'연속 모니터링의 도입 설명만 참고했다. 순차 방법 전체를 구현하거나 증명을 검증한 것은 아니다. 서지 [8].','[7]':'p값만으로 사업이나 정책 결정을 내리지 않는다는 ASA 원칙을 참고했다. 서지 [7].','[1][2]':'Microsoft의 실험 중 및 종료 후 지침을 참고했다. TRI-V의 성과를 인증한 자료는 아니다. 서지 [1], [2].','[4]':'ICH의 추정 질문과 분석 정렬 원칙을 참고했다. 임상 규정을 CRM 규정으로 옮긴 것은 아니다. 서지 [4].'}
notes=[]
pattern='|'.join(re.escape(k) for k in sorted(note_map,key=len,reverse=True))
def note(m):
 number=len(notes)+1;row={'id':f'fn-{number}','number':number,'source_call':m[0],'text':note_map[m[0]]};notes.append(row);return f'<span class="footnote" data-note-id="{row["id"]}">'+html.escape(row['text'])+'</span>'
newbody=re.sub(pattern,note,bodypart)
replace(bodypart,newbody)
for old,new in [('scripts/develop_planning_v15.py','scripts/develop_planning_v15.py'),('scripts/build_ebook_v15.py','scripts/build_ebook_v16.py'),('scripts/prepare_fonts_v15.py','scripts/prepare_fonts_v16.py'),('scripts/verify_ebook_v15_numbers.py','scripts/verify_ebook_v16_numbers.py'),('scripts/render_verify_v15.py','scripts/render_verify_v16.py'),('scripts/verify_v15_integration.py','scripts/verify_v16_integration.py')]:
 if old!=new:replace(old,new)
forbid='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbid)
(OUT/'ebook_review_v16.md').write_text(text,encoding='utf-8',newline='\n')
shutil.copytree(ROOT/'e-book/exports/v15/assets',OUT/'assets',dirs_exist_ok=True)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','counterexample_fixture.json','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json','READ_SCOPE.json','CONCEPT_CHECKS.json','PLANNING_EXAMPLE.json','SELF_CHECK.md']:shutil.copyfile(ROOT/'e-book/exports/v15'/name,OUT/name)
# A raster-free cover proposal is selected for this draft only.
cover=read('e-book/design/v16/covers/cover_A.svg');(OUT/'cover_A.svg').write_text(cover,encoding='utf-8',newline='\n')
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'])
def embed(m):
 name=m[2];svg=(OUT/name).read_text(encoding='utf-8');svg=re.sub(r'<style>.*?</style>','',svg,flags=re.S)
 cls='concept' if name in ['tri_v_workflow_v16.svg','three_judgments_v16.svg','observation_maturity_v16.svg','decision_record_v16.svg'] else 'data' if name in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg'] else 'intro'
 chart_caps={'winner_effect.svg':'배정 분모 A21,637명, B22,024명. 점은 추정, 선은 개별98.33% Wilson–Newcombe 구간(pp). 완료 세 대비 Bonferroni. 점선 +0.5pp는 사후 학습 기준이며 사전 성공 조건이 아니다.','guardrail_effect.svg':'배정 분모 A21,637명, B22,024명. 개별95% Wilson–Newcombe 양측 탐색 구간(pp). 증가가 악화다. 점선 +0.2pp는 사후 예시이며 이 그림만으로 비열등성 안전을 확인하지 않는다.','measurement_v06.svg':'같은 배정 분모인 군당4,000명의 별도 합성 누락 실습. B-A 완료율 차이(pp), 개별95% Newcombe 구간. 원장 대사가 모든 현장 측정 오류를 복구한다는 뜻은 아니다.','segments_v06.svg':'전체는0.5/0.5 고정 구성의95% 층화 Wald, 상태별은97.5% Newcombe 구간(pp). 상태별 군당3,000명, 전체 군당6,000명이다. 구간의 수준과 추정법이 같지 않다.','capacity_v06.svg':'28일, 총12,000명, 일60슬롯의 고정 수요 조건부 모형. B10% 정책의 나머지90%는 A다. 두 패널은 각각0부터 시작하며 단위와 척도가 다르다. 실제 관측 이익이나 신뢰구간이 아니다.'}
 caption=chart_caps.get(name,html.unescape(m[1]))
 return '<figure class="book-figure '+cls+'" data-figure="'+name+'">'+svg+'<figcaption>'+html.escape(caption)+'</figcaption></figure>'
body=re.sub(r'<img[^>]*alt="([^"]*)"[^>]*src="([^"]+\.svg)"[^>]*/?>',embed,body)
body=re.sub(r'<p>(\s*<figure.*?</figure>\s*)</p>',r'\1',body,flags=re.S)
body=re.sub(r'<h1 id="([^"]+)">(\d+)장 (.*?)</h1>',lambda m:f'<h1 class="chapter" id="{m[1]}"><span class="chapter-no">CHAPTER {int(m[2]):02d}</span>{m[2]}장 {m[3]}</h1>',body)
body=re.sub(r'<h2 id="([^"]+)">(사례 [1-6] .*?)</h2>',r'<h2 class="case-opening" id="\1">\2</h2>',body)
body=re.sub(r'<h1 id="([^"]+)">키워드 찾아보기와 설명</h1>',r'<h1 class="glossary-start" id="\1">키워드 찾아보기와 설명</h1>',body)
assert 'class="glossary-start"' in body
pos=body.index('<h1 class="glossary-start"');body=body[:pos]+re.sub(r'<h2 ',r'<h2 class="glossary-term" ',body[pos:])
body=re.sub(r'<p>(<a id="g-[^"]+"></a>)</p>',r'\1',body)
heads=[(m[1],re.sub(r'<span class="chapter-no">.*?</span>','',m[2])) for m in re.finditer(r'<h1[^>]*id="([^"]+)"[^>]*>(.*?)</h1>',body,re.S)]
heads=[(i,re.sub('<[^>]*>','',label)) for i,label in heads]
toc='<nav class="contents" aria-label="목차"><h1>목차</h1>'+''.join(f'<a href="#{i}"><span>{html.escape(label)}</span><span class="folio" data-id="{i}">00</span></a>' for i,label in heads)+'</nav>'
font='@font-face{font-family:ReaderSans;src:url("assets/reader-sans.woff2");font-weight:100 900}@font-face{font-family:ReaderSerif;src:url("assets/reader-serif.woff2");font-weight:100 900}'
basecss=font+'''*{box-sizing:border-box}html,body{margin:0;color:#142D32}body{font:12pt/1.62 ReaderSerif,serif;word-break:keep-all;overflow-wrap:anywhere}h1,h2,h3,th,td,figcaption,.imprint,.contents,.footnote{font-family:ReaderSans,sans-serif}h1{font-size:21pt;line-height:1.34;margin:5mm 0 3mm;break-after:avoid;break-inside:avoid}h2{font-size:15pt;line-height:1.4;margin:4mm 0 2.5mm;break-after:avoid}.chapter-no{display:block;font-size:12pt;letter-spacing:.08em;color:#125E59;margin-bottom:1.5mm}p{margin:.42em 0;text-indent:1em;orphans:3;widows:3}table{width:100%;border-collapse:collapse;font:12pt/1.43 ReaderSans;margin:3.5mm 0}th,td{padding:1.5mm 1mm;border-bottom:1px solid #BAC9C1;text-align:left;vertical-align:top}th{background:#F2F5F1}thead{display:table-header-group}tr{break-inside:avoid}pre{font:12pt/1.4 Consolas,ReaderSans;white-space:pre-wrap;overflow-wrap:anywhere;background:#F2F5F1;padding:2.5mm;break-inside:avoid}code{font:12pt Consolas,ReaderSans}.book-figure{margin:3mm 0 4mm;break-inside:avoid}.book-figure svg{display:block;width:100%;height:auto}.book-figure.concept{max-width:145mm}.book-figure figcaption{font-size:12pt;line-height:1.38;margin-top:1.5mm;color:#4F625F;text-indent:0}svg text{font-family:ReaderSans,sans-serif}.reader-emphasis{text-decoration-thickness:1px;text-underline-offset:3px;text-decoration-color:#125E59}a{color:#125E59;text-underline-offset:2px}.contents{break-after:page}.contents a{display:flex;justify-content:space-between;gap:10mm;text-decoration:none;border-bottom:1px solid #DCE3DE;padding:.9mm 0;line-height:1.38}.folio{min-width:8mm;text-align:right}.imprint{font-size:12pt;line-height:1.5;color:#4F625F;margin-bottom:4mm}.imprint p{text-indent:0;margin:.15em 0}.cover{page:cover;width:190mm;height:270mm;break-after:page;margin:0;padding:0}.cover svg{display:block;width:100%;height:100%}.footnote{font-size:12pt;line-height:1.35;text-indent:0}.footnote{float:footnote}::footnote-call{content:counter(footnote);font-size:8pt;vertical-align:super;line-height:0}::footnote-marker{content:counter(footnote)". ";font-weight:650}.pagedjs_page{margin:0!important;box-shadow:none!important}.glossary-term{margin-top:2.3mm}a[id^="g-"]{display:block;height:0;line-height:0;break-after:avoid}'''
pagecss='''@page{size:190mm 270mm;margin:14mm 15mm 16mm;@bottom-right{content:counter(page);font:10pt ReaderSans;color:#4F625F}@footnote{float:bottom;border-top:1px solid #9CAEA6;padding-top:1.8mm}}@page cover{margin:0;@bottom-right{content:none}}'''
imprint='<section class="imprint"><p>허재혁의 CRM A/B 테스트 실무서 / 저자 검토본0.16</p><p>가제와 표지 A는 제안이며 최종 확정 전이다. JH Motors는 교육용 가상 회사다.</p></section>'
content='<section class="cover">'+cover+'</section><main class="reading">'+imprint+toc+body+'</main>'
printdoc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>그래서, 이 캠페인 계속할까요? | 허재혁 | v0.16</title><style>'+basecss+pagecss+'</style></head><body class="print-source">'+content+'<script>window.PagedConfig={auto:false};</script><script src="assets/paged.polyfill.min.js"></script></body></html>'
(OUT/'ebook_review_v16_print.html').write_text(printdoc,encoding='utf-8',newline='\n')
readcss='html{background:#E3EEE8}.reading{max-width:900px;margin:auto;padding:35px 38px;background:white}.cover{max-width:900px;width:100%;height:auto;aspect-ratio:900/1280;margin:auto}.footnote{display:inline;color:#4F625F;font-size:12pt}.footnote:before{content:"（주）"}@media(max-width:600px){.reading{padding:24px 18px}.book-figure.concept{max-width:100%}table{font-size:12pt}}'
(OUT/'ebook_review_v16.html').write_text('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TRI-V 읽기본0.16</title><style>'+basecss+readcss+'</style></head><body>'+content+'</body></html>',encoding='utf-8',newline='\n')
(OUT/'FOOTNOTES.json').write_text(json.dumps({'notes':notes,'placement':'PDF page bottom using pinned Paged.js0.4.3; must verify in final render','essential_conditions_remain_in_body':True},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.15','changes':changes,'cover_proposal':'A','final_cover_approved':False,'numerical_inference_changed':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'build_manifest_v16.json').write_text(json.dumps({'version':'0.16 visual author review','source_characters':len(text),'notes':len(notes),'methodology_name':'TRI-V','record_fields':6,'cover':'A proposal pending author confirmation','body_pt':12,'note_pt':12,'body_line_height':1.62,'margins_mm':[14,15,16,15],'old_v15_preserved':True,'extra_diagrams':4,'data_charts':5},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'manuscript':'v0.16','notes':len(notes),'source_characters':len(text),'figures':len(re.findall('<figure ',body))},ensure_ascii=False))
