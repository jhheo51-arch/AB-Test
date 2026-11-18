"""Independent v12 interpretation/power audit. No project modules imported/executed.
Run from repository root:
uv run --with scipy --with statsmodels python e-book/review/ai_statistical_v12/interpretation/POWER_RECHECK.py
Only writes sibling RESULTS.json. No simulations, seed changes or manuscript edits.
"""
from pathlib import Path
from statistics import NormalDist
import json
import math
import hashlib
import sys
import scipy
import statsmodels
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    proportion_effectsize, power_proportions_2indep,
    confint_proportions_2indep, test_proportions_2indep,
)

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
ND = NormalDist()

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))

def power(p1, p2, n1, n2, alpha):
    # Fixed planned proportions, not observed proportions. Pooled null SD and
    # unpooled alternative SD; two tails, no continuity correction.
    delta = p1 - p2
    pooled = (n1*p1 + n2*p2)/(n1+n2)
    sd0 = math.sqrt(pooled*(1-pooled)*(1/n1+1/n2))
    sd1 = math.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    critical = ND.inv_cdf(1-alpha/2)*sd0
    return ND.cdf((-critical-delta)/sd1) + ND.cdf((delta-critical)/sd1)

def size_closed(p1, p2, alpha, target):
    mid = (p1+p2)/2
    numerator = (ND.inv_cdf(1-alpha/2)*math.sqrt(2*mid*(1-mid))
                 + ND.inv_cdf(target)*math.sqrt(p1*(1-p1)+p2*(1-p2)))**2
    return numerator/(p1-p2)**2

def size_numeric(p1, p2, alpha, target):
    lo, hi = 1, 2
    while power(p1,p2,hi,hi,alpha) < target:
        hi *= 2
    while lo < hi:
        m = (lo+hi)//2
        if power(p1,p2,m,m,alpha) >= target:
            hi = m
        else:
            lo = m+1
    return lo

def library_power(p1,p2,n1,n2,alpha):
    return float(power_proportions_2indep(p1-p2,p2,n1,ratio=n2/n1,
                 alpha=alpha,alternative='two-sided',return_results=False))

def wilson(x,n,alpha):
    p=x/n
    z=ND.inv_cdf(1-alpha/2)
    denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return center-half,center+half

def newcombe(x1,n1,x2,n2,alpha):
    p1,p2=x1/n1,x2/n2
    l1,u1=wilson(x1,n1,alpha)
    l2,u2=wilson(x2,n2,alpha)
    return [p1-p2-math.hypot(p1-l1,u2-p2),
            p1-p2+math.hypot(u1-p1,p2-l2)]

plan_rel='e-book/virtual-data/v03/experiment_plan.json'
report_rel='e-book/virtual-data/v03/analysis_report.json'
repeat_rel='e-book/virtual-data/v03/repeated_sampling_check.json'
md_rel='e-book/exports/v12/ebook_review_v12.md'
plan, report, repeat = map(read,[plan_rel,report_rel,repeat_rel])
groups={g['arm']:g for g in report['groups']}
results={
    'audit_type':'AI interpretation review plus separately implemented analytic recalculation; NOT independent human review',
    'command':'uv run --with scipy --with statsmodels python e-book/review/ai_statistical_v12/interpretation/POWER_RECHECK.py',
    'runtime':{'python':sys.version,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},
    'input_sha256':{r:hashlib.sha256((ROOT/r).read_bytes()).hexdigest() for r in [plan_rel,report_rel,repeat_rel,md_rel]},
    'methods':{
        'closed_n':'ceil((z_(1-alpha/2)*sqrt(2*pbar*(1-pbar)) + z_power*sqrt(p1*(1-p1)+p2*(1-p2)))^2 / delta^2)',
        'numeric_n':'integer bisection of independent two-tail normal power; pooled planned null variance and unpooled planned alternative variance',
        'h_crosscheck':'Cohen arcsine h / NormalIndPower is a DIFFERENT approximation, not exact validation of pooled-z power',
        'limitations':'Independent Bernoulli outcomes, fixed single look, no clusters/interference/loss, no continuity correction. No exact finite-sample type I error guarantee.'},
    'sample_grid':[], 'current_AB_planned_effect_power':[],
}
for row in plan['sample_size_grid']:
    p0,p1,a,t=row['baseline'],row['target'],row['alpha_each'],row['power_target']
    raw=size_closed(p1,p0,a,t)
    nc=math.ceil(raw)
    nn=size_numeric(p1,p0,a,t)
    h=abs(float(proportion_effectsize(p1,p0)))
    nh=float(NormalIndPower().solve_power(effect_size=h,alpha=a,power=t,ratio=1,alternative='two-sided'))
    own=power(p1,p0,nn,nn,a)
    lib=library_power(p1,p0,nn,nn,a)
    assert abs(own-lib)<1e-11
    assert power(p1,p0,nn-1,nn-1,a)<t<=own
    results['sample_grid'].append({
        'scenario':row['scenario'],'family_comparisons':row['family_comparisons'],
        'p_baseline_planned':p0,'p_target_planned':p1,'alpha_each':a,
        'n_closed_raw':raw,'n_closed_ceil':nc,'n_numeric_minimum':nn,
        'original_n_closed':row['n_each_approx_formula'],'original_n_numeric':row['n_each_numeric_power'],
        'closed_match':nc==row['n_each_approx_formula'],'numeric_match':nn==row['n_each_numeric_power'],
        'numeric_power':own,'library_power':lib,'library_abs_error':abs(own-lib),
        'arcsine_h_n_raw':nh,'arcsine_h_n_ceil':math.ceil(nh),
        'expected_events_at_numeric_n':[nn*p0,nn*p1],
    })
for old in report['metric_readiness']:
    scenario=old['scenario']
    fam=3 if scenario=='drive_primary' else 1
    row=next(r for r in plan['sample_size_grid'] if r['scenario']==scenario and r['family_comparisons']==fam)
    nA,nB=groups['A']['n'],groups['B']['n']
    # A/B original planning assumptions, NOT their realized event rates.
    own=power(row['target'],row['baseline'],nB,nA,row['alpha_each'])
    lib=library_power(row['target'],row['baseline'],nB,nA,row['alpha_each'])
    assert abs(own-lib)<1e-11
    results['current_AB_planned_effect_power'].append({
        'scenario':scenario,'nA_realized':nA,'nB_realized':nB,
        'pA_planned':row['baseline'],'pB_planned':row['target'],'alpha_each':row['alpha_each'],
        'power_direct':own,'power_library':lib,'original_power':old['planning_power_under_stated_effect'],
        'difference_from_original':own-old['planning_power_under_stated_effect'],
        'swapped_n_mapping_direct_power':power(row['target'],row['baseline'],nA,nB,row['alpha_each']),
        'swapped_n_mapping_matches_ledger':abs(power(row['target'],row['baseline'],nA,nB,row['alpha_each'])-old['planning_power_under_stated_effect'])<1e-12,
        'arcsine_h_power':float(NormalIndPower().power(abs(proportion_effectsize(row['target'],row['baseline'])),nA,alpha=row['alpha_each'],ratio=nB/nA)),
        'expected_events_under_planning_scenario':[nA*row['baseline'],nB*row['target']],
    })
# Actual generation assumptions form a coherent three-arm alternative. H is .06,
# not another .09 baseline with a one-pp improvement.
pr=plan['probability_assumptions']
p_complete={arm:pr['booking'][arm]*pr['completion_given_booking'] for arm in ['A','B','H']}
contrasts=[]
for a,b in [('B','A'),('A','H'),('B','H')]:
    pw=power(p_complete[a],p_complete[b],groups[a]['n'],groups[b]['n'],.05/3)
    contrasts.append({'contrast':a+'-'+b,'planned_rates':[p_complete[a],p_complete[b]],'power':pw})
results['three_arm_completion_planned_powers']={
    'individual':contrasts,
    'joint_all_reject_power_not_computed':True,
    'joint_union_bound_lower':min(min(c['power'] for c in contrasts), max(0,sum(c['power'] for c in contrasts)-2)),
    'joint_upper_bound_min_marginal':min(c['power'] for c in contrasts),
    'note':'Shared arms induce dependence. Marginal 80% is not joint 80%. Bounds are under this approximate alternative, not exact binomial joint power.'}
results['observed_primary_interval_check']=[]
for old in report['primary_comparisons']:
    a,b=old['comparison'].split('-')
    g1,g2=groups[a],groups[b]
    x1,n1,x2,n2=g1['completed'],g1['n'],g2['completed'],g2['n']
    own=newcombe(x1,n1,x2,n2,.05/3)
    lib=list(map(float,confint_proportions_2indep(x1,n1,x2,n2,method='newcomb',alpha=.05/3)))
    assert max(abs(v-w) for v,w in zip(own,lib))<1e-12
    results['observed_primary_interval_check'].append({'contrast':old['comparison'],
        'newcombe_direct_pp':[100*v for v in own], 'newcombe_library_pp':[100*v for v in lib],
        'v03_analysis_report_ci_pp':[old['ci_low_pp'],old['ci_high_pp']],
        'note':'Historical v03 analysis report intervals match independently implemented Newcombe in all checked contrasts'})
def constrained_score(xB,nB,xA,nA,d):
    # qB=qA+d. Binomial log-likelihood derivative in qA is strictly
    # decreasing on the feasible interior; independent bisection, no library MLE.
    lo=max(0.0,-d)+1e-14
    hi=min(1.0,1.0-d)-1e-14
    for _ in range(100):
        q=(lo+hi)/2
        qb=q+d
        score=xA/q-(nA-xA)/(1-q)+xB/qb-(nB-xB)/(1-qb)
        if score>0: lo=q
        else: hi=q
    q=(lo+hi)/2; qb=q+d
    variance=(q*(1-q)/nA+qb*(1-qb)/nB)*(nA+nB)/(nA+nB-1)
    return (xB/nB-xA/nA-d)/math.sqrt(variance)

def score_upper(xB,nB,xA,nA,alpha):
    lo=xB/nB-xA/nA
    hi=.2
    critical=ND.inv_cdf(1-alpha)
    for _ in range(90):
        d=(lo+hi)/2
        if constrained_score(xB,nB,xA,nA,d)>-critical: lo=d
        else: hi=d
    return (lo+hi)/2

results['chapter8_fixed_counterexamples']=[]
for label,x1,n1,x2,n2,onealpha in [
    ('ga',45,5000,50,5000,.05),('na',36,4000,40,4000,.025),
    ('da',45,5000,50,5000,.05),('ra',110,5000,50,5000,.05)]:
    # Library crosscheck of declared score upper bound; not a new NI plan.
    ci=confint_proportions_2indep(x1,n1,x2,n2,method='score',alpha=2*onealpha,correction=True)
    test=test_proportions_2indep(x1,n1,x2,n2,value=.005,method='score',alternative='smaller',correction=True)
    z_direct=constrained_score(x1,n1,x2,n2,.005)
    p_direct=ND.cdf(z_direct)
    upper_direct=score_upper(x1,n1,x2,n2,onealpha)*100
    results['chapter8_fixed_counterexamples'].append({'condition':label,'one_sided_alpha':onealpha,
        'score_upper_pp_library':float(ci[1]*100),'NI_margin_pp':.5,'NI_pvalue_library':float(test.pvalue),
        'score_upper_pp_direct':upper_direct,'NI_pvalue_direct':p_direct,
        'library_minus_direct_upper_pp':float(ci[1]*100)-upper_direct,
        'passes_NI_direct':p_direct<onealpha,'passes_NI_library':bool(test.pvalue<onealpha),
        'scope_note':'Nonzero-risk-difference score discrepancy; library agreement alone does not establish correctness. No implication for zero-null pooled z, Wilson-Newcombe or planning power.'})
# Ledger audit only. No RNG invoked: exact historical streams/order/raw repetitions unavailable.
results['repeated_sampling_ledger']={'seed_recorded':repeat['seed'],
    'status':'NOT REPRODUCED: no raw per-replication arrays identified in v03 inventory; original simulation function not executed',
    'not_a_joint_FWER_check':True,'cells':[]}
for cell in repeat['results']:
    n=cell['n_per_arm']; alt=cell['scenario']=='planned_effect'
    target=power(.10,.09,n,n,repeat['alpha_each']) if alt else repeat['alpha_each']
    rate=cell['rejections']/cell['replications']
    se=math.sqrt(target*(1-target)/cell['replications'])
    results['repeated_sampling_ledger']['cells'].append({
        'n':n,'scenario':cell['scenario'],'rate_from_ledger_count':rate,
        'ledger_rate_matches':abs(rate-cell['observed_rejection_rate'])<1e-15,
        'analytic_target':target,'ledger_target':cell['normal_approx_target'],
        'MC_se_at_target':se,'deviation_in_MC_se':(rate-target)/se})
results['checks']={
    'grid_rows':len(results['sample_grid']),
    'all_closed_n_match':all(r['closed_match'] for r in results['sample_grid']),
    'all_numeric_n_match':all(r['numeric_match'] for r in results['sample_grid']),
    'max_power_library_error':max(r['library_abs_error'] for r in results['sample_grid']),
    'no_existing_project_code_imported_or_executed':True,
    'no_repeat_simulation_or_seed_reroll':True,
    'manuscript_or_original_data_modified':False}
(OUT/'RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT/'RESULTS.json'),'checks':results['checks'],
    'current_powers':results['current_AB_planned_effect_power'],
    'three_arm':results['three_arm_completion_planned_powers'],
    'counterexamples':results['chapter8_fixed_counterexamples']},ensure_ascii=False,indent=2))
