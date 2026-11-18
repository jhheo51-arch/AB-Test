"""Independent fixed-count counterexample audit; no original analysis imports."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,math,platform,sys
import scipy,statsmodels
from scipy.stats import norm
from scipy.optimize import brentq
from statsmodels.stats.proportion import confint_proportions_2indep,test_proportions_2indep
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
fixture_path=ROOT/'e-book/exports/v12/counterexample_fixture.json';reference_path=ROOT/'e-book/exports/v12/COUNTEREXAMPLE_RESULTS.json'
fixture=json.loads(fixture_path.read_text(encoding='utf-8'));source_hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [fixture_path,reference_path]}
checks=[];cases=[]
def check(name,actual,expected,tol=1e-8):
 if isinstance(actual,(float,int)) and not isinstance(actual,bool):passed=math.isclose(actual,expected,abs_tol=tol,rel_tol=1e-8)
 else:passed=actual==expected
 checks.append({'check':name,'actual':actual,'expected':expected,'absolute_tolerance':tol,'status':'passed' if passed else 'mismatch'})
def wilson(x,n,alpha):
 p=x/n;z=norm.isf(alpha/2);den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return mid-half,mid+half
def newcombe(xa,na,xb,nb,alpha):
 a,b=xa/na,xb/nb;la,ua=wilson(xa,na,alpha);lb,ub=wilson(xb,nb,alpha);d=b-a
 return d-math.hypot(b-lb,ua-a),d+math.hypot(ub-b,a-la)
def score_z(xa,na,xb,nb,delta):
 lo=max(0.,-delta)+1e-12;hi=min(1.,1-delta)-1e-12
 def derivative(q):return xa/q-(na-xa)/(1-q)+xb/(q+delta)-(nb-xb)/(1-q-delta)
 left,right=derivative(lo),derivative(hi)
 q=brentq(derivative,lo,hi,xtol=1e-14) if left*right<0 else (lo if left<0 else hi)
 qb=q+delta;variance=(q*(1-q)/na+qb*(1-qb)/nb)*(na+nb)/(na+nb-1)
 return (xb/nb-xa/na-delta)/math.sqrt(variance)
def calculate(c,alpha,minimum_pp,margin_pp):
 xa,na,xb,nb=c['completed_A'],c['n_A'],c['completed_B'],c['n_B'];ci=newcombe(xa,na,xb,nb,alpha)
 lib=confint_proportions_2indep(xb,nb,xa,na,method='newcomb',compare='diff',alpha=alpha)
 for k,(x,y) in enumerate(zip(ci,lib)):check(c['id']+f'/manual_newcombe_vs_library/{k}',x,y,1e-12)
 wa,wb=c['withdrawn_A'],c['withdrawn_B'];d=wb/nb-wa/na
 z=score_z(wa,na,wb,nb,margin_pp/100);p=norm.cdf(z)
 libtest=test_proportions_2indep(wb,nb,wa,na,value=margin_pp/100,method='score',compare='diff',alternative='smaller',correction=True)
 check(c['id']+'/manual_constrained_score_z',z,float(libtest.statistic),1e-8);check(c['id']+'/manual_score_p',p,float(libtest.pvalue),1e-9)
 upper=brentq(lambda delta:score_z(wa,na,wb,nb,delta)+norm.isf(alpha),d+1e-10,min(.5,1-1e-8),xtol=1e-13)
 libci=confint_proportions_2indep(wb,nb,wa,na,method='score',compare='diff',alpha=2*alpha,correction=True)
 check(c['id']+'/manual_score_upper_vs_library',upper,float(libci[1]),2e-8)
 guard=p<alpha and upper<margin_pp/100
 state='protection_review' if not guard else ('execution_candidate' if ci[0]>minimum_pp/100 else 'additional_evidence')
 return {'id':c['id'],'difference_pp':100*(xb/nb-xa/na),'performance_interval_pp':[100*x for x in ci],'alpha_per_population':alpha,'guard_difference_pp':100*d,'guard_one_sided_upper_pp':100*upper,'guard_NI_p':float(p),'guard_pass':bool(guard),'state':state,'actual_approval':'not_performed'}
# Calculate everything from the input counts before reading comparison outputs.
for c in fixture['cases']:
 alpha=.05/c['family_size'];r=calculate(c,alpha,c['minimum_effect_pp'],c['guard_margin_pp']);cases.append(r);check(c['id']+'/declared_expected_state',r['state'],c['expected'])
 if 'other_prespecified_group' in c:
  other=dict(c['other_prespecified_group'],id=c['id']+'_other');r['other_group']=calculate(other,alpha,c['minimum_effect_pp'],c['guard_margin_pp'])
reference=json.loads(reference_path.read_text(encoding='utf-8'))
def compare(r,ref):
 for key in ['difference_pp','guard_difference_pp','guard_one_sided_upper_pp','guard_NI_p','guard_pass','state','actual_approval']:check(r['id']+'/reference/'+key,r[key],ref[key],2e-6 if key=='guard_one_sided_upper_pp' else 1e-8)
 for k in range(2):check(r['id']+f'/reference/performance_interval_pp/{k}',r['performance_interval_pp'][k],ref['performance_interval_pp'][k],1e-8)
 if 'other_group' in r:compare(r['other_group'],ref['other_group'])
for r,ref in zip(cases,reference['cases']):compare(r,ref)
for name,sha in source_hashes.items():check('input_unchanged/'+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
report={'kind':'AI and separately implemented numerical audit, not human review','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'environment':{'python':platform.python_version(),'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'input_hashes':source_hashes,'method':'Direct Wilson-Newcombe construction; constrained-binomial likelihood score under fixed risk difference with MN finite-sample correction; one-sided upper bound obtained by root inversion; separate statsmodels checks','cases':cases,'checks':checks,'summary':{'total':len(checks),'passed':sum(x['status']=='passed' for x in checks),'mismatch':sum(x['status']=='mismatch' for x in checks)},'limits':['Fixed educational counts only, no individual event database for these counterexamples','No human expert approval or production validation','No original builder imported, executed or reused','Missing-measurement and optional-survey states of the old user interface are not independently retested here']}
(OUT/'RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
lines=['# 고정 반례의 별도 재계산 검수','',report['kind'],'',report['method'],'','| 사례 | 완료 차이 pp | 완료 구간 pp | 보호 단측 상한 pp | 비열등성 p | 상태 |','|---|---:|---|---:|---:|---|']
for r in cases:lines.append(f"| {r['id']} | {r['difference_pp']:+.6f} | [{r['performance_interval_pp'][0]:+.6f}, {r['performance_interval_pp'][1]:+.6f}] | {r['guard_one_sided_upper_pp']:+.6f} | {r['guard_NI_p']:.9f} | {r['state']} |")
lines+=['',f"검사 {len(checks)}개: 통과 {report['summary']['passed']}개, 불일치 {report['summary']['mismatch']}개. 기존 출력과의 비교는 새 계산을 만든 뒤 수행했다.",'','P02의 다른 사전 집단도 같은 비교 가족 수준에서 재계산했다. 성과와 보호를 함께 충족해야 하는 적용 주장은 교집합 조건이며 두 적용 집단의 Bonferroni 범위와 구분했다. 계산 일치는 사전등록이나 실행 승인, 현장 효과를 입증하지 않는다.','','실행: `uv run --with scipy --with statsmodels python e-book/review/ai_statistical_v12/counterexamples/RECALCULATE.py`','','미검증: 원 UI의 선택 설문 및 측정 누락 분기, 실제 사람 수행과 현장 운영.']
(OUT/'REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report['summary']));sys.exit(0 if not report['summary']['mismatch'] else 1)
