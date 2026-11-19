"""Create the new edition path without changing the v18 inputs."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];S=R/'scripts';D=R/'e-book/manuscript/development_v19';D.mkdir(parents=True,exist_ok=True)
source=(R/'e-book/exports/v18/ebook_review_v18.md').read_text(encoding='utf-8');paras=source.split('\n\n')
pref=[]
for starts,extra in [('책을 따라가며 무엇을 비교하는지',' 독자가 직접 고쳐 쓸 것은 비교 명세와 결과 보고문, 현재 선택을 설명하는 기록이다. 계산 방법의 적정성 검토와 고객 보호 평가, 실제 발송 승인은 각 담당자와 협업해 확인한다. 독자가 써야 할 문장과 담당자에게 요청할 근거를 구분해 읽으면 된다.'),('처음 읽는 독자는 1장부터',' 본문은 결과표와 판단문을 읽는 경로이고, 계산 방법과 구현을 검토하는 경로는 부록 A의 [분석 담당자와 확인할 계산 방법](#analysis-method-notes)으로 나눴다. 분석을 직접 맡는 독자는 두 경로를 함께 확인한다.')]:
 hits=[p for p in paras if p.startswith(starts)];assert len(hits)==1;pref.append({'before':hits[0],'after':hits[0]+extra,'reason':'Define direct writing, professional verification and actual approval as different work.'})
(D/'PREFACE_EDITS.json').write_text(json.dumps(pref,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
base=(S/'build_ebook_v18.py').read_text(encoding='utf-8').replace('v18','v19').replace('V18','V19')
tail=base[base.index('main=re.sub'):]
tail=tail.replace('e-book/exports/v17','e-book/exports/v18').replace('e-book/exports/v18/ebook_review_v17.html','e-book/exports/v18/ebook_review_v18.html')
tail=tail.replace("calc=calc.replace('_v17','_v19').replace('v17_integration','v19_integration')","calc=calc.replace('_v18','_v19').replace('v18_integration','v19_integration')")
tail=tail.replace("guide=sections['부록 B 사례와 자료 길잡이']", "calc=calc.replace('# 부록 A 계산과 자료','# 부록 A 계산과 자료\\n\\n'+appendix_notes,1)\nguide=sections['부록 B 사례와 자료 길잡이']",1)
tail=tail.replace("text.replace(stem+'_v17.svg',stem+'_v19.svg')","text.replace(stem+'_v18.svg',stem+'_v19.svg')")
tail=tail.replace("old=name.replace('_v19','_v17')","old=name.replace('_v19','_v18')")
tail=tail.replace('허재혁의 CRM A/B 테스트 실무서 / 저자 검토본0.18','그래서, 이 캠페인 계속할까요? / CRM A/B 테스트 실무 / 허재혁 / 저자 검토본0.19')
tail=tail.replace('가제와 표지는 제안이며 최종 확정 전이다. JH Motors는 교육용 가상 회사다.','제목 구성은 저자의 진행 승인에 따라 적용했다. 표지의 최종 시각과 출간 승인은 별도다. JH Motors는 교육용 가상 회사다.')
tail=tail.replace('TRI-V 읽기본0.18 | 허재혁','그래서, 이 캠페인 계속할까요? | 허재혁 | v0.19')
tail=tail.replace("' class=\"keep-table\"' if len(rows)<=8 else ''", "' class=\"keep-table reuse-table\"' if '이미 있는 근거와 참조할 것' in header else ' class=\"keep-table\"' if len(rows)<=8 else ''")
tail=tail.replace("pagecss='''@page", "css+='''.reuse-table{table-layout:fixed}.reuse-table th:nth-child(1){width:16%}.reuse-table th:nth-child(2){width:45%}.reuse-table th:nth-child(3){width:39%}.reuse-table code{overflow-wrap:anywhere}.analysis-group{font:650 12pt ReaderSans;break-after:avoid;text-indent:0;margin:3mm 0 1mm}'''\npagecss='''@page")
manifest_line=next(l for l in tail.splitlines() if "MANUSCRIPT_CHANGES.json').write_text" in l)
tail=tail.replace(manifest_line,"(O/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.18','reading_layers':layers,'worked_links':worked,'preface_edits':preface,'prototype':prototype,'original_main_sha256':hashlib.sha256(original_main.encode()).hexdigest(),'technical_source_preserved_in_appendix':True,'definition_count':36,'numerical_inference_changed':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\\n')")
build_line=next(l for l in tail.splitlines() if "build_manifest_v19.json').write_text" in l)
tail=tail.replace(build_line,"(O/'build_manifest_v19.json').write_text(json.dumps({'version':'0.19 reading-path and handoff development','source_characters':len(text),'body_pt':12,'note_pt':12,'notes':8,'figure_count':13,'cover':'Approved title structure applied; final visual and publication approval pending','prototype':prototype},ensure_ascii=False,indent=2),encoding='utf-8',newline='\\n');print('v19 reading edition built; prototype='+str(prototype))")
prefix='''"""Build v19 from the frozen v18 reader and registered content changes."""
from pathlib import Path
from collections import OrderedDict
import re,json,html,shutil,ast,hashlib,sys
import markdown
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v19';O.mkdir(parents=True,exist_ok=True);D=R/'e-book/manuscript/development_v19'
s=(R/'e-book/exports/v18/ebook_review_v18.md').read_text(encoding='utf-8');sections={};order=[]
for block in re.split(r'(?=^# )',s,flags=re.M):
 if not block.strip():continue
 title=block.splitlines()[0][2:];sections[title]=block;order.append(title)
cut=order.index('찾아보기');main=''.join(sections[k] for k in order[:cut]);original_main=main
prototype='--prototype' in sys.argv
preface=json.loads((D/'PREFACE_EDITS.json').read_text(encoding='utf-8'))
for e in preface:
 assert main.count(e['before'])==1;main=main.replace(e['before'],e['after'])
paths=[D/'READING_LAYERS.json',D/'WORKED_LINKS.json'];assert prototype or all(p.exists() for p in paths),'Missing substantive content changes'
layers=[] if prototype else json.loads(paths[0].read_text(encoding='utf-8'));worked=[] if prototype else json.loads(paths[1].read_text(encoding='utf-8'));groups=OrderedDict()
for e in layers:
 assert main.count(e['before'])==1,(e['chapter'],e['before'][:80])
 assert not any(x in e['before'] for x in ['<span','footnote','```','![','<a '])
 main=main.replace(e['before'],e['after']);groups.setdefault(e['appendix_group'],[]).append(e['before'])
for e in worked:
 assert main.count(e['anchor'])==1,(e['chapter'],e['anchor'][:80]);main=main.replace(e['anchor'],e['anchor']+'\\n\\n'+e['text'])
appendix_notes='<a id="analysis-method-notes"></a>\\n\\n## 분석 담당자와 확인할 계산 방법\\n\\n본문에서 결과를 읽고 판단문을 쓰는 흐름과 계산 방법의 적정성 검토를 나누었다. 아래 설명은 해당 본문에서 옮긴 원문이며 기존 분석 조건과 계산 이력을 보존한다. 방법 이름만 다른 자료에 옮겨 붙이지 말고 배정과 추정 대상, 비교 가족과 종료 규칙이 맞는지 분석 담당자와 확인한다.\\n\\n'
for group,paragraphs in groups.items():appendix_notes+='<p class="analysis-group">'+group+'</p>\\n\\n'+'\\n\\n'.join(paragraphs)+'\\n\\n'
'''
(S/'build_ebook_v19.py').write_text(prefix+tail,encoding='utf-8',newline='\n')
for name in ['prepare_fonts','render_verify','verify_visual_geometry']:
 old=S/(name+'_v18.py');new=S/(name+'_v19.py');t=old.read_text(encoding='utf-8').replace('v18','v19').replace('V18','V19').replace('v0.18','v0.19')
 t=t.replace('저자 검토본 0.18','저자 검토본 0.19').replace('저자 검토본0.18','저자 검토본0.19').replace("'version':'0.18 visual author review'","'version':'0.19 reading-path and handoff author review'")
 if name=='render_verify':
  start=t.index(' for old in REVIEW.glob(\'contact_');end=t.index(' selected=',start);t=t[:start]+t[end:]
 new.write_text(t,encoding='utf-8',newline='\n')
t=(S/'verify_ebook_v18_numbers.py').read_text(encoding='utf-8').replace('v18','v19').replace('V18','V19');(S/'verify_ebook_v19_numbers.py').write_text(t,encoding='utf-8',newline='\n')
print('v19 builder and verification entrypoints created; v18 code and exports untouched')
