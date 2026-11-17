"""Separate repeated-sampling demonstration; does not reroll the case dataset.
uv run --with scipy --with statsmodels scripts/simulate_information_v03.py
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import norm
from statsmodels.stats.proportion import power_proportions_2indep
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/virtual-data/v03'
rng=np.random.default_rng(91103)
replications=5000;alpha=.05/3
results=[]
for n in [1000,5000,18001]:
    for scenario,pb in [('no_effect',.09),('planned_effect',.10)]:
        xa=rng.binomial(n,.09,size=replications);xb=rng.binomial(n,pb,size=replications)
        pool=(xa+xb)/(2*n)
        z=(xb/n-xa/n)/np.sqrt(pool*(1-pool)*2/n)
        rejected=int(np.count_nonzero(2*norm.sf(abs(z))<alpha))
        rate=rejected/replications
        expected=alpha if scenario=='no_effect' else float(power_proportions_2indep(.01,.09,n,ratio=1,alpha=alpha,alternative='two-sided',return_results=False))
        mcse=math.sqrt(expected*(1-expected)/replications)
        # A broad stochastic sanity check, not exact method calibration.
        assert abs(rate-expected)<4*mcse+.003
        results.append({'n_per_arm':n,'scenario':scenario,'replications':replications,'rejections':rejected,'observed_rejection_rate':rate,'normal_approx_target':expected,'monte_carlo_se_at_target':mcse})
report={'seed':91103,'alpha_each':alpha,'replications_per_cell':replications,'results':results,'interpretation':'One-contrast repeated independent-binomial normal-approximation tests. Null rejection estimates false positives; alternative rejection estimates power. Same pA=.09 and alternative pB=.10 across N. Not three-arm joint FWER verification or real-world validation. No changes to main generated data or seeds.'}
(OUT/'repeated_sampling_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
