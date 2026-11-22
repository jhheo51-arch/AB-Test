"""Check planning power using a direct normal formula and library API."""
from pathlib import Path
from statistics import NormalDist
from datetime import datetime,timezone,timedelta
import json,math
from statsmodels.stats.proportion import power_proportions_2indep
R=Path('C:/Users/Administrator/Downloads/AB-Test-v07');O=Path(__file__).parent;plan=json.loads((R/'e-book/virtual-data/v03/experiment_plan.json').read_text(encoding='utf-8'));N=NormalDist()
def power(pa,pb,n,alpha):
 p=(pa+pb)/2;null_sd=math.sqrt(2*p*(1-p)/n);alt_sd=math.sqrt((pa*(1-pa)+pb*(1-pb))/n);critical=N.inv_cdf(1-alpha/2)*null_sd;d=pb-pa
 return N.cdf((-critical-d)/alt_sd)+N.cdf((d-critical)/alt_sd)
def needed(pa,pb,alpha,target):
 low=1;high=1000000000
 while low<high:
  mid=(low+high)//2
  if power(pa,pb,mid,alpha)>=target:high=mid
  else:low=mid+1
 return low
rows=[]
for p in plan['sample_size_grid']:
 pa=p['baseline'];pb=p['target'];alpha=p['alpha_each'];target=p['power_target'];n=needed(pa,pb,alpha,target);direct=power(pa,pb,n,alpha);library=float(power_proportions_2indep(pb-pa,pa,n,ratio=1,alpha=alpha,alternative='two-sided',return_results=False));before=power(pa,pb,n-1,alpha)
 assert n==p['n_each_numeric_power'],(p['scenario'],p['family_comparisons'],n,p['n_each_numeric_power']);assert before<target<=direct;assert abs(library-direct)<1e-10;assert p['two_arm_total']==2*n
 if p['three_arm_equal_total'] is not None:assert p['three_arm_equal_total']==3*n
 rows.append({'scenario':p['scenario'],'family_comparisons':p['family_comparisons'],'n_each':n,'plan_numeric_n_matches':True,'power_at_n':direct,'power_at_n_minus_1':before,'library_power':library,'closed_form_approx_n':p['n_each_approx_formula'],'closed_form_approx_is_not_numeric_minimum':p['n_each_approx_formula']!=n})
current=power(.09,.1,10000,.05);lib_current=float(power_proportions_2indep(.01,.09,10000,ratio=1,alpha=.05,alternative='two-sided',return_results=False));assert abs(current-lib_current)<1e-10
n=needed(.09,.1,.05,.8);low=.09+1e-9;high=.5
for _ in range(100):
 mid=(low+high)/2
 if power(.09,mid,10000,.05)<.8:low=mid
 else:high=mid
mde=100*((low+high)/2-.09);assert round(current*100,1)==67.4 and n==13495 and round(mde,2)==1.17
report={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'plan_grid_rows':len(rows),'rows':rows,'chapter6':{'power_at_10000_each':current,'library_power':lib_current,'n_each_for_80pct':n,'power_at_n_minus_1':power(.09,.1,n-1,.05),'mde_pp':mde},'limits':['Equal allocation independent binary normal-approximation planning, not safety noninferiority or realized future power','Closed-form approximate and numeric minimum N are distinct fields; differences do not automatically imply errors']};(O/'POWER_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
