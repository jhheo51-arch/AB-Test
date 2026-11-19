"""Verify edited case numbers against unchanged numeric result ledgers."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'e-book/exports/v05/ebook_review_v05.md').read_text(encoding='utf-8')
case_source=(ROOT/'e-book/manuscript/winner_cases_456_v05.md').read_text(encoding='utf-8')
r=json.loads((ROOT/'e-book/analysis/winner_v04/core_results.json').read_text(encoding='utf-8'))
s=json.loads((ROOT/'e-book/analysis/winner_v04/scenario_results.json').read_text(encoding='utf-8'))
checks=[]
def check(token,where,reason):
    assert token in where,(reason,token)
    checks.append({'token':token,'reason':reason})
# Tables in the main manuscript are populated directly from these exact ledgers.
for row in r['primary_family']:
    check(f"{row['diff_pp']:+.2f}",text,'primary effect')
    check(f"{row['ci_low_pp']:+.2f}",text,'primary interval lower')
    check(f"{row['ci_high_pp']:+.2f}",text,'primary interval upper')
for row in r['financial_exploratory']:
    for key in ['diff_krw','ci95_low_krw','ci95_high_krw']:check(f'{row[key]:+,.0f}',text,'exploratory financial '+key)
for key in ['truth','log']:
    row=s['case4'][key]
    for group in row['groups'].values():check(f"{group['success']:,}/{group['n']:,}",case_source,'case4 raw count')
    check(f"{100*row['difference_B_minus_A']:+.2f}pp",case_source,'case4 effect')
    for value in row['newcombe_ci']:check(f'{100*value:+.2f}pp',case_source,'case4 interval')
    check(f"{row['p_two_sided']:.4g}",case_source,'case4 p')
check(str(s['case4']['injected_missing']),case_source,'case4 omitted events')
for key in ['new','existing']:
    row=s['case5']['segments'][key]
    for group in row['groups'].values():check(f"{group['success']:,}/{group['n']:,}",case_source,'case5 raw count')
    check(f"{100*row['difference_B_minus_A']:+.2f}pp",case_source,'case5 effect')
    for value in row['newcombe_ci']:check(f'{100*value:+.2f}pp',case_source,'case5 interval')
for row,field in [(s['case5']['overall']['stratified_primary'],'wald_ci'),(s['case5']['interaction'],'wald_ci')]:
    check(f"{100*row['estimate']:+.2f}pp",case_source,'stratified/interaction estimate')
    for value in row[field]:check(f'{100*value:+.2f}pp',case_source,'stratified/interaction interval')
    check(f"{row['p_two_sided']:.4g}",case_source,'stratified/interaction p')
for row in s['case6']['summaries']:
    for key in ['requested','completed','waiting_end_window','net_value_krw','accepted','total_cost_krw']:check(f'{row[key]:,}',case_source,'case6 '+key)
# Exact ledgers must be unchanged since the earlier book's verified build.
manifest=json.loads((ROOT/'e-book/build-inputs/v05-numeric-manifest.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/'e-book/analysis/winner_v04/core_results.json').read_bytes()).hexdigest()==manifest['source_analysis_sha256']
assert not re.search(r'^### ',text,re.M)
assert not any(c in text for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
report={'status':'passed','numeric_text_checks':len(checks),'checks':checks,'scope':'Edited prose/table token reconciliation with existing result ledgers, not rerunning statistical inference or human expert review'}
(ROOT/'e-book/exports/v05/numeric_text_validation_v05.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'passed','numeric_text_checks':len(checks)},ensure_ascii=False))
