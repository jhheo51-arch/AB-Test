"""Verify new v13 results against independent audit and frozen sources."""
from pathlib import Path
import re,json,hashlib,sqlite3,math
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v13';REVIEW=ROOT/'e-book/design/v13/review';REVIEW.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
checks=[]
def check(name,condition):checks.append({'check':name,'status':'passed' if condition else 'failed'});assert condition,name
old=(ROOT/'e-book/exports/v12/ebook_review_v12.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v13.md').read_text(encoding='utf-8');replay=old
for change in load('e-book/exports/v13/MANUSCRIPT_CHANGES.json')['changes']:
 check('registered replacement '+change['before'][:55],replay.count(change['before'])==change['occurrences']);replay=replay.replace(change['before'],change['after'])
check('Only registered manuscript corrections',replay==new)
check('Old v12 PDF unchanged',sha('e-book/exports/v12/ebook_review_v12.pdf')==load('e-book/exports/v12/validation_v12.json')['pdf_sha256'])
for name,h in load('e-book/review/ai_statistical_v12/BASELINE.json')['source_hashes'].items():check('frozen '+name,sha(name)==h)
analysis=load('e-book/virtual-data/v13/analysis_report_v13.json');actual={r['scenario']:r for r in analysis['metric_readiness']}
for row in load('e-book/review/ai_statistical_v12/interpretation/RESULTS.json')['current_AB_planned_effect_power']:
 check('corrected power vs independent audit '+row['scenario'],abs(actual[row['scenario']]['planning_power_under_stated_effect']-row['power_direct'])<1e-12)
check('Correct contract and withdrawal displays','51.7%' in new and '59.9%' in new and '51.8%' not in new and '60.0%' not in new)
correct=load('e-book/exports/v13/COUNTEREXAMPLE_RESULTS.json');prior=load('e-book/exports/v12/COUNTEREXAMPLE_RESULTS.json');independent=load('e-book/review/ai_statistical_v12/counterexamples/RESULTS.json')
def compare_score(r,a,old):
 for key in ['guard_NI_p','guard_one_sided_upper_pp']:check(r['id']+' corrected '+key,abs(r[key]-a[key])<1e-8)
 for key in ['difference_pp','performance_interval_pp','state','guard_pass','actual_approval']:check(r['id']+' unchanged '+key,r[key]==old[key])
 if 'other_group' in r:compare_score(r['other_group'],a['other_group'],old['other_group'])
for r,a,p in zip(correct['cases'],independent['cases'],prior['cases']):compare_score(r,a,p)
check('Corrected counterexample fixture unchanged',sha('e-book/exports/v13/counterexample_fixture.json')==sha('e-book/exports/v12/counterexample_fixture.json'))
for n in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md']:check('six field tool unchanged '+n,sha('e-book/exports/v13/'+n)==sha('e-book/exports/v12/'+n))
# Query the actual corrected database read-only, not a stored JSON substitute.
p=ROOT/'e-book/virtual-data/v13/data/jh_motors_v13.sqlite';con=sqlite3.connect(f'file:{p.as_posix()}?mode=ro',uri=True);con.execute('PRAGMA query_only=ON')
source=ROOT/'e-book/virtual-data/v03/data/jh_motors_v03.sqlite';con.execute('ATTACH DATABASE ? AS original',(f'file:{source.as_posix()}?mode=ro',))
tables=[r[0] for r in con.execute("SELECT name FROM original.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
for table in tables:
 assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',table)
 count0=con.execute(f'SELECT COUNT(*) FROM original.{table}').fetchone()[0];count1=con.execute(f'SELECT COUNT(*) FROM main.{table}').fetchone()[0]
 diff=con.execute(f'SELECT COUNT(*) FROM (SELECT * FROM main.{table} EXCEPT SELECT * FROM original.{table})').fetchone()[0]
 back=con.execute(f'SELECT COUNT(*) FROM (SELECT * FROM original.{table} EXCEPT SELECT * FROM main.{table})').fetchone()[0]
 check('derived source table unchanged '+table,count0==count1 and diff==0 and back==0)
rows=con.execute('SELECT arm,COUNT(*),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm').fetchall();ref=[(r['arm'],r['n'],r['completed'],r['withdrawn'],r['contracted']) for r in load('e-book/analysis/winner_v04/core_results.json')['groups']]
check('corrected database outcome counts unchanged',rows==ref);check('corrected database integrity',con.execute('PRAGMA integrity_check').fetchone()[0]=='ok');con.close()
forbid='\u00b7\u2022\u2027\u318d\u22c5\u30fb';check('no forbidden separators',not any(x in new for x in forbid));check('no new microheadings',not re.search(r'^### ',new,re.M))
with pymupdf.open(OUT/'ebook_review_v13.pdf') as pdf:
 toc=pdf.get_toc();pages={}
 for key,title in {'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','scope':'11장 TRI-V의 기여와 적용 범위','chapter6':'6장 고객 수보다 필요한 정보량부터','chapter12':'12장 한 건의 캠페인을 설계에서 결정까지'}.items():
  hits=[n for _,name,n in toc if name==title];check('PDF destination '+key,len(hits)==1);pages[key]=hits[0]
  if key in ['chapter6','chapter12','positive_cases']:pdf[hits[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/(key+'.png'))
 flat='\n'.join(p.get_text() for p in pdf);compact=re.sub(r'\s+','',flat)
 for phrase in ['51.7%','59.9%','MN 유한표본 보정','하한과 상한을 모두 넣었다','PROVENANCE.json','관계 안전은 통과했다고 말할 수 없다','운영 중단 사유로 두며']:check('Final PDF corrected phrase '+phrase,re.sub(r'\s+','',phrase) in compact)
 check('Final PDF no obsolete planning values','51.8%' not in compact and '60.0%' not in compact)
 check('Final PDF forbidden separators absent',not any(x in flat for x in forbid))
 check('No stranded single glossary entry',len([name for level,name,p in toc if level==2 and p==len(pdf)])>=2)
 report={'status':'passed','edition':'v0.13 statistical correction','full_book_pages':len(pdf),'chapter_pages':pages,'checks':checks,'checks_passed':len(checks),'raw_table_equality_count':len(tables),'counterexamples_reconciled':4,'method_axes':3,'minimum_record_fields':6,'minimum_record_pdf_pages':1,'source_v12_preserved':True,'original_plan_exact_byte_issue':'Historical mismatch retained; v13 records the actual source hashes separately','human_review_approved':False,'new_publication_stage_started':False,'original_outcomes_rows':rows}
(OUT/'integration_validation_v13.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
