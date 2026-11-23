"""Validate source evidence for a bounded AI CRM-role review."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import hashlib,json,sys
A=Path(__file__).resolve().parent;R=A.parents[2];source=R/'e-book/exports/v22/ebook_review_v22.md';lines=source.read_text(encoding='utf-8').splitlines();read=lambda p:json.loads(p.read_text(encoding='utf-8'));save=lambda p,j:p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
baseline=read(R/'e-book/review/publication_v22/TECHNICAL_RIGHTS_CHECK.json')['baseline_hashes'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in baseline.items())
anchors=[('comparison',889,'B-A는 안내를 바꿀 이유를 묻고'),('eligible_population',895,'SMS 연락에 동의했고 기존 시승 완료가 없는 고객이다.'),('contact_rights',891,'발송 직전 권한과 철회 반영을 다시 확인해야 하며'),('mandatory_notices',820,'필수 안전 서비스를 보류할 허가가 아니다.'),('minimal_personal_data',822,'개인 식별 정보에 대한 접근과 보존은 최소화한다.'),('capacity',960,'하루 등록 상한 2,000명을 시승 수용 용량이라고 착각해서도 안 된다.'),('role_responsibility',962,'임의의 값으로 빈칸을 채우지 않는다.'),('current_action',988,'현재 허용하는 행동은 후속 설계 준비이며 신규 전면 확대는 승인하지 않는다.')]
for topic,line,quote in anchors:assert quote in lines[line-1],(topic,line)
parent={'review_type':'AI source-to-decision trace, not a real campaign approval','source':'e-book/exports/v22/ebook_review_v22.md','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'read_ranges':[{'start':875,'end':909},{'start':956,'end':988},{'start':820,'end':834}],'source_anchors':[{'topic':topic,'line':line,'quote':quote} for topic,line,quote in anchors],'existing_form':'e-book/exports/v22/MINIMUM_RECORD.md','current_decision':{'allowed_now':'후속 설계 준비와 역할별 근거 확인 요청','not_authorized':'신규 전면 확대와 미승인 제한 발송','planning_request':'실제 도입 기준과 변경 비용, 적격 고객 구성 및 후속 설계의 근거 확인. 승인자와 기한의 미정 값은 확정할 역할로 남김.','protection_request':'발송 직전 동의와 철회 반영, 허용 위험과 보호 평가 및 중대한 피해 대응의 실제 운영 근거 확인.','operations_request':'지점과 날짜별 시승차와 인력, 요청과 취소 및 미수용, 제한 범위와 복구 경로의 실제 근거 확인.','missing_answers_not_fabricated':True,'role_reply_is_not_execution_approval':True},'book_edit':False,'human_review':False}
if '--prepare' in sys.argv:
 save(A/'PARENT_TRACE.json',parent);print(json.dumps({'source_trace':'passed','source_anchors':len(anchors),'protected_files':len(baseline),'reviewer_results_not_read':True},ensure_ascii=False,indent=2));raise SystemExit
assert read(A/'PARENT_TRACE.json')==parent
roles={};ids=set();evidence_count=0;all_items=[];allowed={'covered','confirmed_omission','needs_field_data'}
for folder in ['planning','protection','operations']:
 report=read(A/folder/'FINDINGS.json');assert (A/folder/'REVIEW.md').is_file();assert report['review_type']=='AI role review; not field validation';assert report['read_ranges'] and report['items']
 for span in report['read_ranges']:assert 1<=span['start']<=span['end']<=len(lines)
 for item in report['items']:
  assert item['id'] not in ids;ids.add(item['id']);assert item['classification'] in allowed;assert item['reason'] and item['topic'] and item['evidence'];assert isinstance(item['field_data_needed'],list)
  if item['classification']=='needs_field_data':assert item['field_data_needed']
  for evidence in item['evidence']:
   line=evidence['line'];quote=evidence['quote'];assert isinstance(line,int) and 1<=line<=len(lines) and quote and quote in lines[line-1],(item['id'],line,quote);evidence_count+=1
  all_items.append({'role':folder,**item})
 declared={x if isinstance(x,str) else x['id'] for x in report['confirmed_omissions']};assert declared=={x['id'] for x in report['items'] if x['classification']=='confirmed_omission'}
 assert report['example_decision'];roles[folder]={'items':len(report['items']),'classifications':dict(Counter(x['classification'] for x in report['items']))}
counts=dict(Counter(x['classification'] for x in all_items));findings=[x['id'] for x in all_items if x['classification']=='confirmed_omission'];decision=read(A/'ADJUDICATION.json');assert set(decision['reviewed_item_ids'])==ids and decision['role_reports_read'] is True
assert decision['overrides']==[] and decision['confirmed_manuscript_omissions']==findings
report={'status':'evidence_integrity_verified','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'review_mode':'AI role perspectives, not actual practitioner or field validation','roles':roles,'total_review_items':len(all_items),'classification_counts_before_adjudication':counts,'source_quotes_checked':evidence_count,'candidate_omission_ids':findings,'parent_decision':decision,'protected_source_files_unchanged':len(baseline),'human_review_completed':False,'field_validation_completed':False,'new_mandatory_review_tasks':False,'limits':['Role-item counts are review questions, not independent validation samples','No actual operating facts, legal approval or human learning outcomes established','No PDF citation sweep, contact sheet, recruiting or external transmission']};save(A/'VERIFICATION.json',report);save(A/'ALL_ITEMS.json',all_items);print(json.dumps(report,ensure_ascii=False,indent=2))
