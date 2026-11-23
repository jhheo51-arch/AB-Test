from pathlib import Path
import pymupdf,json
root=Path(__file__).resolve().parents[1]
p=root/'workflow_evidence/GUIDED_JUDGMENT.pdf';d=pymupdf.open(p);text=''.join(page.get_text() for page in d)
need=['판단 유보','SYNTHETIC_REASON','SYNTHETIC_NEW_CHECKS','SYNTHETIC_REVISIT']
assert all(x in text for x in need)
assert 'PRIVATE_VALUE' not in text and 'PRIVATE_UNUSED' not in text
sizes=[s['size'] for page in d for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans'] if s['text'].strip()]
assert min(sizes)>=11.9
r={'status':'PASS','pages':len(d),'minimum_actual_font_pt':min(sizes),'guided_judgment_and_review_conditions_present':True,'raw_omitted_columns_absent':True}
(root/'workflow_evidence/GUIDED_PDF_PROOF.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
