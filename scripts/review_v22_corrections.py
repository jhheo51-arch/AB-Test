"""Record the limited proof corrections and final execution evidence."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,re,hashlib
import pymupdf
R=Path(__file__).resolve().parents[1];D=R/'e-book/manuscript/development_v22';O=R/'e-book/exports/v22';V=R/'e-book/design/v22';compact=lambda t:re.sub(r'\s+','',t)
edits=json.loads((D/'PROOF_CORRECTIONS.json').read_text(encoding='utf-8'));positions={}
with pymupdf.open(O/'ebook_review_v22.pdf') as pdf:
 for e in edits:
  pages=[i+1 for i,p in enumerate(pdf) if compact(e['after']) in compact(p.get_text())];assert len(pages)==1,(e['id'],pages);positions[e['id']]=pages[0]
  if e['id'] in ['F1','F2','F3']:pdf[pages[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1)).save(V/(e['id']+'_corrected.png'))
 old=R/'e-book/packages/JH_CRM_ebook_reader_v21.zip';h=hashlib.sha256(old.read_bytes()).hexdigest();assert h=='a49455c878d74ad36b866b8d957a214a7a79c2f420fecde04347d949ebda555f'
(D/'ARCHIVE_BASELINE.json').write_text(json.dumps({'path':old.relative_to(R).as_posix(),'sha256':h,'matches_previously_delivered_archive':True},indent=2),encoding='utf-8',newline='\n')
report=json.loads((O/'integration_validation_v22.json').read_text(encoding='utf-8'));pr=json.loads((V/'print_validation_v22.json').read_text(encoding='utf-8'))
rows='\n'.join('| '+e['id']+' | '+e['before']+' → '+e['after']+' | '+str(positions[e['id']])+'쪽 |' for e in edits)
notes=f'''# v0.22 검수 교정 기록

기록 시각: {datetime.now(timezone(timedelta(hours=9))).isoformat()} (Asia/Seoul)

새 사례와 이론 및 기능을 늘리지 않고 proof_v21의 확정 문제 네 건과 표현 후보 두 건만 처리했다. 원고 교정은 다섯 곳이고 인쇄 수리는 한 건이다. F1~F3는 참조 오류, F4는 긴 입력 인쇄 누락이다. C1/C2는 확정 통계 오류가 아니라 독해상 범위를 명확히 한 수정이다.

| 식별자 | 전 → 후 | 최종 위치 |
|---|---|---|
{rows}
| F4 | 고정 높이 입력 칸의 보이는 일부만 인쇄 → 인쇄할 때 현재 값을 줄바꿈 보존 텍스트로 변환 | MINIMUM_RECORD.html |

C1은 지점 안과 지점 사이의 특정 한 경우로 좁히지 않고 고객 간 자원 간섭으로 표현했다. C2는 이미 관측한 계약과 아직 확인하지 못한 실제 매출을 구분했다. 숫자와 통계의 결론, TRI-V 세 축과 여섯 항목, 79쪽 완성 결정문은 바꾸지 않았다.

## 실제 실행 확인

- 최종 PDF는 97쪽이고 완성 결정문은 이전 판과 문구가 동일한 물리 79쪽 한 면이다.
- v21 제작 입력과 산출물 65개 SHA-256이 그대로이며 이전에 전달한 v21 ZIP 해시도 일치한다. 원자료나 지난 판은 덮어쓰지 않았다.
- 새 원고는 이전 판에 승인된 다섯 문구 치환과 파일 버전 및 다시 계산한 찾아보기 쪽수만 반영한 결과와 일치한다.
- 기존 수치 문자 및 읽기 전용 SQL, 그림 좌표, 실제 각주 호출과 주석의 같은 쪽 배치, 내부 링크와 본문 및 그림의 인쇄 크기 검사를 통과했다. 정량 그림 다섯 파일의 바이트도 v21과 같다. 통계 분석 전체를 새로 재감사했다는 뜻은 아니다.
- 그림 확대 및 위치와 포커스 복귀 26개 조합, 실제 복사와 차단 시 대체 동작, 텍스트 파일 저장을 재검사했다. 자동 저장이나 외부 전송을 추가하지 않았다.
- 앞서 누락을 재현한 여섯 칸의 13줄씩 입력은 이번에는 3쪽으로 인쇄되고 총 78줄이 빠짐없이 있다. 한 칸이 여러 쪽을 넘는 시험도 5쪽에서 156줄이 모두 보존됐다. 이 숫자는 실제 사용자 기록이 아니라 시험 문구의 검사 범위다.
- 빈 작성 양식은 여전히 한 쪽이다. 인쇄 이후 화면 입력값이 그대로이고 임시 인쇄용 요소는 제거되는 것도 확인했다.
- 변경 전후 색과 기본 글꼴을 유지했다. 인쇄 텍스트는 기존 #142D32 글자와 #FFFFFF 배경을 사용한다. 새 색이나 디자인 체계를 도입하지 않았다.
- 변경된 참조 세 구간과 79쪽 결정문을 개별 렌더했다. 전권 contact sheet와 차단된 PDF 인용 전수 대조는 실행하지 않았다.

이번 판 통합 검사는 {report['check_count']}개이며 해당 판의 보존과 실행 범위다. 검사 수를 글 품질이나 독자 이해 점수로 해석하지 않는다. 구성 확대와 추가 개발은 계속 보류한다. 실제 독자시험, 사람의 통계 검수, 최종 출간 및 권리 승인은 별도이고 Git 커밋과 푸시는 실행하지 않았다.

MANUSCRIPT_CHANGES.json에는 v20에서 이어진 원래 편집 이력을 남겼다. 이번 v21 기준 교정은 development/PROOF_CORRECTIONS.json과 이 기록, 저장소의 BASELINE.json을 따른다.

## 수정 원칙

지시하는 표와 실제 위치만 맞춰 기존 설명을 유지했다.
긴 기록은 한 쪽에 억지로 넣지 않고 여러 쪽에 온전히 인쇄되게 했다.
빈 양식과 기본 읽기 화면, 완성 결정문은 그대로 유지했다.
'''
(D/'CORRECTION_NOTES.md').write_text(notes,encoding='utf-8',newline='\n');(V/'DEVELOPMENT.md').write_text(notes,encoding='utf-8',newline='\n')
review='# v0.22 검토 결과\n\n최종97쪽, 완성 결정문79쪽 한 면과 문구 보존. 승인된 참조 및 표현 다섯 곳과 인쇄 수리만 반영했다.\n\n통합, 수치 및 읽기 전용 SQL, 조판과 그림 검사, 기존 웹 기능의 회귀 검사를 통과했다. 긴 입력 인쇄는 기존 실패 입력과 한 칸이 여러 쪽을 넘는 조건에서 누락 없이 재현했다. 빈 양식은 한 쪽이다. 상세 범위와 미실시 항목은 DEVELOPMENT.md, UI_VALIDATION.json, PRINT_VALIDATION.json을 따른다.\n\n이는 자동 동작 및 AI 검토이지 사람 검수나 실제 독자시험 및 출간 승인이 아니다. 추가 개발과 GitHub 반영은 진행하지 않았다.\n'
(V/'REVIEW.md').write_text(review,encoding='utf-8',newline='\n');(V/'TARGETED_CORRECTIONS.json').write_text(json.dumps(positions,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'positions':positions,'status':report['status'],'print_cases':pr['cases']},ensure_ascii=False,indent=2))
