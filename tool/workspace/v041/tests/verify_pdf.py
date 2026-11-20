"""Verify the actual browser-generated synthetic report, not CSS declarations."""
from pathlib import Path
import json
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
with pymupdf.open(ROOT/'screenshots/SYNTHETIC_RESULT_REPORT.pdf') as pdf:
    spans=[s for page in pdf for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans'] if s['text'].strip()]
    minimum=min(s['size'] for s in spans)
    text='\n'.join(page.get_text() for page in pdf)
    assert minimum>=11.95,minimum
    assert '합성' in text and '13.00%' in text and '15.00%' in text and '승패 보류' in text
    assert '집단 이름과 상세 결과는 공유에서 제외' in text
    assert '"p_raw"' not in text and 'subject_id' not in text
    for index,page in enumerate(pdf):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(ROOT/f'screenshots/report_page_{index+1}.png')
    result={'status':'PASS','pages':len(pdf),'minimum_actual_font_pt':minimum,'excluded_group_detail_checked':True,'rendered_all_pages':True,'scope':'synthetic default report; not all possible user-content pagination'}
(ROOT/'PDF_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
