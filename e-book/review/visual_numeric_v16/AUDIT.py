"""Standalone bounded audit. stdlib only; no project analysis imported/executed."""
from pathlib import Path
import json, math, sqlite3, statistics, hashlib, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
N=statistics.NormalDist()
checks=[]
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def check(name,a,b,tol=1e-8):
    ok=abs(a-b)<=tol if isinstance(a,(float,int)) and not isinstance(a,bool) else a==b
    checks.append(dict(name=name,actual=a,expected=b,tolerance=tol,passed=ok))
def bisect(f,lo,hi):
    fl=f(lo)
    assert fl*f(hi)<=0
    for _ in range(100):
        m=(lo+hi)/2
        if f(m)*fl>0: lo=m; fl=f(lo)
        else: hi=m
    return (lo+hi)/2

def wilson(x,n,alpha):
    p=x/n; z=N.inv_cdf(1-alpha/2); den=1+z*z/n
    mid=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-h,mid+h

def binary(xa,na,xb,nb,alpha=.05):
    a,b=xa/na,xb/nb; la,ua=wilson(xa,na,alpha); lb,ub=wilson(xb,nb,alpha)
    p=(xa+xb)/(na+nb); z=(b-a)/math.sqrt(p*(1-p)*(1/na+1/nb))
    return dict(diff_pp=100*(b-a),ci_low_pp=100*(b-a-math.hypot(b-lb,ua-a)),ci_high_pp=100*(b-a+math.hypot(ub-b,a-la)),p_raw=math.erfc(abs(z)/math.sqrt(2)))

DB=ROOT/'virtual-data/v13/data/jh_motors_v13.sqlite'
c=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
# Raw unique assignments, not outcomes view; inclusive individual windows.
rows=c.execute('''SELECT a.arm, COUNT(*), SUM(EXISTS(SELECT 1 FROM events e WHERE e.assignment_id=a.assignment_id AND e.event_type='test_drive_completed' AND e.event_day BETWEEN a.assigned_day AND a.assigned_day+28)), SUM(EXISTS(SELECT 1 FROM events e WHERE e.assignment_id=a.assignment_id AND e.event_type='consent_withdrawn' AND e.event_day BETWEEN a.assigned_day AND a.assigned_day+28)), SUM(EXISTS(SELECT 1 FROM events e WHERE e.assignment_id=a.assignment_id AND e.event_type='contract_signed' AND e.event_day BETWEEN a.assigned_day AND a.assigned_day+180)) FROM assignments a GROUP BY a.arm ORDER BY a.arm''').fetchall()
groups={r[0]:dict(zip(['n','completed','withdrawn','contracted'],r[1:])) for r in rows}
ledger=load('analysis/winner_v04/core_results.json')
for g in ledger['groups']:
    for k in ['n','completed','withdrawn','contracted']: check('raw/'+g['arm']+'/'+k,groups[g['arm']][k],g[k])
check('preassignment_events',c.execute('SELECT COUNT(*) FROM events e JOIN assignments a USING(assignment_id) WHERE e.event_day<a.assigned_day').fetchone()[0],0)
view=c.execute('SELECT arm,COUNT(*),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm').fetchall()
check('raw_vs_v13_view',rows,view)
core=[]
for r in ledger['primary_family']:
    b,a=r['comparison'].split('-'); ga,gb=groups[a],groups[b]
    v=binary(ga['completed'],ga['n'],gb['completed'],gb['n'],.05/3); v['p_family']=min(1,3*v['p_raw']); v['comparison']=r['comparison']; core.append(v)
    for k in ['diff_pp','ci_low_pp','ci_high_pp']: check(r['comparison']+'/'+k,v[k],r[k])
    check(r['comparison']+'/p_family_relative',v['p_family']/r['p_family'],1.,1e-10)
a,b=groups['A'],groups['B']; guard=binary(a['withdrawn'],a['n'],b['withdrawn'],b['n'])
for k,v in guard.items(): check('guard/'+k,v,ledger['guardrail_exploratory'][k])
c.close()

# Direct constrained-binomial likelihood derivative, interior fixture counts only.
def score(xa,na,xb,nb,d):
    def derivative(q): return xa/q-(na-xa)/(1-q)+xb/(q+d)-(nb-xb)/(1-q-d)
    q=bisect(derivative,max(0.,-d)+1e-12,min(1.,1-d)-1e-12)
    variance=(q*(1-q)/na+(q+d)*(1-q-d)/nb)*(na+nb)/(na+nb-1)
    return ((xb/nb-xa/na)-d)/math.sqrt(variance),q,derivative(q)
fixture=load('exports/v15/counterexample_fixture.json')
fixtures=fixture['cases']
results=load('exports/v15/COUNTEREXAMPLE_RESULTS.json')['cases']
score_results=[]
pairs=list(zip(fixtures,results))
for f,r in list(pairs):
    if 'other_prespecified_group' in f:
        other=dict(f['other_prespecified_group']); other.update(id=r['other_group']['id'],family_size=f['family_size'],guard_margin_pp=f['guard_margin_pp'],minimum_effect_pp=f['minimum_effect_pp'])
        pairs.append((other,r['other_group']))
for f,r in pairs:
    xa,na,xb,nb=f['withdrawn_A'],f['n_A'],f['withdrawn_B'],f['n_B']; alpha=.05/f['family_size']
    z,q,res=score(xa,na,xb,nb,f['guard_margin_pp']/100)
    p=N.cdf(z)
    upper=bisect(lambda d:score(xa,na,xb,nb,d)[0]+N.inv_cdf(1-alpha),xb/nb-xa/na+1e-10,.1)*100
    perf=binary(f['completed_A'],na,f['completed_B'],nb,alpha)
    check(f['id']+'/guard_p',p,r['guard_NI_p'],1e-10)
    check(f['id']+'/guard_upper',upper,r['guard_one_sided_upper_pp'],1e-8)
    check(f['id']+'/likelihood_residual',res,0.,1e-6)
    check(f['id']+'/guard_pass',upper<f['guard_margin_pp'],r['guard_pass'])
    for key,actual,expected in [('effect',perf['diff_pp'],r['difference_pp']),('lower',perf['ci_low_pp'],r['performance_interval_pp'][0]),('upper',perf['ci_high_pp'],r['performance_interval_pp'][1])]: check(f['id']+'/'+key,actual,expected)
    state='protection_review' if upper>=f['guard_margin_pp'] else ('execution_candidate' if perf['ci_low_pp']>=f['minimum_effect_pp'] else 'additional_evidence')
    check(f['id']+'/state',state,r['state'])
    score_results.append(dict(id=f['id'],null_q_A=q,derivative_residual=res,p=p,upper_pp=upper,state=state))

# Pooled-null normal planning power: both tails retained, no arcsine substitution.
def power(n,d):
    pa=.09; pb=pa+d; avg=(pa+pb)/2
    cutoff=N.inv_cdf(.975)*math.sqrt(2*avg*(1-avg)/n)
    se=math.sqrt((pa*(1-pa)+pb*(1-pb))/n)
    return N.cdf((d-cutoff)/se)+N.cdf((-d-cutoff)/se)
plan=load('analysis/development_v15/PLANNING_EXAMPLE.json')['available_plan']
pow20=power(10000,.01); required=math.ceil(bisect(lambda n:power(n,.01)-.8,1000,100000)); mde=bisect(lambda d:power(10000,d)-.8,.001,.05)
planning=dict(power=pow20,required_n_each=required,required_n_total=2*required,additional=2*required-20000,mde=mde,power_previous_integer=power(required-1,.01),power_required_integer=power(required,.01))
for name,a,b in [('power',pow20,plan['power_direct']),('n_each',required,plan['required_n_each']),('n_total',2*required,plan['required_n_total']),('additional',2*required-20000,plan['additional_eligible_customers']),('mde',mde,plan['mde_at_available_n'])]: check('planning/'+name,a,b)
check('planning_export_matches_analysis',load('exports/v15/PLANNING_EXAMPLE.json'),load('analysis/development_v15/PLANNING_EXAMPLE.json'))

svgs=[]
for name in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']:
    path=ROOT/'exports/v15'/name; root=ET.parse(path).getroot()
    texts=[''.join(e.itertext()) for e in root.iter() if e.tag.endswith('text')]
    svgs.append(dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),texts=texts))
# Read actual plotted x-coordinates, invert labeled linear axis.
for name,v,x0,scale in [('winner_effect.svg',core[0],139.,270.),('guardrail_effect.svg',guard,247.,1080.)]:
    root=ET.parse(ROOT/'exports/v15'/name).getroot()
    circles=[e for e in root.iter() if e.tag.endswith('circle')]
    lines=[e for e in root.iter() if e.tag.endswith('line') and e.attrib.get('stroke-width')=='6']
    # Guardrail mapping derived separately from the first two labeled grid positions below.
    ticks=[e for e in root.iter() if e.tag.endswith('text') and e.attrib.get('text-anchor')=='middle']
    t0,t1=ticks[:2]; scale=(float(t1.attrib['x'])-float(t0.attrib['x']))/(float(t1.text)-float(t0.text))
    # Labels in guardrail round -.025 to -.02; use stated full range -.15 to .35 and end ticks.
    if name=='guardrail_effect.svg': scale=(float(ticks[-1].attrib['x'])-float(ticks[0].attrib['x']))/.5
    x0=float(t0.attrib['x'])-float(t0.text)*scale
    for key,coord in [('diff_pp',float(circles[0].attrib['cx'])),('ci_low_pp',float(lines[0].attrib['x1'])),('ci_high_pp',float(lines[0].attrib['x2']))]: check('SVG/'+name+'/'+key,(coord-x0)/scale,v[key],1e-8)

report=dict(scope='v15 bounded separate-code numeric/semantic audit; not full-book validation, not human review',groups=groups,primary=core,guardrail=guard,counterexamples=score_results,planning=planning,svg=svgs,checks=checks,total_checks=len(checks),passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']],limitations=['No scipy/statsmodels installed in current interpreter; stdlib direct calculations only.','No import/exec/call of any historical audit or production analysis.','Score applies only to these five interior fixed-count records; boundary counts and general-purpose solver not validated.','Capacity original demand simulation, financial Welch intervals, historical power grid and Monte Carlo were not rerun.','SVG XML/axis/numeric inspection, not rendered image/pagination inspection.','No old files rewritten; historical LF/CRLF equivalence not asserted.'])
(OUT/'AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# v0.15 수치·그래프 별도 코드 감사','',f"실행 검사 {len(checks)}건, 통과 {report['passed']}건, 불일치 {len(report['failed'])}건. 사람 독립검수나 본책 전체 무오류 판정이 아니다.",'','## 독립 재계산','- v13 SQLite mode=ro: 원배정에서 EXISTS와 개인별 창 양끝을 적용. 3군 × 배정/완료/철회/계약 12개 합계 및 outcomes 뷰 대조.','- 완료 세 대비 pooled z/Bonferroni/Wilson-Newcombe 및 철회 B-A 탐색 95% 재계산.','- 반례 4개와 P02_other 총 5개 고정 카운트: 이항 제약우도 미분 근, MN 보정 score p, 단측 상한 역산, 성과 구간과 표시 상태 대조. 경계 카운트 일반화하지 않음.','- 후속 20,000명: pooled-null 정규 근사의 양쪽 꼬리 합으로 power/MDE 및 정수 최소 n 역산. 기존 함수 미사용.',f'- 계획 재계산: {json.dumps(planning,ensure_ascii=False)}','','## 원문 근거 위치','- exports/v15/ebook_review_v15.md: 274행 후속 표본 계획; 290–294행 6장 원자료/세 대비 계획; 765–792행 12장 DB/집계/방법; 832행 결정문.','- analysis/winner_v04/core_results.json: groups/primary_family/guardrail_exploratory.','- exports/v15/counterexample_fixture.json 및 COUNTEREXAMPLE_RESULTS.json; analysis/development_v15/PLANNING_EXAMPLE.json.','','## 그래프 의미 및 v16 개선','1. winner_effect.svg: 축 pp, 약98.33% CI와 사후 +0.5pp 기준은 적절. 그림 자체에 Wilson–Newcombe, 완료 세 대비 Bonferroni 및 배정 분모 A=21,637/B=22,024를 추가. 점/끝점 숫자도 명시.','2. guardrail_effect.svg: 개별95% 탐색 양측 구간을 안전 비열등성 통과/실패로 해석하지 않도록 유지. 눈금 -0.02/+0.23은 실제 등간격 -0.025/+0.225의 반올림이라 읽기 혼란: -.15,-.05,+.05,+.15,+.25,+.35 같은 일관된 눈금 권장. 증가=악화, 배정 분모와 Newcombe 명시.','3. measurement_v06.svg: 95% Newcombe와 pp 표시 적절. 군당 4,000명 동일 분모, 로그 누락 주입의 별도 합성 실습임을 그림에도 추가. 원장 대조가 모든 현실 측정오류를 복구한다는 일반화 금지.','4. segments_v06.svg: 전체95% 층화 Wald와 상태별97.5% Newcombe를 이미 구분. 전체0.5/0.5 고정 구성, 상태별 군당3,000명/전체 군당6,000명 명시. 개별 구간 차이를 상호작용 유의성으로 대체하지 않음.','5. capacity_v06.svg: 완료 건수와 모형 순가치 만원의 분리 막대, 일60슬롯 고정 수요 조건 명시 적절. 두 열 서로 다른 척도임을 유지하고 0 기준/단위별 눈금 및 모형 기간·총 대상수·10% 정책의 나머지90% 처리를 그림 각주에 명시. 실제 관측 이익/CI 아닌 조건부 결과 표시 유지.','','## 불일치']
lines += [json.dumps(x,ensure_ascii=False) for x in report['failed']] or ['이번 지정 핵심 수치 대조에서 불일치 없음. 전체 책에 이상이 없다는 뜻은 아니다.']
lines += ['','## 미검증/막힘']+['- '+x for x in report['limitations']]
(OUT/'AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(total=report['total_checks'],passed=report['passed'],failed=report['failed'],groups=groups,planning=planning,output=str(OUT)),ensure_ascii=False,indent=2))
