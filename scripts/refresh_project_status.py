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
'validation_v04':'e-book/exports/v04/validation_v04.json',
'book_v05':'e-book/exports/v05/ebook_review_v05.pdf',
'validation_v05':'e-book/exports/v05/validation_v05.json',
'methodology_source':'e-book/planning/AUTHOR_METHOD_AND_VOICE.md',
'book_v06':'e-book/exports/v06/ebook_review_v06.pdf',
'validation_v06':'e-book/exports/v06/validation_v06.json'}
for key,path in required.items():assert (ROOT/path).is_file(),path
con=sqlite3.connect(f'file:{(ROOT/required["database_v03"]).as_posix()}?mode=ro',uri=True)
assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert not con.execute('PRAGMA foreign_key_check').fetchall()
plan_hash=hashlib.sha256((ROOT/required['plan_v03']).read_bytes()).hexdigest()
stored_plan_hash=json.loads(con.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0])
plan_exact_bytes=stored_plan_hash==plan_hash
plan_bytes=(ROOT/required['plan_v03']).read_bytes()
crlf_reconstruction_hash=hashlib.sha256(plan_bytes.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()
plan_line_ending_equivalent=crlf_reconstruction_hash==stored_plan_hash
assert plan_exact_bytes or plan_line_ending_equivalent,'Plan differs beyond the detected newline-only representation'
plan_identity={'exact_bytes_match':plan_exact_bytes,'checkout_sha256':plan_hash,'database_manifest_sha256':stored_plan_hash,'CRLF_reconstruction_sha256':crlf_reconstruction_hash,'newline_only_equivalence':plan_line_ending_equivalent,'original_files_modified':False,'note':'Fresh checkout has LF while DB manifest matches CRLF representation; exact frozen byte identity is NOT claimed. Original plan and DB preserved.'}
counts={name:con.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['customers','assignments','messages','events','contracts']}
arms=dict(con.execute('SELECT arm,COUNT(*) FROM assignments GROUP BY arm'))
con.close()
with pymupdf.open(ROOT/required['chapter_v03']) as d:chapter_pages=len(d)
with pymupdf.open(ROOT/required['book_v02']) as d:book_pages=len(d)
cards=json.loads((ROOT/required['cards_data']).read_text(encoding='utf-8'))
current_pages={}
for key in ['book_v04','workbook_v04','card_reference_v04','book_v05','book_v06']:
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
status={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'author':'허재혁','project':'A/B Test','repository':'https://github.com/jhheo51-arch/AB-Test','latest_data_version':'v0.3 preserved + separate v0.4 teaching scenarios','latest_complete_reader_bundle_version':'v0.4 author review, not final publication','counts_v03':counts,'arms_v03':arms,'chapter_v03_pages':chapter_pages,'reader_v02_pages':book_pages,'current_pdf_pages':current_pages,'six_worked_case_start_pages':case_pages,'diagnostic_cards':len(cards),'diagnostic_dimensions':len({c['dimension'] for c in cards}),'required_paths':required,'checks':['required files exist','v03 SQLite read-only integrity and foreign keys','frozen plan bytes match' if plan_exact_bytes else 'frozen plan byte mismatch: newline-only equivalence verified, original files not changed','actual PDF page counts','v04 six case bookmarks and required text','exact PDFs match renderer hashes'],'not_repeated':['statistical calculations/simulations in this inventory refresh; see actual analysis reports','human statistical/domain/editorial approval','market/rights/distribution checks'],'product_tool_status':'direction documents only, no implemented general analysis application','publication_status':'not ready for sale; author/content/domain/reader/rights review pending'}
v05=json.loads((ROOT/required['validation_v05']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v05']).read_bytes()).hexdigest()==v05['pdf_sha256']
with pymupdf.open(ROOT/required['book_v05']) as d:
    latest_text='\n'.join(p.get_text() for p in d)
    latest_cases={str(i):[t[2] for t in d.get_toc() if re.match(rf'^사례\s*{i}\s',t[1])] for i in range(1,7)}
    assert all(len(x)==1 for x in latest_cases.values())
    assert not any(x in latest_text for x in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
    for term in ['트리아타시스','Tri-Ataxis','Variable Control','Vector Segmentation','Value-Linked Decision']:assert term in latest_text,term
status.update({'latest_reading_edition':'v0.5 method-led main book, author review','main_book_path':required['book_v05'],'six_worked_case_start_pages':latest_cases,'previous_v04_case_pages':case_pages,'methodology_chapter_start_pages':v05['methodology_chapter_start_pages'],'middle_dot_counts':v05['middle_dot_counts'],'companion_scope':'v0.4 workbook/cards preserved, not re-edited in the v0.5 main-book revision'})
status['checks'].extend(['v05 exact PDF hash and six case bookmarks','v05 original method names and zero middle dots'])
v06=json.loads((ROOT/required['validation_v06']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v06']).read_bytes()).hexdigest()==v06['pdf_sha256']
with pymupdf.open(ROOT/required['book_v06']) as d:
    text06='\n'.join(p.get_text() for p in d)
    assert len(d)==v06['pdf_pages']
    assert not any(c in text06 for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
    for term in ['맥락항법','Overall Evaluation Criterion','키워드 찾아보기','Variable Control','Vector Segmentation','Value-Linked Decision']:assert term in text06,term
status.update({'latest_reading_edition':'v0.6 study-integrated main book, author review','main_book_path':required['book_v06'],'six_worked_case_start_pages':{k:[v] for k,v in v06['case_start_pages'].items()},'methodology_chapter_start_pages':v06['methodology_chapter_start_pages'],'glossary_entries':v06['glossary_entries'],'method_title_proposal':'맥락항법: 비교의 근거에서 실행의 결론까지','method_title_approval':'pending','companion_scope':'v0.4 workbook/cards preserved, not re-edited in v0.6'})
status['checks'].extend(['v06 exact PDF hash, 36 glossary targets and zero middle dots','v06 numeric text ledger reconciliation: 103 checks; no inference rerun'])
required.update({'book_v07':'e-book/exports/v07/ebook_review_v07.pdf','validation_v07':'e-book/exports/v07/validation_v07.json'})
v07=json.loads((ROOT/required['validation_v07']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v07']).read_bytes()).hexdigest()==v07['pdf_sha256']
with pymupdf.open(ROOT/required['book_v07']) as d:
    assert len(d)==v07['pdf_pages']
    assert '허재혁' in d.metadata['author']
current_pages['book_v07']=v07['pdf_pages']
status.update({'latest_reading_edition':'v0.7 expanded editorial review edition','main_book_path':required['book_v07'],'six_worked_case_start_pages':{k:[v] for k,v in v07['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v07['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v07['chapter_start_pages'],'same_A4_body_only_control_pages':v07['same_A4_body_only_control_pages'],'persona_review_status':'AI simulated review, not interviews or sales validation','source_characters':v07['source_characters'],'cover_approval':'A selected as recommendation; author approval pending'})
status['checks'].extend(['v07 PDF hash and actual12pt reading-body probe','v07 contents folios,36 glossary targets,103 numeric tokens and read-only chapter12 SQL'])
status['plan_identity']=plan_identity
required.update({'book_v08':'e-book/exports/v08/ebook_review_v08.pdf','validation_v08':'e-book/exports/v08/validation_v08.json','publication_brief':'e-book/planning/PUBLICATION_BRIEF.md','publication_checklist':'e-book/planning/PUBLICATION_CHECKLIST.md'})
v08=json.loads((ROOT/required['validation_v08']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v08']).read_bytes()).hexdigest()==v08['pdf_sha256']
with pymupdf.open(ROOT/required['book_v08']) as d:
    assert len(d)==v08['pdf_pages']
    text08='\n'.join(p.get_text() for p in d)
    assert text08.count('트리아타시스')==1 and text08.count('Tri-Ataxis')==1
    for term in ['맥락항법','Variable Control','Vector Segmentation','Value-Linked Decision']:assert term in text08,term
current_pages['book_v08']=v08['pdf_pages']
status.update({'latest_reading_edition':'v0.8 approved terminology and publication-boundary review edition','main_book_path':required['book_v08'],'six_worked_case_start_pages':{k:[v] for k,v in v08['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v08['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v08['chapter_start_pages'],'glossary_entries':v08['glossary_entries'],'same_A4_body_only_control_pages':v08['same_A4_body_only_control_pages'],'source_characters':v08['source_characters'],'method_title_proposal':'맥락항법','method_title_approval':'author approved proceeding with proposed naming structure; applied to v08','methodology_name':'맥락항법','procedure':'TRI-V','reader_test_status':'protocol and task preparation only; actual participants and learning outcomes not yet tested','field_validation_scope':'No superiority claim; full field proof is not a prerequisite for a scoped educational proposal','publication_gate_scope':'final title, cover, sales promise and publication approval remain pending'})
status['checks'].extend(['v08 exact PDF hash and approved terminology distribution','v08 original103 numeric tokens, read-only chapter12 SQL, printed folios and zero forbidden middle-dot characters'])
required.update({'claim_and_synthetic_audit':'e-book/review/publication/CLAIM_SCOPE_AND_SYNTHETIC_AUDIT.md','reader_protocol':'e-book/review/reader_test_v01/PROTOCOL.md','reader_preparation_validation':'e-book/review/reader_test_v01/PREPARATION_VALIDATION.json'})
prep=json.loads((ROOT/required['reader_preparation_validation']).read_text(encoding='utf-8'))
assert prep['assigned_reading_candidate']['sha256']==v08['pdf_sha256']
assert prep['observation_rows']==0
status.update({'reader_test_protocol':'prepared, recruitment and conditions require approval','reader_test_observation_rows':prep['observation_rows'],'reader_test_preparation_checks':'fixture counts, rates/effects, CI/p recalculated and matched to participant and facilitator files; not learning outcomes','reader_test_source_edition':'v0.7 development baseline, v0.8 assigned reading candidate with recorded exact PDF hash'})
required.update({'book_v09':'e-book/exports/v09/ebook_review_v09.pdf','validation_v09':'e-book/exports/v09/validation_v09.json','operations_validation_v09':'e-book/exports/v09/operations_validation_v09.json'})
v09=json.loads((ROOT/required['validation_v09']).read_text(encoding='utf-8'));ops=json.loads((ROOT/required['operations_validation_v09']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v09']).read_bytes()).hexdigest()==v09['pdf_sha256']
with pymupdf.open(ROOT/required['book_v09']) as d:
    assert len(d)==v09['pdf_pages']
    assert any(t[1]=='TRI-V 공통 운용 기준' and t[2]==ops['operating_contract_page'] for t in d.get_toc())
current_pages['book_v09']=v09['pdf_pages']
status.update({'latest_reading_edition':'v0.9 shared operating contract and decision-record review edition','main_book_path':required['book_v09'],'six_worked_case_start_pages':{k:[v] for k,v in v09['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v09['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v09['chapter_start_pages'],'glossary_entries':v09['glossary_entries'],'source_characters':v09['source_characters'],'same_A4_body_only_control_pages':v09['same_A4_body_only_control_pages'],'operating_contract_page':ops['operating_contract_page'],'method_title_approval':'Existing Korean naming applied in v08; final English spelling not yet selected','english_name_candidates':{'previous_proposal':'Contexvia','user_latest_literal':'contextvia','display_proposal':'Contextvia','approved':False},'three_operating_repairs':'integrated in the actual book, companion card and record; reader usability not yet tested','reader_test_source_edition':'Original preparation retains v08 PDF hash; v09 assignment requires a new explicit version decision before actual testing','reader_test_administration':'User will conduct the test; no independent recruitment or sharing authorized','later_publication_work':'not started anew; user reserved it until methodology/name resolution'})
status['checks'].extend(['v09 PDF exact hash and central operating-contract bookmark','v09 original103 numeric checks and read-only chapter12 SQL','v09 six case-to-record mappings, one-page operating card and three-page decision record; not a statistical classifier'])
required.update({'book_v10':'e-book/exports/v10/ebook_review_v10.pdf','validation_v10':'e-book/exports/v10/validation_v10.json','origin_scope_validation_v10':'e-book/exports/v10/origin_scope_validation_v10.json'})
v10=json.loads((ROOT/required['validation_v10']).read_text(encoding='utf-8'));origin10=json.loads((ROOT/required['origin_scope_validation_v10']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v10']).read_bytes()).hexdigest()==v10['pdf_sha256']
with pymupdf.open(ROOT/required['book_v10']) as d:assert len(d)==v10['pdf_pages']
current_pages['book_v10']=v10['pdf_pages']
status.update({'latest_reading_edition':'v0.10 illustrated introductory explanation and sourced method-scope review','main_book_path':required['book_v10'],'six_worked_case_start_pages':{k:[v] for k,v in v10['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v10['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v10['chapter_start_pages'],'glossary_entries':v10['glossary_entries'],'source_characters':v10['source_characters'],'same_A4_body_only_control_pages':v10['same_A4_body_only_control_pages'],'operating_contract_page':origin10['new_pdf_section_pages']['TRI-V 공통 운용 기준'],'new_explanation_pages':origin10['new_pdf_section_pages'],'methodology_name':'TRI-V','method_title_proposal':'TRI-V as the author-proposed method; another brand is optional','method_title_approval':'Clarified the method/operating-guide distinction in response to the author; no new Contextvia brand or final cover approval inferred','universal_applicability_claim':False,'historical_novelty_claim':False,'origin_scope':'Supplied draft already contains TRI-V; its first coinage is not established by the available excerpt','reader_test_source_edition':'Original preparation retains v08 PDF hash; exact v10 reading/task versions need fixation before actual testing'})
status['checks'].extend(['v10 exact PDF hash, illustrated explanation and origin/scope bookmarks','v10 existing103 numeric tokens and read-only chapter12 SQL; unchanged original data'])
required.update({'book_v11':'e-book/exports/v11/ebook_review_v11.pdf','validation_v11':'e-book/exports/v11/validation_v11.json','integration_v11':'e-book/exports/v11/integration_validation_v11.json','package_smoke_v11':'e-book/exports/v11/package_smoke_v11.json'})
v11=json.loads((ROOT/required['validation_v11']).read_text(encoding='utf-8'));integration11=json.loads((ROOT/required['integration_v11']).read_text(encoding='utf-8'));package11=json.loads((ROOT/required['package_smoke_v11']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v11']).read_bytes()).hexdigest()==v11['pdf_sha256']
with pymupdf.open(ROOT/required['book_v11']) as d:assert len(d)==v11['pdf_pages']
assert integration11['status']=='passed' and integration11['old_v10_pdf_unchanged']
assert package11['integrity']=='passed' and package11['extracted_book_and_minimum_record']=='passed'
assert hashlib.sha256((ROOT/'JH_CRM_ebook_reader_v11.zip').read_bytes()).hexdigest()==package11['sha256']
current_pages['book_v11']=v11['pdf_pages']
status.update({'latest_reading_edition':'v0.11 method refinement integrated into bounded editorial review','latest_complete_reader_bundle_version':'v0.11 portable reading bundle, not a full reproduction environment or approved publication','main_book_path':required['book_v11'],'six_worked_case_start_pages':{k:[v] for k,v in v11['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v11['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v11['chapter_start_pages'],'glossary_entries':v11['glossary_entries'],'source_characters':v11['source_characters'],'same_A4_body_only_control_pages':v11['same_A4_body_only_control_pages'],'operating_contract_page':integration11['chapter_pages']['operating_contract'],'new_explanation_pages':integration11['chapter_pages'],'minimum_record_fields':6,'minimum_record_pdf_pages':1,'minimum_record_path':'e-book/exports/v11/MINIMUM_RECORD.html','counterexample_cases':4,'editorial_gate':'PUB-02 started: first integration and bounded chapter9/10 prose edit technically verified; remaining editorial work and author expression approval pending','later_publication_work':'PUB-02 authorized and started after clarification; no independent human review or publication inferred','reader_test_source_edition':'Original preparation retains v08 PDF hash; v11 reading/tasks/rubric require explicit version fixation before actual testing','reader_bundle':package11,'companion_scope':'v11 six-field record included; v04 historical workbook/cards preserved rather than re-edited'})
status['checks'].extend(['v11 exact PDF hash,89 pages and original103 numeric checks plus read-only chapter12 SQL','v11 old v10 PDF and numeric ledgers preserved, original chapters5/6 and six cases unchanged','v11 four counterexamples reconciled and six-field one-page record exercised','v11 portable33-file ZIP hash, integrity and extracted browser check'])
required.update({'book_v12':'e-book/exports/v12/ebook_review_v12.pdf','validation_v12':'e-book/exports/v12/validation_v12.json','integration_v12':'e-book/exports/v12/integration_validation_v12.json','package_smoke_v12':'e-book/exports/v12/package_smoke_v12.json','human_review_request_v12':'e-book/review/statistical_v12/REVIEW_REQUEST.md'})
v12=json.loads((ROOT/required['validation_v12']).read_text(encoding='utf-8'));integration12=json.loads((ROOT/required['integration_v12']).read_text(encoding='utf-8'));package12=json.loads((ROOT/required['package_smoke_v12']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v12']).read_bytes()).hexdigest()==v12['pdf_sha256']
with pymupdf.open(ROOT/required['book_v12']) as d:assert len(d)==v12['pdf_pages']
assert integration12['status']=='passed' and integration12['old_v11_pdf_unchanged']
assert package12['integrity']=='passed' and package12['extracted_book_and_minimum_record']=='passed'
assert hashlib.sha256((ROOT/'JH_CRM_ebook_reader_v12.zip').read_bytes()).hexdigest()==package12['sha256']
current_pages['book_v12']=v12['pdf_pages']
status.update({'latest_reading_edition':'v0.12 bounded whole-book prose editing applied; author review','latest_complete_reader_bundle_version':'v0.12 portable reading bundle, not full reproduction or approved publication','main_book_path':required['book_v12'],'six_worked_case_start_pages':{k:[v] for k,v in v12['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v12['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v12['chapter_start_pages'],'glossary_entries':v12['glossary_entries'],'source_characters':v12['source_characters'],'same_A4_body_only_control_pages':v12['same_A4_body_only_control_pages'],'operating_contract_page':integration12['chapter_pages']['operating_contract'],'new_explanation_pages':integration12['chapter_pages'],'minimum_record_path':'e-book/exports/v12/MINIMUM_RECORD.html','reader_bundle':package12,'editorial_gate':'PUB-02:29 paragraphs edited across chapters1/5/6/12, prior chapter9/10 editing retained; technical checks passed, final author voice approval pending','human_statistical_review':'PUB-03 request,15-file inventory and empty findings form prepared; no reviewer selected or files shared','later_publication_work':'PUB-02 prose changes applied and PUB-03 preparation only; no human or publication approval inferred','reader_test_source_edition':'Original preparation retains v08 PDF hash; v12 reading/tasks/rubric require explicit version fixation before actual testing','companion_scope':'Same six-field one-page record reused byte-identically from v11; historical workbook/cards preserved','AI_semantic_review':'29 edits reviewed; two weakened protection/safety statements restored by integrator, final phrases asserted in PDF; not human review'})
status['checks'].extend(['v12 ordered numerical tokens, English term sets, tables and code preserved in edited chapters','v12 unedited chapters, six original cases and canonical operating contract unchanged','v12 original103 numeric checks, read-only chapter12 SQL and final PDF protective phrases','v12 package exact hash and extracted browser check; human review remains pending'])
required.update({'book_v13':'e-book/exports/v13/ebook_review_v13.pdf','validation_v13':'e-book/exports/v13/validation_v13.json','integration_v13':'e-book/exports/v13/integration_validation_v13.json','package_smoke_v13':'e-book/exports/v13/package_smoke_v13.json','correction_regression_v13':'e-book/analysis/corrections_v13/REGRESSION_CHECK.json','corrected_database_v13':'e-book/virtual-data/v13/data/jh_motors_v13.sqlite','corrected_analysis_v13':'e-book/virtual-data/v13/analysis_report_v13.json','derived_manifest_v13':'e-book/virtual-data/v13/DERIVED_MANIFEST.json'})
v13=json.loads((ROOT/required['validation_v13']).read_text(encoding='utf-8'));integration13=json.loads((ROOT/required['integration_v13']).read_text(encoding='utf-8'));package13=json.loads((ROOT/required['package_smoke_v13']).read_text(encoding='utf-8'));regression13=json.loads((ROOT/required['correction_regression_v13']).read_text(encoding='utf-8'));derived13=json.loads((ROOT/required['derived_manifest_v13']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v13']).read_bytes()).hexdigest()==v13['pdf_sha256']
with pymupdf.open(ROOT/required['book_v13']) as d:assert len(d)==v13['pdf_pages']
assert integration13['status']=='passed' and integration13['source_v12_preserved']
assert regression13['checks_failed']==0
assert package13['integrity']=='passed' and package13['extracted_book_and_minimum_record']=='passed'
assert hashlib.sha256((ROOT/'JH_CRM_ebook_reader_v13.zip').read_bytes()).hexdigest()==package13['sha256']
assert hashlib.sha256((ROOT/required['corrected_database_v13']).read_bytes()).hexdigest()==derived13['derived_database_sha256']
with sqlite3.connect(f'file:{(ROOT/required["corrected_database_v13"]).as_posix()}?mode=ro',uri=True) as con13:
    assert con13.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not con13.execute('PRAGMA foreign_key_check').fetchall()
current_pages['book_v13']=v13['pdf_pages']
status.update({'latest_reading_edition':'v0.13 statistical findings corrected and reflected in the complete book; author review','latest_complete_reader_bundle_version':'v0.13 portable corrected reading bundle; not full reproduction or approved publication','latest_data_version':'v0.3 original preserved, v0.13 derived copy with corrected outcomes view, separate v0.4 teaching scenarios preserved','main_book_path':required['book_v13'],'six_worked_case_start_pages':{k:[v] for k,v in v13['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v13['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v13['chapter_start_pages'],'source_characters':v13['source_characters'],'operating_contract_page':integration13['chapter_pages']['operating_contract'],'new_explanation_pages':integration13['chapter_pages'],'minimum_record_path':'e-book/exports/v13/MINIMUM_RECORD.html','reader_bundle':package13,'statistical_corrections_v13':{'regression_passed':regression13['checks_passed'],'regression_failed':regression13['checks_failed'],'integration_checks':integration13['checks_passed'],'source_v12_preserved':integration13['source_v12_preserved'],'original_analysis_scripts_preserved':True,'historical_plan_exact_byte_issue':'retained; actual input hashes recorded separately from historical newline representation'},'editorial_gate':'PUB-02 applied statistical corrections, bounded prose and reproducibility-path changes; final author expression approval pending','human_statistical_review':'Not performed. AI/separate-code audit and correction are not PUB-03 human approval; old human request retained as history','later_publication_work':'Stop after delivery of this correction; no new external review, reader recruitment or publication stage','reader_test_source_edition':'Original preparation retains v08 PDF hash; v13 is not automatically assigned to a test','companion_scope':'Same six-field one-page record preserved; counterexample score results and power ledger corrected; old workbook/cards unchanged'})
status['checks'].extend(['v13 exact PDF and archive hashes, corrected database read-only integrity and foreign keys','v13 separate correction regression and independent-audit reconciliation recorded; inventory refresh does not rerun statistics','v13 registered manuscript corrections only, old input hashes preserved and actual12pt reading probe'])
required.update({'book_v14':'e-book/exports/v14/ebook_review_v14.pdf','validation_v14':'e-book/exports/v14/validation_v14.json','integration_v14':'e-book/exports/v14/integration_validation_v14.json','package_smoke_v14':'e-book/exports/v14/package_smoke_v14.json','study_comparison_v14':'e-book/exports/v14/COMPARISON.md','study_coverage_v14':'e-book/exports/v14/COVERAGE_AFTER.json'})
v14=json.loads((ROOT/required['validation_v14']).read_text(encoding='utf-8'));integration14=json.loads((ROOT/required['integration_v14']).read_text(encoding='utf-8'));package14=json.loads((ROOT/required['package_smoke_v14']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v14']).read_bytes()).hexdigest()==v14['pdf_sha256']
with pymupdf.open(ROOT/required['book_v14']) as d:assert len(d)==v14['pdf_pages']
assert integration14['status']=='passed' and integration14['source_v13_preserved']
assert package14['integrity']=='passed' and package14['extracted_book_and_minimum_record']=='passed'
assert hashlib.sha256((ROOT/'JH_CRM_ebook_reader_v14.zip').read_bytes()).hexdigest()==package14['sha256']
current_pages['book_v14']=v14['pdf_pages']
status.update({'latest_reading_edition':'v0.14 supplied study-note gaps integrated into complete book; author review','latest_complete_reader_bundle_version':'v0.14 scoped study integration reader; not full reproduction or approved publication','main_book_path':required['book_v14'],'six_worked_case_start_pages':{k:[v] for k,v in v14['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v14['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v14['chapter_start_pages'],'source_characters':v14['source_characters'],'operating_contract_page':integration14['chapter_pages']['operating_contract'],'new_explanation_pages':integration14['chapter_pages'],'minimum_record_path':'e-book/exports/v14/MINIMUM_RECORD.html','reader_bundle':package14,'study_integration_v14':{'concepts_compared':integration14['concept_count'],'before_status_counts':integration14['coverage_counts_before'],'paragraphs_added':integration14['paragraphs_added'],'integration_checks_passed':integration14['checks_passed'],'direct_Notion_body_read':False,'scope':'Full supplied pasted passage only; linked Notion body login blocked; Georgiev original chapter numbers not verified','new_sequential_engine_implemented':False,'original_statistics_unchanged':True},'editorial_gate':'Bounded study-note integration applied to chapters2/6/9, original method axes and six fields preserved; final author and human technical review pending','reader_test_source_edition':'Original preparation retains v08 PDF hash; v14 not automatically assigned to any actual reader test','later_publication_work':'Only supplied-note integration authorized; no new human review, external sharing or publication release','companion_scope':'Original v13 corrected numerical ledgers and six-field record retained byte-identically; comparison and read-scope records included'})
status['checks'].extend(['v14 exact90-page PDF and41-file reading bundle hashes, source v13 preserved','v14 sixteen concepts compared; eleven existing explanations retained and five linked explanations added','v14 original103 numeric checks, read-only SQL and disclosed analytic teaching examples; no new field experiment'])
required.update({'book_v15':'e-book/exports/v15/ebook_review_v15.pdf','validation_v15':'e-book/exports/v15/validation_v15.json','integration_v15':'e-book/exports/v15/integration_validation_v15.json','package_smoke_v15':'e-book/exports/v15/package_smoke_v15.json','development_v15':'e-book/exports/v15/DEVELOPMENT.md','planning_example_v15':'e-book/analysis/development_v15/PLANNING_EXAMPLE.json'})
v15=json.loads((ROOT/required['validation_v15']).read_text(encoding='utf-8'));integration15=json.loads((ROOT/required['integration_v15']).read_text(encoding='utf-8'));package15=json.loads((ROOT/required['package_smoke_v15']).read_text(encoding='utf-8'));plan15=json.loads((ROOT/required['planning_example_v15']).read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/required['book_v15']).read_bytes()).hexdigest()==v15['pdf_sha256']
with pymupdf.open(ROOT/required['book_v15']) as d:assert len(d)==v15['pdf_pages']
assert integration15['status']=='passed' and integration15['source_v14_preserved']
assert package15['integrity']=='passed' and package15['extracted_book_and_minimum_record']=='passed'
assert hashlib.sha256((ROOT/'JH_CRM_ebook_reader_v15.zip').read_bytes()).hexdigest()==package15['sha256']
current_pages['book_v15']=v15['pdf_pages']
status.update({'latest_reading_edition':'v0.15 principles developed into design choices and decision records; author review','latest_complete_reader_bundle_version':'v0.15 portable developed reader, not full reproduction or approved publication','main_book_path':required['book_v15'],'six_worked_case_start_pages':{k:[v] for k,v in v15['case_start_pages'].items()},'methodology_chapter_start_pages':{k:v15['chapter_start_pages'][k] for k in ['1','2','3','4']},'all_chapter_start_pages':v15['chapter_start_pages'],'source_characters':v15['source_characters'],'operating_contract_page':integration15['chapter_pages']['operating_contract'],'new_explanation_pages':integration15['chapter_pages'],'minimum_record_path':'e-book/exports/v15/MINIMUM_RECORD.html','reader_bundle':package15,'development_v15':{'groups':len(integration15['developments']),'integration_checks_passed':integration15['checks_passed'],'planning_example':plan15['available_plan'],'historical_statistics_unchanged':True,'new_experiment_conducted':False,'sequential_engine_implemented':False,'self_check_questions':3,'self_check_is_real_reader_test':False},'editorial_gate':'Developed chapters2/6/9 design choices and decision writing; human technical and author review pending','reader_test_source_edition':'Original preparation retains v08 PDF hash; v15 self-check is not administration of the formal reader test','later_publication_work':'Bounded development only; no actual customer recruitment, send, external review or publication release','companion_scope':'Original six-field record and corrected statistics retained byte-identically; development note, planning illustration and three self-check questions included'})
status['checks'].extend(['v15 exact PDF and reading archive hashes, original v14 and numeric inputs preserved','v15 existing103 numeric checks plus new planning power and MDE calculation comparisons','v15 design tables and complete developed paragraphs located in final PDF; not evidence of learning effectiveness'])
(ROOT/'PROJECT_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(status,ensure_ascii=False,indent=2))
