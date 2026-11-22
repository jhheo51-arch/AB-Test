"""Separate raw-record implementation for AI review cross-checking."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from statistics import NormalDist,mean,variance
from collections import Counter
import math,json,sqlite3,hashlib
from scipy.stats import t as student_t
R=Path('C:/Users/Administrator/Downloads/AB-Test-v07');O=R/'e-book/maintenance/ai_stat_review/parent';O.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads((R/p).read_text(encoding='utf-8'));plan=read('e-book/virtual-data/v03/experiment_plan.json');reference=read('e-book/analysis/winner_v04/core_results.json');baseline=read('e-book/review/publication_v22/TECHNICAL_RIGHTS_CHECK.json')['baseline_hashes'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert all(sha(R/p)==h for p,h in baseline.items())
with sqlite3.connect((R/'e-book/virtual-data/v13/data/jh_motors_v13.sqlite').as_uri()+'?mode=ro',uri=True) as db:
 db.execute('PRAGMA query_only=ON');assignments=db.execute('SELECT assignment_id,customer_id,arm,assigned_day FROM assignments').fetchall();events=db.execute('SELECT assignment_id,event_type,event_day FROM events').fetchall();attempts=dict(db.execute('SELECT assignment_id,COUNT(*) FROM messages GROUP BY assignment_id').fetchall());outcomes=db.execute('SELECT assignment_id,booked_28,completed_28,withdrawn_28,contracted_180 FROM outcomes').fetchall()
records={aid:{'customer':cid,'arm':arm,'day':day,'flags':[0,0,0,0]} for aid,cid,arm,day in assignments};assert len(records)==len(assignments)==len({x[1] for x in assignments})
index={'booking':(0,28),'test_drive_completed':(1,28),'consent_withdrawn':(2,28),'contract_signed':(3,180)};outside=0;orphans=0
for aid,event_type,day in events:
 if aid not in records:orphans+=1;continue
 i,window=index[event_type];rec=records[aid]
 if rec['day']<=day<=rec['day']+window:rec['flags'][i]=1
 else:outside+=1
assert not orphans;assert len(outcomes)==len(records)
for aid,*flags in outcomes:assert records[aid]['flags']==flags,aid
checks=[]
def check(label,actual,expected,atol=1e-8,rtol=1e-9):
 ok=abs(actual-expected)<=atol+rtol*abs(expected);checks.append({'label':label,'actual':actual,'expected':expected,'absolute_difference':abs(actual-expected),'passed':ok});assert ok,label
counts={};values={};econ=plan['economics_assumptions']
for arm in ['A','B','H']:
 chosen=[(aid,v) for aid,v in records.items() if v['arm']==arm];n=len(chosen);flags=[sum(v['flags'][i] for aid,v in chosen) for i in range(4)];counts[arm]={'n':n,'booked':flags[0],'completed':flags[1],'withdrawn':flags[2],'contracted':flags[3]};ref=next(x for x in reference['groups'] if x['arm']==arm)
 for name,value in counts[arm].items():check(arm+'.'+name,value,ref[name],atol=0,rtol=0)
 values[arm]=[econ['contribution_before_campaign']*v['flags'][3]-econ['drive_operating_cost']*v['flags'][1]-econ['message_attempt_cost']*attempts.get(aid,0)-(econ['B_fixed_setup_cost']/n if arm=='B' else 0) for aid,v in chosen];check(arm+'.net_mean',mean(values[arm]),reference['financial_means'][arm],atol=1e-6)
def wilson(x,n,z):
 p=x/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;s=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return c-s,c+s
def compare(new,base,metric,level):
 nb=counts[new]['n'];na=counts[base]['n'];xb=counts[new][metric];xa=counts[base][metric];pb=xb/nb;pa=xa/na;pool=(xa+xb)/(na+nb);z=(pb-pa)/math.sqrt(pool*(1-pool)*(1/na+1/nb));p=math.erfc(abs(z)/math.sqrt(2));q=NormalDist().inv_cdf((1+level)/2);la,ua=wilson(xa,na,q);lb,ub=wilson(xb,nb,q);d=pb-pa
 return {'diff_pp':100*d,'p_raw':p,'ci_low_pp':100*(d-math.sqrt((pb-lb)**2+(ua-pa)**2)),'ci_high_pp':100*(d+math.sqrt((ub-pb)**2+(pa-la)**2))}
for ref in reference['primary_family']:
 new,base=ref['comparison'].split('-');actual=compare(new,base,'completed',ref['ci_level'])
 for key,value in actual.items():check('completion.'+ref['comparison']+'.'+key,value,ref[key],atol=0 if key=='p_raw' else 1e-12,rtol=1e-7 if key=='p_raw' else 1e-9)
 check('completion.'+ref['comparison']+'.p_family',min(1,3*actual['p_raw']),ref['p_family'],atol=0,rtol=1e-7)
g=compare('B','A','withdrawn',.95)
for key,value in g.items():check('withdrawal.B-A.'+key,value,reference['guardrail_exploratory'][key],atol=1e-12)
financial=[]
for ref in reference['financial_exploratory']:
 new,base=ref['comparison'].split('-');a=values[base];b=values[new];sa=variance(a)/len(a);sb=variance(b)/len(b);se=math.sqrt(sa+sb);df=(sa+sb)**2/(sa*sa/(len(a)-1)+sb*sb/(len(b)-1));d=mean(b)-mean(a);q=student_t.ppf(.975,df);actual={'diff_krw':d,'ci95_low_krw':d-q*se,'ci95_high_krw':d+q*se,'p_unadjusted':2*student_t.sf(abs(d/se),df),'welch_df':df}
 for key,value in actual.items():check('financial.'+ref['comparison']+'.'+key,float(value),ref[key],atol=1e-6 if key!='p_unadjusted' else 1e-12)
 financial.append({'comparison':ref['comparison'],**{k:float(v) for k,v in actual.items()}})
assert all(sha(R/p)==h for p,h in baseline.items())
report={'status':'passed','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'implementation':'New Python raw-event reconstruction and formulas; production analysis code not imported or executed','kind':'AI cross-check, not independent human certification','assigned_records':len(records),'raw_outcome_fields_compared':sum(len(row)-1 for row in outcomes),'event_rows':len(events),'events_outside_relevant_window':outside,'orphan_events':orphans,'groups':counts,'financial':financial,'comparison_count':len(checks),'checks':checks,'baseline_unchanged':True,'limits':['Same-model AI review cannot establish independent human agreement','Synthetic cost model only','No independent timestamp authentication of historical preregistration','No human reading test or real OEM performance validation']}
(O/'RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','financial']},ensure_ascii=False,indent=2))
