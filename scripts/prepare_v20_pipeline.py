"""Prepare v20 without modifying any frozen v19 artifact."""
from pathlib import Path
import json,hashlib
from datetime import datetime,timezone,timedelta
R=Path(__file__).resolve().parents[1];S=R/'scripts';D=R/'e-book/manuscript/development_v20';O=R/'e-book/exports/v20';V=R/'e-book/design/v20';D.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
relocation=json.loads((D/'BASELINE_RELOCATION.json').read_text(encoding='utf-8')) if (D/'BASELINE_RELOCATION.json').exists() else {'paths':[]}
relocated={row['original_path']:row['current_path'] for row in relocation['paths']}
if (D/'BASELINE.json').exists():
 manifest=json.loads((D/'BASELINE.json').read_text(encoding='utf-8'))
 for path,h in manifest['hashes'].items():assert hashlib.sha256((R/relocated.get(path,path)).read_bytes()).hexdigest()==h,path
else:
 inputs=sorted(p for p in (R/'e-book/exports/v19').rglob('*') if p.is_file())+[R/p for p in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json','e-book/virtual-data/v03/experiment_plan.json','e-book/virtual-data/v13/data/jh_motors_v13.sqlite','e-book/packages/JH_CRM_ebook_reader_v19.zip','scripts/build_ebook_v19.py','scripts/render_verify_v19.py']]
 manifest={'baseline':'v0.19','created_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'scope':'Preserved inputs; no new statistical inference','hashes':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
 (D/'BASELINE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
# Copy visual assets, changing only the edition label on the inherited cover.
visuals=[]
for p in (R/'e-book/exports/v19').glob('*.svg'):
 name=p.name.replace('_v19','_v20');raw=p.read_bytes()
 if name=='cover_A.svg':raw=raw.replace('저자 검토본 0.19'.encode(),'저자 검토본 0.20'.encode())
 (O/name).write_bytes(raw);visuals.append({'source':p.relative_to(R).as_posix(),'target':name,'same_bytes':raw==p.read_bytes()})
(O/'FIGURE_DATA_V20.json').write_bytes((R/'e-book/exports/v19/FIGURE_DATA_V19.json').read_bytes())
(V/'VISUAL_PROVENANCE.json').write_text(json.dumps({'source':'v0.19','new_charts':False,'new_inference':False,'assets':visuals},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
base=(R/relocated.get('scripts/build_ebook_v19.py','scripts/build_ebook_v19.py')).read_text(encoding='utf-8').replace('v19','v20').replace('V19','V20').replace('v0.19','v0.20').replace('저자 검토본0.19','저자 검토본0.20')
tail=base[base.index('main=re.sub'):].replace('e-book/exports/v18','e-book/exports/v19').replace('ebook_review_v18.html','ebook_review_v19.html')
tail=tail.replace("calc=calc.replace('_v18','_v20').replace('v18_integration','v20_integration')","calc=calc.replace('_v19','_v20').replace('v19_integration','v20_integration')")
tail=tail.replace("calc=calc.replace('# 부록 A 계산과 자료','# 부록 A 계산과 자료\\n\\n'+appendix_notes,1)\n",'')
tail=tail.replace("old=name.replace('_v20','_v18')","old=name.replace('_v20','_v19')").replace("text.replace(stem+'_v18.svg',stem+'_v20.svg')","text.replace(stem+'_v19.svg',stem+'_v20.svg')")
needle="for i,label in enumerate(['1 예약과 완료'"
pos=tail.index(needle)
tail=tail[:pos]+"guide=re.sub(r'<a id=\"materials-case-[1-6]\"></a>\\[([^\\]]+)\\]\\(#case-[1-6]\\) <span class=\"folio\" data-id=\"case-[1-6]\">\\d+</span>쪽',r'\\1',guide)\n"+tail[pos:]
line=next(l for l in tail.splitlines() if "MANUSCRIPT_CHANGES.json').write_text" in l)
tail=tail.replace(line,"(O/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.19','stages':stages,'stage_order':[p['name'] for p in stages],'prototype':False,'original_main_sha256':hashlib.sha256(original_main.encode()).hexdigest(),'definition_count':36,'numerical_inference_changed':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\\n')")
line=next(l for l in tail.splitlines() if "build_manifest_v20.json').write_text" in l)
tail=tail.replace(line,"(O/'build_manifest_v20.json').write_text(json.dumps({'version':'0.20 compression, guided-record and transfer development','source_characters':len(text),'body_pt':12,'note_pt':12,'notes':8,'figure_count':13,'cover':'Previously approved title structure retained; final visual and publication approval pending','prototype':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\\n');print('Full v20 built in the authorized three-stage order')")
prefix='''"""Build v20 by replaying three registered stages against v19."""
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
stages=[];numeric=lambda t:Counter(re.findall(r'(?<![A-Za-z])[-+]?\\d[\\d,]*(?:\\.\\d+)?',t))
for name in ['01_COMPRESSION','02_GUIDED_RECORD','03_TRANSFER']:
 entries=json.loads((D/(name+'.json')).read_text(encoding='utf-8'));assert entries
 before=main
 for e in entries:
  assert main.count(e['before'])==1,(name,e['id']);assert e['before']!=e['after'];assert not any(c in e['after'] for c in '\\u00b7\\u2022\\u2027\\u318d\\u22c5\\u30fb');main=main.replace(e['before'],e['after'])
 if name=='01_COMPRESSION':assert sum(len(e['after']) for e in entries)<sum(len(e['before']) for e in entries)
 if name=='03_TRANSFER':assert numeric(before)==numeric(main),'Transfer must preserve the numerical multiset while moving design details ahead of answers'
 stages.append({'name':name,'edits':entries,'before_characters':len(before),'after_characters':len(main)})
assert re.findall(r'data-note-id="(fn-\\d+)"',main)==re.findall(r'data-note-id="(fn-\\d+)"',original_main)
'''
(S/'build_ebook_v20.py').write_text(prefix+tail,encoding='utf-8',newline='\n')
for name in ['prepare_fonts','render_verify','verify_visual_geometry','verify_ebook']:
 src=S/(name+'_v19.py')
 if not src.exists():continue
 t=src.read_text(encoding='utf-8').replace('v19','v20').replace('V19','V20').replace('0.19 reading-path and handoff author review','0.20 compression and transfer author review').replace('저자 검토본0.19','저자 검토본0.20')
 (S/(name+'_v20.py')).write_text(t,encoding='utf-8',newline='\n')
t=(S/'verify_ebook_v19_numbers.py').read_text(encoding='utf-8').replace('v19','v20');(S/'verify_ebook_v20_numbers.py').write_text(t,encoding='utf-8',newline='\n')
t=(S/'package_reader_v19.py').read_text(encoding='utf-8').replace('v19','v20').replace('V19','V20').replace('v0.19','v0.20')
t=t.replace("['AUTHOR_DECISION.md','READING_LAYERS.md','WORKED_LINKS.md']","['EDITING_SEQUENCE.md']")
t=t.replace('필수 독해와 분석 구현의 경로를 나누고, 기존 명세의 재사용 및 요청과 회신을 반영한 판단문 수정 과정을 보완했습니다.','반복 설명을 압축한 뒤 같은 설계 기록의 연속 수정을 연결하고, 기존 과제에서 판단 근거를 먼저 고르게 했습니다.')
(S/'package_reader_v20.py').write_text(t,encoding='utf-8',newline='\n')
print('v20 pipeline prepared; frozen inputs',len(manifest['hashes']),'visuals',len(visuals))
