"""Copy frozen v18 figures and apply the approved v19 title hierarchy."""
from pathlib import Path
import json,shutil,html,hashlib
R=Path(__file__).resolve().parents[1];B=R/'e-book/exports/v18';O=R/'e-book/exports/v19';O.mkdir(parents=True,exist_ok=True)
figures=[]
for p in B.glob('*.svg'):
 if p.name=='cover_A.svg':continue
 dest=O/p.name.replace('_v18','_v19');shutil.copyfile(p,dest);figures.append({'source':p.relative_to(R).as_posix(),'output':dest.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'unchanged_bytes':True})
shutil.copyfile(B/'FIGURE_DATA_V18.json',O/'FIGURE_DATA_V19.json')
INK='#142D32';TEAL='#125E59';MUTED='#4F625F';PAPER='#F5F1E8'
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1280" role="img" font-family="ReaderSans,sans-serif"><title>그래서, 이 캠페인 계속할까요?</title><desc>CRM A/B 테스트 실무. TRI-V로 근거를 점검하고 적용 범위와 다음 행동을 정하는 법. 허재혁 지음.</desc><rect width="900" height="1280" fill="'+PAPER+'"/>']
def text(x,y,t,size,weight=500,color=INK,anchor='start'):
 s.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(t)}</text>')
text(74,125,'CRM A/B 테스트 실무',48,750,TEAL)
text(76,185,'자동차 CRM 사례로 배우는 실험과 판단',27,500,MUTED)
s.append('<path d="M76 228H824" stroke="'+TEAL+'" stroke-width="2"/>')
text(70,378,'그래서, 이 캠페인',84,800)
text(70,550,'계속할까요?',104,800)
text(76,642,'TRI-V로 근거를 점검하고',34,600)
text(76,697,'적용 범위와 다음 행동을 정하는 법',34,600)
text(72,922,'TRI-V',92,750,TEAL)
text(76,999,'근거  /  적용 범위  /  다음 행동',30,500,MUTED)
s.append('<path d="M76 1080H824" stroke="'+TEAL+'" stroke-width="2"/>')
text(76,1190,'허재혁 지음',32,650)
text(824,1190,'저자 검토본 0.19',22,500,MUTED,'end')
s.append('</svg>');(O/'cover_A.svg').write_text(''.join(s),encoding='utf-8',newline='\n')
(R/'e-book/design/v19').mkdir(parents=True,exist_ok=True)
(R/'e-book/design/v19/VISUAL_PROVENANCE.json').write_text(json.dumps({'title':'그래서, 이 캠페인 계속할까요?','genre':'CRM A/B 테스트 실무','subtitle':'TRI-V로 근거를 점검하고 적용 범위와 다음 행동을 정하는 법','title_structure_authorized':True,'final_visual_approved':False,'publication_approved':False,'figures':figures,'numeric_inference_changed':False,'rationale':['주제어를 크게 먼저 읽게 한다.','작은 설명 카드를 빼고 제목과 방법론에 위계를 준다.','도표 수치와 기존 세 축 및 여섯 항목은 바꾸지 않는다.']},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Approved title hierarchy applied to cover; existing numerical/conceptual SVG bytes copied unchanged')
