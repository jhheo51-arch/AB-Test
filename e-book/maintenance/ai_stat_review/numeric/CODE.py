"""AI 별도구현 수치 검수. 생산 분석 모듈을 읽거나 실행하지 않는다.
Run from any directory: uv run --no-project --with scipy --with statsmodels CODE.py
Only writes RESULTS.json and REVIEW.md beside this file. SQLite mode=ro + query_only.
"""
from pathlib import Path
import sys, json, math, hashlib, sqlite3, subprocess, platform
from collections import Counter, defaultdict
from statistics import NormalDist
import numpy as np
import scipy
from scipy import stats
import statsmodels
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DB = ROOT / 'e-book/virtual-data/v13/data/jh_motors_v13.sqlite'
PLAN = ROOT / 'e-book/virtual-data/v03/experiment_plan.json'
LEDGER = ROOT / 'e-book/analysis/winner_v04/core_results.json'
MANUSCRIPT = ROOT / 'e-book/exports/v22/ebook_review_v22.md'
GIT = 'C:/Program Files/Git/cmd/git.exe'
COMMAND = 'uv run --no-project --with scipy --with statsmodels "C:/Users/Administrator/Downloads/AB-Test-v07/e-book/maintenance/ai_stat_review/numeric/CODE.py"'

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def inventory():
    # Entire repository working files, including reports/task status; never .git or own output.
    result = {}
    def visit(d):
        for p in d.iterdir():
            if p == OUT.parent or p.name == '.git':
                continue
            if p.is_dir():
                visit(p)
            elif p.is_file():
                result[p.relative_to(ROOT).as_posix()] = digest(p)
    visit(ROOT)
    return result

def git_status():
    return subprocess.check_output([GIT, '-C', str(ROOT), 'status', '--porcelain=v1', '--untracked-files=all'], text=True)

before = inventory()
git_before = git_status()
checks = []
def check(name, actual, expected, atol=0.0, rtol=0.0):
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        delta = float(actual) - float(expected)
        ok = math.isfinite(float(actual)) and abs(delta) <= atol + rtol * abs(float(expected))
    else:
        delta = None
        ok = actual == expected
    checks.append(dict(name=name, passed=bool(ok), actual=actual, expected=expected,
                       delta=delta, absolute_tolerance=atol, relative_tolerance=rtol))

plan = json.loads(PLAN.read_text(encoding='utf-8'))
ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
text = MANUSCRIPT.read_text(encoding='utf-8')
c = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
check('database.query_only', c.execute('PRAGMA query_only').fetchone()[0], 1)
schema = [dict(type=t, name=n, sql=s) for t,n,s in c.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','view') ORDER BY type,name")]
manifest = {k:json.loads(v) for k,v in c.execute('SELECT key,value_json FROM generation_manifest')}
check('plan.sha256_vs_ledger', digest(PLAN), ledger['source_plan_sha256'])
check('plan.sha256_vs_database_manifest', digest(PLAN), manifest['plan_sha256'])
plan_crlf_sha = hashlib.sha256(PLAN.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()
check('plan.CRLF_representation_matches_stored_hash', plan_crlf_sha, ledger['source_plan_sha256'])
check('plan.confirmatory_family', plan['confirmatory_family'], ['B-A completed','A-H completed','B-H completed'])
check('plan.family_alpha', plan['family_alpha'], .05)

# Raw assignments/events/messages/contracts are materialized before outcomes is queried.
assignments = {a:dict(customer_id=u, arm=g, day=d, probability=p) for a,u,g,d,p in c.execute('SELECT assignment_id,customer_id,arm,assigned_day,probability FROM assignments')}
events = list(c.execute('SELECT event_id,assignment_id,event_type,event_day FROM events'))
messages = list(c.execute('SELECT message_id,assignment_id,attempt_day,delivered FROM messages'))
contracts = list(c.execute('SELECT contract_id,assignment_id,signed_day,synthetic_contract_value,synthetic_contribution FROM contracts'))
customers = {u: (life, consent, prior) for u,life,consent,prior in c.execute('SELECT customer_id,lifecycle,sms_consent,prior_drive FROM customers')}
check('assignments.unique_customer', len({x['customer_id'] for x in assignments.values()}), len(assignments))
check('assignments.all_windows_mature', sum(x['day']+180 <= manifest['observation_cutoff_day'] for x in assignments.values()), len(assignments))
check('assignments.eligible', sum(customers[x['customer_id']] == ('prospect',1,0) for x in assignments.values()), len(assignments))
check('assignments.probability', sum(abs(x['probability']-1/3)<1e-15 for x in assignments.values()), len(assignments))

metrics = {'booking':('booked',28), 'test_drive_completed':('completed',28), 'consent_withdrawn':('withdrawn',28), 'contract_signed':('contracted',180)}
raw = {a:dict.fromkeys(['booked','completed','withdrawn','contracted'],0) for a in assignments}
raw_counts = Counter()
window_diagnostics = Counter()
for eid,a,t,d in events:
    if a not in assignments:
        window_diagnostics['orphan_events'] += 1
        continue
    metric, window = metrics[t]
    age = d - assignments[a]['day']
    window_diagnostics[t+'.total'] += 1
    if age < 0:
        window_diagnostics[t+'.pre_assignment'] += 1
    elif age > window:
        window_diagnostics[t+'.after_window'] += 1
    else:
        window_diagnostics[t+'.in_window_rows'] += 1
        raw[a][metric] = 1
        raw_counts[a,t] += 1
check('events.orphans', window_diagnostics['orphan_events'], 0)
# Event duplicates are not double-counted. Preserve diagnostics, not an assumption of one event.
window_diagnostics['duplicate_in_window_assignment_type_rows'] = sum(max(0,n-1) for n in raw_counts.values())

attempts = Counter(a for _,a,_,_ in messages)
check('messages.orphans', sum(a not in assignments for _,a,_,_ in messages), 0)
check('messages.H_count', sum(assignments[a]['arm']=='H' for _,a,_,_ in messages), 0)
check('messages.AB_one_attempt_each', sum(attempts[a] == 1 for a,x in assignments.items() if x['arm']!='H'), sum(x['arm']!='H' for x in assignments.values()))
check('messages.at_assignment', sum(d == assignments[a]['day'] for _,a,d,_ in messages), len(messages))

view = {a:(u,g,d,b,k,w,t) for a,u,g,d,b,k,w,t in c.execute('SELECT assignment_id,customer_id,arm,assigned_day,booked_28,completed_28,withdrawn_28,contracted_180 FROM outcomes')}
check('outcomes.assignment_ids', sorted(view), sorted(assignments))
# Avoid storing 65k identifiers in a successful aggregate check.
checks[-1]['actual'] = len(view)
checks[-1]['expected'] = len(assignments)
cell_mismatches = Counter()
examples = []
for a,x in assignments.items():
    expected = (x['customer_id'],x['arm'],x['day'],*[raw[a][k] for k in ['booked','completed','withdrawn','contracted']])
    actual = view.get(a)
    if actual is None:
        cell_mismatches['missing_row'] += 1
        continue
    for k,v,z in zip(['customer_id','arm','assigned_day','booked','completed','withdrawn','contracted'],actual,expected):
        if v != z:
            cell_mismatches[k] += 1
            if len(examples)<10: examples.append(dict(assignment_id=a, field=k, view=v, raw=z))
for k in ['customer_id','arm','assigned_day','booked','completed','withdrawn','contracted']:
    check('raw_vs_outcomes.'+k+'.mismatch_count', cell_mismatches[k], 0)

contract_by_id = {a:(d,v,z) for _,a,d,v,z in contracts}
check('contracts.orphans', sum(a not in assignments for a in contract_by_id), 0)
check('contracts.window_count_matches_event_flag', sum(0<=contract_by_id[a][0]-x['day']<=180 for a,x in assignments.items() if a in contract_by_id), sum(x['contracted'] for x in raw.values()))
check('contracts.assignment_flags_match', sum(int(a in contract_by_id) != raw[a]['contracted'] for a in assignments), 0)
check('contracts.contribution_matches_plan', sum(z == plan['economics_assumptions']['contribution_before_campaign'] for _,_,_,_,z in contracts), len(contracts))
check('contracts.event_signed_day_match', sum(any(aa==a and t=='contract_signed' and ed==d for _,aa,t,ed in events) for _,a,d,_,_ in contracts), len(contracts))

groups = {}
for g in 'ABH':
    ids = [a for a,x in assignments.items() if x['arm']==g]
    groups[g] = dict(arm=g,n=len(ids), **{k:sum(raw[a][k] for a in ids) for k in ['booked','completed','withdrawn','contracted']})
    ref = next(x for x in ledger['groups'] if x['arm']==g)
    for k in ['n','booked','completed','withdrawn','contracted']:
        check('ledger.groups.'+g+'.'+k, groups[g][k], ref[k])

def wilson(x,n,alpha):
    p=x/n; z=NormalDist().inv_cdf(1-alpha/2); z2=z*z
    center=(p+z2/(2*n))/(1+z2/n)
    half=z*math.sqrt(p*(1-p)/n+z2/(4*n*n))/(1+z2/n)
    return center-half, center+half

def binary(target, base, metric, alpha):
    n0=groups[base]['n']; n1=groups[target]['n']
    x0=groups[base][metric]; x1=groups[target][metric]
    p0=x0/n0; p1=x1/n1; diff=p1-p0
    pooled=(x0+x1)/(n0+n1)
    z=diff/math.sqrt(pooled*(1-pooled)*(1/n0+1/n1))
    p=math.erfc(abs(z)/math.sqrt(2))
    l0,u0=wilson(x0,n0,alpha); l1,u1=wilson(x1,n1,alpha)
    low=diff-math.hypot(p1-l1,u0-p0)
    high=diff+math.hypot(u1-p1,p0-l0)
    return dict(n_A=n0,n_B=n1,events_A=x0,events_B=x1,rate_A=p0,rate_B=p1,diff_pp=diff*100,relative_lift=diff/p0,p_raw=p,ci_level=1-alpha,ci_low_pp=low*100,ci_high_pp=high*100,z=z,wilson_base=[l0,u0],wilson_target=[l1,u1])

primary = []
for ref in ledger['primary_family']:
    label=ref['comparison']; target,base=label.split('-')
    x=binary(target,base,'completed',plan['family_alpha']/3)
    x.update(comparison=label,p_family=min(1,3*x['p_raw']))
    for k,v in ref.items():
        if isinstance(v,(int,float)):
            # Pure relative p tolerance: tiny p values must not pass via a broad absolute tolerance.
            check('ledger.primary.'+label+'.'+k,x[k],v,atol=0 if k.startswith('p_') else 1e-11,rtol=1e-10)
    libp=float(proportions_ztest([x['events_B'],x['events_A']],[x['n_B'],x['n_A']])[1])
    libci=confint_proportions_2indep(x['events_B'],x['n_B'],x['events_A'],x['n_A'],method='newcomb',alpha=plan['family_alpha']/3)
    check('library.primary.'+label+'.p', x['p_raw'],libp,rtol=1e-10)
    for key,val in zip(['ci_low_pp','ci_high_pp'],libci): check('library.primary.'+label+'.'+key,x[key],float(val)*100,atol=1e-11)
    primary.append(x)
guard = binary('B','A','withdrawn',.05)
for k,v in ledger['guardrail_exploratory'].items():
    check('ledger.guardrail.'+k,guard[k],v,atol=1e-11,rtol=1e-10)

# Net contribution vectors retain within-customer dependence: contract and completion
# are NEVER modeled as independent Bernoulli terms. Fixed B setup allocation is constant.
econ=plan['economics_assumptions']
net={}; finance_groups={}; covariances={}
for g in 'ABH':
    ids=[a for a,x in assignments.items() if x['arm']==g]
    K=np.array([raw[a]['contracted'] for a in ids],dtype=float)
    D=np.array([raw[a]['completed'] for a in ids],dtype=float)
    M=np.array([attempts[a] for a in ids],dtype=float)
    C=np.array([contract_by_id[a][2] if raw[a]['contracted'] else 0 for a in ids],dtype=float)
    fixed=econ['B_fixed_setup_cost']/len(ids) if g=='B' else 0
    X=C-econ['drive_operating_cost']*D-econ['message_attempt_cost']*M-fixed
    net[g]=X
    covariance=np.cov(np.array([K,D,M]),ddof=1)
    weights=np.array([econ['contribution_before_campaign'],-econ['drive_operating_cost'],-econ['message_attempt_cost']],dtype=float)
    var_cov=float(weights@covariance@weights)
    finance_groups[g]=dict(n=len(X),mean_krw=float(np.mean(X)),sample_variance=float(np.var(X,ddof=1)),total_krw=float(np.sum(X)),message_attempts=int(M.sum()),delivered=sum(delivered for _,a,_,delivered in messages if assignments[a]['arm']==g),fixed_cost_per_assigned=fixed)
    covariances[g]=dict(variable_order=['contracted','completed','attempts'],sample_covariance=covariance.tolist(),variance_from_full_covariance=var_cov,variance_ignoring_covariance=float(np.sum(weights**2*np.diag(covariance))))
    check('finance.'+g+'.variance_covariance_identity',finance_groups[g]['sample_variance'],var_cov,rtol=1e-10)
    check('ledger.financial_means.'+g,finance_groups[g]['mean_krw'],ledger['financial_means'][g],atol=1e-8)
financial=[]
for ref in ledger['financial_exploratory']:
    label=ref['comparison']; target,base=label.split('-')
    X,Y=net[target],net[base]
    vx=float(np.var(X,ddof=1))/len(X); vy=float(np.var(Y,ddof=1))/len(Y)
    se=math.sqrt(vx+vy); df=(vx+vy)**2/(vx*vx/(len(X)-1)+vy*vy/(len(Y)-1))
    diff=float(np.mean(X)-np.mean(Y)); t=diff/se
    critical=float(stats.t.ppf(.975,df)); p=float(2*stats.t.sf(abs(t),df))
    result=dict(comparison=label,diff_krw=diff,ci95_low_krw=diff-critical*se,ci95_high_krw=diff+critical*se,p_unadjusted=p,welch_df=df,standard_error=se,t=t)
    for k in ['diff_krw','ci95_low_krw','ci95_high_krw','p_unadjusted','welch_df']:
        check('ledger.financial.'+label+'.'+k,result[k],ref[k],atol=0 if k=='p_unadjusted' else 1e-7,rtol=1e-10)
    lib=stats.ttest_ind(X,Y,equal_var=False)
    check('library.welch.'+label+'.p',p,float(lib.pvalue),rtol=1e-10)
    financial.append(result)
sensitivity=[]
for ref in ledger['financial_sensitivity']:
    contribution=ref['assumed_contribution_per_contract']; means={}
    for g in 'ABH':
        means[g]=(contribution*groups[g]['contracted']-econ['drive_operating_cost']*groups[g]['completed']-econ['message_attempt_cost']*finance_groups[g]['message_attempts']-(econ['B_fixed_setup_cost'] if g=='B' else 0))/groups[g]['n']
        check('ledger.sensitivity.'+str(contribution)+'.'+g,means[g],ref['means_krw'][g],atol=1e-8)
    diff=means['B']-means['H']
    check('ledger.sensitivity.'+str(contribution)+'.B-H',diff,ref['B_minus_H_krw'],atol=1e-8)
    sensitivity.append(dict(assumed_contribution_per_contract=contribution,means_krw=means,B_minus_H_krw=diff))

# Verify exact rendered case-2/3 table rows against recomputed values, not an all-book audit.
for x in primary:
    row=f"| {x['comparison']} | {x['diff_pp']:+.2f} | [{x['ci_low_pp']:+.2f}, {x['ci_high_pp']:+.2f}] | {x['p_family']:.6g} |"
    check('manuscript.primary_table.'+x['comparison'], row in text, True)
for g in 'ABH':
    row=f"| {g} | {finance_groups[g]['mean_krw']:,.0f}원 |"
    check('manuscript.financial_mean_table.'+g,row in text,True)
for x in financial:
    row=f"| {x['comparison']} | {x['diff_krw']:+,.0f}원 | [{x['ci95_low_krw']:+,.0f}, {x['ci95_high_krw']:+,.0f}]원 |"
    check('manuscript.financial_interval_table.'+x['comparison'],row in text,True)
c.close()
after=inventory()
changed=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
check('preservation.all_non_output_working_files',len(changed),0)
git_after=git_status()
def outside_status(s):
    return '\n'.join(line for line in s.splitlines() if 'e-book/maintenance/ai_stat_review/' not in line)
check('preservation.git_status_outside_output',outside_status(git_after),outside_status(git_before))
failures=[x for x in checks if not x['passed']]
numeric_failures=[x for x in failures if not x['name'].startswith('plan.sha256_')]
provenance_findings = ([dict(kind='confirmed_byte_provenance_mismatch_not_numeric_error', current_sha256=digest(PLAN), stored_sha256=ledger['source_plan_sha256'], crlf_representation_sha256=plan_crlf_sha, explanation='Current LF bytes differ from stored plan hash; CRLF-only representation exactly matches. No numerical or semantic plan change established. Existing historical issue, not caused by this review.')] if digest(PLAN)!=ledger['source_plan_sha256'] else [])
result=dict(review_type='AI separate implementation; not independent human review or field utility guarantee',execution_command=COMMAND,runtime=dict(python=platform.python_version(),scipy=scipy.__version__,statsmodels=statsmodels.__version__,numpy=np.__version__),source_paths=dict(database=str(DB),plan=str(PLAN),ledger=str(LEDGER),manuscript=str(MANUSCRIPT)),database_access=dict(mode='ro',query_only=True),schema=schema,generation_manifest=manifest,raw_counts=dict(assignments=len(assignments),events=len(events),messages=len(messages),contracts=len(contracts)),event_window_diagnostics=dict(window_diagnostics),raw_outcome_comparison=dict(rows=len(assignments),fields_per_row=7,compared_cells=len(assignments)*7,mismatches=dict(cell_mismatches),examples=examples),groups=groups,primary_family=primary,guardrail_exploratory=guard,financial_groups=finance_groups,covariance_evidence=covariances,financial_exploratory=financial,financial_sensitivity=sensitivity,checks=checks,check_summary=dict(total=len(checks),passed=len(checks)-len(failures),failed=len(failures)),preservation=dict(scope='Every working file below repository root except .git and concurrent ai_stat_review outputs; before/after SHA256; no source writes',file_count=len(before),before_sha256=before,after_sha256=after,changed=changed,git_status_before=git_before,git_status_after=git_after),findings=dict(confirmed_numeric_errors=numeric_failures,confirmed_provenance_discrepancies=provenance_findings,candidates=[],out_of_scope=['case1 and other case datasets','PDF citations/contact sheets','data-generation realism and randomization implementation','human/domain review and actual OEM profit','cancellation/delivery/warranty/cluster/interference/sequential monitoring','external registration timestamp and genuine field utility']))
(OUT/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
lines=['# v0.22 AI 별도구현 통계 수치 검수','', '이 검수는 원자료를 별도 구현으로 계산한 AI 검수다. 독립된 사람의 통계 검수 또는 현장 효용 보장이 아니다. 생산 분석코드를 import/exec/호출하지 않았다.','', '## 실행',f'`{COMMAND}`','',f"Python {platform.python_version()}, scipy {scipy.__version__}, statsmodels {statsmodels.__version__}, numpy {np.__version__}.",'','## 결과',f"- 명시 검사 {len(checks)}건 중 {len(checks)-len(failures)} 통과, {len(failures)} 실패.",f"- 원자료 배정 {len(assignments):,}건, 사건 {len(events):,}건, 메시지 시도 {len(messages):,}건, 계약 {len(contracts):,}건.",f"- outcomes와 {len(assignments):,}행 × 7필드 = {len(assignments)*7:,}셀 대조. 불일치 {sum(cell_mismatches.values())}셀.",'- 원자료 사건은 assignment_id별 배정일부터 28일(예약/완료/철회), 180일(계약)까지 양끝 포함해 직접 0/1로 집계했다. outcomes는 집계 후 대조 대상으로만 읽었다.','- 메시지 미도달을 분석 제외하거나 비용에서 빼지 않았다. 모든 배정 고객을 유지했다.','','| 군 | N | 예약 | 완료 | 철회 | 계약 |','|---|---:|---:|---:|---:|---:|']
for g,x in groups.items(): lines.append(f"| {g} | {x['n']} | {x['booked']} | {x['completed']} | {x['withdrawn']} | {x['contracted']} |")
lines += ['','## 완료 주분석','양측 pooled z, 세 대비 Bonferroni p, Wilson 결합 Newcombe 구간(개별 98.3333%). 각 p와 구간은 statsmodels 별도 대조. 극소 p는 절대 오차 허용으로 뭉개지 않고 상대 오차로 비교했다.','','| 대비 | 차이 pp | 미보정 p | 가족 p | Newcombe 구간 pp |','|---|---:|---:|---:|---|']
for x in primary: lines.append(f"| {x['comparison']} | {x['diff_pp']:.9f} | {x['p_raw']:.12g} | {x['p_family']:.12g} | [{x['ci_low_pp']:.9f}, {x['ci_high_pp']:.9f}] |")
lines += ['', '## 보호 탐색',f"B-A 철회 차이 {guard['diff_pp']:.9f}pp, 개별 미보정 95% 구간 [{guard['ci_low_pp']:.9f}, {guard['ci_high_pp']:.9f}]pp, p={guard['p_raw']:.12g}.", '상한은 사후 교육용 +0.2pp보다 높다. 비유의는 안전 입증이 아니며, 원 계획에는 정식 비열등성 한계가 없다. 완료 하한이 사후 +0.5pp보다 낮다는 해석도 유지된다.','','## 고객별 합성 순기여와 Welch','고객별 계약 기여액 − 15,000×28일 완료 − 20×실제 발송시도 − B 고정비 200,000/N_B를 계산했다. 분산은 고객별 순기여 표본분산(ddof=1)이다. 계약/완료/시도의 전체 표본 공분산 행렬로 같은 분산을 얻는지 검증했다. 독립 사건의 분산을 단순 합산하지 않았다. 고정비는 평균만 바꾸고 분산은 바꾸지 않는다. 양측 개별 미보정 95% Welch 구간이며 scipy ttest_ind로 p도 대조했다.','','| 대비 | 차이 원/고객 | 95% 구간 | 미보정 p | df |','|---|---:|---|---:|---:|']
for x in financial: lines.append(f"| {x['comparison']} | {x['diff_krw']:.9f} | [{x['ci95_low_krw']:.9f}, {x['ci95_high_krw']:.9f}] | {x['p_unadjusted']:.12g} | {x['welch_df']:.9f} |")
lines += ['', '## 차이 판정',f"- 확정 수치 오류: {len(numeric_failures)}건. 각 수치 차이, 절대/상대 허용오차, 통과 여부는 RESULTS.json의 checks에 전부 보존.",f"- 확인된 바이트 출처 불일치: {len(provenance_findings)}건(장부/DB에서 2회 검출된 동일 문제). 현 LF 계획 해시는 {digest(PLAN)}, 저장 해시는 {ledger['source_plan_sha256']}. LF를 CRLF로만 바꾼 표현 해시 {plan_crlf_sha}가 저장 해시와 일치한다. 통계 수치 오류나 계획 내용 변경의 증거가 아니다. 기존 역사적 표현 차이를 보존하고 원본을 고치지 않는다.",'- 후보: 추가 후보 없음. 본 검수 범위 밖 숫자의 무오류까지 선언하지 않는다.','- 범위외: 작은 A/B 사례와 다른 후속 합성 사례, PDF 인용 전수, contact sheet, 생성모형 현실성, 사람/도메인 심사, 실제 제조사 수익, 외부 동결시각, 현장 효과.','- 원고 사례 2/3의 주분석 표 3행, 재무 평균 3행, Welch 표 3행을 재계산값의 표시 반올림과 대조했다. 원고 전체 수치/인용 전수 검수는 아니다.','- 원계획의 재무 지위는 탐색이며 실제 회계 검증이 아니다. B-A 탐색 손익의 양수 구간을 확증 재무 승리로 확대하지 않는다.','','## 보존',f"- .git과 동시 작업 ai_stat_review 산출물 폴더를 제외한 저장소 작업 파일 {len(before):,}개의 실행 전후 SHA256 대조, 변경 {len(changed)}개.",'- DB는 mode=ro와 PRAGMA query_only=ON. 원본, DB, 생산 분석코드, 기존 보고서, 작업상태를 쓰지 않았다. Git status만 읽었고 commit/push/fetch/index 변경을 하지 않았다.','- 해시 전후 목록과 Git 상태는 RESULTS.json에 보존. 출력은 이 폴더의 CODE.py, RESULTS.json, REVIEW.md뿐이다.']
if failures:
    lines += ['', '### 실패 내역']+[f"- {x['name']}: actual={x['actual']!r}, expected={x['expected']!r}, delta={x['delta']!r}" for x in failures]
(OUT/'REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(output_directory=str(OUT),checks=result['check_summary'],protected_files=len(before),changed=changed,failures=failures,groups=groups,primary=primary,financial=financial),ensure_ascii=False,indent=2))
sys.exit(1 if numeric_failures else 0)
