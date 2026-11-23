from pathlib import Path
import hashlib,json,pymupdf
R=Path(__file__).resolve().parents[1];f=R/'lineage_evidence/LINEAGE_REPORT.pdf';d=pymupdf.open(f);text=''.join(p.get_text() for p in d);flat=''.join(text.split())
raw='variant,converted,participants\nA,1,10\nB,2,10';canonical='arm,success,total\nA,1,10\nB,2,10'
expected=[hashlib.sha256(s.encode('utf-8')).hexdigest() for s in [raw,canonical]]
assert all(h in flat for h in expected)
assert all(s in text for s in ['최초 입력의 기록','복원 전 직전 계산 기록','이번 계산 입력','원자료를 다시 검증하지 않았습니다'])
sizes=[s['size'] for page in d for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans'] if s['text'].strip()];assert min(sizes)>=11.9
for i,page in enumerate(d):page.get_pixmap(matrix=pymupdf.Matrix(1.1,1.1)).save(R/f'lineage_evidence/lineage_pdf_page_{i+1}.png')
r={'status':'PASS','pages':len(d),'minimum_actual_font_pt':min(sizes),'computed_origin_and_current_sha256_present':True,'typed_labels_and_no_raw_revalidation_warning_present':True,'pdf_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(R/'lineage_evidence/LINEAGE_PDF_PROOF.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
