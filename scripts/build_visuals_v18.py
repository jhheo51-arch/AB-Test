"""Reader-first figures: question, visual comparison, defensible takeaway."""
from pathlib import Path
import json,html,hashlib,shutil,re
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v18';O.mkdir(parents=True,exist_ok=True)
for p in (R/'e-book/exports/v17').glob('*.svg'):shutil.copyfile(p,O/p.name.replace('_v17','_v18'))
C=json.loads((R/'e-book/analysis/winner_v04/core_results.json').read_text(encoding='utf-8'));S=json.loads((R/'e-book/analysis/winner_v04/scenario_results.json').read_text(encoding='utf-8'))
INK,TEAL,MUTED,WARM='#142D32','#125E59','#4F625F','#8D4029';GREEN,PEACH='#E3EEE8','#FAE9DD';manifest=[]
class Fig:
 def __init__(self,name,h,title):self.name=name;self.h=h;self.p=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {h}" role="img" font-family="ReaderSans,sans-serif"><title>{html.escape(title)}</title><rect width="900" height="{h}" fill="white"/>'];self.text(24,42,title,32,700)
 def text(self,x,y,s,size=26,weight=500,color=INK,anchor='start',region=None):
  rg=f' data-region="{html.escape(json.dumps(region))}"' if region else '';self.p.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{rg}>{html.escape(str(s))}</text>')
 def rect(self,x,y,w,h,color=GREEN,stroke=None):
  outline=f' stroke="{stroke}" stroke-width="2"' if stroke else '';self.p.append(f'<rect x="{x}" y="{y}" width="{max(0,w)}" height="{h}" rx="4" fill="{color}"{outline}/>')
 def line(self,x1,y1,x2,y2,color=MUTED,width=2,dash=False):self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
 def dot(self,x,y,color=TEAL):self.p.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>')
 def save(self,data):
  self.p.append('</svg>');(O/self.name).write_text(''.join(self.p),encoding='utf-8',newline='\n');manifest.append({'file':self.name,'takeaway':data.pop('takeaway'),'data':data,'source':'Frozen core_results.json or scenario_results.json; display transforms only'})
p=next(r for r in C['primary_family'] if r['comparison']=='B-A');g=C['guardrail_exploratory']
f=Fig('winner_effect.svg',550,'B의 완료율은 높다. 도입 기준 충족은 별개다')
f.text(24,88,'배정 고객 전체의 28일 완료율 / 합성 A/B 비교',26,color=MUTED)
x=lambda v:280+v/12*480
for t in [0,4,8,12]:f.line(x(t),116,x(t),242,'#D1D8D6',1);f.text(x(t),280,str(t)+'%',25,anchor='middle')
for i,(label,rate,n,events,color) in enumerate([('A',p['rate_A'],p['n_A'],p['events_A'],MUTED),('B',p['rate_B'],p['n_B'],p['events_B'],TEAL)]):
 y=132+i*70;f.text(24,y+29,f'{label} {events:,}/{n:,}명',25,700);f.rect(280,y,rate*100/12*480,32,color);f.text(840,y+29,f'{rate*100:.2f}%',30,700,anchor='end')
f.text(24,333,'같은 1,000명 기준으로 환산하면 완료 차이는 약 '+f'{p["diff_pp"]*10:.1f}'+'명',28,700)
f.text(24,378,f'B-A {p["diff_pp"]:+.2f}pp / 구간 [{p["ci_low_pp"]:+.2f}, {p["ci_high_pp"]:+.2f}]pp',26,700)
x2=lambda v:130+(v+.2)/2*680
f.line(x2(0),405,x2(0),456,INK);f.line(x2(.5),405,x2(.5),456,WARM,2,True);f.line(x2(p['ci_low_pp']),430,x2(p['ci_high_pp']),430,TEAL,7);f.dot(x2(p['diff_pp']),430)
f.text(x2(0),500,'0 차이 없음',25);f.text(x2(.5),500,'+0.5pp 사업 문턱(사후 예시)',25,color=WARM)
f.text(24,540,'구간이 문턱 아래도 포함하므로 도입 충분성은 미확인',25,color=MUTED)
f.save({'takeaway':'Completion superiority does not establish exceeding the retrospective business threshold','rates':{'A':p['rate_A'],'B':p['rate_B']},'difference_pp':p['diff_pp'],'interval_pp':[p['ci_low_pp'],p['ci_high_pp']],'normalized_per_1000':p['diff_pp']*10,'normalized_is_not_observed_count':True,'confidence':p['ci_level'],'threshold':.5,'threshold_retrospective':True})
f=Fig('guardrail_effect.svg',370,'철회 차이가 뚜렷하지 않아도 안전 확인은 아니다')
f.text(24,88,'철회율 차이 B-A(pp), 증가가 악화 / 개별 95% 양측 탐색 구간',26,color=MUTED)
x=lambda v:100+(v+.15)/.5*720
f.rect(x(.2),124,x(.35)-x(.2),102,PEACH)
for v in [-.1,0,.1,.2,.3]:f.line(x(v),124,x(v),226,MUTED if v==0 else '#D1D8D6');f.text(x(v),272,f'{v:+.1f}',25,anchor='middle')
f.line(x(.2),124,x(.2),226,WARM,2,True);f.line(x(g['ci_low_pp']),182,x(g['ci_high_pp']),182,TEAL,7);f.dot(x(g['diff_pp']),182)
f.text(24,325,f'추정 {g["diff_pp"]:+.3f}pp / 상한 {g["ci_high_pp"]:+.3f}pp는 +0.2pp를 넘는다',26,700)
f.text(24,365,'+0.2pp는 사후 예시이며 정식 비열등성 판정이 아니다',25,color=WARM)
f.save({'takeaway':'Nonsignificant withdrawal contrast is not demonstrated safety','difference_pp':g['diff_pp'],'interval_pp':[g['ci_low_pp'],g['ci_high_pp']],'threshold_pp':.2,'threshold_retrospective':True,'confidence':.95})
a=S['case4'];f=Fig('measurement_v06.svg',540,'승자가 바뀐 듯 보인 원인은 B의 기록 누락이다')
f.text(24,88,f'B 완료 {a["injected_missing"]}건이 빠진 합성 실습 / 각 군 4,000명',26,color=MUTED)
for panel,(key,title) in enumerate([('log','결함 로그(완료 건수)'),('truth','원장 대사 후(완료 건수)')]):
 left=24+panel*458;f.text(left,142,title,29,700);start=left+56;width=304
 for tick in [0,350,700]:f.line(start+tick/700*width,170,start+tick/700*width,302,'#D1D8D6');f.text(start+tick/700*width,345,str(tick),25,anchor='middle')
 for i,arm in enumerate(['A','B']):
  y=184+i*74;count=a[key]['groups'][arm]['success'];f.text(left,y+25,arm,28,700);f.rect(start,y,count/700*width,30,MUTED if arm=='A' else TEAL);f.text(start+count/700*width+8,y+25,str(count),27,700)
for i,(key,label) in enumerate([('log','로그'),('truth','원장')]):
 r=a[key];v=r['difference_B_minus_A']*100;lo,hi=[t*100 for t in r['newcombe_ci']];f.text(24,408+i*49,f'{label} B-A {v:+.2f}pp / 95% 구간 [{lo:+.2f}, {hi:+.2f}]pp',26)
f.text(24,526,'같은 배정 분모를 지켜도 사건 기록이 빠지면 방향이 뒤집힌다',26,700)
f.save({'takeaway':'Injected missing events reverse the observed direction; this is not a message effect reversal','missing_B':a['injected_missing'],'groups_log':a['log']['groups'],'groups_truth':a['truth']['groups'],'log_effect':a['log']['difference_B_minus_A'],'truth_effect':a['truth']['difference_B_minus_A'],'confidence':.95})
a=S['case5'];f=Fig('segments_v06.svg',540,'전체 평균의 개선이 기존 고객의 개선은 아니다')
f.text(24,88,'완료율 차이 B-A(pp) / 왼쪽은 감소, 오른쪽은 증가',26,color=MUTED)
series=[('전체',a['overall']['stratified_primary']['estimate']*100,[v*100 for v in a['overall']['stratified_primary']['wald_ci']],'95% 층화 Wald'),('신규 고객',a['segments']['new']['difference_B_minus_A']*100,[v*100 for v in a['segments']['new']['newcombe_ci']],'97.5% Newcombe'),('기존 고객',a['segments']['existing']['difference_B_minus_A']*100,[v*100 for v in a['segments']['existing']['newcombe_ci']],'97.5% Newcombe')]
x=lambda v:290+(v+6)/16*540
for i,(label,val,(lo,hi),method) in enumerate(series):
 y=146+i*112;f.text(24,y,label,29,700);f.text(24,y+42,method,25,color=MUTED);f.text(290,y,f'{val:+.2f}pp [{lo:+.2f}, {hi:+.2f}]',26);f.line(x(0),y+25,x(0),y+73,INK);f.rect(min(x(0),x(val)),y+38,abs(x(val)-x(0)),22,GREEN if val>=0 else PEACH);f.line(x(lo),y+49,x(hi),y+49,TEAL if val>=0 else WARM,5);f.dot(x(val),y+49,TEAL if val>=0 else WARM)
for v in [-6,-2,0,4,8,10]:f.text(x(v),472,f'{v:+g}' if v else '0',25,anchor='middle')
f.text(24,514,'고객군별 효과의 차이와 신규 전용 정책의 검증은 구분한다',26,700)
f.save({'takeaway':'An aggregate positive effect coexists with a negative existing-customer effect','series':[{'label':label,'estimate_pp':v,'interval_pp':ci,'method':m} for label,v,ci,m in series],'overall_fixed_weights':[.5,.5]})
policies=[r for r in S['case6']['summaries'] if r['capacity_per_day']==60];policies.sort(key=lambda r:['all_A','pilot_10pct_B','all_B'].index(r['policy']))
f=Fig('capacity_v06.svg',485,'완료가 가장 많아도 순가치는 최대가 아니다')
f.text(24,88,'하루 60슬롯 / 28일, 같은 12,000명 수요의 조건부 모형',26,color=MUTED)
cols=[(220,180,'완료(건)',1600,'completed'),(455,180,'순가치(만원)',2400,'net_value_krw'),(690,180,'미수용률(%)',30,'waiting_fraction_of_requests')]
for left,w,title,maximum,key in cols:f.text(left,143,title,27,700)
for i,r in enumerate(policies):
 y=202+i*91;label={'all_A':'A 전면','pilot_10pct_B':'B 10%, A 90%','all_B':'B 전면'}[r['policy']];f.text(24,y+31,label,26,700)
 for left,w,title,maximum,key in cols:
  value=r[key]/10000 if key=='net_value_krw' else r[key]*100 if key=='waiting_fraction_of_requests' else r[key];text=f'{value:,.1f}' if key=='net_value_krw' else f'{value:.2f}%' if key=='waiting_fraction_of_requests' else f'{value:,}'
  peak=key in ['completed','net_value_krw'] and r[key]==max(row[key] for row in policies)
  f.text(left,y,text+(' 최대' if peak else ''),27,700,color=WARM if key=='waiting_fraction_of_requests' and value>10 else TEAL if peak else INK);f.rect(left,y+12,value/maximum*w,20,PEACH if key=='waiting_fraction_of_requests' and value>10 else TEAL if peak else GREEN,WARM if key=='waiting_fraction_of_requests' and value>10 else TEAL);f.line(left,y+38,left+w,y+38,'#BAC9C1',1)
  if key=='waiting_fraction_of_requests':f.line(left+10/maximum*w,y+8,left+10/maximum*w,y+39,WARM,2,True)
f.text(24,460,'점선 10%는 모형의 보호 기준. B 전면은 27.05%로 넘는다',26,700)
f.save({'takeaway':'Within three modeled policies, all-B maximizes completions but fails the modeled10% unmet-request constraint; pilot has the highest modeled value','rows':policies,'units':['completed','ten_thousand_KRW','percent_of_requests'],'all_zero_based':True,'protective_threshold_percent':10,'observed_field_results':False})
# A cover built around the concrete contrast, not an unexplained set diagram.
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1280" role="img" font-family="ReaderSans,sans-serif"><title>그래서, 이 캠페인 계속할까요?</title><desc>동일한 비교틀의 가치 안내 A와 편의 안내 B. 표지는 비유이며 실제 발송 실적을 나타내지 않는다.</desc><rect width="900" height="1280" fill="#F5F1E8"/>']
def ct(x,y,t,size=28,weight=500,color=INK,anchor='start'):s.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(t)}</text>')
ct(76,98,'CRM A/B 테스트 실무서',26,600);s.append('<path d="M76 130H824" stroke="#125E59" stroke-width="2"/>')
for y,t in [(268,'그래서,'),(410,'이 캠페인'),(552,'계속할까요?')]:ct(70,y,t,91,800)
s.append('<path d="M76 584H634" stroke="#125E59" stroke-width="5"/>');ct(76,650,'차이를 읽고, 실행할 범위를 정하는 법',32,600)
for x,letter,title,sub in [(76,'A','차량 가치 안내','차량의 장점을 전한다'),(466,'B','시승 편의 안내','예약을 편하게 돕는다')]:
 s.append(f'<rect x="{x}" y="720" width="358" height="222" rx="8" fill="white" stroke="#BAC9C1" stroke-width="2"/>');ct(x+28,775,letter,40,700,TEAL);ct(x+28,843,title,32,700);ct(x+28,897,sub,25,color=MUTED)
ct(76,1030,'같은 조건에서 비교하고, 다른 결과를 읽습니다',27);ct(76,1103,'TRI-V',32,750,TEAL);ct(232,1103,'근거와 선택을 연결하는 저자의 방법론',25,color=MUTED);ct(76,1200,'허재혁 지음',27,650);ct(824,1200,'저자 검토본0.18',22,color=MUTED,anchor='end');s.append('</svg>');(O/'cover_A.svg').write_text(''.join(s),encoding='utf-8',newline='\n')
(O/'FIGURE_DATA_V18.json').write_text(json.dumps({'charts':manifest,'count':5,'frozen_inputs':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']},'new_inference_performed':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('Reader-first five charts and concrete-comparison cover created')
