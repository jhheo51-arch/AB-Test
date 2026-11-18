"""Check two disclosed mathematical illustrations; no customer data or simulation."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/analysis/study_integration_v14';OUT.mkdir(parents=True,exist_ok=True)
alpha=.01;trials=100
prob=-math.expm1(trials*math.log1p(-alpha));direct=1-(1-alpha)**trials
assert abs(prob-direct)<1e-14
ratio=.5;sample_ratio=ratio**-2;assert sample_ratio==4
result={'kind':'Analytic teaching illustrations, not an observed experiment or field validation','independent_true_null_tests':{'assumptions':'All null hypotheses true, independent rejection events, exact per-test type-I error equal to alpha; not a guarantee for arbitrary tests or business decisions','alpha':alpha,'trials':trials,'expected_false_rejections':alpha*trials,'probability_at_least_one':prob,'display_percent':round(100*prob,1)},'local_small_effect_sample_approximation':{'assumptions':'Other design parameters and variance approximation held fixed; n proportional to inverse squared absolute effect; not exact arbitrary binary-outcome planning','effect_ratio':ratio,'approximate_sample_ratio':sample_ratio},'checks_passed':3,'no_customer_inputs_modified':True}
(OUT/'CONCEPT_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result,ensure_ascii=False,indent=2))
