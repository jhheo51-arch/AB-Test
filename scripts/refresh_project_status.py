from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / "e-book/exports/v19"


def load(name):
    return json.loads((EDITION / name).read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


layout = load("validation_v19.json")
integration = load("integration_validation_v19.json")
numbers = load("numeric_text_validation_v19.json")
sql = load("chapter12_sql_validation_v19.json")
package = load("package_smoke_v19.json")
pdf = EDITION / "ebook_review_v19.pdf"
archive = ROOT / package["archive"]
if digest(pdf) != layout["pdf_sha256"] or digest(archive) != package["sha256"]:
    raise ValueError("PDF 또는 ZIP이 검증 당시 파일과 다릅니다.")
with ZipFile(archive) as bundle:
    if (bundle.testzip() is not None or len(bundle.namelist()) != package["file_count"]
            or sha256(bundle.read(pdf.name)).hexdigest() != layout["pdf_sha256"]):
        raise ValueError("읽기 ZIP의 무결성 또는 본책 사본을 확인하세요.")

status = {
    "checked_at_seoul": datetime.now(timezone(timedelta(hours=9))).date().isoformat(),
    "latest_reading_edition": "v0.19",
    "book_title": "그래서, 이 캠페인 계속할까요?",
    "publication_status": "저자 검토본",
    "book": {
        "pdf": pdf.relative_to(ROOT).as_posix(),
        "html": (EDITION / "ebook_review_v19.html").relative_to(ROOT).as_posix(),
        "pages": layout["pdf_pages"],
        "sha256": layout["pdf_sha256"],
    },
    "reader_bundle": package,
    "verification": {
        "integration_checks": integration["checks_passed"],
        "numeric_text_checks": numbers["numeric_text_checks"],
        "read_only_sql_ledger_match": sql["ledger_match"],
        "actual_reader_test": integration["actual_reader_test"],
        "human_approved": integration["human_approved"],
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
print(f"v0.19 PDF {status['book']['pages']}쪽과 ZIP {package['file_count']}개 항목의 무결성 확인")
