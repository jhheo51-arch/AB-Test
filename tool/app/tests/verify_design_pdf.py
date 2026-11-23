"""Read the actual Chrome PDFs; run after verify_design.py."""
from pathlib import Path
import json,pymupdf
R=Path(__file__).resolve().parents[1];E=R/'design-evidence'
texts={n:' '.join(p.get_text() for p in pymupdf.open(E/n)) for n in ['RESULT_REPORT.pdf','INVALIDATED_REPORT.pdf']}
checks={'current_context_present':'시승 예약 완료를 늘리기' in texts['RESULT_REPORT.pdf'],'private_situation_excluded':'SYNTHETIC_SITUATION' not in texts['RESULT_REPORT.pdf'],'invalidated_notice_present':'현재 확인된 보고서가 없습니다' in texts['INVALIDATED_REPORT.pdf'],'stale_purpose_excluded':'시승 예약 완료를 늘리기' not in texts['INVALIDATED_REPORT.pdf']}
assert all(checks.values()),checks
(E/'PDF_TEXT_VERIFICATION.json').write_text(json.dumps({'status':'PASS','checks':checks,'texts':texts},ensure_ascii=False,indent=2),encoding='utf-8');print('PASS 4 actual PDF text checks')
