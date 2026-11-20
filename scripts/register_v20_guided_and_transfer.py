"""Register v20's guided revision and transfer tasks against frozen v19."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];D=R/'e-book/manuscript/development_v20';D.mkdir(parents=True,exist_ok=True)
s=(R/'e-book/exports/v19/ebook_review_v19.md').read_text(encoding='utf-8');paras=s.split('\n\n')
def para(start):
 hits=[p for p in paras if p.lstrip('\n').startswith(start)];assert len(hits)==1,(start,len(hits));return hits[0]
def edit(id,ch,start,after,reason):return {'id':id,'chapter':ch,'before':para(start),'after':after,'reason':reason}
guided=[
edit('G2',2,'이 축의 작성 결과는', '''여기서부터 4장까지는 같은 JH Motors 설계 기록의 문장을 이어서 고쳐 보자. 뒤에서 읽을 큰 A/B/H 실습에 연결되는 기록이며 새 실험 결과를 만드는 것은 아니다. 출발 문장은 “편의 안내 B를 모든 고객에게 보내 시승을 늘린다”다. 이는 아직 효과를 확인하지 않은 기획 초안이다. 정화에서는 B가 좋다는 말을 보태기보다 비교할 수 있는 문장으로 바꾼다.

“기준 시점 SMS 동의가 있고 기존 시승 완료가 없는 잠재 고객에게 기존 안내 A와 편의 안내 B, 해당 메시지 미발송 H를 고객별로 무작위 배정해 비교한다. 정한 개인별 관측 창의 완료를 배정 고객 전체에서 읽는다. B-A의 안내 변경 질문과 A-H 및 B-H의 발송 질문은 나누어 둔다.” 누구에게 보낼지와 무엇을 비교할지가 처음 초안보다 좁아졌다. 전달 성공자나 예약자만 남기겠다는 조건도 없다.

이 문장은 배정과 측정을 실제로 확인했다는 보고가 아니다. 원장과 관측 창을 대조한 뒤 해석 가능, 일부 지표 제한, 비교 보류 중 현재 상태를 같은 기록에 남긴다. 확인하지 못한 근거는 소유자와 확인 기한 또는 기한을 정할 역할에 연결한다. 다음 장에서는 이 비교 명세를 다시 쓰지 않고 적용 범위 문장을 고친다.''','Replace a generic output reminder with a guided revision of one planning record.'),
edit('G3',3,'여기서 남길 것은 공통 운용 기준의 적용 범위 문장이다.', '''앞 장에서 고친 비교 명세는 그대로 참조한다. 이번에는 처음 문장의 ‘모든 고객’을 어떻게 고칠지 생각해 보자. 현재 기록은 동의한 미시승 잠재 고객의 전체 비교를 계획한다. 이 정보만으로 특정 지역이나 차종에서 B가 더 좋다고 적을 수는 없다.

적용 범위 문장은 “이번 계획은 정한 적격 잠재 고객 구성의 전체 효과를 묻는다. 이미 시승한 고객이나 다른 고객 구성까지 같은 효과라고 쓰지 않는다. 고객군별로 정책을 달리하는 선택이 필요하면 배정 전 집단 정의와 효과 차이, 정보량 및 다중성의 검토를 별도 질문으로 남긴다”로 고친다. 현재 전체 범위만 읽는 최소 경로와 집단별 적용을 위한 추가 질문이 갈라진다.

모든 고객에게 효과가 같다고 가정한 것도, 지금 당장 세분화를 모두 수행하라는 뜻도 아니다. 이 장에서는 누구에게 적용할지 바뀌는 질문을 기록에 더했다. 다음 대상의 구성이 달라져 선택이 달라질 수 있다면 그때 어느 근거를 다시 열어야 하는지 남긴다. 4장에서는 이 범위를 지킨 채 현재 할 일을 고른다.''','Continue the same record through V2 without inventing subgroup findings or mandatory segmentation.'),
edit('G4',4,'이 축의 산출물은 공통 운용 기준의 결정문이다.', '''처음의 “B를 모든 고객에게 보낸다”는 문장은 이제 비교 명세와 적용 범위를 건너뛸 수 없다. 앞의 두 장에서 고친 문장은 그대로 두고 현재 선택만 이어 쓴다. “현재는 정한 대상의 비교 설계와 보호 평가를 준비한다. 완료 결과와 실제 변경 비용, 보호 근거 및 수용 가능한 운영 범위를 확인한 뒤 도입 범위와 승인 요청 여부를 정한다. 아직 발송을 승인한 기록은 아니다.”

효과가 없어서 중단한다는 결론을 낸 것은 아니다. 결과를 보기 전의 설계 단계에서 할 일과 결정 조건을 정한 것이다. 이처럼 같은 기록에서 비교할 조건을 바로잡고, 적용할 대상을 좁히고, 지금 허용하는 행동을 고치면 세 축이 문장을 바꾼다. 책임과 기한, 다시 검토할 조건은 기존 여섯 항목에 연결한다. 사업과 보호 기준은 결과 전에 정하고 사후 변경은 별도 이력으로 남긴다. 뒤의 통계와 사례에서는 이 기록에 어떤 결과를 넣을 수 있는지 확인한다.''','Complete a planning-stage action, not an invented outcome or approval.')]
transfer=[]
old_rules=para('이 예제에서만 사용할 판단 규칙은')
old_group=para('조건 나는 배정 전에 두 고객군의 적용 주장을 정하고')
sentences=old_group.split(' ')
# Carry the design and all second-group counts ahead of the answer, not its conclusion.
context='조건 가와 다와 라는 현재 대상 범위, 조건 나는 미리 정한 첫 고객군의 적용을 묻는다. 조건 나는 배정 전에 두 고객군의 적용 주장을 정하고 각 집단의 성과와 보호를 함께 요구한 설정이다. 두 적용 주장에는 Bonferroni로 각 유의수준 0.025를 사용했다. 첫 이용 대상의 완료 구간은 97.5%, 보호 상한은 단측 97.5% 수준이다. 다른 사전 집단은 A 1,200/4,000명과 B 1,200/4,000명이며 완료 차이의 97.5% 구간은 [-2.30, +2.30]pp다.'
transfer.append({'id':'T8-brief','chapter':8,'before':old_rules,'after':old_rules+'\n\n'+context+'\n\n두 표를 모두 읽은 뒤 해설로 넘어가기 전에 각 조건의 현재 선택을 한 문장으로 적어 보자. 그 선택을 지지하는 완료와 보호 근거, 적용할 대상 범위를 연결하고, 더 확인한다면 어떤 답이 선택을 바꿀지 하나만 남긴다. 결론을 보류로 통일하거나 모든 조건에 새 실험을 붙이지 않는다. 필요한 확인이 없다면 그 이유를 적는다. 기존 여섯 항목을 쓰되 새 양식을 만들 필요는 없다.','reason':'Put all necessary design information ahead of the transfer exercise; postpone classifications.'})
for id,head in [('T8-completion','| 조건 | A 완료와 배정 |'),('T8-protection','| 조건 | A와 B의 철회 |')]:
 before=para(head);after=before
 for label in ['가: 현재 범위','나: 사전 집단','다: 정보 부족','라: 보호 검토']:after=after.replace(label,label[0])
 if id=='T8-protection':
  lines=[]
  for line in after.splitlines():
   cells=line.split('|');lines.append('|'.join(cells[:-2]+['']))
  after='\n'.join(lines)
 transfer.append({'id':id,'chapter':8,'before':before,'after':after,'reason':'Remove answer-bearing labels and the current-judgment column; retain all observed counts, limits and levels.'})
transfer.append({'id':'T8-answer','chapter':8,'before':old_group,'after':'조건 나는 정한 첫 집단의 성과와 보호 근거가 적용 기준을 충족한다. 따라서 해당 집단의 실행 후보로 넘길 수 있지만 다른 집단의 우위나 두 효과의 차이까지 입증한 것은 아니다. 반대로 정한 첫 집단 안의 적용을 판단할 때 무조건 다시 실험하라는 요구도 하지 않는다. 자신의 답에서 어느 집단의 어떤 주장에 해당하는지 확인해 보자.','reason':'Keep the interpretation after the unlabelled problem; design details were moved ahead, not deleted.'})
transfer.append(edit('T10-question',10,'이전 결론을 그대로 옮기거나 자료를 모두 버리고', '''해설을 읽기 전에 이전 기록에서 그대로 참조할 문장과 다시 열어야 할 문장을 각각 골라 보자. 정책과 고객 및 사건의 정의, 수요와 가용 슬롯, 비용, 보호 조건 가운데 무엇이 바뀌었다는 근거가 있는지 살핀다. 슬롯이 늘었다는 회신만 있을 때 현재 선택을 바꿀 수 있는가. 더 묻는다면 어떤 답 하나가 선택을 바꾸는가. 아직 주어지지 않은 비용과 승인, 담당자 및 기한을 채워 넣지는 않는다.

선택한 문장은 기존 기록의 근거와 적용 범위, 현재 선택 및 추가 확인에 연결한다. 마지막으로 자기 CRM 업무의 제약 하나를 떠올리고, 그 제약이 달라져도 유지할 근거와 다시 확인할 근거를 같은 방식으로 구분해 보자. 숫자를 바꾸어 새 효과를 계산하는 문제가 아니라, 이전 판단을 어디까지 이어 쓸지 정하는 문제다. 이 장 끝에서 자신의 선택 이유를 해설과 대조한다.''','Require record reuse and a decision-changing question before the existing answer.'))
anchor=para('따라서 새 결정문에는')
transfer.append({'id':'T10-feedback','chapter':10,'before':anchor,'after':anchor+'\n\n자신의 답에서 정책과 고객 및 사건의 정의를 참조할 근거로 골랐다면, 이번에도 같은지 확인한다는 조건이 붙었는지 보자. 슬롯 증가만으로 수요와 비용 및 보호 상태까지 좋아졌다고 적었다면 그 주장을 다시 연다. 이전 결과를 모두 버리거나 슬롯만 늘었으니 즉시 확대한다는 두 답 사이에는 재사용할 근거와 새로 필요한 답을 나누는 선택이 있다. 어떤 추가 답이 와야 현재 행동을 바꿀 수 있는지 설명했다면 해설과 문장이 달라도 판단 근거를 대조할 수 있다. 답의 첨부와 실행 승인도 별개로 남아 있어야 한다.','reason':'Give feedback on the reasoning and boundary, not exact wording or a compulsory new experiment.'})
for name,items in [('02_GUIDED_RECORD.json',guided),('03_TRANSFER.json',transfer)]:
 state=s
 for e in items:
  assert state.count(e['before'])==1,e['id'];assert e['before']!=e['after'];assert not any(c in e['after'] for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb');state=state.replace(e['before'],e['after'])
 (D/name).write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
 print(name,len(items),'registered; source unchanged')
