"""Check v0.11 integration, frozen evidence and the real PDF destinations."""
from pathlib import Path
import re,json,hashlib
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v11';REVIEW=ROOT/'e-book/design/v11/review';REVIEW.mkdir(parents=True,exist_ok=True)
old=(ROOT/'e-book/exports/v10/ebook_review_v10.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v11.md').read_text(encoding='utf-8')
def between(text,a,b):return text.split(a,1)[1].split(b,1)[0]
assert between(old,'# 5장 ','# 7장 ')==between(new,'# 5장 ','# 7장 ')
assert between(old,'# 7장 ','# 8장 ')==between(new,'# 7장 ','# 8장 ')
old12=between(old,'# 12장 ','# 부록 사례와 자료를 찾아가는 길').strip();new12=between(new,'# 12장 ','# 부록 사례와 자료를 찾아가는 길').strip();assert new12.startswith(old12)
old_edit=old[old.index('# 9장 학습을 실험 설계로 옮기기'):old.index('# 11장 TRI-V의 기여와 적용 범위')]
new_edit=new[new.index('# 9장 학습을 실험 설계로 옮기기'):new.index('# 11장 TRI-V의 기여와 적용 범위')]
number_pattern=r'\d+(?:\.\d+)?(?:%|:\d+)?';assert re.findall(number_pattern,old_edit)==re.findall(number_pattern,new_edit)
english_pattern=r'[A-Za-z]+(?:[-/][A-Za-z]+)*';assert set(re.findall(english_pattern,old_edit))==set(re.findall(english_pattern,new_edit))
oldval=json.loads((ROOT/'e-book/exports/v10/validation_v10.json').read_text(encoding='utf-8'));assert hashlib.sha256((ROOT/'e-book/exports/v10/ebook_review_v10.pdf').read_bytes()).hexdigest()==oldval['pdf_sha256']
ledgers=json.loads((ROOT/'e-book/exports/v10/build_manifest_v10.json').read_text(encoding='utf-8'))['old_numeric_ledgers']
for file,sha in ledgers.items():assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==sha
assert len(re.findall(r'^# \d+장 ',new,re.M))==12 and len(re.findall(r'^## 사례 [1-6] ',new,re.M))==6
assert not re.search(r'^### ',new,re.M)
for term in ['가능한 대안과 적용 범위','추가 분석을 멈추는 것, 실험을 종료하는 것, 운영을 중단하는 것','B를 채택하지 않더라도 A가 모든 대안 중 최선','어떤 확인 결과가 어떤 선택을 바꾸는지','차주와 차량 정보가 공란인 접수','담당 팀장이 없는 경우','PDCA','충분한 근거가 있을 때 검토를 끝내기']:assert term in new,term
counter=json.loads((OUT/'COUNTEREXAMPLE_RESULTS.json').read_text(encoding='utf-8'));fixture=json.loads((OUT/'counterexample_fixture.json').read_text(encoding='utf-8'));sec=between(new,'## 충분한 근거가 있을 때 검토를 끝내기','# 9장 ')
for c,r in zip(fixture['cases'],counter['cases']):
 for term in [f'{c["completed_A"]:,}/{c["n_A"]:,}명',f'{c["completed_B"]:,}/{c["n_B"]:,}명',f'{r["performance_interval_pp"][0]:+.2f}',f'{r["performance_interval_pp"][1]:+.2f}',f'{r["guard_one_sided_upper_pp"]:+.3f}pp']:assert term in sec,term
assert all(counter['checks'].values())
forbid='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(x in new for x in forbid)
with pymupdf.open(OUT/'ebook_review_v11.pdf') as pdf:
 toc=pdf.get_toc();pages={}
 targets={'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','scope':'11장 TRI-V의 기여와 적용 범위','chapter9':'9장 학습을 실험 설계로 옮기기','chapter10':'10장 실험을 조직의 기억으로 남기기'}
 for key,title in targets.items():
  found=[p for level,name,p in toc if name==title];assert len(found)==1,(title,found);pages[key]=found[0]
  pdf[found[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/(key+'.png'))
 flat='\n'.join(p.get_text() for p in pdf)
 flat_compact=re.sub(r'\s+','',flat)
 for term in ['753,458','666','공통 운용 기준','조건 가','조건 나','조건 다','조건 라','+1.75','+0.222','97.5%']:assert re.sub(r'\s+','',term) in flat_compact,term
 assert not any(x in flat for x in forbid)
 record=json.loads((OUT/'VALIDATION.json').read_text(encoding='utf-8'));assert record['pdf_pages']==1 and record['input_count']==6 and record['minimum_text_pt']>=11.9
 report={'status':'passed','chapter_pages':pages,'full_book_pages':len(pdf),'old_v10_pdf_unchanged':True,'chapters5_6_and_six_existing_cases_exactly_preserved':True,'chapter12_existing_analysis_preserved':True,'old_ledgers_unchanged':ledgers,'new_counterexamples_reconciled':len(counter['cases']),'method_axes':3,'minimum_record_fields':6,'minimum_record_pdf_pages':record['pdf_pages'],'chapter9_10_editorial_scope':'Bounded prose edit, author and human review pending','human_reader_or_field_effect_proven':False,'PUB_02':'started and technically verified within this revision, not author-approved completion'}
(OUT/'integration_validation_v11.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
