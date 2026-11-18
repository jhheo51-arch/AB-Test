"""Recalculate one shared educational A/B case for PDCA and TRI-V."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,csv,random,sqlite3,hashlib,math,platform
import numpy as np,scipy,statsmodels
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.stats.proportion import test_proportions_2indep,confint_proportions_2indep
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/ab_only_methods_v01';fixture=json.loads((D/'design_fixture.json').read_text(encoding='utf-8'));plan=fixture['plan_in_the_story'];rng=random.Random(plan['seed'])
records=[];cell_data=[]
for stratum in plan['strata']:
 cells={c['arm']:c for c in fixture['fixed_cells'] if c['stratum']==stratum}
 labels=['A']*cells['A']['assigned']+['B']*cells['B']['assigned'];rng.shuffle(labels)
 ids={a:[f'{fixture["case_id"]}_{stratum}_{i:05d}' for i,label in enumerate(labels) if label==a] for a in ['A','B']}
 for arm in ['A','B']:
  c=cells[arm];complete=[1]*c['completed']+[0]*(c['assigned']-c['completed']);withdraw=[1]*c['withdrawn']+[0]*(c['assigned']-c['withdrawn']);rng.shuffle(complete);rng.shuffle(withdraw)
  for cid,y,w in zip(ids[arm],complete,withdraw):
   contribution=y*(plan['economics']['contribution_before_coupon_per_completed_customer_KRW']-(plan['economics']['B_discount_per_completed_customer_KRW'] if arm=='B' else 0))
   records.append({'customer_id':cid,'pre_stratum':stratum,'arm':arm,'observed_days':30,'completed_30':y,'withdrawn_30':w,'contribution_30_KRW':contribution})
  vals=np.array([r['contribution_30_KRW'] for r in records if r['pre_stratum']==stratum and r['arm']==arm],dtype=float)
  comp=np.array([r['completed_30'] for r in records if r['pre_stratum']==stratum and r['arm']==arm],dtype=float)
  cell_data.append({'stratum':stratum,'arm':arm,'n':len(vals),'completed':int(comp.sum()),'mean_KRW':float(vals.mean()),'variance_of_mean':float(vals.var(ddof=1)/len(vals)),'completion_rate':float(comp.mean()),'completion_variance_of_mean':float(comp.var(ddof=1)/len(comp))})
path=D/'customer_fixture.csv'
with path.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
with path.open(encoding='utf-8-sig',newline='') as f:reread=list(csv.DictReader(f))
assert len(reread)==len(records) and len({r['customer_id'] for r in reread})==len(records)
con=sqlite3.connect(':memory:');con.execute('CREATE TABLE customers(id TEXT PRIMARY KEY,s TEXT,arm TEXT,days INT,completed INT,withdrawn INT,cm INT)');con.executemany('INSERT INTO customers VALUES(?,?,?,?,?,?,?)',[(r['customer_id'],r['pre_stratum'],r['arm'],r['observed_days'],r['completed_30'],r['withdrawn_30'],r['contribution_30_KRW']) for r in records]);assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
actual=con.execute('SELECT s,arm,COUNT(*),SUM(completed),SUM(withdrawn),SUM(cm) FROM customers GROUP BY s,arm ORDER BY s,arm').fetchall()
for stratum,arm,n,c,w,cm in actual:
 expected=next(x for x in fixture['fixed_cells'] if x['stratum']==stratum and x['arm']==arm);assert [n,c,w]==[expected['assigned'],expected['completed'],expected['withdrawn']]
assert con.execute('SELECT COUNT(*) FROM customers WHERE days<>30 OR completed NOT IN(0,1) OR withdrawn NOT IN(0,1)').fetchone()[0]==0
arms=[]
for arm,n,c,w,cm in con.execute('SELECT arm,COUNT(*),SUM(completed),SUM(withdrawn),SUM(cm) FROM customers GROUP BY arm ORDER BY arm'):
 arms.append({'arm':arm,'assigned':n,'completed':c,'completed_rate_pct':100*c/n,'withdrawn':w,'total_contribution_KRW':cm,'mean_contribution_KRW':cm/n})
con.close();means=np.array([c['mean_KRW'] for c in cell_data]);vars_=np.array([c['variance_of_mean'] for c in cell_data]);rates=np.array([c['completion_rate'] for c in cell_data]);rvars=np.array([c['completion_variance_of_mean'] for c in cell_data])
X=np.zeros((len(records),4));y=np.array([r['contribution_30_KRW'] for r in records],float)
for i,r in enumerate(records):X[i,plan['strata'].index(r['pre_stratum'])*2+['A','B'].index(r['arm'])]=1
fit=sm.OLS(y,X).fit(cov_type='HC2',use_t=False)
def contrast(coeff):
 l=np.array(coeff,float);effect=float(l@means);variance=float((l*l)@vars_);se=math.sqrt(variance);ci=[effect-norm.ppf(.975)*se,effect+norm.ppf(.975)*se];p=float(2*norm.sf(abs(effect/se)))
 check=fit.t_test(l);assert abs(float(np.asarray(check.effect).item())-effect)<1e-7;assert abs(float(np.asarray(check.sd).item())-se)<1e-7;assert abs(float(check.pvalue)-p)<1e-10
 return {'effect_B_minus_A_KRW':effect,'se_KRW':se,'ci95_KRW':[float(x) for x in ci],'p_two_sided_normal':p,'method':'fixed-stratum weighted mean difference, within-cell sample variance, normal Wald; crosschecked with saturated cell-mean OLS HC2 contrast'}
weights=[plan['target_weights'][s] for s in plan['strata']];l=np.array([-weights[0],weights[0],-weights[1],weights[1]])
primary=contrast(l);groups={s:contrast([-1,1,0,0] if s==plan['strata'][0] else [0,0,-1,1]) for s in plan['strata']};interaction=contrast([-1,1,1,-1]);interaction['meaning']='first_service effect minus repeat_service effect; exploratory, not a multiplicity-adjusted confirmation'
rd=float(l@rates);rse=math.sqrt(float((l*l)@rvars));completion={'difference_pp':rd*100,'ci95_pp':[float(100*(rd-norm.ppf(.975)*rse)),float(100*(rd+norm.ppf(.975)*rse))],'role':'exploratory diagnostic; not a replacement for contribution primary'}
a,b=arms;na,nb=a['assigned'],b['assigned'];wa,wb=a['withdrawn'],b['withdrawn'];delta=.003
ni=test_proportions_2indep(wb,nb,wa,na,value=delta,method='score',compare='diff',alternative='smaller',correction=True)
ci90=confint_proportions_2indep(wb,nb,wa,na,method='score',compare='diff',alpha=.10,correction=True)
guard={'difference_pp':100*(wb/nb-wa/na),'margin_pp':100*delta,'one_sided_95_upper_score_pp':float(100*ci90[1]),'p_noninferiority_score':float(ni.pvalue),'passes_at_alpha_05':bool(ni.pvalue<.05),'scope':'illustrative predeclared in the fictional story; homogeneous withdrawal rates across the two equal-size strata. No retrospective margin or adequate-power claim.'}
assert guard['passes_at_alpha_05']==(ci90[1]<delta)
primary['passes_story_business_rule']=bool(primary['ci95_KRW'][0]>plan['business_minimum_KRW_per_assigned_customer']);primary['supports_decrease_under_model']=bool(primary['ci95_KRW'][1]<0)
report={'case_id':fixture['case_id'],'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'status':'fixed educational example calculated, not a real company result or randomized field validation','row_count':len(records),'source_sha256':hashlib.sha256((D/'design_fixture.json').read_bytes()).hexdigest(),'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'assumptions':'Independent customers, no interference, complete mature windows, fixed contribution amounts and selected teaching counts. These are not verified facts about an OEM.','cells':cell_data,'arms':arms,'primary':primary,'exploratory_completed_rate':completion,'exploratory_group_contribution':groups,'exploratory_interaction':interaction,'guardrail':guard,'changes':{'additional_completed_B_minus_A':b['completed']-a['completed'],'total_contribution_B_minus_A_KRW':b['total_contribution_KRW']-a['total_contribution_KRW']},'current_decision':'Reject rollout of coupon B to the whole tested target; retain a first_service-only new-cohort test as an exploratory follow-up hypothesis, not an approved mixed policy.','claims_not_supported':['campaign versus no-contact incrementality','new-customer rollout superiority without follow-up','lifetime value','safe rollout from nonsignificance','real OEM conversion rates or costs','PDCA or TRI-V improves real organizational outcomes']}
(D/'calculated_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
