"""Readable v16 charts from frozen ledgers, with explicit uncertainty and units."""
from pathlib import Path
import json,hashlib,html,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v16';OUT.mkdir(parents=True,exist_ok=True)
core=json.loads((ROOT/'e-book/analysis/winner_v04/core_results.json').read_text(encoding='utf-8'));scenarios=json.loads((ROOT/'e-book/analysis/winner_v04/scenario_results.json').read_text(encoding='utf-8'))
INK='#142D32';MUTED='#4F625F';TEAL='#125E59';WARM='#8D4029'
def t(x,y,s,size=22,anchor='start',color=INK):return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{html.escape(s)}</text>'
def wrap(body,w,h,label):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}" font-family="ReaderSans,sans-serif"><rect width="{w}" height="{h}" fill="white"/>{body}</svg>'
def interval(name,row,domain,ticks,title,level,threshold,threshold_label):
 lo,hi=domain;x=lambda v:85+(v-lo)/(hi-lo)*540
 s=t(18,32,title,25)+t(18,66,level,20)
 for value in ticks:
  at=x(value);s+=f'<line x1="{at}" x2="{at}" y1="82" y2="166" stroke="#C5D1CA"/>'+t(at,193,f'{value:+.2f}',20,'middle',MUTED)
 s+=f'<line x1="{x(0)}" x2="{x(0)}" y1="82" y2="166" stroke="{INK}" stroke-width="2"/><line x1="{x(threshold)}" x2="{x(threshold)}" y1="82" y2="166" stroke="{WARM}" stroke-width="2" stroke-dasharray="7 5"/>'
 s+=f'<line x1="{x(row["ci_low_pp"])}" x2="{x(row["ci_high_pp"])}" y1="135" y2="135" stroke="{TEAL}" stroke-width="7"/><circle cx="{x(row["diff_pp"])}" cy="135" r="7" fill="{TEAL}"/>'
 s+=t(360,106,f'추정 {row["diff_pp"]:+.3f}  [{row["ci_low_pp"]:+.3f}, {row["ci_high_pp"]:+.3f}] pp',20,'middle')
 s+=t(18,229,f'배정 분모 A {row["n_A"]:,}명 / B {row["n_B"]:,}명',20)+t(18,261,'점은 추정, 선은 구간. 단위 pp. 0은 차이 없음.',20)+t(18,293,threshold_label,20,color=WARM)
 if name=='guardrail_effect.svg':s+=t(18,325,'철회 증가가 악화. 이 양측 탐색 구간은 안전 확인이 아니다.',20)
 h=346 if name=='guardrail_effect.svg' else 316
 (OUT/name).write_text(wrap(s,720,h,title),encoding='utf-8',newline='\n');return {'file':name,'source':row,'axis_domain_pp':domain,'axis_ticks_pp':ticks,'threshold_is_retrospective_example':True,'minimum_font_svg':20}
rows=[];primary=next(r for r in core['primary_family'] if r['comparison']=='B-A')
rows.append(interval('winner_effect.svg',primary,[-.2,1.8],[-.2,.3,.8,1.3,1.8],'시승 완료의 차이: B − A','개별98.33% Wilson–Newcombe 구간, 완료 세 대비 Bonferroni',.5,'점선 +0.5pp: 사후 학습 기준이며 사전 성공 조건이 아님'))
rows.append(interval('guardrail_effect.svg',core['guardrail_exploratory'],[-.15,.35],[-.15,-.05,.05,.15,.25,.35],'동의 철회의 차이: B − A','개별95% Wilson–Newcombe 양측 탐색 구간',.2,'점선 +0.2pp: 사후 허용 악화 예시이며 사전 보호 한계가 아님'))
ET.register_namespace('','http://www.w3.org/2000/svg')
for name,footer in [('measurement_v06.svg','같은 배정 분모: 군당4,000명. 별도 합성 누락 실습.'),('segments_v06.svg','전체는0.5/0.5 고정 구성. 상태별 군당3,000명, 전체 군당6,000명.')]:
 r=ET.fromstring((ROOT/'e-book/exports/v15'/name).read_text(encoding='utf-8'));vb=list(map(float,r.get('viewBox').split()));oldh=vb[3]
 for el in r.iter():
  if el.tag.endswith('text') and el.get('font-size') and float(el.get('font-size'))<20:el.set('font-size','20')
  if el.get('fill') in ['#162B33','#142D32']:el.set('fill',INK)
  if el.get('fill') in ['#526168','#4F625F']:el.set('fill',MUTED)
  if el.get('fill')=='#8B431D':el.set('fill',WARM)
 r.append(ET.fromstring(t(12,oldh+24,footer,20)));vb[3]=oldh+40;r.set('viewBox',' '.join(map(str,vb)));r.set('font-family','ReaderSans,sans-serif')
 (OUT/name).write_text(ET.tostring(r,encoding='unicode'),encoding='utf-8',newline='\n');rows.append({'file':name,'source':'Frozen v15 SVG geometry and values unchanged; footer from scenario ledger','minimum_font_svg':20})
c6=scenarios['case6'];candidates=[v for v in c6.values() if isinstance(v,list) and v and isinstance(v[0],dict) and 'capacity_per_day' in v[0]];assert len(candidates)==1
policy=[r for r in candidates[0] if r['capacity_per_day']==60];order=['all_A','pilot_10pct_B','all_B'];policy.sort(key=lambda r:order.index(r['policy']));assert len(policy)==3

s=t(18,34,'같은 수요에서 완료와 모형 가치의 순위가 달라진다',28)
s+=t(200,76,'완료(건)',25)+t(550,76,'모형 순가치(만원)',25)
for value in [0,500,1000,1500]:
 x=200+value/1800*245;s+=f'<line x1="{x}" x2="{x}" y1="95" y2="350" stroke="#C5D1CA"/>'+t(x,108,str(value),24,'middle',MUTED)
for value in [0,1000,2000]:
 x=550+value/2400*300;s+=f'<line x1="{x}" x2="{x}" y1="95" y2="350" stroke="#C5D1CA"/>'+t(x,108,str(value),24,'middle',MUTED)
for i,r in enumerate(policy):
 y=155+i*88;label={'all_A':'A 전면','pilot_10pct_B':'B10%, A90%','all_B':'B 전면'}[r['policy']];s+=t(18,y+28,label,25)
 s+=f'<rect x="200" y="{y}" width="{r["completed"]/1800*245}" height="25" rx="8" fill="{TEAL}"/>'+t(200,y-7,f'{r["completed"]:,}건',25)
 s+=f'<rect x="550" y="{y}" width="{r["net_value_krw"]/10000/2400*300}" height="25" rx="8" fill="{WARM}"/>'+t(550,y-7,f'{r["net_value_krw"]/10000:,.1f}만원',25)
s+=t(18,392,'28일, 총12,000명, 일60슬롯의 고정 수요 모형. 두 패널의 척도는 다르다.',24)+t(18,426,'실제 관측 이익이나 신뢰구간이 아니다. 10% 정책의 나머지90%는 A.',24)
(OUT/'capacity_v06.svg').write_text(wrap(s,900,452,'완료 건수와 조건부 모형 순가치의 별도 영점 막대'),encoding='utf-8',newline='\n');rows.append({'file':'capacity_v06.svg','source_rows':policy,'zero_axes':True,'independent_units':True,'minimum_font_svg':24})
# Move explanatory footer text to real figure captions, shortening atomic image blocks.
for name,cut in [('winner_effect.svg',214),('guardrail_effect.svg',214),('measurement_v06.svg',274),('segments_v06.svg',346),('capacity_v06.svg',366)]:
 r=ET.fromstring((OUT/name).read_text(encoding='utf-8'));removed=[]
 for parent in r.iter():
  for el in list(parent):
   if el.tag.endswith('text') and float(el.get('y','0'))>cut:
    removed.append(''.join(el.itertext()));parent.remove(el)
 vb=r.get('viewBox').split();vb[3]=str(cut);r.set('viewBox',' '.join(vb));(OUT/name).write_text(ET.tostring(r,encoding='unicode'),encoding='utf-8',newline='\n')
 next(row for row in rows if row['file']==name)['footer_text_moved_to_caption']=removed
manifest={'charts':rows,'chart_count':len(rows),'frozen_source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']},'inference_not_changed':True,'styles_are_proposals':True}
(OUT/'FIGURE_DATA.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('Five numerical charts generated from frozen sources, clear units and source conditions.')
