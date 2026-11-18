# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "statsmodels"]
# ///
"""Read-only source audit, cases 4-6. Writes only sibling RESULTS.json/REVIEW.md.
No original analysis/generator imports or execution. Separate AI/code review, not human review.
Run from repository: uv run e-book/review/ai_statistical_v12/scenarios/RECALCULATE.py
"""
from pathlib import Path
from collections import Counter, defaultdict
from statistics import NormalDist
from importlib.metadata import version
import csv, hashlib, json, math, platform, re, subprocess, sys
import numpy as np
from scipy import stats
from scipy.special import logsumexp
import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint, confint_proportions_2indep, proportions_ztest

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DATA = ROOT / 'e-book/analysis/winner_v04/scenarios'
LEDGER = ROOT / 'e-book/analysis/winner_v04/scenario_results.json'
MANUSCRIPT = ROOT / 'e-book/exports/v12/ebook_review_v12.md'
CHECKS = []

def check(name, actual, expected, tolerance=0, blocked=False, note=None):
    if blocked:
        status = 'blocked'
    else:
        def same(a, b):
            if isinstance(b, dict):
                return isinstance(a, dict) and set(a) == set(b) and all(same(a[k], v) for k,v in b.items())
            if isinstance(b, (list, tuple)):
                return isinstance(a, (list, tuple)) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
            if isinstance(b, (float, int)) and not isinstance(b, bool):
                return isinstance(a, (float,int)) and math.isfinite(a) and abs(a-b)<=tolerance
            return a == b
        status = 'passed' if same(actual,expected) else 'mismatch'
    row = dict(id=name, actual=actual, expected=expected, tolerance=tolerance, status=status)
    if note: row['note']=note
    CHECKS.append(row)

def read(name):
    with (DATA/name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def fingerprint(paths):
    return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def wilson(x,n,alpha):
    p=x/n; z=NormalDist().inv_cdf(1-alpha/2); zz=z*z
    mid=(p+zz/(2*n))/(1+zz/n)
    radius=z/(1+zz/n)*math.sqrt(p*(1-p)/n+zz/(4*n*n))
    return [mid-radius,mid+radius]

def tail(z): return math.erfc(abs(z)/math.sqrt(2))

def fisher_manual(xb,nb,xa,na):
    # Fixed-margin hypergeometric table probability; two-sided probability ordering.
    total=na+nb; events=xa+xb
    def lc(n,k): return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
    def lp(k): return lc(events,k)+lc(total-events,nb-k)-lc(total,nb)
    observed=lp(xb)
    values=[lp(k) for k in range(max(0,nb-(total-events)),min(nb,events)+1)]
    return min(1.,float(math.exp(logsumexp([v for v in values if v<=observed+1e-9]))))

def comparison(rows,label,alpha=.05,fisher=False):
    groups={}
    for arm in ('A','B'):
        vals=[int(r['completed']) for r in rows if r['arm']==arm]
        n=len(vals); x=sum(vals)
        groups[arm]=dict(n=n,success=x,rate=x/n,wilson_ci=wilson(x,n,alpha))
        check(label+'.'+arm+'.Wilson_vs_statsmodels',groups[arm]['wilson_ci'],list(proportion_confint(x,n,alpha=alpha,method='wilson')),1e-12)
    a,b=groups['A'],groups['B']; pa,pb=a['rate'],b['rate']; d=pb-pa
    al,au=a['wilson_ci']; bl,bu=b['wilson_ci']
    ci=[d-math.hypot(pb-bl,au-pa),d+math.hypot(bu-pb,pa-al)]
    pooled=(a['success']+b['success'])/(a['n']+b['n'])
    z=d/math.sqrt(pooled*(1-pooled)*(1/a['n']+1/b['n']))
    p=tail(z)
    check(label+'.Newcombe_vs_statsmodels',ci,list(confint_proportions_2indep(b['success'],b['n'],a['success'],a['n'],method='newcomb',alpha=alpha)),1e-12)
    lz,lp=proportions_ztest([b['success'],a['success']],[b['n'],a['n']])
    check(label+'.z_vs_statsmodels',z,float(lz),1e-12)
    check(label+'.p_vs_statsmodels',p,float(lp),max(1e-300,abs(p)*1e-10))
    out=dict(groups=groups,difference_B_minus_A=d,newcombe_ci=ci,confidence=1-alpha,z=z,p_two_sided=p)
    if fisher:
        fp=fisher_manual(b['success'],b['n'],a['success'],a['n'])
        library=float(stats.fisher_exact([[b['success'],b['n']-b['success']],[a['success'],a['n']-a['success']]]).pvalue)
        check(label+'.Fisher_vs_scipy',fp,library,max(1e-300,library*1e-8))
        out['fisher_exact_two_sided_p']=fp
    return out

def numeric_ledger(actual,expected,prefix):
    # Compare calculated fields only; no claim of rerunning generation/seeds.
    for key,a in actual.items():
        name=prefix+'.'+key
        if key not in expected:
            check(name,a,None,note='calculated field absent from existing ledger')
        elif isinstance(a,dict): numeric_ledger(a,expected[key],name)
        elif isinstance(a,list) and a and isinstance(a[0],dict):
            for i,item in enumerate(a): numeric_ledger(item,expected[key][i],name+f'[{i}]')
        elif isinstance(a,(int,float,list)):
            tol=0 if isinstance(a,int) else (max(abs(a)*1e-8,1e-300) if isinstance(a,float) and ('p_two' in key or 'fisher' in key or 'bonferroni' in key) else 1e-12)
            check(name,a,expected[key],tol)


def main():
    # The bundled MSYS git may not launch via native Windows CreateProcess.
    git='C:/Program Files/Git/cmd/git.exe' if Path('C:/Program Files/Git/cmd/git.exe').is_file() else 'git'
    head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    tracked=subprocess.check_output([git,'ls-files'],cwd=ROOT,text=True).splitlines()
    protected=[ROOT/p for p in tracked if p.endswith('.csv') or 'plan' in p.lower() or p.endswith('_results.json') or p in ('e-book/exports/v12/ebook_review_v12.md','scripts/build_winner_scenarios_v04.py','e-book/manuscript/winner_cases_456_v04.md')]
    protected=[p for p in protected if p.is_file()]
    before=fingerprint(protected)
    check('repository.HEAD',head,'eefdd4ee9ea026c06d65a760706a742e02407bce')
    old=json.loads(LEDGER.read_text(encoding='utf-8'))
    text=MANUSCRIPT.read_text(encoding='utf-8'); lines=text.splitlines()
    truth=read('case4_truth.csv'); logs=read('case4_log.csv'); c5=read('case5_customers.csv')
    for name,rows,n in [('case4.truth',truth,8000),('case4.log',logs,8000),('case5',c5,12000)]:
        check(name+'.rows',len(rows),n)
        check(name+'.unique_IDs',len({r['customer_id'] for r in rows}),n)
        check(name+'.28_day_invalid_rows',sum(r['observation_days']!='28' for r in rows),0)
        check(name+'.binary_and_valid_arm_invalid_rows',sum(r['completed'] not in ('0','1') or r['arm'] not in ('A','B') for r in rows),0)
    ti={r['customer_id']:r for r in truth}; li={r['customer_id']:r for r in logs}
    check('case4.ID_sets_symmetric_difference',len(set(ti)^set(li)),0)
    joined=[(ti[k],li[k]) for k in ti.keys() & li.keys()]
    check('case4.customer_join.arm_window_and_outcome_minus_log_equals_missing.invalid',sum(a['arm']!=b['arm'] or a['observation_days']!=b['observation_days'] or int(a['completed'])-int(b['completed'])!=int(b['injected_missing']) for a,b in joined),0)
    missing={arm:sum(int(b['injected_missing']) for a,b in joined if a['arm']==arm) for arm in ('A','B')}
    check('case4.missing_only_B_completed.invalid',sum(b['injected_missing'] not in ('0','1') or (int(b['injected_missing']) and (a['arm']!='B' or a['completed']!='1')) for a,b in joined),0)
    case4=dict(truth=comparison(truth,'case4.truth',fisher=True),log=comparison(logs,'case4.log',fisher=True),injected_missing=sum(missing.values()))
    check('case4.opposite_sign_CIs',[case4['truth']['newcombe_ci'][0]>0,case4['log']['newcombe_ci'][1]<0],[True,True])
    numeric_ledger(case4,old['case4'],'ledger.case4')
    segments={s:comparison([r for r in c5 if r['pretreatment_segment']==s],'case5.'+s,alpha=.025) for s in ('new','existing')}
    check('case5.segment_values',sorted({r['pretreatment_segment'] for r in c5}),['existing','new'])
    for s,v in segments.items():
        check('case5.'+s+'.arm_sizes',[v['groups'][a]['n'] for a in ('A','B')],[3000,3000])
        v['bonferroni_two_group_p']=min(1.,2*v['p_two_sided'])
    overall=comparison(c5,'case5.pooled_reference')
    # Independent per-cell binomial variances and customer-level HC0 covariance.
    cells=[(s,a) for s in ('new','existing') for a in ('A','B')]
    means=np.array([segments[s]['groups'][a]['rate'] for s,a in cells])
    variances=np.array([segments[s]['groups'][a]['rate']*(1-segments[s]['groups'][a]['rate'])/segments[s]['groups'][a]['n'] for s,a in cells])
    X=np.array([[float((r['pretreatment_segment'],r['arm'])==c) for c in cells] for r in c5])
    y=np.array([int(r['completed']) for r in c5])
    fitted=sm.OLS(y,X).fit(cov_type='HC0',use_t=False)
    effects={}
    for name,w in [('stratified_primary',np.array([-.5,.5,-.5,.5])),('interaction',np.array([-1.,1.,1.,-1.]))]:
        estimate=float(w@means); se=math.sqrt(float((w*w)@variances)); zcrit=NormalDist().inv_cdf(.975)
        result=dict(estimate=estimate,se=se,wald_ci=[estimate-zcrit*se,estimate+zcrit*se],confidence=.95,p_two_sided=tail(estimate/se))
        library=fitted.t_test(w)
        check('case5.'+name+'.estimate_vs_statsmodels_HC0',estimate,float(np.asarray(library.effect).item()),1e-12)
        check('case5.'+name+'.se_vs_statsmodels_HC0',se,float(np.asarray(library.sd).item()),1e-12)
        check('case5.'+name+'.CI_vs_statsmodels_HC0',result['wald_ci'],np.asarray(library.conf_int()).ravel().tolist(),1e-12)
        check('case5.'+name+'.p_vs_statsmodels_HC0',result['p_two_sided'],float(np.asarray(library.pvalue).item()),max(result['p_two_sided']*1e-9,1e-300))
        effects[name]=result
    overall['stratified_primary']=effects['stratified_primary']
    case5=dict(overall=overall,segments=segments,interaction=effects['interaction'])
    numeric_ledger(case5,old['case5'],'ledger.case5')
    check('case5.equal_weight_point_identity',overall['difference_B_minus_A'],effects['stratified_primary']['estimate'],1e-12)
    transfer=.2*segments['new']['difference_B_minus_A']+.8*segments['existing']['difference_B_minus_A']

    base=read('case6_fixed_demand.csv'); ops=read('case6_operations.csv'); spec=old['case6']['generation']
    check('case6.fixed_rows',len(base),12000); check('case6.fixed_unique_IDs',len({r['customer_id'] for r in base}),12000)
    check('case6.pilot_B_count',sum(int(r['pilot_B']) for r in base),1200)
    check('case6.latent_invalid_rows',sum(not (1<=int(r['arrival_day'])<=28 and r['pilot_B'] in ('0','1') and all(0<=float(r[k])<1 for k in ('request_u','completion_u','arrival_priority'))) for r in base),0)
    check('case6.operations_rows',len(ops),108000)
    buckets=defaultdict(list)
    for row in ops: buckets[(int(row['capacity_per_day']),row['policy'])].append(row)
    capacities=[40,60,90]; policies=['all_A','pilot_10pct_B','all_B']
    check('case6.scenario_keys',sorted([list(k) for k in buckets]),sorted([[c,p] for c in capacities for p in policies]))
    summaries=[]
    for cap in capacities:
        for policy in policies:
            label=f'case6.{cap}.{policy}'; actual_rows=buckets[(cap,policy)]
            actual={r['customer_id']:r for r in actual_rows}
            check(label+'.rows',len(actual_rows),12000)
            check(label+'.unique_IDs',len(actual),12000)
            check(label+'.ID_set_delta',len(set(actual)^{r['customer_id'] for r in base}),0)
            # Separately implement FCFS: construct requests, partition by day, then select
            # first capacity requests per day's order. No incremental original slot loop.
            daily=defaultdict(list); reconstructed={}
            for r in base:
                arm='B' if policy=='all_B' or (policy=='pilot_10pct_B' and int(r['pilot_B'])==1) else 'A'
                requested=int(float(r['request_u'])<spec['request_probability'][arm])
                result=dict(arm=arm,arrival_day=int(r['arrival_day']),requested=requested)
                reconstructed[r['customer_id']]=result
                if requested: daily[int(r['arrival_day'])].append(r)
            selected=set()
            for day,requests in daily.items():
                ordered=sorted(requests,key=lambda r:(float(r['arrival_priority']),r['customer_id']))
                selected.update(r['customer_id'] for r in ordered[:cap])
            totals=Counter(); arm_totals={a:dict(arm=a,n=0,completed=0) for a in ('A','B')}
            wrong=Counter()
            for r in base:
                k=r['customer_id']; result=reconstructed[k]; arm=result['arm']
                accepted=int(k in selected); waiting=result['requested']-accepted
                done=int(accepted and float(r['completion_u'])<spec['completion_given_accepted'][arm])
                contact=spec['contact_cost_krw'][arm]
                cost=contact+accepted*spec['accepted_service_cost_krw']+waiting*spec['unserved_request_cost_krw']
                result.update(accepted=accepted,waiting_end_window=waiting,completed=done,contact_cost_krw=contact,variable_cost_krw=cost)
                stored=actual.get(k,{})
                for field,value in result.items():
                    observed=stored.get(field)
                    if field!='arm' and observed is not None: observed=int(observed)
                    wrong[field]+=int(observed!=value)
                totals.update({key:result[key] for key in ('requested','accepted','waiting_end_window','completed','variable_cost_krw')})
                arm_totals[arm]['n']+=1; arm_totals[arm]['completed']+=done
            for field in reconstructed[base[0]['customer_id']]: check(label+'.row_reconstruction.'+field+'.mismatches',wrong[field],0)
            check(label+'.row_funnel_invalid',sum(not (int(r['completed'])<=int(r['accepted'])<=int(r['requested']) and int(r['requested'])==int(r['accepted'])+int(r['waiting_end_window'])) for r in actual_rows),0)
            daycounts=Counter()
            for r in actual_rows: daycounts[int(r['arrival_day'])]+=int(r['accepted'])
            check(label+'.daily_capacity_exceeded_days',sum(v>cap for v in daycounts.values()),0)
            capacity_cost=cap*spec['days']*spec['staffed_slot_day_cost_krw']
            value=totals['completed']*spec['value_per_completion_krw']; total_cost=totals['variable_cost_krw']+capacity_cost
            summary=dict(capacity_per_day=cap,policy=policy,customers=len(base),**totals,capacity_cost_krw=capacity_cost,total_cost_krw=total_cost,completed_value_krw=value,net_value_krw=value-total_cost,waiting_fraction_of_requests=totals['waiting_end_window']/totals['requested'],pilot_arm_descriptive=list(arm_totals.values()))
            reference=next(s for s in old['case6']['summaries'] if s['capacity_per_day']==cap and s['policy']==policy)
            numeric_ledger(summary,reference,'ledger.'+label)
            summaries.append(summary)
    for policy in policies:
        ss=[s for s in summaries if s['policy']==policy]
        check('case6.'+policy+'.requests_constant_across_capacities',len({s['requested'] for s in ss}),1)
        check('case6.'+policy+'.accepted_monotone',[s['accepted'] for s in ss],sorted(s['accepted'] for s in ss))
    focus={s['policy']:s for s in summaries if s['capacity_per_day']==60}
    a,b=focus['all_A'],focus['all_B']
    pilot=focus['pilot_10pct_B']['pilot_arm_descriptive']; pa,pb=pilot
    pilot_rd=pb['completed']/pb['n']-pa['completed']/pa['n']
    naive_extrapolation=pilot_rd*12000

    # Manuscript numeric assertions: actual=recomputed, expected=printed; tolerance
    # is half the printed last digit, separately for every numeric token.
    number_re=re.compile(r'(?<![A-Za-z_])[-+]?\d[\d,]*(?:\.\d+)?(?:e[-+]?\d+)?',re.I)
    def prose(line,expected):
        tokens=number_re.findall(lines[line-1])
        check(f'manuscript.L{line}.numeric_token_count',len(tokens),len(expected))
        for i,(token,value) in enumerate(zip(tokens,expected)):
            raw=token.replace(',',''); mant,_,exponent=raw.lower().partition('e')
            digits=len(mant.split('.')[1]) if '.' in mant else 0
            tolerance=(.5*10**(int(exponent or '0')-digits)) if ('.' in raw or exponent) else 0
            check(f'manuscript.L{line}.token{i+1}',float(value),float(raw),tolerance+abs(value)*1e-14,note='source token '+token)
    t=case4['truth']; l=case4['log']; p=effects['stratified_primary']; inter=effects['interaction']; n=segments['new']; e=segments['existing']
    prose(423,[.50,case4['injected_missing']]); prose(425,[4000])
    prose(427,[480,4000,12,630,4000,15.75,100*t['difference_B_minus_A'],95,*[100*x for x in t['newcombe_ci']],t['p_two_sided'],480,4000,12,289,4000,100*l['groups']['B']['rate'],100*l['difference_B_minus_A'],95,*[100*x for x in l['newcombe_ci']],l['p_two_sided'],0])
    prose(429,[95,*[100*x for x in t['groups']['A']['wilson_ci']],*[100*x for x in t['groups']['B']['wilson_ci']],*[100*x for x in l['groups']['A']['wilson_ci']],*[100*x for x in l['groups']['B']['wilson_ci']],t['fisher_exact_two_sided_p'],l['fisher_exact_two_sided_p']])
    prose(455,[100*p['estimate'],95,*[100*x for x in p['wald_ci']],p['p_two_sided'],820,6000,100*820/6000,960,6000,16,100*overall['difference_B_minus_A'],95,*[100*x for x in overall['newcombe_ci']],overall['p_two_sided'],1])
    prose(457,[217,3000,100*217/3000,455,3000,100*455/3000,100*n['difference_B_minus_A'],97.5,*[100*x for x in n['newcombe_ci']],n['p_two_sided'],n['bonferroni_two_group_p'],603,3000,20.10,505,3000,100*505/3000,100*e['difference_B_minus_A'],97.5,*[100*x for x in e['newcombe_ci']],e['p_two_sided'],e['bonferroni_two_group_p'],97.5])
    prose(459,[100*inter['estimate'],100*inter['se'],95,*[100*x for x in inter['wald_ci']],inter['p_two_sided'],1])
    prose(465,[100*p['estimate'],20,80,100*transfer,.2,.8])
    prose(479,[60,b['completed']-a['completed'],abs(b['net_value_krw']-a['net_value_krw']),100*b['waiting_fraction_of_requests']])
    for line,s in zip(range(493,502),summaries):
        labelnum=[10] if s['policy']=='pilot_10pct_B' else []
        prose(line,[s['capacity_per_day'],*labelnum,s['requested'],s['completed'],s['waiting_end_window'],s['net_value_krw']])
    prose(503,[40,10,*[s['accepted'] for s in summaries[:3]],*[s['total_cost_krw'] for s in summaries[:3]],60,*[s['accepted'] for s in summaries[3:6]],*[s['total_cost_krw'] for s in summaries[3:6]],90,*[s['accepted'] for s in summaries[6:]],*[s['total_cost_krw'] for s in summaries[6:]]])
    prose(505,[a['completed'],10,focus['pilot_10pct_B']['completed'],b['completed'],b['requested'],b['waiting_end_window'],100*b['waiting_fraction_of_requests'],10])
    prose(511,[90,summaries[-1]['completed'],summaries[-1]['net_value_krw']])
    for phrase in ['고정한 한 수요 세계의 조건부 결과','개인 독립 95% 신뢰구간이나 두 이항비율 검정 p값을 붙이지 않는다','주분석과 함께 확증하는 가족 전체 오류율을 통제한 설계는 아니다','전체 pooled z검정과 Newcombe 구간은 참고값']:
        check('manuscript.interpretation.'+phrase,phrase in text,True)
    check('inference.national_rollout_effect',None,'independent location/time or saturation policy experiment',blocked=True,note='Customer-level effect cannot identify national rollout under interference. Fixed-world simulation is not such an estimate.')
    check('provenance.prospective_plan_timing',None,'dated frozen case4-6 plan prior to outcomes',blocked=True,note='Specification and manuscript state prespecification; CSV/ledger cannot authenticate prospective timing or absence of seed selection. Existing v03 plan is preserved, not evidence for these added scenarios.')
    check('validity.real_outcomes_costs_safety',None,'real OEM operational validation and guardrail data',blocked=True,note='Synthetic data only; no human-independent review, real safety, external validity, cluster design or repeated-demand inference tested.')
    after=fingerprint(protected)
    for path,digest in before.items(): check('preservation.sha256.'+path,after[path],digest)
    counts={status:sum(c['status']==status for c in CHECKS) for status in ('passed','mismatch','blocked')}
    command='uv run e-book/review/ai_statistical_v12/scenarios/RECALCULATE.py'
    result=dict(review_type='separate AI/code recomputation, NOT independent human statistical review',head=head,command=command,environment=dict(python=platform.python_version(),numpy=version('numpy'),scipy=version('scipy'),statsmodels=version('statsmodels')),source_hashes_before=before,source_hashes_after=after,methods=dict(case4='customer-ID join; manual Wilson/Newcombe/pooled-z/Fisher checked against statsmodels/scipy',case5='fixed 0.5/0.5 standardized risk difference and within-cell binomial Wald variance; saturated cell-means OLS HC0 normal-contrast library check; pooled Newcombe reference only',case6='full per-customer FCFS reconstruction from fixed latent CSV by day-wise sorted request selection; no carry-over or slot reuse; all saved fields checked, not just totals'),case4=case4,case4_missing_by_arm=missing,case5=case5,case5_transfer_new20_existing80=transfer,case6=dict(summaries=summaries,pilot60_descriptive_risk_difference=pilot_rd,invalid_naive_national_extrapolation_count=naive_extrapolation,actual_fixed_world_allB_minus_allA_completions=b['completed']-a['completed'],inference='single fixed demand world, no inferential CI'),summary=counts,checks=CHECKS)
    (OUT/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    mismatches=[c for c in CHECKS if c['status']=='mismatch']
    review=['# v0.12 사례 4–6 별도 AI/코드 재계산 검수','',f'- HEAD: `{head}`',f'- 검사 상태: {counts}. 사람 독립검수·외부 전문가 승인 아님.',f'- 실행 명령: `{command}`',f'- Python {platform.python_version()}; numpy {version("numpy")}, scipy {version("scipy")}, statsmodels {version("statsmodels")}. 의존성은 RECALCULATE.py PEP 723로 선언.','', '## 발견사항',f'- 사례 4: ID 연결 누락 A={missing["A"]}, B={missing["B"]}. 원장 B−A {100*t["difference_B_minus_A"]:+.4f}pp → 로그 {100*l["difference_B_minus_A"]:+.4f}pp. 분모 유지, B 완료 사건 누락으로 구간 방향도 역전.',f'- 사례 5: 고정 0.5/0.5 주효과 {100*p["estimate"]:+.6f}pp, 95% Wald {p["wald_ci"]}, p={p["p_two_sided"]:.10g}. pooled Newcombe는 참고값.',f'- 신규 {100*n["difference_B_minus_A"]:+.6f}pp, 기존 {100*e["difference_B_minus_A"]:+.6f}pp. 각 97.5% Newcombe 및 Bonferroni p 대조. 상호작용 {100*inter["estimate"]:+.6f}pp, 95% Wald {inter["wald_ci"]}. 주·보조 전체 가족 통제 아님.',f'- 신규20%/기존80% 전이 점추정 {100*transfer:+.6f}pp. 새 실험으로 해석하지 않음.',f'- 사례 6: 잠재수요 12,000명에서 9개 정책×용량 108,000행의 요청·선착순 수용·미수용·완료·연락비·변동비를 전부 재구성. 합계검사만 한 검수가 아님.',f'- 일60 슬롯 B전면−A전면: 완료 {b["completed"]-a["completed"]:+,}건, 순가치 {b["net_value_krw"]-a["net_value_krw"]:+,}원, 미수용 {100*b["waiting_fraction_of_requests"]:.6f}%.',f'- 일60 파일럿 A/B 완료율 차이 {100*pilot_rd:.6f}pp를 12,000명에 기계 곱하면 {naive_extrapolation:.6f}건이지만, 이는 **잘못된 확대 계산**이다. 동일 잠재수요 고정정책의 실제 계산 +489건과 추론 대상을 혼동하면 안 됨. 정책별 요청 수 자체는 동일하지 않음.','', '## 기존 장부·본문 대조','- scenario_results.json의 계산된 모든 군별 수·비율·Wilson/Newcombe 구간·z/p/Fisher·주효과·상호작용·운영 요약 수치를 필드별 대조했다. 검사별 actual/expected/tolerance/status는 RESULTS.json에 보존.','- v12 L423,425,427,429,455,457,459,465,479,493–505,511의 주요 숫자를 문서에서 직접 토큰 추출하여 반올림 자릿수 절반 허용오차로 대조했다. L504 등 숫자 없는 중간 문단은 제외. 숫자 토큰 수 검사로 누락을 탐지한다.','- 참고값/주분석, 명목 상호작용, 조건부 시뮬레이션 해석 문구도 점검. 본문 편집·새 출판·SVG/PDF 렌더링 검수는 하지 않았다.']
    review+=['', '### 불일치']
    review += [f'- `{c["id"]}` actual={c["actual"]!r}; expected={c["expected"]!r}; tolerance={c["tolerance"]}' for c in mismatches] or ['- 재계산 장부 및 검사 대상 본문 숫자에서 불일치 없음.']
    review+=['','## 미검증 / blocked','- 실제 OEM 원장 정확성·비용 타당성·민원/안전·전국 확대 효과는 미검증. 단일 수요의 재계산은 인과적 전국 확대 효과나 정책 반복 CI가 아님.','- 결과 전 명세 동결 시점·시드 사전 선택 여부는 CSV로 검증 불가. 원생성기/분석 함수 import·실행·재사용 안 함. 원 RNG 스트림 재생성도 안 함.','- 배정의 무작위성/사전 상태의 현실 정확성은 설계 가정으로 읽었으며 관측 자료만으로 보증하지 않음.','', '## 보존과 산출물',f'- 원 CSV·계획·기존 결과·관련 원고/생성기 등 {len(before)}개 파일의 전후 SHA-256이 RESULTS.json에 수록됨.','- 새 파일만 생성: `RECALCULATE.py`, `RESULTS.json`, `REVIEW.md` (이 폴더). 원자료·원계획·기존결과 및 원고 수정 안 함.','- 실행 시 mismatch가 있으면 exit 1, 없으면 exit 0. blocked는 미확인 범위이며 성공으로 승격하지 않음.']
    (OUT/'REVIEW.md').write_text('\n'.join(review)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(OUT),summary=counts,mismatches=mismatches),ensure_ascii=False,indent=2))
    return 1 if mismatches else 0

if __name__=='__main__': sys.exit(main())
