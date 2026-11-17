"""Verify binary-outcome calculations against statsmodels.
Run: uv run --with scipy --with statsmodels scripts/analyze_ebook_cases.py
"""
import csv
import platform
from importlib.metadata import version
import json
import math
import sqlite3
from pathlib import Path
from statistics import NormalDist
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/analysis/v02'
OUT.mkdir(parents=True,exist_ok=True)
con=sqlite3.connect(f'file:{(ROOT/"e-book/virtual-data/v01/data/oem_crm.sqlite").as_posix()}?mode=ro',uri=True)
zcrit=NormalDist().inv_cdf(.975)
def wilson(x,n):
    p=x/n;den=1+zcrit*zcrit/n
    center=(p+zcrit*zcrit/(2*n))/den
    half=zcrit*math.sqrt(p*(1-p)/n+zcrit*zcrit/(4*n*n))/den
    return center-half,center+half
rows=[]
for metric,role in [('completed','primary'),('booked','diagnostic'),('opted_out','guardrail')]:
    raw=con.execute(f'SELECT arm,COUNT(*),SUM({metric}) FROM experiment_outcomes GROUP BY arm ORDER BY arm').fetchall()
    (aa,na,xa),(bb,nb,xb)=raw
    pa,pb=xa/na,xb/nb;d=pb-pa;pool=(xa+xb)/(na+nb)
    z=d/math.sqrt(pool*(1-pool)*(1/na+1/nb));p=math.erfc(abs(z)/math.sqrt(2))
    la,ua=wilson(xa,na);lb,ub=wilson(xb,nb)
    ci=(d-math.sqrt((pb-lb)**2+(ua-pa)**2),d+math.sqrt((ub-pb)**2+(pa-la)**2))
    zz,pp=proportions_ztest([xb,xa],[nb,na],alternative='two-sided')
    independent_ci=confint_proportions_2indep(xb,nb,xa,na,method='newcomb',compare='diff',alpha=.05)
    assert abs(p-float(pp))<1e-12
    assert abs(z-float(zz))<1e-12
    assert max(abs(a-b) for a,b in zip(ci,independent_ci))<1e-12
    # Direct event table aggregation independently reconciles the view.
    event={'completed':'test_drive_completed','booked':'booking','opted_out':'opt_out'}[metric]
    direct=dict(con.execute('SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM assignments a JOIN journey_events e USING(assignment_id) WHERE e.event_type=? AND julianday(e.event_at) BETWEEN julianday(a.assigned_at) AND julianday(a.assigned_at)+28 GROUP BY a.arm',(event,)))
    assert direct['A']==xa and direct['B']==xb
    rows.append({'metric':metric,'role':role,'n_A':na,'events_A':xa,'n_B':nb,'events_B':xb,'rate_A':pa,'rate_B':pb,'diff_B_minus_A':d,'diff_pp':d*100,'relative_lift':d/pa,'ci95_low_pp':ci[0]*100,'ci95_high_pp':ci[1]*100,'p_two_sided_pooled_z':p,'independent_check':'statsmodels z and Newcombe CI matched; raw-event SQL matched','multiplicity':'Unadjusted per-metric results; diagnostic and guardrail tests do not establish a multi-metric winner.'})
con.close()
p0,p1,alpha,power=.09,.11,.05,.8
mid=(p0+p1)/2
n=math.ceil(((norm.ppf(1-alpha/2)*math.sqrt(2*mid*(1-mid))+norm.ppf(power)*math.sqrt(p0*(1-p0)+p1*(1-p1)))/(p1-p0))**2)
report={'dataset':'JH Motors synthetic v01','analysis_status':'Retrospective educational analysis, not a preregistered field experiment. Independence and binary outcomes assumed; no optional stopping correction.','methods':'Two-sided pooled two-proportion z test; 95% Newcombe difference interval from Wilson score limits; individual metric intervals are not simultaneous.','metrics':rows,'planning_example':{'baseline_rate':p0,'target_rate':p1,'alpha_two_sided':alpha,'power':power,'approx_n_per_arm':n,'status':'Separate approximate future-planning example, not the design that produced existing data; assumes independent individual equal allocation, no loss and fixed single primary comparison.'},'limits':['No observed vehicle revenue, margin, contract or LTV outcomes.','No guardrail non-inferiority margin defined; nonsignificance cannot establish safety.','No sequential, cluster or multiple comparison correction implemented for this sample.','These checks verify implementation and aggregation, not real OEM effectiveness.']}
report['runtime']={'python':platform.python_version(),'scipy':version('scipy'),'statsmodels':version('statsmodels'),'numpy':version('numpy')}
(OUT/'verified_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'metric_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(report,ensure_ascii=False,indent=2))
