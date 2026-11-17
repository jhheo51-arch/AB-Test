"""Read current artifacts and generate an inventory, without regenerating data."""
import hashlib
import json
import sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path

import pymupdf
ROOT=Path(__file__).resolve().parents[1]
required={
'summary':'PROJECT_SUMMARY.md',
'company_v03':'e-book/virtual-company/JH_Motors_v03.md',
'database_v03':'e-book/virtual-data/v03/data/jh_motors_v03.sqlite',
'plan_v03':'e-book/virtual-data/v03/experiment_plan.json',
'analysis_v03':'e-book/virtual-data/v03/analysis_report.json',
'chapter_v03':'e-book/exports/v03/sample_and_data_chapter_v03.pdf',
'book_v02':'e-book/exports/v02/ebook_review_v02.pdf',
'visual_cards':'e-book/exports/v02/diagnostic_atlas_v02.html',
'cards_data':'e-book/workflow/diagnostic_cards_v02.json',
'market_review':'e-book/planning/MARKET_COMPARISON_AND_REDESIGN_REVIEW.md',
'workbook':'e-book/workbook/workbook_v02.md',
'product_direction':'tool/DIRECTION.md',
'book_v04':'e-book/exports/v04/ebook_review_v04.pdf',
'workbook_v04':'e-book/exports/v04/workbook_v04.pdf',
'card_reference_v04':'e-book/exports/v04/diagnostic_cards_reference_v04.pdf',
'winner_core':'e-book/analysis/winner_v04/core_results.json',
'winner_scenarios':'e-book/analysis/winner_v04/scenario_results.json',
'validation_v04':'e-book/exports/v04/validation_v04.json'}
for key,path in required.items():assert (ROOT/path).is_file(),path
con=sqlite3.connect(f'file:{(ROOT/required["database_v03"]).as_posix()}?mode=ro',uri=True)
assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert not con.execute('PRAGMA foreign_key_check').fetchall()
plan_hash=hashlib.sha256((ROOT/required['plan_v03']).read_bytes()).hexdigest()
assert json.loads(con.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])==plan_hash
counts={name:con.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['customers','assignments','messages','events','contracts']}
arms=dict(con.execute('SELECT arm,COUNT(*) FROM assignments GROUP BY arm'))
con.close()
with pymupdf.open(ROOT/required['chapter_v03']) as d:chapter_pages=len(d)
with pymupdf.open(ROOT/required['book_v02']) as d:book_pages=len(d)
cards=json.loads((ROOT/required['cards_data']).read_text(encoding='utf-8'))
current_pages={}
for key in ['book_v04','workbook_v04','card_reference_v04']:
    with pymupdf.open(ROOT/required[key]) as d:current_pages[key]=len(d)
with pymupdf.open(ROOT/required['book_v04']) as d:
    import re
    text='\n'.join(p.get_text() for p in d)
    case_pages={str(i):[entry[2] for entry in d.get_toc() if re.match(rf'^사례\s*{i}\s*[·.]',entry[1])] for i in range(1,7)}
    assert all(len(x)==1 for x in case_pages.values())
    for term in ['최소 사업 효과','가드레일','0.00274','Welch','상호작용','용량']:assert term in text,term
validation=json.loads((ROOT/required['validation_v04']).read_text(encoding='utf-8'))
for key,name in [('ebook_review_v04','book_v04'),('workbook_v04','workbook_v04'),('diagnostic_cards_reference_v04','card_reference_v04')]:
    assert hashlib.sha256((ROOT/required[name]).read_bytes()).hexdigest()==validation['outputs'][key]['sha256']
status={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'author':'허재혁','project':'A/B Test','repository':'https://github.com/jhheo51-arch/AB-Test','latest_data_version':'v0.3 preserved + separate v0.4 teaching scenarios','latest_complete_reader_bundle_version':'v0.4 author review, not final publication','counts_v03':counts,'arms_v03':arms,'chapter_v03_pages':chapter_pages,'reader_v02_pages':book_pages,'current_pdf_pages':current_pages,'six_worked_case_start_pages':case_pages,'diagnostic_cards':len(cards),'diagnostic_dimensions':len({c['dimension'] for c in cards}),'required_paths':required,'checks':['required files exist','v03 SQLite read-only integrity and foreign keys','frozen plan hash matches database','actual PDF page counts','v04 six case bookmarks and required text','exact PDFs match renderer hashes'],'not_repeated':['statistical calculations/simulations in this inventory refresh; see actual analysis reports','human statistical/domain/editorial approval','market/rights/distribution checks'],'product_tool_status':'direction documents only, no implemented general analysis application','publication_status':'not ready for sale; author/content/domain/reader/rights review pending'}
(ROOT/'PROJECT_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(status,ensure_ascii=False,indent=2))
