"""Refresh current reader metadata without loading local historical editions."""
from pathlib import Path
from hashlib import sha256
import json
from check_latest_ebook import check_latest

ROOT = Path(__file__).resolve().parents[1]
verification = check_latest(ROOT)
status = {
    'checked_at_seoul': verification['checked_at_seoul'],
    'book_title': '그래서, 이 캠페인 계속할까요?',
    'author': '허재혁',
    'publication_status': '별도 출판과 판매하지 않음. 공개 참고 자료',
    'book': {
        'pdf': 'e-book/ebook.pdf', 'html': 'e-book/ebook.html',
        'markdown': 'e-book/ebook.md', 'pages': verification['pdf_pages_recorded'],
        'decision_page': verification['decision_page_recorded'],
        'sha256': verification['pdf_sha256'],
    },
    'storage_policy': {
        'github': 'single_latest_without_version_paths',
        'previous_editions_sources_and_reviews': 'local_only',
        'git_history_rewritten': False,
    },
    'current_integrity_check': verification,
    'management_mode': 'reported_errors_only',
    'prior_review_notice': '저자 승인에 따른 전권 서술 개정과 두 읽기 경로 분리, 핵심 개념 36개 참고 해설 확장을 반영했다. 이후 승인된 장별 새 쪽, 데이터 그림 다섯 개의 시각 편집과 표지 간소화를 적용하고 조판 및 독서 기능을 재검사했다. 기존 실험 수치와 표, 코드 및 각주를 보존하고 AI 의미 대조와 독서 기능 및 조판을 검사했다. 과거 검수와 원자료는 로컬에 보존한다. 이 시각은 파일 무결성 검사 시각이며 통계 재계산이나 실제 독자시험의 완료 시각이 아니다.',
    'known_historical_plan_byte_difference': 'LF/CRLF 차이 고지 유지. 과거 원본을 수정해 차이를 지우지 않음.',
    'actual_reader_test_completed': False,
    'independent_human_review_completed': False,
    'tool_roadmap': 'tool/ROADMAP.md',
    'tool_prd': 'tool/prd/README.md',
    'video_workflow': 'video-production/README.md',
}
(ROOT / 'PROJECT_STATUS.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(verification, ensure_ascii=False, indent=2))
