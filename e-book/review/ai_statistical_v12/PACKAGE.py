"""Package only audit outputs; do not redistribute original databases."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,tempfile,os
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];dest=ROOT/'TRI_V_v12_AI_STATISTICAL_AUDIT.zip'
files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.md','.json','.csv','.npz'] and p.name not in ['PACKAGE_CHECK.json']]
required=['REPORT.md','SUMMARY.json','FINDINGS.csv','EXECUTION_LOG.json','BASELINE.json','PRESERVATION_CHECK.json','SAMPLING_REPLAY.json','counterexamples/FINDING_SCORE.md']
assert all((OUT/n).is_file() for n in required)
start='''# v0.12 AI 및 별도 코드 통계 검수

REPORT.md부터 읽으세요. 전체 무오류 합격이 아니며 수정할 수치와 구현 불일치를 기록한 결과입니다. 사람 독립 통계 검수는 미실시입니다. 원고와 원자료는 수정하지 않았고 이번 검수에서 멈춥니다.

SUMMARY.json과 FINDINGS.csv가 요약과 발견 장부이며, 각 하위 폴더에 새 계산 코드와 결과 및 검토 문서가 있습니다. EXECUTION_LOG.json은 통합 담당자가 재실행한 실제 명령과 종료 상태입니다. core와 counterexamples의 종료1은 발견사항을 보존하는 실패 판정이며 숨기지 않았습니다.

이 ZIP은 원 DB나 고객 CSV를 포함하는 전체 재현 환경이 아닙니다. 재실행에는 저장소의 기준 커밋 eefdd4ee9ea026c06d65a760706a742e02407bce와 입력 파일이 필요합니다. 별도 작업 사본에서 기준 커밋을 열고 이 파일들을 e-book/review/ai_statistical_v12/에 놓으세요. 일부 검사는 기준 HEAD까지 확인하므로 다른 커밋에서 실행하면 입력이 같아도 HEAD 검사만 실패할 수 있습니다. 라이브러리 버전은 각 RESULTS.json에 기록돼 있으며 재실행 시 같은 버전을 맞춰야 당시 수치를 정확히 비교할 수 있습니다.

기존 분석기를 실행하거나 원 DB 및 계획, 지난 결과를 덮어쓰지 마세요. 명령은 EXECUTION_LOG.json을 따릅니다. SAMPLING_REPLAY.py는 같은 기록 seed와 순서로 새 배열을 재구성한 코드이며, NPZ는 역사적 원배열이 아닙니다. 원시 배열의 역사적 보존과 사전 동결은 별개 미확인 사항입니다.
'''
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(OUT).as_posix())
 z.writestr('START_HERE.md',start)
with tempfile.TemporaryDirectory(prefix='stat_audit_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:
  assert z.testzip() is None;count=len(z.namelist());z.extractall(td)
 for p in files:
  q=Path(td)/p.relative_to(OUT);assert q.read_bytes()==p.read_bytes()
 for name in ['SUMMARY.json','core/RESULTS.json','scenarios/RESULTS.json','interpretation/RESULTS.json','counterexamples/RESULTS.json']:json.loads((Path(td)/name).read_text(encoding='utf-8'))
 assert json.loads((Path(td)/'SUMMARY.json').read_text(encoding='utf-8'))['finding_count']==5
report={'archive':str(dest),'file_count':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'zip_integrity':'passed','extracted_entry_bytes':'passed','extracted_reports_parse':'passed','original_databases_included':False,'human_review_completed':False,'next_publication_stage_started':False}
(OUT/'PACKAGE_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
