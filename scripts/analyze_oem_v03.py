"""Analyze the frozen v0.3 plan without replacing missing evidence.
uv run --with scipy --with statsmodels scripts/analyze_oem_v03.py
"""
import csv
import hashlib
import json
import math
import platform
import sqlite3
from importlib.metadata import version
from pathlib import Path
import numpy as np
from scipy.stats import chisquare,norm
from statsmodels.stats.proportion import proportions_ztest,confint_proportions_2indep,power_proportions_2indep
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/virtual-data/v03'
plan=json.loads((OUT/'experiment_plan.json').read_text(encoding='utf-8'))
con=sqlite3.connect(f'file:{(OUT/"data/jh_motors_v03.sqlite").as_posix()}?mode=ro',uri=True)
saved_hash=json.loads(con.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])
assert saved_hash==hashlib.sha256((OUT/'experiment_plan.json').read_bytes()).hexdigest()
rows=[dict(zip(['arm','n','booked','completed','withdrawn','contracted'],r)) for r in con.execute('SELECT arm,COUNT(*),SUM(booked_28),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm')]
groups={r['arm']:r for r in rows}
# Reconcile every outcome view with direct raw event distinct-assignment counts.
for field,event,window in [('completed','test_drive_completed',28),('booked','booking',28),('withdrawn','consent_withdrawn',28),('contracted','contract_signed',180)]:
    raw=dict(con.execute('SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM events e JOIN assignments a USING(assignment_id) WHERE event_type=? AND event_day BETWEEN assigned_day AND assigned_day+? GROUP BY a.arm',(event,window)))
    assert all(raw[r['arm']]==r[field] for r in rows)
comparisons=[]
for left,right in [('B','A'),('A','H'),('B','H')]:
    l,r=groups[left],groups[right]
    z,p=proportions_ztest([l['completed'],r['completed']],[l['n'],r['n']],alternative='two-sided')
    pooled=(l['completed']+r['completed'])/(l['n']+r['n'])
    diff=l['completed']/l['n']-r['completed']/r['n']
    ownz=diff/math.sqrt(pooled*(1-pooled)*(1/l['n']+1/r['n']))
    assert abs(float(z)-ownz)<1e-12
    assert abs(float(p)-math.erfc(abs(ownz)/math.sqrt(2)))<1e-12
    ci=confint_proportions_2indep(l['completed'],l['n'],r['completed'],r['n'],compare='diff',method='newcomb',alpha=plan['family_alpha']/3)
    comparisons.append({'comparison':left+'-'+right,'metric':'completed_28','diff_pp':diff*100,'p_raw':float(p),'p_bonferroni':min(1,float(p)*3),'simultaneous_approx_ci_level':1-.05/3,'ci_low_pp':float(ci[0])*100,'ci_high_pp':float(ci[1])*100,'reject_at_family_05':float(p)*3<.05,'limits':'Bonferroni family of three completed-outcome contrasts; approximate marginal score intervals, conservative simultaneous coverage; not a universal adoption decision.'})
readiness=[]
na,nb=groups['A']['n'],groups['B']['n']
for scenario in ['drive_primary','contract_rare','optout_risk','complaint_rare','drive_tiny']:
    # Contract and guardrail are exploratory, not quietly promoted into confirmatory family.
    family=3 if scenario=='drive_primary' else 1
    row=next(x for x in plan['sample_size_grid'] if x['scenario']==scenario and x['family_comparisons']==family)
    power=float(power_proportions_2indep(row['target']-row['baseline'],row['baseline'],na,ratio=nb/na,alpha=row['alpha_each'],alternative='two-sided',return_results=False))
    readiness.append({'scenario':scenario,'nA':na,'nB':nb,'required_equal_n_each':row['n_each_numeric_power'],'planning_power_under_stated_effect':power,'meets_80pct_planning_power':power>=.8,'role':'confirmatory primary family' if family==3 else 'design-feasibility scenario only; not proof of safety/equivalence or a new confirmatory outcome'})
# Descriptive economics only: contract contribution is a synthetic assumption.
econ=[]
for arm in ['A','B','H']:
    r=groups[arm];messages=con.execute('SELECT COUNT(*) FROM messages JOIN assignments USING(assignment_id) WHERE arm=?',(arm,)).fetchone()[0]
    gross=r['contracted']*plan['economics_assumptions']['contribution_before_campaign']
    cost=messages*20+r['completed']*15000+(200000 if arm=='B' else 0)
    econ.append({'arm':arm,'synthetic_contract_contribution':gross,'modeled_campaign_and_drive_cost':cost,'synthetic_net_total':gross-cost,'synthetic_net_per_assigned':(gross-cost)/r['n'],'status':'Descriptive model only; not delivered revenue, causal profit inference or real OEM margin.'})
srm=float(chisquare([r['n'] for r in rows]).pvalue)
# Actual-source access recheck, separate from customer/event data.
access=json.loads((ROOT/'e-book/references/OEM_SOURCE_ACCESS_CHECK.json').read_text(encoding='utf-8'))
real=[]
for key in ['hyundai_sales_by_model','toyota_customer_service_report']:
    a=access[key];path=Path(a['cached_file']);available=path.exists()
    match=hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256'] if available else None
    real.append({'source':key,'url':a['url'],'cached_file_available':available,'hash_matches_prior_download':match,'grain':'aggregate OEM public report','use_in_v03':'Context and provenance only; no conversion or customer-distribution calibration','raw_redistribution':'Not included in package; commercial rights not cleared'})
real.append({'source':'kia_sales_library','url':'https://worldwide.kia.com/en/company/investor-relations/library/performance-and-plans','grain':'public sales library listing','use_in_v03':'Source inventory and proposed company assessment only; individual file not validated','raw_redistribution':'Not included'})
con.close()
result={'company':'JH Motors synthetic v0.3','population_n':plan['population_n'],'assigned_n':sum(r['n'] for r in rows),'groups':rows,'primary_comparisons':comparisons,'metric_readiness':readiness,'descriptive_economics':econ,'srm_global_p':srm,'real_data_utilization':real,'runtime':{'python':platform.python_version(),'scipy':version('scipy'),'statsmodels':version('statsmodels'),'numpy':version('numpy')},'validation':'Frozen plan hash, raw-event SQL and own z/p calculations matched; no independent human/domain validation.','warning':'Large synthetic samples do not validate real OEM generalizability. Power values use planned effect assumptions, not observed-effect post hoc power.'}
(OUT/'analysis_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'metric_readiness.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(readiness[0]));w.writeheader();w.writerows(readiness)
lines=['# JH Motors v0.3 · 표본과 데이터 재설계 결과','모든 고객·확률·비용은 교육용 합성 가정이다. 실제 OEM 공개자료는 고객 데이터와 분리했다.','',f"전체 고객 {plan['population_n']:,}명 중 적격 배정 {result['assigned_n']:,}명.",'','## 배정과 관측','| 군 | 배정 | 예약28일 | 시승28일 | 철회28일 | 계약180일 |','|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {r['arm']} | {r['n']:,} | {r['booked']:,} | {r['completed']:,} | {r['withdrawn']:,} | {r['contracted']:,} |")
lines+=['','## 지표별 설계 가능성','아래 검정력은 관측 효과가 아니라 미리 정한 기준 비율·목표 효과와 실제 배정 수로 계산한 설계 시나리오다. 희귀 불만은 아직 이벤트를 생성하지 않은 타당성 점검용 질문이다.','| 질문 | 동일 배정 기준 군당 필요 | 현 배정의 계획 검정력 | 80% 충족 |','|---|---:|---:|---|']
for r in readiness:lines.append(f"| {r['scenario']} | {r['required_equal_n_each']:,} | {r['planning_power_under_stated_effect']:.1%} | {'예' if r['meets_80pct_planning_power'] else '아니오'} |")
lines+=['','## 주지표 가족: 3개 대비 Bonferroni','이 구간·검정은 시승 완료의 세 대비 가족에만 적용한다. 계약·철회·이익의 성공이나 안전을 함께 보증하지 않는다.','| 대비 | 차이 pp | 가족보정 p | 약98.33% 구간 pp |','|---|---:|---:|---:|']
for r in comparisons:lines.append(f"| {r['comparison']} | {r['diff_pp']:+.2f} | {r['p_bonferroni']:.6f} | [{r['ci_low_pp']:+.2f}, {r['ci_high_pp']:+.2f}] |")
lines+=['','## 결론의 범위','현재 합성 조건에서 주지표 비교는 설계한 표본 목표를 충족한다. 그러나 동일 고객 수로 희귀한 계약·철회 위험·작은 효과를 모두 충분히 검출할 수 있는 것은 아니다. 부족한 검정력은 분석 자체가 불가능하거나 관측된 유의성을 무조건 부정한다는 뜻이 아니라, 명시한 크기의 효과를 안정적으로 구분하기 어렵다는 뜻이다.','실제 제조사의 집계 판매량을 캠페인의 전환율·개인별 반응·표본 추출 분포로 바꾸지 않았다. 큰 합성 데이터는 코드·설계 학습을 위한 것이고 실세계 타당성은 별도다.']
(OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'assigned_n':result['assigned_n'],'groups':rows,'primary':comparisons,'readiness':readiness,'real_sources':real},ensure_ascii=False,indent=2))
