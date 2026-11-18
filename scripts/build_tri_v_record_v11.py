"""Clarify the existing six-field record for the v0.11 reading edition."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v11';OUT.mkdir(parents=True,exist_ok=True)
OLD=ROOT/'e-book/review/methodology/tri_v_refinement_v03'
s=(ROOT/'scripts/build_tri_v_refinement_v03.py').read_text(encoding='utf-8')
s=s.replace("D=ROOT/'e-book/review/methodology/tri_v_refinement_v03';fixture=", "D=ROOT/'e-book/exports/v11';fixture=")
shutil.copyfile(OLD/'counterexample_fixture.json',OUT/'counterexample_fixture.json')
changes=[
('무엇을 누구에게 적용할지. 기존 대비를 다시 쓰지 말고 참조 가능.','가능한 대안과 적용 범위. 전체 전환인지 제한 적용인지 먼저 적기.'),
('필요 시 질문, 조건별 행동, 담당과 기한. 없으면 생략 이유와 예외.','어떤 확인 결과가 선택을 바꾸는지. 담당과 기한 또는 생략 이유.'),
('어떤 관측 또는 가정 변화가 생기면 현재 선택을 다시 볼지.','어떤 변화가 선택을 바꾸는지. 추가 분석, 실험 종료와 운영 중지를 구분.'),
('실행 후보 / 조건부 후보 / 추가 확인 / 미확대 / 중단. 보호와 실제 승인 상태.','실행 후보 / 조건부 후보 / 추가 확인 / 미확대 / 운영 중지. 실제 승인 상태.'),
('같은 적격 조건과 정책 범위에서 안내 B를 실행 후보로 넘길지 판단한다.','현행 A 유지와 같은 적격 범위의 B 전환 가운데 B를 실행 후보로 넘길지 판단한다.'),
('계획 참조에서 대비, 동의, 배정과 분석 단위, 주지표와 분모, 관측과 종료, 다중성 및 사업과 보호 기준을 확인할 수 없으면 먼저 그 공백을 보완합니다. 실행 후보는 실제 승인이 아닙니다. 안전과 권리 및 감사 의무는 생략하지 않습니다. 입력은 서버로 전송하거나 자동 저장하지 않습니다.','기존 계획에 대비, 동의, 배정과 분석, 지표와 분모, 관측과 통계적 종료, 다중성 및 사업과 보호 기준이 없으면 먼저 보완합니다. 추가 분석 생략은 실험의 조기 종료가 아닙니다. 실행 후보는 승인이 아니며 안전과 권리 및 감사 의무는 생략하지 않습니다. 입력은 전송하거나 자동 저장하지 않습니다.')]
for before,after in changes:
 assert before in s,before;s=s.replace(before,after)
s=s.replace('v0.3','v0.11')
exec(compile(s,__file__,'exec'),globals())
md=(OLD/'MINIMUM_RECORD.md').read_text(encoding='utf-8').replace('v0.3','v0.11')
for before,after in [
('무엇을 누구에게 적용할지 정한다.','가능한 대안과 적용 범위를 적는다. 전체 전환, 제한 적용, 현행 유지와 새 검증 중 무엇을 판단하는지 먼저 정한다.'),
('필요하면 질문과 조건별 행동, 담당과 기한을 연결한다. 필요 없으면 생략 이유와 예외를 적는다.','어떤 확인 결과가 어떤 선택을 바꿀지 적는다. 필요하면 담당과 기한을 연결하고 생략하면 이유와 예외를 남긴다.'),
('미확대 또는 중단 제안.','미확대 또는 운영 중단 제안.'),
('어떤 관측이나 가정 변화가 생기면 현재 선택을 다시 볼지 적는다.','어떤 관측이나 가정 변화가 선택을 바꿀지 적는다. 추가 분석 중단, 통계적 실험 종료와 운영 중지를 구분한다.')]:
 assert before in md,before;md=md.replace(before,after)
md+='\nB를 채택하지 않았다는 이유로 A가 모든 대안 중 최적이라고 쓰지 않는다. 이번에 비교한 대안과 범위 안에서 현행을 유지하는 선택과 최적성의 증명은 다르다. 추가 분석을 그만하는 판단은 사전에 정한 실험 종료 규칙을 바꾸거나 보호 대응을 늦추는 근거가 아니다.\n'
(OUT/'MINIMUM_RECORD.md').write_text(md,encoding='utf-8',newline='\n')
