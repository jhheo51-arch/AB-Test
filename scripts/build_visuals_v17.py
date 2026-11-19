"""Editorial diagrams: shared alignment, readable regions, no invented data."""
from pathlib import Path
import html,json,shutil,xml.etree.ElementTree as ET
ET.register_namespace('','http://www.w3.org/2000/svg')
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v17';O.mkdir(parents=True,exist_ok=True)
for p in (R/'e-book/exports/v16').glob('*.svg'):shutil.copyfile(p,O/p.name)
capacity=O/'capacity_v06.svg';r=ET.fromstring(capacity.read_text(encoding='utf-8'))
for e in r.iter():
 for a in ['y','y1','y2']:
  if e.get(a) and float(e.get(a))>=100:e.set(a,str(float(e.get(a))+18))
vb=r.get('viewBox').split();vb[3]=str(float(vb[3])+18);r.set('viewBox',' '.join(vb));capacity.write_text(ET.tostring(r,encoding='unicode'),encoding='utf-8',newline='\n')
INK='#142D32';TEAL='#125E59';MUTED='#4F625F';WARM='#8D4029';GREEN='#E3EEE8';PEACH='#FAE9DD'
class Figure:
 def __init__(self,name,height,title):self.name=name;self.h=height;self.parts=[f'<title>{html.escape(title)}</title><desc>학습용 개념도이며 실측 데이터가 아니다.</desc><rect width="840" height="{height}" fill="white"/>']
 def box(self,x,y,w,h,color=GREEN):self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{color}" stroke="#BAC9C1"/>');return [x+14,y+12,w-28,h-24]
 def text(self,x,y,t,size=27,weight=500,color=INK,anchor='start',region=None):
  region=f' data-region="{html.escape(json.dumps(region))}"' if region else ''
  self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{color}"{region}>{html.escape(t)}</text>')
 def line(self,x1,y1,x2,y2,dash=False):self.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{TEAL}" stroke-width="2"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
 def save(self):
  s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 {self.h}" role="img" font-family="ReaderSans,sans-serif">'+''.join(self.parts)+'</svg>';ET.fromstring(s);(O/self.name).write_text(s,encoding='utf-8',newline='\n')
f=Figure('tri_v_workflow_v17.svg',600,'TRI-V: 비교 조건에서 선택과 다음 확인까지')
f.text(420,40,'무엇을 비교하고, 어디까지 결정할까?',31,700,anchor='middle')
for y,num,title,sub,lines,col in [(74,'01','정화','비교와 측정',['비교를 유지할 수 있는가?','해석 가능 / 지표 제한 / 비교 보류'],GREEN),(210,'02','해체와 입체화','고객과 적용 범위',['전체의 답을 누구에게 적용할까?','전체부터 읽고 필요할 때만 나눈다'],GREEN),(346,'03','언어의 전환','사업과 보호의 선택',['지금 무엇을 선택할 수 있는가?','선택과 다음 확인을 기록한다'],PEACH)]:
 reg=f.box(30,y,780,114,col);f.text(58,y+49,num,27,700,TEAL,region=reg);f.text(114,y+49,title,29,700,region=reg);f.text(114,y+94,sub,26,color=MUTED,region=reg)
 f.line(358,y+18,358,y+96)
 for i,t in enumerate(lines):f.text(386,y+49+i*45,t,26,region=reg)
 if y<346:f.line(420,y+114,420,y+130);f.parts.append(f'<path d="M414 {y+124}L420 {y+131}L426 {y+124}" fill="none" stroke="{TEAL}" stroke-width="2"/>')
f.text(420,502,'根拠'.replace('根拠','근거')+'가 비면 해당 질문으로 돌아간다',27,anchor='middle')
f.text(420,544,'실행 후보는 실제 승인이 아니다',28,700,WARM,'middle')
f.text(420,582,'분석 종료, 실험 종료, 보호 운영 중단은 구별한다',26,color=MUTED,anchor='middle');f.save()
f=Figure('three_judgments_v17.svg',460,'관측에서 통계로, 통계에서 선택으로')
for i,(title,question,col) in enumerate([('관측','실제로 어떤 차이가 보였나?',GREEN),('통계적 판단','효과와 불확실성은 어느 정도인가?',GREEN),('사업과 보호 판단','비용과 관계 위험까지 감당할 수 있나?',PEACH)]):
 y=20+i*144;reg=f.box(30,y,780,126,col);f.text(56,y+49,title,29,700,region=reg);f.text(56,y+100,question,27,region=reg);f.text(774,y+72,f'{i+1:02}',29,700,TEAL,'end',reg)
f.save()
f=Figure('observation_maturity_v17.svg',440,'모집이 끝나도 관측은 계속된다')
f.text(420,40,'모집 종료와 결과 확정을 따로 적는다',31,700,anchor='middle')
f.line(180,120,780,120);f.line(480,108,480,344,True)
f.text(480,92,'모집 종료',27,700,TEAL,'middle')
for y,title,start,end in [(172,'먼저 배정',190,570),(278,'나중 배정',350,730)]:
 f.text(30,y+9,title,28,700);f.parts.append(f'<rect x="{start}" y="{y-18}" width="{end-start}" height="34" rx="4" fill="{GREEN}"/>');f.text(start,y+64,'배정',26,anchor='middle');f.text(end,y+64,'관측 창 종료',26,anchor='middle')
f.text(420,392,'마지막 고객도 정한 기간을 채워야 한다',28,700,anchor='middle');f.text(420,430,'기간과 길이는 개념 설명이며 실제 날짜가 아니다',26,color=MUTED,anchor='middle');f.save()
f=Figure('decision_record_v17.svg',550,'근거와 선택을 연결하는 여섯 칸')
f.text(420,40,'새 서류보다 기존 근거를 연결하는 기록',31,700,anchor='middle')
items=[('지금 결정할 것','대안과 적용 범위'),('V1 믿고 쓸 근거와 제한','결과와 사용할 수 없는 근거'),('V2 적용 대상','배정, 분석, 적용의 차이'),('V3 현재 선택','보호 조건과 실제 승인 상태'),('추가 확인 또는 생략','선택을 바꿀 확인과 생략 이유'),('다시 검토할 조건','어떤 변화가 선택을 바꾸나?')]
for i,(title,sub) in enumerate(items):
 x=30+(i%2)*400;y=70+(i//2)*140;reg=f.box(x,y,380,126,PEACH if i in [3,4] else GREEN)
 f.text(x+190,y+50,f'{i+1:02}  '+title,28,700,anchor='middle',region=reg);f.text(x+190,y+100,sub,26,anchor='middle',region=reg)
f.text(420,530,'계획과 분석의 원문은 링크로 재사용한다',26,color=MUTED,anchor='middle');f.save()
# Highlight differences symmetrically: neither A nor B is predeclared the winner.
s=(R/'e-book/design/v16/covers/cover_A.svg').read_text(encoding='utf-8').replace('0.16','0.17')
s=s.replace('<circle cx="340" cy="908" r="149" fill="#E3EEE8" stroke="#125E59" stroke-width="3"/><circle cx="559" cy="908" r="149" fill="#F5F1E8" stroke="#125E59" stroke-width="3"/>','<defs><clipPath id="cover-right"><circle cx="559" cy="908" r="149"/></clipPath></defs><circle cx="340" cy="908" r="149" fill="#E3EEE8"/><circle cx="559" cy="908" r="149" fill="#FAE9DD"/><circle cx="340" cy="908" r="149" fill="#F5F1E8" clip-path="url(#cover-right)"/><circle cx="340" cy="908" r="149" fill="none" stroke="#125E59" stroke-width="3"/><circle cx="559" cy="908" r="149" fill="none" stroke="#125E59" stroke-width="3"/>')
s=s.replace('친근한 질문 말풍선과 겹치는 A/B 원. 원의 크기와 겹침은 데이터가 아닌 비교의 개념 표현이다.','차이를 대칭으로 강조한 표지 비유. 실제 고객 집합의 중복이나 인과 효과를 나타내는 집합도가 아니다. A와 B의 우열을 색으로 미리 정하지 않는다.')
(O/'cover_A.svg').write_text(s,encoding='utf-8',newline='\n');# Keep statistical annotations outside the plotting area.
for name in ['winner_effect.svg','guardrail_effect.svg']:
 p=O/name;r=ET.fromstring(p.read_text(encoding='utf-8'))
 for e in r.iter():
  if e.tag.endswith('text') and ''.join(e.itertext()).startswith('추정'):continue
  for attr in ['y','y1','y2','cy']:
   if e.get(attr) and float(e.get(attr))>=80:e.set(attr,str(float(e.get(attr))+42))
 vb=r.get('viewBox').split();vb[3]=str(float(vb[3])+42);r.set('viewBox',' '.join(vb));p.write_text(ET.tostring(r,encoding='unicode'),encoding='utf-8',newline='\n')
import re,hashlib
forest_rows=[]
for name,domain,ticks,labels,subtitle in [
 ('measurement_v06.svg',[-8,6],list(range(-8,7,2)),['누락된 로그','원장 대조 후'],'군당4,000명 / 개별95% Newcombe 구간'),
 ('segments_v06.svg',[-6,10],list(range(-6,11,2)),['전체 / 95% Wald','신규 / 97.5% Newcombe','기존 / 97.5% Newcombe'],'전체는 고정 구성의 층화 추정, 상태별은 사전 고객 상태')]:
 old_path=R/'e-book/exports/v16'/name;old=ET.fromstring(old_path.read_text(encoding='utf-8'));dots=[e for e in old.iter() if e.tag.endswith('circle')];cis=[e for e in old.iter() if e.tag.endswith('path') and e.get('stroke-width')=='4'];values=[e for e in old.iter() if e.tag.endswith('text') and ' pp' in ''.join(e.itertext())]
 assert len(dots)==len(cis)==len(values)==len(labels)
 bottom=132*(len(labels)-1)+246;height=bottom+64;low,high=domain;x=lambda v:435+(v-low)/(high-low)*415;inverse=lambda a:low+(a-225)/395*(high-low)
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {height}" role="img" font-family="ReaderSans,sans-serif"><title>차이와 구간을 별도 열로 읽기</title><rect width="900" height="{height}" fill="white"/>']
 def txt(xx,yy,t,size=26,anchor='start',region=None):
  rg=f' data-region="{html.escape(json.dumps(region))}"' if region else ''
  parts.append(f'<text x="{xx}" y="{yy}" font-size="{size}" fill="{INK}" text-anchor="{anchor}"{rg}>{html.escape(t)}</text>')
 txt(24,38,'기록을 고치면 방향이 바뀐다' if len(labels)==2 else '전체의 개선이 모두의 개선은 아니다',30);txt(24,82,subtitle,26)
 for tick in ticks:
  xx=x(tick);parts.append(f'<path d="M{xx} 104V{bottom}" stroke="{MUTED if tick==0 else "#D1D8D6"}" stroke-width="{2 if tick==0 else 1}"/>');txt(xx,bottom+36,f'{tick:+g}' if tick else '0',26,'middle')
 series=[]
 for i,(dot,ci,value,label) in enumerate(zip(dots,cis,values,labels)):
  match=re.fullmatch(r'M([\d.]+) ([\d.]+)H([\d.]+)',ci.get('d'));assert match
  point=inverse(float(dot.get('cx')));lower=inverse(float(match[1]));upper=inverse(float(match[3]));yy=126+i*132;cy=yy+38;numbers=re.findall(r'[+-]?\d+(?:\.\d+)?',''.join(value.itertext()));assert len(numbers)==3
  region=[16,yy-36,376,140];txt(24,yy,label,28,region=region);txt(24,yy+44,'추정 '+numbers[0]+' pp',26,region=region);txt(24,yy+88,'['+numbers[1]+', '+numbers[2]+'] pp',26,region=region)
  parts.append(f'<path d="M{x(lower)} {cy}H{x(upper)}" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/><circle cx="{x(point)}" cy="{cy}" r="7" fill="{TEAL}"/>');series.append({'label':label,'point_pp_from_vector':point,'lower_pp_from_vector':lower,'upper_pp_from_vector':upper,'printed_numbers_preserved':numbers})
 parts.append('</svg>');(O/name).write_text(''.join(parts),encoding='utf-8',newline='\n');forest_rows.append({'file':name,'source_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(),'domain_pp':domain,'axis_pixels':[435,850],'series':series,'scope':'Inverse of frozen, rounded SVG coordinates; not a new statistical recalculation'})
(O/'GRAPH_LAYOUT_V17.json').write_text(json.dumps(forest_rows,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Four editorial diagrams and five re-aligned quantitative graphics created')
