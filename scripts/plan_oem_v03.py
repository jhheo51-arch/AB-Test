"""Plan sample sizes before synthetic experiment generation.
uv run --with scipy --with statsmodels scripts/plan_oem_v03.py
"""
import csv
import json
import math
from pathlib import Path
from scipy.stats import norm
from scipy.optimize import brentq
from statsmodels.stats.proportion import power_proportions_2indep
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/virtual-data/v03'
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'experiment_plan.json').exists():
    raise SystemExit('Plan exists; refusing to alter frozen assumptions')
scenarios=[('click_large','点击/관심 큰 변화',.10,.12,7),('drive_primary','시승 완료',.09,.10,28),('contract_rare','계약',.01,.012,180),('optout_risk','수신 거부 악화 탐지',.008,.010,28),('complaint_rare','희귀 불만',.001,.0012,28),('drive_tiny','시승의 작은 상대 변화',.09,.0909,28)]
rows=[]
for sid,label,p0,p1,window in scenarios:
    for family in [1,3]:
        alpha=.05/family;target=.8;mid=(p0+p1)/2;d=p1-p0
        own=((norm.ppf(1-alpha/2)*math.sqrt(2*mid*(1-mid))+norm.ppf(target)*math.sqrt(p0*(1-p0)+p1*(1-p1)))/d)**2
        def power(n):
            return float(power_proportions_2indep(d,p0,n,ratio=1,alpha=alpha,alternative='two-sided',return_results=False))
        root=brentq(lambda n:power(n)-target,2,1e9)
        n=math.ceil(root)
        rows.append({'scenario':sid,'metric':label,'baseline':p0,'target':p1,'absolute_pp':d*100,'relative_change':d/p0,'family_comparisons':family,'alpha_each':alpha,'power_target':target,'n_each_approx_formula':math.ceil(own),'n_each_numeric_power':n,'two_arm_total':2*n,'three_arm_equal_total':3*n if family==3 else None,'observation_days':window,'planning_type':'Independent binary outcomes, equal allocation, two-sided normal approximation; no cluster/loss/sequential correction'})
with (OUT/'sample_size_grid.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
plan={'version':'0.3','company':'JH Motors','synthetic':True,'population_n':120000,'seeds':{'population':31001,'assignment':31002,'delivery':31003,'outcomes':31004,'timing':31005},'design':'Individual Bernoulli equal A/B/H allocation, one persistent assignment; H no experimental message. Only one studied contact, no other campaigns modeled.','eligibility':'Prospect and baseline SMS consent and no baseline test-drive completion','population_probabilities':{'prospect':.8,'consent':.85,'no_prior_drive':.8},'enroll_per_day_cap':2000,'primary_metric':'test_drive_completed within 28 days per assigned customer','confirmatory_family':['B-A completed','A-H completed','B-H completed'],'family_alpha':.05,'multiplicity':'Bonferroni; alpha_each=.05/3; conservative simultaneous intervals.','roles':{'booking':'diagnostic, unadjusted exploration','contract':'exploratory long-term, 180-day window, not predeclared confirmatory','opt_out':'guardrail, descriptive uncertainty; no safety non-inferiority design','net_contribution':'exploratory financial teaching outcome, not validated OEM economics'},'probability_assumptions':{'booking':{'H':.10,'A':.15,'B':1/6},'completion_given_booking':.60,'contract_given_completion':{'H':1/6,'A':1/9,'B':.12},'opt_out':{'H':.001,'A':.008,'B':.010},'delivery':.96},'mechanism':'Outcome probabilities are policy-level ITT assumptions: incomplete delivery is already subsumed, not multiplied again. Outcomes can occur organically after non-delivery. Opt-outs and outcomes are separate Bernoulli mechanisms; no repeated messages.','economics_assumptions':{'vehicle_revenue':40000000,'contribution_before_campaign':2000000,'message_attempt_cost':20,'drive_operating_cost':15000,'B_fixed_setup_cost':200000},'sample_size_grid':rows,'limitations':['All population sizes, probabilities, costs and timings are instructional assumptions, not inferred from Hyundai/Kia data.','No household/dealer interference, capacity constraints or cluster correction implemented.','Artificially larger N improves precision for the assumed synthetic population, not realism or real-world validity.','Uniform policy effect within each arm; subgroup discovery is not validated.','Contract economics omit cancellation, delivery, warranty and real accounting; synthetic contract contribution is not actual vehicle revenue recognized.','No conditional targeting after observing outcomes; no seed rerolling.'],'actual_pre_registration_status':'Frozen locally before new data generation, not externally timestamped registration or a real field experiment.'}
(OUT/'experiment_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'plan':str(OUT/'experiment_plan.json'),'grid':rows},ensure_ascii=False,indent=2))
