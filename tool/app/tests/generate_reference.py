"""Independent synthetic reference; never imports/reads the application engine.
Run using the isolated SciPy/statsmodels interpreter; --check does not write.
Counts below are fixed before first computation; no RNG or outcome selection.
"""
import argparse
from fractions import Fraction
from math import comb, erfc, isclose, sqrt
from pathlib import Path
import json
import platform
import importlib.metadata

import scipy
from scipy.stats import fisher_exact, norm
import statsmodels
from statsmodels.stats.proportion import proportion_confint, confint_proportions_2indep
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05
Z = float(norm.ppf(1 - ALPHA / 2))
# Preselected scenarios: labels describe counts, not desired significance.
FIXED_CASES = [
    ('ordinary_positive', 120, 1000, 155, 1000),
    ('ordinary_negative', 155, 1000, 120, 1000),
    ('same_rate_balanced', 30, 100, 30, 100),
    ('same_rate_unbalanced', 3, 10, 30, 100),
    ('both_zero', 0, 100, 0, 80),
    ('zero_a', 0, 30, 7, 40),
    ('zero_b', 7, 40, 0, 30),
    ('both_all_success', 50, 50, 80, 80),
    ('all_success_b', 12, 20, 20, 20),
    ('all_success_a', 20, 20, 12, 20),
    ('opposite_extremes', 0, 20, 20, 20),
    ('opposite_extremes_reverse', 20, 20, 0, 20),
    ('unbalanced_small_a', 2, 7, 140, 1000),
    ('unbalanced_small_b', 140, 1000, 2, 7),
    ('rare_balanced', 1, 10000, 5, 10000),
    ('rare_unbalanced', 0, 200000, 3, 150000),
    ('rare_equal', 1, 200000, 1, 200000),
    ('large_moderate', 50000, 200000, 51000, 200000),
    ('large_equal', 100000, 200000, 100000, 200000),
    ('large_unbalanced', 70000, 200000, 18000, 50000),
    ('large_extreme_underflow', 0, 200000, 200000, 200000),
    ('small_classic', 1, 10, 9, 14),
    ('small_probability_ties', 2, 6, 4, 6),
    ('single_observation_opposite', 0, 1, 1, 1),
    ('single_observation_equal', 1, 1, 1, 1),
    ('near_all_success', 999, 1000, 997, 1000),
    ('near_zero_unequal', 1, 97, 2, 113),
    ('unequal_central', 19, 47, 31, 83),
]
INTERACTION_CASES = [
    ('different_effects', (20,100,40,100), (30,100,32,100)),
    ('same_effect', (20,100,30,100), (40,100,50,100)),
    ('negative_interaction', (20,100,22,100), (30,100,50,100)),
    ('unbalanced', (10,50,48,160), (90,300,32,80)),
    ('boundary_five', (5,10,5,10), (5,15,10,15)),
    ('success_four_unsupported', (4,10,6,10), (5,10,5,10)),
    ('failure_four_unsupported', (6,10,5,10), (5,10,5,10)),
    ('zero_unsupported', (0,20,7,20), (8,20,9,20)),
    ('all_success_unsupported', (20,20,17,20), (8,20,9,20)),
    ('zero_denominator_unsupported', (0,0,7,20), (8,20,9,20)),
    ('large', (50000,200000,51000,200000), (40000,200000,40500,200000)),
]
HOLM_CASES = [
    ('one_hypothesis', [0.03], []),
    ('four_unsorted', [0.04,0.001,0.03,0.2], []),
    ('ties', [0.01,0.01,0.04,0.04], []),
    ('stepdown_monotonic', [0.02,0.021,0.022,0.023], []),
    ('zero_and_one', [0.0,1.0,0.5,0.001], []),
    ('unsupported_retained', [0.01,0.02,0.03,1.0], [3]),
    ('all_unsupported', [1.0,1.0,1.0,1.0], [0,1,2,3]),
    ('alpha_boundary', [0.0125,0.02,0.04,0.9], []),
]


def inputs(values):
    return dict(zip(('a_success','a_total','b_success','b_total'), values))


def exact_fisher(a, n, b, m):
    """Probability-ordering two-sided Fisher, exact integer ties, no epsilon."""
    s = a + b
    lo, hi = max(0, s-m), min(n, s)
    denominator = comb(n+m, s)
    observed = comb(n,a) * comb(m,s-a)
    numerator = sum(w for x in range(lo, hi+1)
                    if (w := comb(n,x)*comb(m,s-x)) <= observed)
    return Fraction(numerator, denominator)


def wilson(x, n):
    p, z2 = x/n, Z*Z
    center = (p + z2/(2*n))/(1+z2/n)
    radius = Z*sqrt(p*(1-p)/n+z2/(4*n*n))/(1+z2/n)
    return [max(0.0, center-radius), min(1.0, center+radius)]


def assert_close(actual, expected, label):
    if not isclose(float(actual), float(expected), rel_tol=2e-10, abs_tol=2e-12):
        raise AssertionError(f'{label}: {actual!r} != {expected!r}')


def group_case(name, values, errors):
    a,n,b,m = values
    wa = [float(v) for v in proportion_confint(a,n,alpha=ALPHA,method='wilson')]
    wb = [float(v) for v in proportion_confint(b,m,alpha=ALPHA,method='wilson')]
    ci = [float(v) for v in confint_proportions_2indep(
        b,m,a,n,method='newcomb',compare='diff',alpha=ALPHA,correction=False)]
    d = b/m-a/n
    aw,bw = wilson(a,n),wilson(b,m)
    manual_ci = [d-sqrt((b/m-bw[0])**2+(aw[1]-a/n)**2),
                 d+sqrt((bw[1]-b/m)**2+(a/n-aw[0])**2)]
    for key, actual, expected in [('wilson_a',aw,wa),('wilson_b',bw,wb),('newcombe',manual_ci,ci)]:
        for x,y in zip(actual,expected):
            assert_close(x,y,key)
            errors[key] = max(errors[key],abs(x-y))
    p = float(fisher_exact([[a,n-a],[b,m-b]], alternative='two-sided').pvalue)
    case = {'id':name,'input':inputs(values),'expected':{
        'fisher_p':p,'wilson_a':wa,'wilson_b':wb,'newcombe_diff_ci':ci,'diff':d}}
    if n+m <= 200:
        exact = exact_fisher(a,n,b,m)
        assert_close(p,float(exact),'Fisher exact')
        errors['fisher_exact'] = max(errors['fisher_exact'],abs(p-float(exact)))
        case['exact_fisher_fraction'] = {'numerator':str(exact.numerator),'denominator':str(exact.denominator)}
    if p == 0.0:
        case['numeric_note'] = 'SciPy binary64 underflow; mathematical p is positive, not exactly zero.'
    return case


def interaction_case(name, g1, g2, errors):
    valid_denominators = all(v[1]>0 and v[3]>0 for v in (g1,g2))
    diff = ((g1[2]/g1[3]-g1[0]/g1[1])-(g2[2]/g2[3]-g2[0]/g2[1])) if valid_denominators else None
    supported = valid_denominators and all(min(x,n-x)>=5 for g in (g1,g2) for x,n in ((g[0],g[1]),(g[2],g[3])))
    expected = {'supported':supported,'diff':diff,'standard_error':None,'z':None,'p_raw':None,'ci':None,'holm_input_p':1.0}
    if supported:
        variance = sum((x/n)*(1-x/n)/n for g in (g1,g2) for x,n in ((g[0],g[1]),(g[2],g[3])))
        se = sqrt(variance)
        z = diff/se
        p = float(2*norm.sf(abs(z)))
        manual_p = erfc(abs(z)/sqrt(2))
        assert_close(p,manual_p,'interaction normal tail')
        errors['interaction_p'] = max(errors['interaction_p'],abs(p-manual_p))
        expected.update(standard_error=se,z=z,p_raw=p,ci=[diff-Z*se,diff+Z*se],holm_input_p=p)
    return {'id':name,'input':{'g1':inputs(g1),'g2':inputs(g2)},'expected':expected}


def holm_case(name, pvals, unsupported, errors):
    adjusted = [float(x) for x in multipletests(pvals,alpha=ALPHA,method='holm')[1]]
    order = sorted(range(len(pvals)),key=lambda i:pvals[i])
    manual = [0.0]*len(pvals)
    running = 0.0
    for rank,i in enumerate(order):
        running = max(running,(len(pvals)-rank)*pvals[i])
        manual[i] = min(1.0,running)
    for x,y in zip(manual,adjusted):
        assert_close(x,y,'Holm')
        errors['holm'] = max(errors['holm'],abs(x-y))
    return {'id':name,'input':{'p_values':pvals,'unsupported_indices':unsupported},
            'expected':{'p_adjusted':adjusted,'reject':[p<=ALPHA for p in adjusted]}}


def build():
    errors = dict.fromkeys(['fisher_exact','wilson_a','wilson_b','newcombe','interaction_p','holm'],0.0)
    cases = [group_case(name,values,errors) for name,*values in FIXED_CASES]
    # All possible success counts for both totals in 1..4; no random sampling.
    for n in range(1,5):
        for m in range(1,5):
            for a in range(n+1):
                for b in range(m+1):
                    cases.append(group_case(f'exhaustive_{a}_{n}_{b}_{m}',(a,n,b,m),errors))
    interactions = [interaction_case(*case,errors) for case in INTERACTION_CASES]
    holm = [holm_case(*case,errors) for case in HOLM_CASES]
    return {
        'schema_version':'1.0','synthetic':True,'alpha':ALPHA,'confidence_level':1-ALPHA,
        'selection':{'rng_used':False,'seed':None,'fixed_scenarios':len(FIXED_CASES),'exhaustive_small_total_range':[1,4]},
        'reference':{'python':platform.python_version(),'scipy':scipy.__version__,'statsmodels':statsmodels.__version__,
                     'installed_distributions':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()))},
        'methods':{'fisher':'scipy.stats.fisher_exact, alternative=two-sided, default exact method, rows A/B, columns success/failure; exact Fraction cross-check when combined n<=200',
                   'wilson':'statsmodels proportion_confint(method=wilson, alpha=0.05)',
                   'newcombe':'statsmodels confint_proportions_2indep(count1=B, count2=A, method=newcomb, compare=diff, alpha=0.05, correction=False)',
                   'interaction':'unpooled Wald risk-difference contrast G1-G2, independent four-binomial variance; scipy norm.sf two-sided; each success/failure>=5',
                   'holm':'statsmodels multipletests(method=holm, alpha=0.05); unsupported hypotheses retained as 1, not computed p'},
        'recommended_tolerances':{'probability_and_ci_absolute':1e-10,'p_relative':1e-7,
             'tiny_p_policy':'For 0<reference p<1e-10 require relative error <=1e-7 instead of absolute tolerance; do not accept zero. For reference underflow zero, accept binary64 zero but do not interpret as mathematical zero.'},
        'verification':{'max_absolute_discrepancy':errors,'exact_fraction_case_count':sum('exact_fisher_fraction' in c for c in cases)},
        'cases':cases,'interaction_cases':interactions,'holm_cases':holm}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Recompute and compare existing JSON without writing')
    args = parser.parse_args()
    result = build()
    path = Path(__file__).resolve().with_name('golden_reference.json')
    if args.check:
        existing = json.loads(path.read_text(encoding='utf-8'))
        if existing != result:
            raise AssertionError('Fixture differs from recomputed output (including environment versions)')
    else:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','mode':'check' if args.check else 'generate',
        'path':str(path),'group_cases':len(result['cases']),
        'interaction_cases':len(result['interaction_cases']),'holm_cases':len(result['holm_cases']),
        'verification':result['verification'],'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},indent=2))


if __name__ == '__main__':
    main()
