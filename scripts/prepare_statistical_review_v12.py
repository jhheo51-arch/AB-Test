"""Prepare a versioned inventory for human statistical review, without sharing files."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,csv
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/review/statistical_v12';OUT.mkdir(parents=True,exist_ok=True)
paths=['e-book/exports/v12/ebook_review_v12.pdf','e-book/exports/v12/ebook_review_v12.md','e-book/exports/v12/validation_v12.json','e-book/exports/v12/integration_validation_v12.json','e-book/exports/v12/numeric_text_validation_v12.json','e-book/exports/v12/chapter12_sql_validation_v12.json','e-book/exports/v12/counterexample_fixture.json','e-book/exports/v12/COUNTEREXAMPLE_RESULTS.json','e-book/analysis/v02/verified_analysis.json','e-book/virtual-data/v03/experiment_plan.json','e-book/virtual-data/v03/data/jh_motors_v03.sqlite','e-book/virtual-data/v03/analysis_report.json','e-book/virtual-data/v03/repeated_sampling_check.json','e-book/analysis/winner_v04/core_results.json','e-book/analysis/winner_v04/scenario_results.json']
files=[]
for name in paths:
 p=ROOT/name;assert p.is_file(),name;files.append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
findings=OUT/'FINDINGS_TEMPLATE.csv';fields=['finding_id','reviewer','source_path','location','claim','severity','evidence','proposed_fix','disposition','recheck_status']
if not findings.exists():
 with findings.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerow(fields)
with findings.open(encoding='utf-8-sig',newline='') as f:
 reader=csv.DictReader(f);assert reader.fieldnames==fields;rows=list(reader)
manifest={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'reading_edition':'v0.12 author review','purpose':'Prepared human review request; not performed review or permission to share','files':files,'findings_rows':len(rows),'human_reviewer_selected':False,'human_review_completed':False,'external_sharing_authorized':False,'original_data_modified':False,'exact_plan_byte_identity_issue':'Open: LF checkout versus CRLF database manifest; newline-only equivalence does not establish exact original bytes'}
(OUT/'INPUT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'inventory_files':len(files),'findings_rows':len(rows),'external_files_shared':False,'human_review_completed':False},ensure_ascii=False))
