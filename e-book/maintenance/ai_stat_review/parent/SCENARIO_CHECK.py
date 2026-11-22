"""Reconstruct cases 4-6 from frozen CSV inputs without generator imports."""
from pathlib import Path
from collections import defaultdict
from statistics import NormalDist
from datetime import datetime,timezone,timedelta
import csv,json,math
R=Path('C:/Users/Administrator/Downloads/AB-Test-v07');B=R/'e-book/analysis/winner_v04';O=Path(__file__).parent;ref=json.loads((B/'scenario_results.json').read_text(encoding='utf-8'));checks=[]
def rows(name):
 with (B/'scenarios'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def check(name,a,b):
 tolerance=0 if 'p_two_sided' in name else 1e-9;ok=math.isclose(a,b,rel_tol=1e-7,abs_tol=tolerance);checks.append({'name':name,'actual':a,'expected':b,'passed':ok});assert ok,name
z=NormalDist().inv_cdf(.975)
def interval(pa,na,pb,nb,confidence):
 z=NormalDist().inv_cdf((1+confidence)/2)
 def w(p,n):
  den=1+z*z/n;m=(p+z*z/(2*n))/den;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return m-r,m+r
 la,ua=w(pa,na);lb,ub=w(pb,nb);d=pb-pa;return [d-math.hypot(pb-lb,ua-pa),d+math.hypot(ub-pb,pa-la)]
def groups(data):
 out={}
 for arm in ['A','B']:
  part=[x for x in data if x['arm']==arm];out[arm]={'n':len(part),'success':sum(int(x['completed']) for x in part)}
 return out
def check_groups(name,g,target):
 for arm in g:
  for key in ['n','success']:check(name+'.'+arm+'.'+key,g[arm][key],target['groups'][arm][key])
 na=g['A']['n'];nb=g['B']['n'];pa=g['A']['success']/na;pb=g['B']['success']/nb;diff=pb-pa;pooled=(g['A']['success']+g['B']['success'])/(na+nb);p=math.erfc(abs(diff/math.sqrt(pooled*(1-pooled)*(1/na+1/nb)))/math.sqrt(2));ci=interval(pa,na,pb,nb,target['confidence'])
 check(name+'.difference',diff,target['difference_B_minus_A']);check(name+'.p_two_sided',p,target['p_two_sided'])
 for i,value in enumerate(ci):check(name+'.newcombe.'+str(i),value,target['newcombe_ci'][i])
 return diff,pa*(1-pa)/na+pb*(1-pb)/nb
truth=rows('case4_truth.csv');logged=rows('case4_log.csv');assert len(truth)==len(logged);by_id={x['customer_id']:x for x in truth};missing=0
for x in logged:
 original=by_id[x['customer_id']];assert original['arm']==x['arm'];d=int(original['completed'])-int(x['completed']);assert d==int(x['injected_missing']) and d in [0,1]
 if d:assert x['arm']=='B';missing+=d
check('case4.injected_missing',missing,ref['case4']['injected_missing']);check_groups('case4.truth',groups(truth),ref['case4']['truth']);check_groups('case4.log',groups(logged),ref['case4']['log'])
customers=rows('case5_customers.csv');check_groups('case5.overall',groups(customers),ref['case5']['overall']);segment={}
for name in ['new','existing']:segment[name]=check_groups('case5.'+name,groups([x for x in customers if x['pretreatment_segment']==name]),ref['case5']['segments'][name])
def wald(name,estimate,var,target):
 se=math.sqrt(var);check(name+'.estimate',estimate,target['estimate']);check(name+'.se',se,target['se']);check(name+'.p_two_sided',math.erfc(abs(estimate/se)/math.sqrt(2)),target['p_two_sided']);check(name+'.ci.low',estimate-z*se,target['wald_ci'][0]);check(name+'.ci.high',estimate+z*se,target['wald_ci'][1])
wald('case5.stratified',.5*(segment['new'][0]+segment['existing'][0]),.25*(segment['new'][1]+segment['existing'][1]),ref['case5']['overall']['stratified_primary']);wald('case5.interaction',segment['new'][0]-segment['existing'][0],segment['new'][1]+segment['existing'][1],ref['case5']['interaction'])
demand=rows('case6_fixed_demand.csv');operations=rows('case6_operations.csv');actual={(int(x['capacity_per_day']),x['policy'],x['customer_id']):x for x in operations};assert len(actual)==len(operations);g=ref['case6']['generation'];summary=[];matched=0
for cap in g['daily_capacities']:
 for policy in ['all_A','pilot_10pct_B','all_B']:
  predicted={};daily=defaultdict(list)
  for x in demand:
   arm='B' if policy=='all_B' or (policy=='pilot_10pct_B' and int(x['pilot_B'])) else 'A';req=int(float(x['request_u'])<g['request_probability'][arm]);predicted[x['customer_id']]={'arm':arm,'requested':req,'accepted':0,'completed':0,'arrival_day':int(x['arrival_day']),'completion_u':float(x['completion_u'])}
   if req:daily[int(x['arrival_day'])].append(x)
  for day,people in daily.items():
   for x in sorted(people,key=lambda x:float(x['arrival_priority']))[:cap]:
    rec=predicted[x['customer_id']];rec['accepted']=1;rec['completed']=int(rec['completion_u']<g['completion_given_accepted'][rec['arm']])
  totals={'customers':len(demand),'requested':0,'accepted':0,'waiting_end_window':0,'completed':0,'variable_cost_krw':0}
  for cid,x in predicted.items():
   x['waiting_end_window']=x['requested']-x['accepted'];x['contact_cost_krw']=g['contact_cost_krw'][x['arm']];x['variable_cost_krw']=x['contact_cost_krw']+x['accepted']*g['accepted_service_cost_krw']+x['waiting_end_window']*g['unserved_request_cost_krw'];old=actual[(cap,policy,cid)];assert x['arm']==old['arm']
   for key in ['arrival_day','requested','accepted','waiting_end_window','completed','contact_cost_krw','variable_cost_krw']:assert x[key]==int(old[key]),(cap,policy,cid,key)
   for key in totals:
    if key!='customers':totals[key]+=x[key]
   matched+=1
  totals['capacity_cost_krw']=cap*g['days']*g['staffed_slot_day_cost_krw'];totals['total_cost_krw']=totals['variable_cost_krw']+totals['capacity_cost_krw'];totals['completed_value_krw']=totals['completed']*g['value_per_completion_krw'];totals['net_value_krw']=totals['completed_value_krw']-totals['total_cost_krw'];totals['waiting_fraction_of_requests']=totals['waiting_end_window']/totals['requested'];target=next(x for x in ref['case6']['summaries'] if x['capacity_per_day']==cap and x['policy']==policy)
  for key,value in totals.items():check('case6.'+str(cap)+'.'+policy+'.'+key,value,target[key])
  summary.append({'capacity_per_day':cap,'policy':policy,**totals})
assert matched==len(operations)
report={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'implementation':'New CSV reconstruction, no imports or calls to production generators/analysis','scalar_comparisons':len(checks),'checks':checks,'case4_truth_rows':len(truth),'case4_missing':missing,'case5_rows':len(customers),'case6_operations_rows_matched':matched,'case6_policy_capacity_cells':len(summary),'case6_summary':summary,'limits':['Conditional single-seed simulation, not real operating outcomes or uncertainty certification','Scope is frozen realizations and recorded policy assumptions; does not validate customer behavioral assumptions']};(O/'SCENARIO_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','case6_summary']},ensure_ascii=False,indent=2))
