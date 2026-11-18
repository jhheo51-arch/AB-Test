"""Run: uv run --python 3.12 --with scipy --with numpy python scripts/correct_statistics_v13.py
Only writes the two authorized v13 output directories. Never executes old code.
"""
import copy
import hashlib
import json
import math
import platform
import sqlite3
import subprocess
import shutil
import os
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np
import scipy
from numpy.polynomial import Polynomial as P
from scipy.optimize import minimize_scalar
from scipy.special import ndtr, ndtri
from statistics_v13 import planned_power, constrained_fit, score_ni

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'e-book/analysis/corrections_v13'
DATA = ROOT/'e-book/virtual-data/v13'
OLD = ROOT/'e-book/virtual-data/v03'
AUDIT = ROOT/'e-book/review/ai_statistical_v12'
OUT.mkdir(parents=True, exist_ok=True)
(DATA/'data').mkdir(parents=True, exist_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def relative(path):
    return path.relative_to(ROOT).as_posix()


def ro(path):
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)


def tables_fingerprint(con):
    result = {}
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        quoted = '"'+name.replace('"', '""')+'"'
        columns = len(con.execute('PRAGMA table_info('+quoted+')').fetchall())
        h = hashlib.sha256()
        count = 0
        for row in con.execute('SELECT * FROM '+quoted+' ORDER BY '+','.join(str(i+1) for i in range(columns))):
            h.update((json.dumps(row, ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf-8'))
            count += 1
        result[name] = {'rows':count, 'sorted_content_sha256':h.hexdigest()}
    return result


def aggregate(con):
    return [list(r) for r in con.execute('SELECT arm,COUNT(*),SUM(booked_28),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm')]


# Snapshot all v03 inputs and v12 historical audit/fixtures, not just opened JSON.
protected = sorted(set(p for base in [OLD, AUDIT, ROOT/'e-book/exports/v12'] for p in base.rglob('*') if p.is_file()))
input_hashes = {relative(p):digest(p) for p in protected}
plan = read(OLD/'experiment_plan.json')
report_old = read(OLD/'analysis_report.json')
report = copy.deepcopy(report_old)
fixture = read(ROOT/'e-book/exports/v12/counterexample_fixture.json')
counter_old = read(ROOT/'e-book/exports/v12/COUNTEREXAMPLE_RESULTS.json')
counter = copy.deepcopy(counter_old)
interpretation = read(AUDIT/'interpretation/RESULTS.json')
prior_counter = read(AUDIT/'counterexamples/RESULTS.json')
prior_diagnostic = read(AUDIT/'counterexamples/SCORE_DIAGNOSTIC.json')
checks = []


def check(name, passed, details=None):
    checks.append({'name':name, 'pass':bool(passed), 'details':details})
    if not passed:
        raise AssertionError(name+': '+str(details))


# A01: every readiness row, preserving all other legacy report fields.
power_history = []
for row in report['metric_readiness']:
    scenario = row['scenario']
    family = 3 if scenario == 'drive_primary' else 1
    planned = next(r for r in plan['sample_size_grid'] if r['scenario']==scenario and r['family_comparisons']==family)
    args = dict(p_A=planned['baseline'], n_A=row['nA'], p_B=planned['target'], n_B=row['nB'], alpha=planned['alpha_each'])
    value = planned_power(**args)
    simultaneous_swap = planned_power(p_A=args['p_B'], n_A=args['n_B'], p_B=args['p_A'], n_B=args['n_A'], alpha=args['alpha'])
    wrong_mapping = planned_power(p_A=args['p_A'], n_A=args['n_B'], p_B=args['p_B'], n_B=args['n_A'], alpha=args['alpha'])
    # Independent vector-form normal calculation via scipy, not shared function.
    probabilities = np.array([args['p_A'], args['p_B']])
    sizes = np.array([args['n_A'], args['n_B']])
    pooled = np.dot(probabilities, sizes)/sum(sizes)
    crit = ndtri(1-args['alpha']/2)*np.sqrt(pooled*(1-pooled)*sum(1/sizes))
    sd = np.sqrt(sum(probabilities*(1-probabilities)/sizes))
    delta = probabilities[1]-probabilities[0]
    independent = float(ndtr((-crit-delta)/sd)+ndtr((delta-crit)/sd))
    check('power_label_swap_'+scenario, abs(value-simultaneous_swap)<1e-12)
    check('power_independent_'+scenario, abs(value-independent)<1e-12)
    check('power_wrong_mapping_detected_'+scenario, abs(value-wrong_mapping)>1e-8 and abs(wrong_mapping-row['planning_power_under_stated_effect'])<1e-12)
    history = dict(scenario=scenario, inputs=args, original=row['planning_power_under_stated_effect'], corrected=value,
                   simultaneous_label_swap=simultaneous_swap, wrong_n_mapping=wrong_mapping, independent=independent)
    power_history.append(history)
    row['planning_power_under_stated_effect'] = value
    row['meets_80pct_planning_power'] = value >= .8
    row['planning_inputs_v13'] = args
    prior = next((r for r in interpretation['current_AB_planned_effect_power'] if r['scenario']==scenario), None)
    if prior:
        check('prior_power_audit_comparison_'+scenario, abs(value-prior['power_direct'])<1e-12)
report['correction_history_v13'] = {'source':relative(OLD/'analysis_report.json'), 'changes':power_history,
    'method':'Two-sided normal planned power, weighted pooled-null variance and unpooled alternative variance; explicit A/B mapping. Not observed-effect post-hoc power.',
    'legacy_other_fields_preserved':True}
report_compare = copy.deepcopy(report)
report_compare.pop('correction_history_v13')
for new, old in zip(report_compare['metric_readiness'], report_old['metric_readiness']):
    new.pop('planning_inputs_v13')
    new['planning_power_under_stated_effect'] = old['planning_power_under_stated_effect']
    new['meets_80pct_planning_power'] = old['meets_80pct_planning_power']
check('analysis_other_fields_preserved', report_compare == report_old)
write(DATA/'analysis_report_v13.json', report)

# A02: clone every old key; replace ONLY p and upper, including nested group.
score_history = []


def correct_case(target, counts, alpha):
    args = dict(x_A=counts['withdrawn_A'], n_A=counts['n_A'], x_B=counts['withdrawn_B'], n_B=counts['n_B'])
    margin = target['guard_limit_pp']/100
    result = score_ni(**args, margin=margin, alpha=alpha)
    q = result['fit_at_margin']['q_A']
    d = margin
    # Multiply each rational derivative term by the common denominator;
    # solve the polynomial independently from the likelihood root solver.
    qa, one_a, qb, one_b = P([0,1]), P([1,-1]), P([d,1]), P([1-d,-1])
    polynomial = args['x_A']*one_a*qb*one_b - (args['n_A']-args['x_A'])*qa*qb*one_b + args['x_B']*qa*one_a*one_b - (args['n_B']-args['x_B'])*qa*one_a*qb
    feasible = [float(z.real) for z in polynomial.roots() if abs(z.imag)<1e-10 and max(0,-d)<z.real<min(1,1-d)]
    check('polynomial_unique_'+target['id'], len(feasible)==1, feasible)
    def neglog(q0):
        q1 = q0+d
        return -(args['x_A']*math.log(q0)+(args['n_A']-args['x_A'])*math.log1p(-q0)+args['x_B']*math.log(q1)+(args['n_B']-args['x_B'])*math.log1p(-q1))
    optimized = minimize_scalar(neglog, bounds=(max(0,-d)+1e-12, min(1,1-d)-1e-12), method='bounded', options={'xatol':1e-15})
    check('likelihood_score_residual_'+target['id'], abs(result['fit_at_margin']['score_residual'])<1e-6)
    check('polynomial_agreement_'+target['id'], abs(q-feasible[0])<1e-10)
    check('optimization_agreement_'+target['id'], optimized.success and abs(q-optimized.x)<2e-8)
    check('upper_root_'+target['id'], abs(result['upper_inversion_residual'])<1e-9)
    check('p_upper_decision_'+target['id'], (result['p']<alpha)==(result['upper']<margin)==target['guard_pass'])
    for test_margin in [result['upper']-1e-6, result['upper']+1e-6, margin]:
        test_p = float(ndtr(constrained_fit(**args, difference=test_margin)['z']))
        check('inversion_decision_'+target['id']+'_'+str(test_margin), (test_p<alpha)==(result['upper']<test_margin))
    old_p, old_upper = target['guard_NI_p'], target['guard_one_sided_upper_pp']
    target['guard_NI_p'], target['guard_one_sided_upper_pp'] = result['p'], result['upper']*100
    score_history.append(dict(id=target['id'], inputs=args, alpha=alpha, margin=margin, original_p=old_p,
        original_upper_pp=old_upper, corrected_p=result['p'], corrected_upper_pp=result['upper']*100,
        q_A=q, polynomial_q_A=feasible[0], polynomial_coefficients_ascending=polynomial.coef.tolist(),
        optimized_q_A=float(optimized.x), negative_log_likelihood=neglog(q), **result))


for case, fixed in zip(counter['cases'], fixture['cases']):
    check('fixture_id_'+case['id'], case['id']==fixed['id'])
    correct_case(case, fixed, case['alpha_per_population'])
    if 'other_group' in case:
        correct_case(case['other_group'], fixed['other_prespecified_group'], case['other_group']['alpha_per_population'])
    prior = next(r for r in prior_counter['cases'] if r['id']==case['id'])
    check('prior_counter_audit_'+case['id'], abs(case['guard_NI_p']-prior['guard_NI_p'])<1e-11 and abs(case['guard_one_sided_upper_pp']-prior['guard_one_sided_upper_pp'])<1e-9)
for example in prior_diagnostic['examples']:
    xA,nA,xB,nB = example['counts']
    fit = constrained_fit(x_A=xA,n_A=nA,x_B=xB,n_B=nB,difference=example['null_difference'])
    check('prior_diagnostic_'+str(example['counts']), abs(fit['q_A']-example['direct_score_root_qA'])<1e-10)
restored = copy.deepcopy(counter)
for new, old in zip(restored['cases'], counter_old['cases']):
    for key in ['guard_NI_p','guard_one_sided_upper_pp']:
        new[key] = old[key]
        if 'other_group' in new:
            new['other_group'][key] = old['other_group'][key]
check('counter_all_other_keys_values_states_preserved', restored == counter_old)
write(OUT/'COUNTEREXAMPLE_RESULTS.json', counter)
write(OUT/'SCORE_DETAILS.json', score_history)

# A03: read-only SQLite backup; only outcomes view changes in the derived DB.
source_path = OLD/'data/jh_motors_v03.sqlite'
new_path = DATA/'data/jh_motors_v13.sqlite'
source = ro(source_path)
old_sql = source.execute("SELECT sql FROM sqlite_master WHERE name='outcomes'").fetchone()[0]
new_sql = old_sql.replace('AND e.event_day<=a.assigned_day+', 'AND e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+')
check('four_lower_bounds_added', new_sql.count('e.event_day>=a.assigned_day')==4)
(OUT/'outcomes_v13.sql').write_text('DROP VIEW IF EXISTS outcomes;\n'+new_sql+';\n', encoding='utf-8', newline='\n')
source_tables = tables_fingerprint(source)
source_schema = source.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
old_totals = aggregate(source)
new = sqlite3.connect(new_path)
source.backup(new)
new.executescript('DROP VIEW outcomes;\n'+new_sql+';')
new.commit()
check('derived_tables_content_unchanged', tables_fingerprint(new)==source_tables, source_tables)
expected_schema = [(typ,name,tbl,new_sql if typ=='view' and name=='outcomes' else sql) for typ,name,tbl,sql in source_schema]
check('only_outcomes_schema_changed', new.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()==expected_schema)
new_totals = aggregate(new)
check('derived_aggregates_match_original_view', new_totals==old_totals, new_totals)
ledger_totals = [[r[k] for k in ['arm','n','booked','completed','withdrawn','contracted']] for r in sorted(report_old['groups'], key=lambda r:r['arm'])]
check('derived_aggregates_match_legacy_ledger', new_totals==ledger_totals)
for col,event,window in [('booked_28','booking',28),('completed_28','test_drive_completed',28),('withdrawn_28','consent_withdrawn',28),('contracted_180','contract_signed',180)]:
    direct = dict(new.execute('SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM assignments a JOIN events e USING(assignment_id) WHERE e.event_type=? AND e.event_day BETWEEN a.assigned_day AND a.assigned_day+? GROUP BY a.arm',(event,window)))
    from_view = dict(new.execute('SELECT arm,SUM('+col+') FROM outcomes GROUP BY arm'))
    check('raw_lower_upper_aggregate_'+col, direct==from_view)
# Independent tiny boundary fixtures use exactly the canonical SQL, not a mock predicate.
boundaries = []
for event,col,window in [('booking','booked_28',28),('test_drive_completed','completed_28',28),('consent_withdrawn','withdrawn_28',28),('contract_signed','contracted_180',180)]:
    for offset,expected in [(-1,0),(0,1),(window,1),(window+1,0)]:
        mem = sqlite3.connect(':memory:')
        mem.executescript('CREATE TABLE assignments(assignment_id TEXT,customer_id TEXT,arm TEXT,assigned_day INT); CREATE TABLE events(assignment_id TEXT,event_type TEXT,event_day INT);'+new_sql+';')
        mem.execute("INSERT INTO assignments VALUES('x','c','A',10)")
        mem.execute('INSERT INTO events VALUES(?,?,?)',('x',event,10+offset))
        actual = mem.execute('SELECT '+col+' FROM outcomes').fetchone()[0]
        check('time_boundary_'+event+'_'+str(offset), actual==expected)
        boundaries.append(dict(event=event, offset=offset, expected=expected, actual=actual))
        mem.close()
# Inject contamination into a full IN-MEMORY backup, never the saved derived DB.
mem = sqlite3.connect(':memory:')
new.backup(mem)
before = aggregate(mem)
injected = []
for event,col in [('booking','booked_28'),('test_drive_completed','completed_28'),('consent_withdrawn','withdrawn_28'),('contract_signed','contracted_180')]:
    aid,day = mem.execute('SELECT assignment_id,assigned_day FROM outcomes WHERE '+col+'=0 LIMIT 1').fetchone()
    mem.execute('INSERT INTO events(assignment_id,event_type,event_day) VALUES(?,?,?)',(aid,event,day-1))
    injected.append(dict(event=event, assignment_id=aid, event_day=day-1))
mem.commit()
check('preassignment_injection_new_view_unchanged', aggregate(mem)==before, injected)
mem.executescript('DROP VIEW outcomes;'+old_sql+';')
check('preassignment_injection_old_bug_detected', aggregate(mem)!=before, aggregate(mem))
mem.close()
new.close()
source.close()
# Read back final persisted DB, then prove original byte hashes unchanged.
with ro(new_path) as persisted:
    check('persisted_database_integrity', persisted.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    check('persisted_tables_match_source', tables_fingerprint(persisted)==source_tables)
    check('persisted_view_and_aggregates', persisted.execute("SELECT sql FROM sqlite_master WHERE name='outcomes'").fetchone()[0]==new_sql and aggregate(persisted)==ledger_totals)
check('all_original_input_hashes_preserved', all(digest(ROOT/p)==h for p,h in input_hashes.items()))
# Historical plan hash is preserved, not repaired or overwritten.
with ro(source_path) as original:
    historical_hash = json.loads(original.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])
plan_bytes = (OLD/'experiment_plan.json').read_bytes()
# Some packaged Windows git executables are blocked to child Python processes.
# Try PATH first, then the standard installed Git; neither writes repository state.
git_errors = []
for git_exe in [shutil.which('git'), str(Path(os.environ.get('ProgramFiles', 'C:/Program Files'))/'Git/cmd/git.exe')]:
    if not git_exe:
        continue
    try:
        git_result = subprocess.run([git_exe,'show','HEAD:e-book/virtual-data/v03/experiment_plan.json'], cwd=ROOT, capture_output=True, check=True)
        git_head = subprocess.run([git_exe,'rev-parse','HEAD'], cwd=ROOT, capture_output=True, check=True).stdout.decode().strip()
        break
    except (OSError, subprocess.CalledProcessError) as exc:
        git_errors.append(str(exc))
else:
    raise RuntimeError('Cannot read HEAD plan for provenance: '+repr(git_errors))
git_bytes = git_result.stdout
plan_provenance = dict(actual_file_sha256=digest(OLD/'experiment_plan.json'), historical_manifest_sha256=historical_hash,
    actual_bytes_match_historical=digest(OLD/'experiment_plan.json')==historical_hash,
    LF_normalized_sha256=hashlib.sha256(plan_bytes.replace(b'\r\n',b'\n')).hexdigest(),
    CRLF_representation_sha256=hashlib.sha256(plan_bytes.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest(),
    git_HEAD_blob_sha256=hashlib.sha256(git_bytes).hexdigest(),
    git_HEAD_JSON_semantically_equal=json.loads(plan_bytes)==json.loads(git_bytes),
    git_HEAD_LF_representation_equal=plan_bytes.replace(b'\r\n',b'\n')==git_bytes.replace(b'\r\n',b'\n'),
    status='Historical exact-byte discrepancy retained. Representation equivalence does not repair exact-byte provenance or establish historical freeze.')
provenance = dict(kind='Derived correction, not regeneration or human review', git_HEAD=git_head, runtime=dict(python=platform.python_version(),scipy=scipy.__version__,numpy=np.__version__),
    command='uv run --python 3.12 --with scipy --with numpy python scripts/correct_statistics_v13.py',
    input_sha256_actual=input_hashes, plan_provenance=plan_provenance, source_tables=source_tables,
    database_derivation=dict(source=relative(source_path),destination=relative(new_path),method='SQLite backup from mode=ro source; replace outcomes view only',original_tables_unchanged=True, other_views_unchanged=True),
    code_sha256={relative(ROOT/'scripts'/name):digest(ROOT/'scripts'/name) for name in ['statistics_v13.py','correct_statistics_v13.py']},
    limitations=['Normal approximate planned power; no exact finite-sample or joint-FWER guarantee.', 'NI score API explicitly supports interior counts only; boundary-count generalization not validated.', 'No new experiment, seed change, historical hash repair, external sharing or human review.', 'Historical repeated arrays/freeze provenance not newly established.'])
write(OUT/'PROVENANCE.json', provenance)
write(DATA/'DERIVED_MANIFEST.json', dict(source_database_sha256_actual=input_hashes[relative(source_path)], derived_database_sha256=digest(new_path),
    plan=plan_provenance, canonical_analysis=relative(DATA/'analysis_report_v13.json'), provenance=relative(OUT/'PROVENANCE.json'), outcomes_sql=relative(OUT/'outcomes_v13.sql')))
write(OUT/'REGRESSION_CHECK.json', dict(status='PASS', checks_passed=len(checks),checks_failed=0,checks=checks,boundaries=boundaries,power_history=power_history,aggregates=new_totals,
    verification='Actually executed deterministic numerical, schema, row-content, persisted-database and byte-preservation checks; not independent human validation.'))
lines = ['# v13 통계 교정 실행 보고서','', '결과: 세 수정사항을 새 canonical 경로에서 실행했고 모든 회귀검사를 통과했다. 원자료·기존 결과·v12 감사는 변경하지 않았다.','',
    '## A01: 군별 계획 검정력','| 지표 | 원장 % | 교정 % | A n | B n |','|---|---:|---:|---:|---:|']
for h in power_history:
    lines.append(f"| {h['scenario']} | {h['original']*100:.9f} | {h['corrected']*100:.9f} | {h['inputs']['n_A']} | {h['inputs']['n_B']} |")
lines += ['', '5개 metric_readiness 행 모두 수정했다. A=계획 baseline, B=계획 target과 각각의 실제 배정 n을 명시했다. 관측효과 사후 검정력이 아니다. 나머지 원장 값은 보존했다.','',
    '## A02: 비영 위험차 보호 score', '직접 이항 제약우도 미분 root + MN N/(N−1) 분산 보정, 단측 정규 p 및 단측 상한 역산을 사용했다. 라이브러리 비영차 score 호출이나 패치를 사용하지 않았다.',
    '| 사례 | 교정 p | 교정 단측 상한 pp |','|---|---:|---:|']
for h in score_history:
    lines.append(f"| {h['id']} | {h['corrected_p']:.12g} | {h['corrected_upper_pp']:.12g} |")
lines += ['', 'COUNTEREXAMPLE_RESULTS.json은 기존의 모든 키와 다른 숫자·문구·상태를 그대로 복사했고 보호 p/상한 두 필드만 교정했다. 중첩 other_group도 포함한다. 기존 감사값은 비교목표로만 사용했으며 새 계산에서 생성했다.','',
    '## A03: 파생 DB와 시간 창','v03 DB를 읽기 전용으로 열어 SQLite backup으로 v13 DB를 만들고 outcomes 뷰에 배정일 이상 하한만 추가했다. 모든 원테이블의 행 수·정렬 내용 해시와 다른 스키마는 같고, 새 뷰 집계는 기존 원장과 일치한다.','',
    '## 회귀검사', f'실행 통과 {len(checks)}건. 확률/n 동시 라벨 교환 불변, 불균등 n 역매핑 오류 검출, 독립 정규 계산, 우도 잔차·다항식 root·수치 최적화, p/상한 판정 일관성, 네 사건의 −1/0/window/window+1 경계 16개와 원DB 복제본의 오염 주입을 검사했다. 최종 저장 DB를 재개방하여 integrity·테이블 내용·뷰·집계도 확인했다.','',
    '## 산출물', '- e-book/virtual-data/v13/analysis_report_v13.json','- e-book/virtual-data/v13/data/jh_motors_v13.sqlite','- e-book/virtual-data/v13/DERIVED_MANIFEST.json','- e-book/analysis/corrections_v13/COUNTEREXAMPLE_RESULTS.json','- e-book/analysis/corrections_v13/SCORE_DETAILS.json','- e-book/analysis/corrections_v13/REGRESSION_CHECK.json','- e-book/analysis/corrections_v13/PROVENANCE.json','- e-book/analysis/corrections_v13/outcomes_v13.sql','',
    '## 미해결 한계','원계획의 정확 바이트 해시 문제는 고치지 않았다. 실제 입력 해시·DB의 역사적 해시·LF/CRLF 표현 해시·HEAD JSON/표현 동등성을 분리 기록했으며, 동등성을 역사적 정확 바이트 보존으로 승격하지 않는다. 계획/DB 원본과 원 generation_manifest는 불변이다. 정규 근사와 내부 성공/실패 카운트의 score 경로만 검증했으며 경계 카운트 일반화·정확 공동 FWER·현장 타당성·사람 검수·출간 승인은 범위 밖이다. 원고·표지·새 실험·외부 공유는 수행하지 않았다.']
(OUT/'CORRECTION_REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(status='PASS', checks_passed=len(checks), regression=relative(OUT/'REGRESSION_CHECK.json'), report=relative(OUT/'CORRECTION_REPORT.md'), powers=power_history, corrected_score=[{k:h[k] for k in ['id','corrected_p','corrected_upper_pp']} for h in score_history], plan_provenance=plan_provenance), ensure_ascii=False, indent=2))
