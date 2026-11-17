"""Separate winner evidence from adoption; do not change the frozen trial plan.
uv run --with statsmodels scripts/analyze_winner_depth.py
"""
import json
from pathlib import Path
from statsmodels.stats.proportion import confint_proportions_2indep
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'e-book/virtual-data/v03/analysis_report.json').read_text(encoding='utf-8'))
g={r['arm']:r for r in base['groups']}
a,b=g['A'],g['B'];primary=base['primary_comparisons'][0]
guard_ci=confint_proportions_2indep(b['withdrawn'],b['n'],a['withdrawn'],a['n'],compare='diff',method='newcomb',alpha=.05)
economics={r['arm']:r['synthetic_net_per_assigned'] for r in base['descriptive_economics']}
report={
 'dataset':'JH Motors synthetic v0.3',
 'primary':{'rate_A':a['completed']/a['n'],'rate_B':b['completed']/b['n'],'difference_pp':primary['diff_pp'],'relative_lift':(b['completed']/b['n'])/(a['completed']/a['n'])-1,'p_family_adjusted':primary['p_bonferroni'],'simultaneous_approx_ci_level':primary['simultaneous_approx_ci_level'],'ci_low_pp':primary['ci_low_pp'],'ci_high_pp':primary['ci_high_pp']},
 'minimum_benefit_sensitivity':[{'threshold_pp':x,'interval_lower_exceeds_threshold':primary['ci_low_pp']>x,'threshold_status':'Retrospective teaching threshold, not a preregistered business cutoff or valid post-hoc success rule'} for x in [0,.25,.5,1]],
 'guardrail':{'rate_A':a['withdrawn']/a['n'],'rate_B':b['withdrawn']/b['n'],'difference_pp':100*(b['withdrawn']/b['n']-a['withdrawn']/a['n']),'unadjusted_ci95_low_pp':float(guard_ci[0])*100,'unadjusted_ci95_high_pp':float(guard_ci[1])*100,'safety_margin_status':'Not defined in frozen experiment plan; no safety/non-inferiority winner declared','illustrative_margin_pp':.2,'unadjusted_ci_upper_below_illustrative_margin':float(guard_ci[1])*100<.2,'limits':'Exploratory individual 95% interval, different from primary family intervals; hypothetical post-hoc margin does not create safety confirmation.'},
 'descriptive_synthetic_economics':{'per_assigned':economics,'A_minus_H':economics['A']-economics['H'],'B_minus_A':economics['B']-economics['A'],'B_minus_H':economics['B']-economics['H'],'limits':'Descriptive fixed-assumption contract contribution, no profit effect inference or real OEM financial winner.'},
 'winner_status':{'primary_superiority':'Supported under the planned synthetic model and analysis assumptions','minimum_business_benefit':'No externally approved minimum adoption benefit; sensitivity examples only','guardrail_safety':'Not established','net_business_value':'Not established by formal financial inference or real economics','full_rollout':'Not authorized; human review and operational evidence required'},
 'warning':'Do not select a threshold after seeing results, translate p into P(B is best), confuse primary superiority with adoption, or compare v0.2 and v0.3 significance as N-only change.'
}
out=ROOT/'e-book/analysis/winner_depth';out.mkdir(parents=True,exist_ok=True)
(out/'winner_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
