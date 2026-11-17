"""Read-only source verification plus exploratory educational economics.
uv run --with scipy --with statsmodels scripts/analyze_winner_v04.py
"""
import hashlib,json,math,sqlite3,platform
from pathlib import Path
from statistics import NormalDist
from importlib.metadata import version
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest,confint_proportions_2indep
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/analysis/winner_v04';OUT.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def conn(p):return sqlite3.connect(f'file:{(ROOT/p).as_posix()}?mode=ro',uri=True)
def compare(xa,na,xb,nb,alpha=.05):
    pa,pb=xa/na,xb/nb;d=pb-pa;po=(xa+xb)/(na+nb)
    ownz=d/math.sqrt(po*(1-po)*(1/na+1/nb));ownp=math.erfc(abs(ownz)/math.sqrt(2))
    z,p=proportions_ztest([xb,xa],[nb,na]);assert abs(z-ownz)<1e-12 and abs(p-ownp)<1e-12
    c=NormalDist().inv_cdf(1-alpha/2)
    def wilson(x,n):
        q=x/n;den=1+c*c/n;mid=(q+c*c/(2*n))/den;half=c*math.sqrt(q*(1-q)/n+c*c/(4*n*n))/den
        return mid-half,mid+half
    la,ua=wilson(xa,na);lb,ub=wilson(xb,nb)
    ownci=[d-math.hypot(pb-lb,ua-pa),d+math.hypot(ub-pb,pa-la)]
    ci=confint_proportions_2indep(xb,nb,xa,na,compare='diff',method='newcomb',alpha=alpha)
    assert max(abs(a-b) for a,b in zip(ownci,ci))<1e-12
    return dict(n_A=na,n_B=nb,events_A=xa,events_B=xb,rate_A=pa,rate_B=pb,diff_pp=100*d,relative_lift=d/pa,p_raw=float(p),ci_level=1-alpha,ci_low_pp=100*ci[0],ci_high_pp=100*ci[1])
old=load('e-book/analysis/v02/verified_analysis.json');c=conn('e-book/virtual-data/v01/data/oem_crm.sqlite')
assert c.execute('pragma integrity_check').fetchone()[0]=='ok' and not c.execute('pragma foreign_key_check').fetchall()
case1={}
for field in ['completed','booked','opted_out']:
    rows=c.execute(f'SELECT arm,COUNT(*),SUM({field}) FROM experiment_outcomes GROUP BY arm ORDER BY arm').fetchall()
    a,b=rows;result=compare(a[2],a[1],b[2],b[1]);stored=next(r for r in old['metrics'] if r['metric']==field)
    assert abs(result['diff_pp']-stored['diff_pp'])<1e-10
    et={'completed':'test_drive_completed','booked':'booking','opted_out':'opt_out'}[field]
    raw=dict(c.execute('SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM assignments a JOIN journey_events e USING(assignment_id) WHERE e.event_type=? AND julianday(e.event_at) BETWEEN julianday(a.assigned_at) AND julianday(a.assigned_at)+28 GROUP BY a.arm',(et,)))
    assert raw['A']==a[2] and raw['B']==b[2]
    case1[field]=result
c.close()
planpath=ROOT/'e-book/virtual-data/v03/experiment_plan.json';plan=load('e-book/virtual-data/v03/experiment_plan.json');base=load('e-book/virtual-data/v03/analysis_report.json')
c=conn('e-book/virtual-data/v03/data/jh_motors_v03.sqlite');assert c.execute('pragma integrity_check').fetchone()[0]=='ok' and not c.execute('pragma foreign_key_check').fetchall()
planhash=hashlib.sha256(planpath.read_bytes()).hexdigest();assert json.loads(c.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])==planhash
rows=[dict(zip(['arm','n','booked','completed','withdrawn','contracted'],r)) for r in c.execute('SELECT arm,COUNT(*),SUM(booked_28),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm')];assert rows==base['groups'];g={r['arm']:r for r in rows}
for field,event,window in [('completed','test_drive_completed',28),('booked','booking',28),('withdrawn','consent_withdrawn',28),('contracted','contract_signed',180)]:
    raw=dict(c.execute('SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM events e JOIN assignments a USING(assignment_id) WHERE event_type=? AND event_day BETWEEN assigned_day AND assigned_day+? GROUP BY a.arm',(event,window)))
    assert all(raw[r['arm']]==r[field] for r in rows)
comparisons=[]
for left,right in [('B','A'),('A','H'),('B','H')]:
    a,b=g[right],g[left];r=compare(a['completed'],a['n'],b['completed'],b['n'],alpha=.05/3);r['comparison']=left+'-'+right;r['p_family']=min(1,3*r['p_raw']);comparisons.append(r)
    prior=next(s for s in base['primary_comparisons'] if s['comparison']==r['comparison']);assert abs(prior['ci_low_pp']-r['ci_low_pp'])<1e-10
A,B=g['A'],g['B'];guard=compare(A['withdrawn'],A['n'],B['withdrawn'],B['n'])
# Query assignment outcome records; one message attempt per assigned A/B is verified.
assert c.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0]==sum(r['n'] for r in rows)
assert c.execute('SELECT COUNT(DISTINCT assignment_id) FROM outcomes').fetchone()[0]==sum(r['n'] for r in rows)
message_n=dict(c.execute('SELECT arm,COUNT(*) FROM messages JOIN assignments USING(assignment_id) GROUP BY arm'))
assert message_n['A']==A['n'] and message_n['B']==B['n'] and message_n.get('H',0)==0
attempt_counts=c.execute('SELECT a.arm,COUNT(m.assignment_id) FROM assignments a LEFT JOIN messages m USING(assignment_id) GROUP BY a.assignment_id,a.arm').fetchall()
assert len(attempt_counts)==sum(r['n'] for r in rows)
assert all(n==(0 if arm=='H' else 1) for arm,n in attempt_counts)
vectors={}
for arm in ['A','B','H']:
    data=c.execute('SELECT completed_28,contracted_180 FROM outcomes WHERE arm=?',(arm,)).fetchall()
    x=np.array([v[1]*2000000-v[0]*15000-(20 if arm!='H' else 0) for v in data],dtype=float)
    if arm=='B':x=x-200000/len(x)
    assert abs(float(x.mean())-next(e['synthetic_net_per_assigned'] for e in base['descriptive_economics'] if e['arm']==arm))<1e-7
    vectors[arm]=x
financial=[]
for left,right in [('B','A'),('A','H'),('B','H')]:
    b,a=vectors[left],vectors[right];va,vb=float(a.var(ddof=1)),float(b.var(ddof=1));se=math.sqrt(va/len(a)+vb/len(b));df=(va/len(a)+vb/len(b))**2/((va/len(a))**2/(len(a)-1)+(vb/len(b))**2/(len(b)-1));diff=float(b.mean()-a.mean());crit=float(stats.t.ppf(.975,df))
    check=stats.ttest_ind(b,a,equal_var=False);ownp=float(2*stats.t.sf(abs(diff/se),df));assert abs(float(check.pvalue)-ownp)<1e-12
    financial.append(dict(comparison=left+'-'+right,currency='KRW',diff_krw=diff,ci95_low_krw=diff-crit*se,ci95_high_krw=diff+crit*se,p_unadjusted=ownp,welch_df=df,method='Exploratory individual unadjusted two-sided 95% Welch mean-difference interval; independent assignment units assumed, no stopping/selection/cluster correction; no OEM accounting validation'))
sensitivity=[]
for margin in [500000,1000000,2000000,3000000]:
    means={}
    for arm in ['A','B','H']:
        r=g[arm];cost=message_n.get(arm,0)*20+r['completed']*15000+(200000 if arm=='B' else 0)
        means[arm]=(r['contracted']*margin-cost)/r['n']
    sensitivity.append(dict(assumed_contribution_per_contract=margin,means_krw=means,B_minus_H_krw=means['B']-means['H']))
c.close()
report=dict(version='0.4',source_datasets=['v01 source used in v02 reader','v03 unchanged'],source_plan_sha256=planhash,case1=case1,groups=rows,primary_family=comparisons,guardrail_exploratory=guard,financial_means={k:float(v.mean()) for k,v in vectors.items()},financial_exploratory=financial,financial_sensitivity=sensitivity,independent_checks=['Read-only SQL outcomes versus raw distinct-assignment event counts','Own pooled z and NormalDist Wilson-Newcombe versus statsmodels','Exploratory Welch scipy ttest versus own t/df calculation','Customer-level net means versus previous economic summary'],runtime={'python':platform.python_version(),'scipy':version('scipy'),'statsmodels':version('statsmodels')},limits=['All data and costs synthetic','Business effect 0.5pp and guardrail 0.2pp are retrospective teaching thresholds, not preregistered decisions','Economics intervals exploratory and unadjusted, conditional on fixed contribution/cost assumptions; not real delivered profit','Not human statistical/domain review'])
(OUT/'core_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
