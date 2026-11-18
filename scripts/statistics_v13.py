"""Canonical v13 corrections. No legacy modules or library score tests used.
Power: fixed planned probabilities, weighted pooled-null normal approximation.
NI: constrained binomial likelihood root, MN N/(N-1), one-sided inversion.
Inputs use B-A risk difference. Requires scipy and numpy; see runner command.
"""
import math
from statistics import NormalDist
from scipy.optimize import brentq

NORMAL = NormalDist()


def planned_power(*, p_A, n_A, p_B, n_B, alpha):
    if not (0 < p_A < 1 and 0 < p_B < 1 and n_A > 0 and n_B > 0 and 0 < alpha < 1):
        raise ValueError('Interior planning probabilities, positive group sizes and valid alpha required')
    pooled = (n_A*p_A + n_B*p_B)/(n_A+n_B)
    null_sd = math.sqrt(pooled*(1-pooled)*(1/n_A+1/n_B))
    alt_sd = math.sqrt(p_A*(1-p_A)/n_A + p_B*(1-p_B)/n_B)
    delta = p_B-p_A
    critical = NORMAL.inv_cdf(1-alpha/2)*null_sd
    return NORMAL.cdf((-critical-delta)/alt_sd) + NORMAL.cdf((delta-critical)/alt_sd)


def likelihood_derivative(q_A, *, x_A, n_A, x_B, n_B, difference):
    q_B = q_A+difference
    return x_A/q_A - (n_A-x_A)/(1-q_A) + x_B/q_B - (n_B-x_B)/(1-q_B)


def constrained_fit(*, x_A, n_A, x_B, n_B, difference):
    # All frozen fixtures have interior successes/failures. Explicitly reject
    # unsupported boundary-count cases instead of silently clipping their MLE.
    if not (0 < x_A < n_A and 0 < x_B < n_B and -1 < difference < 1):
        raise ValueError('This canonical path supports interior counts and -1 < difference < 1 only')
    lo = max(0., -difference)
    hi = min(1., 1.-difference)
    eps = min(1e-14, (hi-lo)*1e-8)
    args = dict(x_A=x_A, n_A=n_A, x_B=x_B, n_B=n_B, difference=difference)
    q_A = brentq(lambda q: likelihood_derivative(q, **args), lo+eps, hi-eps,
                 xtol=5e-324, rtol=1e-14)
    q_B = q_A+difference
    variance = (q_A*(1-q_A)/n_A + q_B*(1-q_B)/n_B)*(n_A+n_B)/(n_A+n_B-1)
    z = (x_B/n_B-x_A/n_A-difference)/math.sqrt(variance)
    return dict(q_A=q_A, q_B=q_B, variance_MN=variance, z=z,
                score_residual=likelihood_derivative(q_A, **args))


def score_ni(*, x_A, n_A, x_B, n_B, margin, alpha):
    counts = dict(x_A=x_A, n_A=n_A, x_B=x_B, n_B=n_B)
    fitted = constrained_fit(**counts, difference=margin)
    p = NORMAL.cdf(fitted['z'])
    observed = x_B/n_B-x_A/n_A
    critical = NORMAL.inv_cdf(1-alpha)
    upper = brentq(lambda d: constrained_fit(**counts, difference=d)['z']+critical,
                   observed, 1.-1e-8, xtol=1e-14, rtol=1e-14)
    return dict(p=p, upper=upper, passes=p < alpha, fit_at_margin=fitted,
                upper_inversion_residual=constrained_fit(**counts, difference=upper)['z']+critical)
