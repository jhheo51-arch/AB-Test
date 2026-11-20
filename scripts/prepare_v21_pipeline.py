"""Prepare v21 as a separate edition; preserve every v20 baseline byte."""
from pathlib import Path
import json,hashlib,re,shutil
from datetime import datetime,timezone,timedelta
R=Path(__file__).resolve().parents[1];S=R/'scripts';D=R/'e-book/manuscript/development_v21';O=R/'e-book/exports/v21';V=R/'e-book/design/v21'
for p in [D,O,V]:p.mkdir(parents=True,exist_ok=True)
inputs=list((R/'e-book/exports/v20').rglob('*'))+[S/n for n in ['build_ebook_v20.py','render_verify_v20.py','prepare_fonts_v20.py','verify_ebook_v20_numbers.py','package_reader_v20.py']]
inputs=[p for p in inputs if p.is_file()];hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
baseline=D/'BASELINE.json'
if baseline.exists():assert json.loads(baseline.read_text(encoding='utf-8'))['hashes']==hashes
else:baseline.write_text(json.dumps({'baseline':'v0.20','created_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'hashes':hashes},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
for p in (R/'e-book/exports/v20').glob('*.svg'):
 raw=p.read_bytes();name=p.name.replace('_v20','_v21')
 if name=='cover_A.svg':raw=raw.replace('저자 검토본 0.20'.encode(),'저자 검토본 0.21'.encode())
 (O/name).write_bytes(raw)
(O/'FIGURE_DATA_V21.json').write_bytes((R/'e-book/exports/v20/FIGURE_DATA_V20.json').read_bytes())
base=(S/'build_ebook_v20.py').read_text(encoding='utf-8');tail=base[base.index('main=re.sub'):]
tail=re.sub(r'v(19|20)',lambda m:'v'+str(int(m[1])+1),tail);tail=tail.replace('V20','V21');tail=re.sub(r'v0\.(19|20)',lambda m:'v0.'+str(int(m[1])+1),tail);tail=tail.replace('저자 검토본0.20','저자 검토본0.21').replace("'version':'0.20 compression, guided-record and transfer development'","'version':'0.21 reading and decision refinement'")
prefix='''"""Build v21 from the frozen v20 manuscript and explicit editorial ledger."""
from pathlib import Path
from collections import OrderedDict,Counter
import re,json,html,shutil,ast,hashlib
import markdown
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v21';D=R/'e-book/manuscript/development_v21'
s=(R/'e-book/exports/v20/ebook_review_v20.md').read_text(encoding='utf-8');sections={};order=[]
for block in re.split(r'(?=^# )',s,flags=re.M):
 if not block.strip():continue
 title=block.splitlines()[0][2:];sections[title]=block;order.append(title)
cut=order.index('찾아보기');main=''.join(sections[k] for k in order[:cut]);original_main=main;stages=[]
entries=json.loads((D/'EDITORIAL_EDITS.json').read_text(encoding='utf-8'))
for e in entries:
 assert main.count(e['before'])==1,e['id'];assert not any(c in e['after'] for c in '\\u00b7\\u2022\\u2027\\u318d\\u22c5\\u30fb');main=main.replace(e['before'],e['after'])
stages.append({'name':'EDITORIAL_EDITS','edits':entries,'before_characters':len(original_main),'after_characters':len(main)})
assert Counter(re.findall(r'data-note-id="(fn-\\d+)"',main))==Counter(re.findall(r'data-note-id="(fn-\\d+)"',original_main))
'''
tail=tail.replace("contents='<nav", "body=re.sub(r'(<h1 class=\"chapter\"[^>]*><span class=\"chapter-no\">CHAPTER 06</span>.*?)(?=<h1 class=\"chapter\")',r'<div class=\"planning-chapter\">\\1</div>',body,flags=re.S)\ncontents='<nav")
tail=tail.replace("cover=(O/'cover_A.svg')", "pagecss+='.planning-chapter p{line-height:1.68}'\ncover=(O/'cover_A.svg')")
tail += "\nfrom reader_features_v21 import install\ninstall(O)\n"
(S/'build_ebook_v21.py').write_text(prefix+tail,encoding='utf-8',newline='\n')
for stem in ['prepare_fonts','render_verify','verify_visual_geometry','verify_ebook_v20_numbers']:
 src=S/(stem+'.py' if stem=='verify_ebook_v20_numbers' else stem+'_v20.py');target=S/src.name.replace('v20','v21');t=src.read_text(encoding='utf-8').replace('v20','v21').replace('V20','V21').replace('0.20 compression and transfer author review','0.21 reading and decision refinement author review').replace('저자 검토본0.20','저자 검토본0.21')
 if stem=='prepare_fonts':t=t.replace('e-book/design/v07/covers/selected_cover.html','e-book/build-inputs/selected_cover.html').replace("ROOT/'e-book/exports/v10/assets'","ROOT/'e-book/exports/v20/assets'").replace('Preserved v0.10 upstream','Preserved v0.20 upstream').replace('integrated v0.19 reader','integrated v0.21 reader')
 target.write_text(t,encoding='utf-8',newline='\n')
print('Prepared v21; frozen v20 files:',len(hashes))
