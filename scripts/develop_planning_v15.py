"""A disclosed future-planning illustration, not a new CRM experiment."""
from pathlib import Path
import json,math
from scipy.optimize import brentq
from statsmodels.stats.proportion import power_proportions_2indep
from statistics_v13 import planned_power
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/analysis/development_v15';OUT.mkdir(parents=True,exist_ok=True)
p_A=.09;delta=.01;n_A=n_B=10000;alpha=.05;goal=.80
power=planned_power(p_A=p_A,p_B=p_A+delta,n_A=n_A,n_B=n_B,alpha=alpha)
reference=power_proportions_2indep(delta,p_A,n_B,ratio=n_A/n_B,alpha=alpha,alternative='two-sided',return_results=False)
assert math.isclose(power,reference,abs_tol=1e-12)
n_float=brentq(lambda n:planned_power(p_A=p_A,p_B=p_A+delta,n_A=n,n_B=n,alpha=alpha)-goal,100,100000)
n=math.ceil(n_float)
assert planned_power(p_A=p_A,p_B=p_A+delta,n_A=n,n_B=n,alpha=alpha)>=goal
assert planned_power(p_A=p_A,p_B=p_A+delta,n_A=n-1,n_B=n-1,alpha=alpha)<goal
mde=brentq(lambda d:planned_power(p_A=p_A,p_B=p_A+d,n_A=n_A,n_B=n_B,alpha=alpha)-goal,1e-5,.20)
ref_mde=brentq(lambda d:power_proportions_2indep(d,p_A,n_B,ratio=n_A/n_B,alpha=alpha,alternative='two-sided',return_results=False)-goal,1e-5,.20)
assert math.isclose(mde,ref_mde,abs_tol=1e-12)
result={'scope':'Separate hypothetical follow-up design before results; not the historical A/B/H design or a completed experiment','assumptions':{'allocation':'Equal independent individuals, two arms A/B only; no holdout claim','p_A':p_A,'target_p_B':p_A+delta,'alpha_two_sided':alpha,'target_power':goal,'available_n_total':n_A+n_B,'observation_window_days':28,'loss_clustering_sequential_adjustment_included':False,'guardrail_sample_requirement_calculated':False},'available_plan':{'n_A':n_A,'n_B':n_B,'power_direct':power,'power_library':float(reference),'power_display_percent':round(100*power,1),'required_n_each':n,'required_n_total':2*n,'additional_eligible_customers':2*n-(n_A+n_B),'mde_at_available_n':mde,'mde_display_pp':round(100*mde,2),'mde_library':ref_mde},'checks_passed':4,'statistics_are_planning_approximations':True,'not_authorized_to_recruit_or_send':True,'old_data_or_ledgers_modified':False}
(OUT/'PLANNING_EXAMPLE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result,ensure_ascii=False,indent=2))
