"""Read current artifacts and generate an inventory, without regenerating data."""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
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
'product_direction':'tool/DIRECTION.md'}
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
status={'checked_at_seoul':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),'author':'허재혁','project':'A/B Test','repository':'https://github.com/jhheo51-arch/AB-Test','latest_data_version':'v0.3','latest_complete_reader_bundle_version':'v0.2 author review, not final publication','counts_v03':counts,'arms_v03':arms,'chapter_v03_pages':chapter_pages,'reader_v02_pages':book_pages,'diagnostic_cards':len(cards),'diagnostic_dimensions':len({c['dimension'] for c in cards}),'required_paths':required,'checks':['required files exist','v03 SQLite integrity and foreign keys','frozen plan hash matches database','actual PDF page counts'],'not_repeated':['statistical calculations and simulations; existing reports retained','human statistical/domain/editorial approval','market/rights/distribution checks'],'product_tool_status':'direction documents only, no implemented general analysis application','publication_status':'not ready for sale; author/content/domain/reader/rights review pending'}
(ROOT/'PROJECT_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(status,ensure_ascii=False,indent=2))
