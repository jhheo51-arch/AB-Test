"""Prepare only the authorized proof corrections; keep v21 unchanged."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];S=R/'scripts';D=R/'e-book/manuscript/development_v22';O=R/'e-book/exports/v22';V=R/'e-book/design/v22'
for p in [D,O,V]:p.mkdir(parents=True,exist_ok=True)
inputs=[p for p in (R/'e-book/exports/v21').rglob('*') if p.is_file()]+[p for p in S.glob('*v21.py') if p.is_file()]+[R/'e-book/manuscript/development_v21/EDITORIAL_EDITS.json']
hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs};p=D/'BASELINE.json'
if p.exists():assert json.loads(p.read_text(encoding='utf-8'))['hashes']==hashes
else:p.write_text(json.dumps({'baseline':'v0.21','created_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'hashes':hashes},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
findings=json.loads((R/'e-book/review/proof_v21/FINDINGS.json').read_text(encoding='utf-8'));edits=[]
for f in findings:
 if f['id']=='F4':continue
 after=f['minimal_change']
 if f['id']=='C1':after='고객 간 자원 간섭이 있으면 개인 비교를 그대로 승인하지 않는다'
 if f['id']=='C2':after='계약 관측만으로 실제 매출을 알 수 없는 한계'
 edits.append({'id':f['id'],'before':f['quote'],'after':after,'classification':f['status'],'reason':f['reason']})
(D/'PROOF_CORRECTIONS.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
shutil.copyfile(R/'e-book/manuscript/development_v21/EDITORIAL_EDITS.json',D/'EDITORIAL_EDITS.json')
for p in (R/'e-book/exports/v21').glob('*.svg'):
 raw=p.read_bytes();name=p.name.replace('_v21','_v22')
 if name=='cover_A.svg':raw=raw.replace('저자 검토본 0.21'.encode(),'저자 검토본 0.22'.encode())
 (O/name).write_bytes(raw)
(O/'FIGURE_DATA_V22.json').write_bytes((R/'e-book/exports/v21/FIGURE_DATA_V21.json').read_bytes())
for stem in ['build_ebook','prepare_fonts','render_verify','verify_visual_geometry','verify_ebook_v21_numbers','reader_features','verify_reader_features','package_reader']:
 src=S/(stem+'.py' if stem=='verify_ebook_v21_numbers' else stem+'_v21.py');t=src.read_text(encoding='utf-8').replace('v21','v22').replace('V21','V22').replace('v0.21','v0.22').replace('저자 검토본0.21','저자 검토본0.22').replace('0.21 reading and decision refinement','0.22 proof correction')
 if stem=='build_ebook':
  needle="(O/'ebook_review_v22.md').write_text"
  injection="for correction in json.loads((D/'PROOF_CORRECTIONS.json').read_text(encoding='utf-8')):\n assert text.count(correction['before'])==1,correction['id'];text=text.replace(correction['before'],correction['after'])\n"
  t=t.replace(needle,injection+needle).replace('Full v22 built in the authorized three-stage order','Full v22 proof corrections built')
 if stem=='reader_features':
  t=t.replace('import re','import re\nfrom record_print_v22 import PRINT_CSS,PRINT_JS',1).replace("s=s.replace('</body>','<script>'+RECORD_JS+'</script></body>')","s=s.replace('</head>',PRINT_CSS+'</head>').replace('</body>','<script>'+RECORD_JS+'</script>'+PRINT_JS+'</body>')")
 if stem=='package_reader':
  t=t.replace('EDITORIAL_NOTES.md','CORRECTION_NOTES.md')
  t=t.replace("start=f'''", "entries['PRINT_VALIDATION.json']=V/'print_validation_v22.json'\nentries['development/PROOF_CORRECTIONS.json']=R/'e-book/manuscript/development_v22/PROOF_CORRECTIONS.json'\nstart=f'''")
  t=t.replace('6장은 기존 결과와 관측 성숙을 먼저 묶고 후속 설계를 이어 배치했습니다. 11장은 저자의 선택 이유로 시작하며 12장은 직접 판단 기록을 작성하는 과제로 바꿨습니다. 기존 정량 자료는 그대로입니다.','이번 판은 검수에서 확인한 참조 오류와 두 표현의 범위, 긴 입력의 인쇄 누락만 고쳤습니다. 입력한 기록이 길면 여러 쪽으로 인쇄됩니다. 빈 양식은 한 쪽을 유지합니다. 기존 정량 자료와 79쪽 결정문은 그대로입니다.')
 (S/src.name.replace('v21','v22')).write_text(t,encoding='utf-8',newline='\n')
print('Frozen v21 input files:',len(hashes),'text corrections:',len(edits))
