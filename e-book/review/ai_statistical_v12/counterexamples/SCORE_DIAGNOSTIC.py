"""Diagnose constrained-score disagreement using likelihood and polynomial checks."""
from pathlib import Path
import json,math,inspect,hashlib
import numpy as np
from scipy.optimize import brentq,minimize_scalar
from statsmodels.stats.proportion import score_test_proportions_2indep
OUT=Path(__file__).resolve().parent
results=[]
for xa,na,xb,nb in [(50,5000,45,5000),(40,4000,36,4000),(50,5000,110,5000)]:
 d=.005;lo=max(0,-d)+1e-12;hi=min(1,1-d)-1e-12
 def score(q):return xa/q-(na-xa)/(1-q)+xb/(q+d)-(nb-xb)/(1-q-d)
 def ll(q):return xa*math.log(q)+(na-xa)*math.log1p(-q)+xb*math.log(q+d)+(nb-xb)*math.log1p(-q-d)
 q=brentq(score,lo,hi,xtol=1e-14);opt=minimize_scalar(lambda v:-ll(v),bounds=(lo,hi),method='bounded',options={'xatol':1e-15})
 # Independently multiply each term by the common denominator using polynomials.
 P=np.polynomial.Polynomial;Q=P([0.,1.]);one=P([1.]);D=Q+d
 poly=xa*(one-Q)*D*(one-D)-(na-xa)*Q*D*(one-D)+xb*Q*(one-Q)*(one-D)-(nb-xb)*Q*(one-Q)*D
 roots=[float(z.real) for z in poly.roots() if abs(z.imag)<1e-10 and lo<z.real<hi];assert len(roots)==1
 lib=score_test_proportions_2indep(xb,nb,xa,na,value=d,compare='diff',alternative='smaller',correction=True)
 qlib=float(lib.prop2_null)
 results.append({'counts':[xa,na,xb,nb],'null_difference':d,'direct_score_root_qA':q,'numerical_likelihood_max_qA':float(opt.x),'polynomial_root_qA':roots[0],'library_null_qA':qlib,'library_null_qB':float(lib.prop1_null),'direct_score_residual':score(q),'library_score_residual':score(qlib),'loglik_direct_minus_library':ll(q)-ll(qlib),'direct_vs_opt_abs':abs(q-opt.x),'direct_vs_polynomial_abs':abs(q-roots[0]),'polynomial_coefficients_ascending':poly.coef.tolist()})
 assert abs(q-opt.x)<1e-8 and abs(q-roots[0])<1e-10
source=inspect.getsource(score_test_proportions_2indep)
report={'diagnosis':'At the installed statsmodels version, returned constrained null proportions do not solve the binomial likelihood score equations for these nonzero risk differences. Direct score root agrees with independently multiplied polynomial root and numerical likelihood optimization. This is a scoped library implementation discrepancy, not proof that every score calculation is affected.','examples':results,'library_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'library_coefficient_lines':[line.strip() for line in source.splitlines() if 'tmp1 =' in line or 'tmp0 =' in line or 'tmp2 =' in line],'original_data_modified':False,'decision_states_changed':False}
(OUT/'SCORE_DIAGNOSTIC.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
