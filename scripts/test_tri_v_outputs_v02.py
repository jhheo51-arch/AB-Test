"""Exercise sharpened TRI-V outputs; never infer human effectiveness from fixture tests."""
from pathlib import Path
from statistics import mean,variance,NormalDist
from copy import deepcopy
import csv,json,math,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'e-book/review/ab_only_methods_v01';D=ROOT/'e-book/review/methodology/tri_v_sharpening_v02'
ledger=json.loads((OLD/'calculated_results.json').read_text(encoding='utf-8'))
with (OLD/'customer_fixture.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
assert hashlib.sha256((OLD/'customer_fixture.csv').read_bytes()).hexdigest()==ledger['csv_sha256']
assert len(rows)==ledger['row_count'] and len({r['customer_id'] for r in rows})==len(rows)
assert all(int(r['observed_days'])==30 for r in rows)
strata=['first_service','repeat_service'];z=NormalDist().inv_cdf(.975)
def estimate(cost):
 cells=[]
 for s in strata:
  for a in ['A','B']:
   rs=[r for r in rows if r['pre_stratum']==s and r['arm']==a]
   vs=[int(r['completed_30'])*(40000-(cost if a=='B' else 0)) for r in rs]
   if cost==10000:assert all(v==int(r['contribution_30_KRW']) for v,r in zip(vs,rs))
   cells.append((mean(vs),variance(vs)/len(vs)))
 effects=[cells[i+1][0]-cells[i][0] for i in [0,2]];effect=sum(effects)/2;se=math.sqrt(sum(x[1] for x in cells)/4)
 return {'net_B_cost_per_completion_KRW':cost,'difference_KRW_per_assigned':effect,'ci95_KRW':[effect-z*se,effect+z*se],'method':'fixed 0.5/0.5 strata, within-cell variance normal Wald; original outcomes and consumer coupon held fixed'}
original=estimate(10000);assert abs(original['difference_KRW_per_assigned']-ledger['primary']['effect_B_minus_A_KRW'])<1e-9
assert max(abs(x-y) for x,y in zip(original['ci95_KRW'],ledger['primary']['ci95_KRW']))<1e-7
sensitivity=[estimate(c) for c in [8000,10000,12000]]
# Upper CI is affine plus a norm of affine coefficients, hence convex in cost.
# Its maximum on a closed interval is at an endpoint; this is not a grid-only proof.
max_upper=max(sensitivity[0]['ci95_KRW'][1],sensitivity[-1]['ci95_KRW'][1]);assert max_upper<0
for c in range(8000,12001,10):assert estimate(c)['ci95_KRW'][1]<=max_upper+1e-7

def next_check(question,evidence,condition,yes,no,owner='실험 분석 책임자',required=True):
 return {'question':question,'evidence_required':evidence,'acceptance_condition':condition,'if_met':yes,'if_not_met':no,'owner_role':owner,'deadline_status':'미정. 해당 역할이 실제 기한과 재판단 담당자를 정해야 함','required_for_current_question':required,'burden':'미확인. 실제 수집 시간과 비용을 기록하기 전 최적 또는 최소라고 주장하지 않음'}
def claim(cid,role,depends,status,inference,statement,forbidden,effect=None):
 return {'claim_id':cid,'analysis_role':role,'dependencies':depends,'measurement_status':status,'inference_status':inference,'permitted_statement':statement,'prohibited_statement':forbidden,'estimate_or_interval':effect}
def base(cid,title):
 return {'case_id':cid,'title':title,'provenance':'기존 합성 쿠폰 자료의 교육용 조건변형. 새 현장 실험이나 실제 사전등록 아님. 기록은 완성 예시이며 실제 참여자의 응답이 아님.','evidence':{'completion_ledger':'available','cost_assumption':'available','withdrawal_ledger':'available'},'independent_withdrawal_audit_in_story':True,'V1':{'original_primary':'profit_30_per_assigned','post_result_primary_replacement':False,'unit':'고객','denominator':'각 군의 모든 배정 고객','window':'개인별 30일 성숙 창','claims':[]},'V2':{'assigned_population':'첫 이용 대상과 기존 고객이 절반씩인 현재 적격 집단','analysis_population':'원래 배정 전체. 지표별 측정 제한은 V1에 별도 기재','proposed_population':'원래 전체 대상','selection_timing':'첫 이용과 기존 고객의 정의는 배정 전. 새로운 적용 요청은 결과 후 제안','new_policy_evidence':False,'scope_status':'original_scope','scope_statement':'현재 실험의 모집단과 대비 안에서만 해석','new_policy_contrast':'해당 없음'},'V3':{'current_choice':'전체 B 확대를 제안하지 않음','basis_claim_ids':[],'guardrail_safety':'unconfirmed','guardrail_passes':False,'approval_status':'proposal_not_approved','criteria_origin':'가상 원 실험 이야기의 기준. 새 민감도 가정과 후속 계획은 사후 제안으로 분리','reopen_if':[],'next_checks':[],'not_now':[],'stop_rule':'현재 선택을 바꾸지 않는 확인은 생략 검토. 보호와 권리, 법정 감사 및 다른 질문의 의무는 제외하지 않음','range_supported_in_story':None,'skip_precise_cost_for_current_choice':False}}

c1=base('C01','완료 원장 결함은 어느 주장까지 전파되는가')
c1['evidence']['completion_ledger']='limited';c1['provenance']+=' 완료 원장 불완전과 철회 원장의 독립 대사가 확인됐다는 가상 조건을 추가한다. 실제 원장에서 결함을 발견한 것이 아니다.'
c1['V1']['claims']=[claim('completion','exploratory',['completion_ledger'],'limited','not_evaluated','완료 차이를 현재 근거로 평가하지 않음','불완전한 완료 수치로 승자를 선택'),claim('profit','primary',['completion_ledger','cost_assumption'],'limited','not_evaluated','완료 기반 이익 차이도 현재 근거로 평가하지 않음','원본 정답을 알고 있다는 이유로 이익 추정을 사용'),claim('withdrawal','guardrail',['withdrawal_ledger'],'available','inconclusive','독립 대사됐다는 조건에서 철회 비교만 남김. 보호 한계 내라는 근거는 부족','완료 원장 결함을 모든 지표 무효로 확대하거나 철회 비교로 전체 안전을 승인',ledger['guardrail'])]
c1['V3'].update(current_choice='현재 손상된 근거로 B 확대를 승인하지 않고 완료와 종속 이익의 비교를 보류',basis_claim_ids=['completion','profit','withdrawal'],reopen_if=['완료 원장의 누락 범위와 복구 결과가 확인됨','철회 원장의 독립 대사 가정이 깨짐'])
c1['V3']['next_checks']=[next_check('완료 누락과 이익 영향 범위를 복구할 수 있는가','배정 ID별 완료 원천과 집계 경로 대사, 누락 및 중복과 관측 창','원천과 집계가 고객 단위로 대사되고 잔여 결함의 영향 범위를 명시','해당 지표와 종속 이익만 재추정하고 원 계획 기준으로 재판단','복구 불가능한 현재 주장은 제한을 유지하고 새 수집 설계를 검토','데이터 원장 책임자')]
c1['V3']['not_now']=[{'task':'손상된 완료 결과를 세그먼트와 고급 모형으로 더 세분화','reason':'현재 비교 근거를 복구하지 못하며 원본 정답 유입 위험이 있음','exception':'결함 범위 진단을 위한 분할은 허용. 독립 유효 지표를 폐기하지 않음'}]

c2=base('C02','첫 이용 대상의 탐색 신호를 새 정책으로 바꾸려는 요청')
c2['V1']['claims']=[claim('profit','primary',['completion_ledger','cost_assumption'],'available','supports_decrease','고정 원가 모형 아래 현재 전체 대상의 이익 감소를 지지','완료 관측 순위로 주지표 성공을 선언',original),claim('first_group','exploratory',['completion_ledger','cost_assumption'],'available','supports_increase','첫 이용 대상의 탐색 추정은 긍정적. 확증과 새 혼합 정책은 별도','집단의 탐색 구간을 새 정책 승인으로 바꿈',ledger['exploratory_group_contribution']['first_service'])]
c2['V2'].update(proposed_population='첫 이용 대상에게만 B, 기존 고객에게 A인 혼합 정책',scope_status='new_policy_unconfirmed',scope_statement='전체 정책에 대한 결론을 유지. 새 혼합 정책의 검증은 없음',new_policy_contrast='새 적격 코호트에서 첫 이용 대상의 A 대 B 또는 실제 혼합 정책 대비. 필요한 근거는 목표와 간섭 및 기존 확증 범위에 맞게 설계')
c2['V3'].update(basis_claim_ids=['profit','first_group'],reopen_if=['새 정책을 뒷받침할 적합한 확증 자료가 확보됨','실제 원가, 대상 정의 또는 간섭 가정이 달라짐'])
c2['V3']['next_checks']=[next_check('첫 이용 대상의 후속 정책 검증을 설계할 사업 필요가 있는가','실제 원가와 적격 대상, 기존 확증 범위, 보호 조건, 정보량 및 운영 용량','정책 대비와 사업 필요가 정의되고 설계 및 책임자가 승인할 수 있음','새 자료를 보기 전에 필요한 후속 검증을 고정','추가 고객 노출과 데이터 수집을 자동으로 진행하지 않음','실험 기획 책임자',False)]
c2['V3']['not_now']=[{'task':'좋게 보이는 고객군을 계속 찾아 즉시 적용','reason':'원 실험의 실패를 지우고 선택 편향과 다중 비교를 키울 수 있음','exception':'별도 탐색 목적과 가족을 밝힌 연구는 가능하되 현재 확증으로 쓰지 않음'}]

c3=base('C03','완료율 차이의 구간이 0을 포함하면 표본부터 늘려야 하는가')
c3['V1']['claims']=[claim('completion','exploratory',['completion_ledger'],'available','inconclusive','완료 차이의 탐색 구간은 0을 포함. 증가와 감소 가능성이 모두 남으며 실질적 차이 여부의 기준은 별도','유의하지 않음을 무효과나 동등으로 바꾸거나 원 주지표로 교체',ledger['exploratory_completed_rate']),claim('profit','primary',['completion_ledger','cost_assumption'],'available','supports_decrease','원래 전체 정책의 이익 감소 근거는 별도로 유지','완료율 미결을 이유로 원 주지표 결론을 지움',original)]
c3['V3'].update(basis_claim_ids=['completion','profit'],reopen_if=['완료율 자체에 대한 별도 사업 질문과 판단 범위가 정해짐','원래 이익 추정의 자료 또는 가정이 바뀜'])
c3['V3']['next_checks']=[next_check('완료율에 대한 별도 결론이 현재 또는 새 사업 결정에 필요한가','원래 주지표 계약과 새 질문, 실제 필요한 효과 범위, 기존 종료 규칙','기존 이익 판단과 다른 의사결정 질문이 구체적으로 존재','그 질문에 맞는 후속 설계와 정보량을 결과 전에 검토','현재 결정을 위해 고객을 자동 추가하거나 종료 규칙을 바꾸지 않음','실험 의사결정 책임자',False)]
c3['V3']['not_now']=[{'task':'유의해질 때까지 같은 실험의 표본을 추가','reason':'고정 종료 계약을 위반할 수 있고 현재 이익 판단의 목적과 다름','exception':'처음부터 적절히 설계한 순차 절차나 새 질문을 위한 새 계약은 별도 검토'}]

c4=base('C04','정밀 원가 재추정이 현재 선택을 바꾸는가')
c4['provenance']+=' 기업 부담액의 범위가 가상 검토에서 정당화됐다는 조건이다. 실제 재무 검증이 아니다. 소비자 쿠폰과 결과는 그대로이고 비용 분담 및 처리비를 포함한 기업 순부담만 변한다.'
c4['V1']['claims']=[claim('profit_range','primary',['completion_ledger','cost_assumption'],'available','supports_decrease','가상으로 근거가 확인된 기업 순부담 범위 안에서 각 조건부 구간의 상한도 음수','가정 범위 밖의 실제 비용이나 모든 금전 불확실성까지 해결했다고 주장',{'range_KRW':[8000,12000],'evaluations':sensitivity,'maximum_conditional_ci_upper_KRW':max_upper})]
c4['V3'].update(basis_claim_ids=['profit_range'],range_supported_in_story=True,skip_precise_cost_for_current_choice=True,reopen_if=['부담액 범위의 정당화가 철회되거나 실제 비용이 범위 밖임','완료 원장, 대상 구성 또는 비용의 적용 단위가 바뀜','현재 미확인인 보호와 운영 조건에 새 정보가 생김'])
c4['V3']['next_checks']=[next_check('정당화된 범위와 측정 조건이 계속 유지되는가','범위 산출 근거와 실제 정산의 예외, 완료 원장의 변화','제시 범위와 비용 단위 및 측정 조건이 유지','현재 B 미확대 판단을 위해 정밀 비용 점추정을 더 요구하지 않음','범위와 모형을 다시 정당화하고 민감도를 재계산. 이것만으로 B 승인을 내리지 않음','재무 검토 책임자',False)]
c4['V3']['not_now']=[{'task':'현재 전체 B 미확대 결론만을 위해 순부담액을 정밀 점추정','reason':'정당화된 범위 안에서 해당 선택의 근거 방향이 바뀌지 않음','exception':'범위 근거 미확인, 다른 정책 질문, 실제 결산과 법정 감사 및 보호 의무는 생략하지 않음'}]
records=[c1,c2,c3,c4]

EVIDENCE_SOURCES={
 'completion_ledger':{'file':(OLD/'customer_fixture.csv').relative_to(ROOT).as_posix(),'fields':['customer_id','pre_stratum','arm','observed_days','completed_30'],'calculation_file':'scripts/test_tri_v_outputs_v02.py','calculation_symbol':'estimate','scope':'합성 원자료. 현재 조건변형의 측정 제한이 원본의 알려진 정답보다 우선함'},
 'cost_assumption':{'file':(OLD/'design_fixture.json').relative_to(ROOT).as_posix(),'json_pointer':'/plan_in_the_story/economics','calculation_file':'scripts/test_tri_v_outputs_v02.py','calculation_symbol':'estimate and sensitivity','scope':'원래 금액과 이번 비용 범위 모두 교육용 가정. 범위는 사후 조건변형으로 실제 재무 근거가 아님'},
 'withdrawal_ledger':{'file':(OLD/'customer_fixture.csv').relative_to(ROOT).as_posix(),'fields':['customer_id','pre_stratum','arm','withdrawn_30'],'calculation_file':(OLD/'calculated_results.json').relative_to(ROOT).as_posix(),'json_pointer':'/guardrail','scope':'기존 score 출력 재사용. 독립 원장 대사 여부는 조건변형 가정이고 실제 현장 검증이 아님'}
}
for src in EVIDENCE_SOURCES.values():
 assert (ROOT/src['file']).is_file() and (ROOT/src['calculation_file']).is_file()
 if 'fields' in src:assert set(src['fields'])<=set(rows[0])
for rec in records:
 rec['evidence_sources']=deepcopy(EVIDENCE_SOURCES)
 for cl in rec['V1']['claims']:
  pointers={'completion':'/exploratory_completed_rate','profit':'/primary','first_group':'/exploratory_group_contribution/first_service','withdrawal':'/guardrail','profit_range':'/cost_sensitivity'}
  target=D/'RULE_AND_SENSITIVITY_TEST.json' if cl['claim_id']=='profit_range' else OLD/'calculated_results.json'
  cl['result_reference']={'file':target.relative_to(ROOT).as_posix(),'json_pointer':pointers[cl['claim_id']],'scope':'출처 위치는 알려진 원본 계산 또는 조건부 재계산. 현재 주장 사용 여부는 측정 제한과 분석 역할을 우선함'}

def errors(r):
 e=[];claims=r['V1']['claims'];ids={c['claim_id'] for c in claims}
 if len(ids)!=len(claims):e.append('duplicate_claim')
 for c in claims:
  if not c['dependencies'] or any(d not in r['evidence'] or d not in r.get('evidence_sources',{}) for d in c['dependencies']) or not c.get('result_reference'):e.append('missing_dependency')
  blocked=any(r['evidence'].get(d)!='available' for d in c['dependencies'])
  if blocked and (c['measurement_status']=='available' or c['inference_status']!='not_evaluated' or c['estimate_or_interval'] is not None):e.append('blocked_claim_used')
  if c['claim_id']=='withdrawal' and c['measurement_status']=='available' and not r['independent_withdrawal_audit_in_story']:e.append('independence_not_supported')
  if not c['permitted_statement'] or not c['prohibited_statement']:e.append('missing_boundary')
 if r['V1']['post_result_primary_replacement']:e.append('primary_switched')
 if not r['V3']['basis_claim_ids'] or not set(r['V3']['basis_claim_ids'])<=ids:e.append('unlinked_decision')
 if r['V2']['scope_status']=='new_policy_confirmed' and not r['V2']['new_policy_evidence']:e.append('unsupported_policy')
 if r['V3']['guardrail_safety']=='confirmed' and not r['V3']['guardrail_passes']:e.append('unsupported_safety')
 if r['V3']['approval_status']!='proposal_not_approved':e.append('invented_approval')
 if not r['V3']['reopen_if']:e.append('missing_reopen_trigger')
 if r['V3']['skip_precise_cost_for_current_choice'] and r['V3']['range_supported_in_story'] is not True:e.append('unjustified_skip')
 for q in r['V3']['next_checks']:
  if not all(q.get(k) for k in ['question','evidence_required','acceptance_condition','if_met','if_not_met','owner_role','deadline_status']):e.append('unactionable_request')
 return sorted(set(e))
for r in records:assert not errors(r),(r['case_id'],errors(r))
# A competent reference procedure is allowed the same conclusions and links.
reference=deepcopy(records)
for r in reference:r['presentation']='표준 절차 참조안의 동등 완성 기록. 실제 참여자 수행 아님';assert not errors(r)
mutations=[]
def bad(case,label,edit,expected):
 x=deepcopy(case);edit(x);found=errors(x);assert expected in found,(label,found);mutations.append({'deliberate_mutation':label,'expected_rule':expected,'detected_rules':found,'rejected':True})
bad(c1,'제한된 이익 추정 사용',lambda x:x['V1']['claims'][1].update(estimate_or_interval=original),'blocked_claim_used')
bad(c1,'누락된 완료의 효과 방향 선언',lambda x:x['V1']['claims'][0].update(inference_status='supports_increase'),'blocked_claim_used')
bad(c2,'미검증 새 정책을 확증으로 변경',lambda x:x['V2'].update(scope_status='new_policy_confirmed'),'unsupported_policy')
bad(c3,'결과 후 주지표 변경',lambda x:x['V1'].update(post_result_primary_replacement=True),'primary_switched')
bad(c2,'보호 미확인을 안전 확인으로 변경',lambda x:x['V3'].update(guardrail_safety='confirmed'),'unsupported_safety')
bad(c2,'실제 승인 없이 승인 상태 생성',lambda x:x['V3'].update(approval_status='approved'),'invented_approval')
bad(c1,'자료 요청 담당 역할 제거',lambda x:x['V3']['next_checks'][0].update(owner_role=''),'unactionable_request')
bad(c2,'재판단 조건 제거',lambda x:x['V3'].update(reopen_if=[]),'missing_reopen_trigger')
bad(c4,'근거 없는 비용 범위로 정밀 확인 생략',lambda x:x['V3'].update(range_supported_in_story=False),'unjustified_skip')
bad(c1,'독립성 미확인인데 철회 비교 보존',lambda x:x.update(independent_withdrawal_audit_in_story=False),'independence_not_supported')
obs=D/'OBSERVATIONS.csv'
with obs.open(encoding='utf-8-sig',newline='') as f:observations=list(csv.DictReader(f))
assert not observations
report={'status':'조건변형과 고의 오류에 대한 개발 검사. 실제 독자 효과 비교 아님','base_row_count':len(rows),'base_result_reconciled':True,'source_csv_sha256':ledger['csv_sha256'],'cost_sensitivity':sensitivity,'max_conditional_upper_KRW_over_band':max_upper,'range_note':'범위와 비용 모형은 교육용 조건. 이익 상한의 볼록성으로 양 끝점 최대를 사용하고 격자도 점검. 동시 추론 보정이나 실제 원가 신뢰구간이 아님. 소비자 혜택 변경의 행동 효과를 추정하지 않음.','case_count':len(records),'valid_TRI_V_records':len(records),'valid_reference_records':len(reference),'same_substantive_reference_conclusions':True,'deliberate_mutations':mutations,'mutation_count':len(mutations),'human_observation_rows':len(observations),'effectiveness_claim':'누락, 시간, 업무 비용 및 조직 성과 개선은 미검증','guardrail_note':'철회 score 결과는 기존 계산 JSON을 출처와 함께 재사용. 이번 stdlib 계산에서 score 검정을 다시 계산한 것은 아님.'}
for name,value in [('WORKED_RECORDS.json',records),('REFERENCE_WORKED_RECORDS.json',reference),('RULE_AND_SENSITIVITY_TEST.json',report)]:
 (D/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
md='# 산출물 개정의 조건변형 적용 결과\n\n고정 교육용 자료의 개발 검사다. 실제 사람의 비교시험과 효과 검증은 아니다.\n\n'
for rec in records:
 md+='## '+rec['case_id']+' '+rec['title']+'\n\n'+rec['provenance']+'\n\n'
 md+='| 주장 | 측정 상태 | 추론 상태 | 허용할 문장 | 금지할 해석 |\n|---|---|---|---|---|\n'
 for cl in rec['V1']['claims']:md+='| '+' | '.join([cl['claim_id'],cl['measurement_status'],cl['inference_status'],cl['permitted_statement'],cl['prohibited_statement']])+' |\n'
 md+='\n**적용 범위:** '+rec['V2']['scope_statement']+'\n\n**현재 선택:** '+rec['V3']['current_choice']+'\n\n**재판단 조건:** '+' / '.join(rec['V3']['reopen_if'])+'\n\n'
 for q in rec['V3']['next_checks']:md+='**다음 확인:** '+q['question']+'\n\n필요 자료: '+q['evidence_required']+'\n\n담당 역할과 기한: '+q['owner_role']+' / '+q['deadline_status']+'\n\n수용 조건: '+q['acceptance_condition']+'\n\n충족하면: '+q['if_met']+'\n\n미충족이면: '+q['if_not_met']+'\n\n'
 for q in rec['V3']['not_now']:md+='**지금 생략 검토:** '+q['task']+'\n\n이유: '+q['reason']+'\n\n예외: '+q['exception']+'\n\n'
md+='## 비용 가정의 실제 재계산\n\n고객 쿠폰은 1만원으로 고정하고 기업의 완료당 순부담만 바꾼 사후 민감도다. 분담 및 처리 비용 변화가 고객 반응과 다른 조건을 바꾸지 않는다고 가정한다.\n\n| 완료당 기업 순부담 | 고객당 이익 B-A | 조건부 95% 구간 |\n|---|---|---|\n'
for x in sensitivity:md+=f'| {x["net_B_cost_per_completion_KRW"]:,}원 | {x["difference_KRW_per_assigned"]:+,.0f}원 | [{x["ci95_KRW"][0]:+,.0f}, {x["ci95_KRW"][1]:+,.0f}]원 |\n'
md+=f'\n설정한 범위의 조건부 상한 최대는 {max_upper:+,.0f}원이다. 범위의 정당성이 확인됐다는 교육용 조건 아래 현재 B 미확대 판단을 위해 정밀 원가 점추정을 더 요구하지 않을 수 있다. 범위 자체를 확인하지 못했거나 별도 보호와 결산 의무가 있으면 생략할 근거가 되지 않는다.\n\n'
md+=f'완성 기록은 TRI-V {len(records)}개와 표준 참조 {len(reference)}개 모두 같은 규칙을 충족했다. 고의 오류 {len(mutations)}개는 해당 규칙에서 거부됐다. 사람의 관찰 자료는 {len(observations)}행이다. 이 수치를 정확도나 시간 절감률로 바꾸지 않는다.\n'
(D/'WORKED_RESULTS.md').write_text(md,encoding='utf-8',newline='\n')
for rec in records:
 for cl in rec['V1']['claims']:
  ref=cl['result_reference'];value=json.loads((ROOT/ref['file']).read_text(encoding='utf-8'))
  for key in ref['json_pointer'].strip('/').split('/'):value=value[key]
  assert value is not None
for p in D.iterdir():
 if p.suffix in ['.md','.json','.csv']:
  text=p.read_text(encoding='utf-8-sig')
  assert not any(ch in text for ch in ['\u00b7','\u2022','\u2027','\u318d','\u22c5','\u30fb']),p.name
files=[p for p in D.iterdir() if p.is_file() and p.name!='PACKAGE_CHECK.json']+[Path(__file__),OLD/'design_fixture.json',OLD/'customer_fixture.csv',OLD/'calculated_results.json']
archive=ROOT/'TRI_V_outputs_v02_AUTHOR_REVIEW.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zf:
 for p in files:zf.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as zf:assert zf.testzip() is None;assert len(zf.namelist())==len(files)
package={'file':str(archive),'file_count':len(files),'zip_crc':'passed','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'audience':'저자와 개발 검토용. 정답 포함. 참여자에게 전체 ZIP을 전달하지 않음','original_book_changed':False}
(D/'PACKAGE_CHECK.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'base_reconciled':True,'cost_sensitivity':sensitivity,'max_upper_KRW':max_upper,'records_each':len(records),'mutations_rejected':len(mutations),'human_rows':len(observations),'package':package},ensure_ascii=False,indent=2))
