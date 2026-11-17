"""Reconcile final prose against the frozen ledger, then execute the book SQL read-only."""
from pathlib import Path
import json,sqlite3,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_ebook_v05_numbers.py').read_text(encoding='utf-8')
s=s.replace('e-book/exports/v05/ebook_review_v05.md','e-book/exports/v07/ebook_review_v07.md').replace("case_source=(ROOT/'e-book/manuscript/winner_cases_456_v05.md').read_text(encoding='utf-8')",'case_source=text').replace('e-book/exports/v05/numeric_text_validation_v05.json','e-book/exports/v07/numeric_text_validation_v07.json')
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
text=(ROOT/'e-book/exports/v07/ebook_review_v07.md').read_text(encoding='utf-8');r=json.loads((ROOT/'e-book/analysis/winner_v04/core_results.json').read_text(encoding='utf-8'))
p=ROOT/'e-book/virtual-data/v03/data/jh_motors_v03.sqlite';con=sqlite3.connect(f'file:{p.as_posix()}?mode=ro',uri=True)
q='SELECT arm,COUNT(*) AS assigned,SUM(completed_28) AS completed,SUM(withdrawn_28) AS withdrawn,SUM(contracted_180) AS contracted FROM outcomes GROUP BY arm ORDER BY arm'
rows=con.execute(q).fetchall();expected=[(x['arm'],x['n'],x['completed'],x['withdrawn'],x['contracted']) for x in r['groups']];assert rows==expected,(rows,expected)
for row in rows:
 for value in row[1:]:assert f'{value:,}' in text,value
for arm,value in r['financial_means'].items():assert f'{value:,.0f}원' in text
assert f"{100*r['primary_family'][0]['relative_lift']:+.2f}%" in text
assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';con.close()
report={'status':'passed','scope':'Final manuscript existing103 token checks plus read-only execution of chapter12 aggregate SQL; not a new full statistical or field validation','chapter12_sql':q,'actual_rows':rows,'ledger_match':True,'numeric_sources_unchanged':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']}}
(ROOT/'e-book/exports/v07/chapter12_sql_validation_v07.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
