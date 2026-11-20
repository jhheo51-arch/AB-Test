from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / "e-book/exports/v22"


def load(name):
    return json.loads((EDITION / name).read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


layout = load("validation_v22.json")
integration = load("integration_validation_v22.json")
numbers = load("numeric_text_validation_v22.json")
sql = load("chapter12_sql_validation_v22.json")
package = load("package_smoke_v22.json")
pdf = EDITION / "ebook_review_v22.pdf"
archive = ROOT / package["archive"]
if digest(pdf) != layout["pdf_sha256"] or digest(archive) != package["sha256"]:
    raise ValueError("PDF 또는 ZIP이 검증 당시 파일과 다릅니다.")
with ZipFile(archive) as bundle:
    if (bundle.testzip() is not None or len(bundle.namelist()) != package["file_count"]
            or sha256(bundle.read(pdf.name)).hexdigest() != layout["pdf_sha256"]):
        raise ValueError("읽기 ZIP의 무결성 또는 본책 사본을 확인하세요.")

preserved = 0
for edition in ['v20', 'v21', 'v22']:
    folder = ROOT / ('e-book/manuscript/development_' + edition)
    baseline = json.loads((folder / 'BASELINE.json').read_text(encoding='utf-8'))
    mapping = {}
    if (folder / 'BASELINE_RELOCATION.json').exists():
        mapping = {r['original_path']: r['current_path'] for r in json.loads((folder / 'BASELINE_RELOCATION.json').read_text(encoding='utf-8'))['paths']}
    for source, expected in baseline['hashes'].items():
        if digest(ROOT / mapping.get(source, source)) != expected:
            raise ValueError('동결 입력과 다릅니다: ' + source)
        preserved += 1
ui = json.loads((ROOT / 'e-book/design/v22/ui_validation_v22.json').read_text(encoding='utf-8'))
printing = json.loads((ROOT / 'e-book/design/v22/print_validation_v22.json').read_text(encoding='utf-8'))
assert integration['status'] == package['status'] == ui['status'] == printing['status'] == 'passed'
assert layout['pdf_pages'] == 97
assert [u['page'] for u in layout['atomic_layout_units'] if 'worked-record' in u['cls']] == [79]

review_folder = ROOT / 'e-book/review/publication_v22'
next_steps = json.loads((review_folder / 'NEXT_STEPS.json').read_text(encoding='utf-8'))
assert next_steps['edition'] == 'v0.22'
assert len({task['id'] for task in next_steps['tasks']}) == len(next_steps['tasks'])
for name in ['PUBLICATION_REVIEW.md', 'PUBLICATION_GATES.md', 'NEXT_STEPS.md']:
    assert (review_folder / name).is_file(), name
assert next_steps['active'] is False
maintenance = json.loads((ROOT / 'e-book/maintenance/TASKS.json').read_text(encoding='utf-8'))
assert maintenance['goal'] == 'private_github_learning_reference'
assert maintenance['publication_intent'] is False
assert len({t['id'] for t in maintenance['tasks']}) == len(maintenance['tasks'])
for name in ['repository_check.json', 'regression_check.json']:
    assert json.loads((ROOT / 'e-book/maintenance/checks' / name).read_text(encoding='utf-8'))['status'] == 'passed'

status = {
    "checked_at_seoul": datetime.now(timezone(timedelta(hours=9))).isoformat(),
    "latest_reading_edition": "v0.22",
    "book_title": "그래서, 이 캠페인 계속할까요?",
    "publication_status": "출판하지 않음. 비공개 GitHub 참고 자료",
    "book": {
        "pdf": pdf.relative_to(ROOT).as_posix(),
        "html": (EDITION / "ebook_review_v22.html").relative_to(ROOT).as_posix(),
        "pages": layout["pdf_pages"],
        "sha256": layout["pdf_sha256"],
    },
    "reader_bundle": package,
    "verification": {
        "integration_checks": integration["check_count"],
        "integration_scope": "v0.22 최소 교정 보존 및 출력 검사. 이전 판 검사와 별도 범위.",
        "preserved_input_checks": preserved,
        "zoom_and_return_cases": len(ui['zoom_cases']),
        "long_input_print_cases": printing['cases'],
        "numeric_text_checks": numbers["numeric_text_checks"],
        "read_only_sql_ledger_match": sql["ledger_match"],
        "actual_reader_test": integration["actual_reader_test"],
        "human_approved": integration["human_approval"],
    },
    "repository_maintenance": maintenance,
    "publication_review": {
        "active": False,
        "kind": "과거 AI 편집 검토 보존. 출판 계획과 판매 준비는 중단함.",
        "assessment": next_steps['current_assessment'],
        "development_scope": next_steps['scope'],
        "report": 'e-book/review/publication_v22/PUBLICATION_REVIEW.md',
        "next_steps": 'e-book/review/publication_v22/NEXT_STEPS.md',
        "gates": 'e-book/review/publication_v22/PUBLICATION_GATES.md',
        "submission_route": next_steps['submission_route'],
        "human_review_completed": next_steps['human_review_completed'],
        "actual_reader_test_completed": next_steps['actual_reader_test_completed'],
        "publication_approved": next_steps['publication_approved'],
        "superseded_by": "e-book/maintenance/TASKS.json",
    },
    "synthetic_data": {
        "original": "e-book/virtual-data/v03/README.md",
        "corrected": "e-book/virtual-data/v13/README.md",
    },
    "video_workflow": "video-production/README.md",
    "tool_prd": "tool/prd/v01/README.md",
}
(ROOT / "PROJECT_STATUS.json").write_text(
    json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
)
print(f"v0.22 PDF {status['book']['pages']}쪽과 ZIP {package['file_count']}개 항목의 무결성 확인")
