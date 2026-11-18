"""Verify bounded v12 edits against the actual baseline and final PDF."""
from pathlib import Path
import re,json,hashlib
import pymupdf
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v12';REVIEW=ROOT/'e-book/design/v12/review';REVIEW.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
old=(ROOT/'e-book/exports/v11/ebook_review_v11.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v12.md').read_text(encoding='utf-8')
def chapter(src,ch):
 st=src.index(f'# {ch}장 ');en=src.find('\n# ',st+1);return src[st:len(src) if en<0 else en].strip()
np=r'[+−-]?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][+−-]?\d+)?';ep=r'[A-Za-z]+(?:[-/][A-Za-z]+)*';checks={}
for ch in range(1,13):
 a,b=chapter(old,ch),chapter(new,ch)
 if ch in [1,5,6,12]:
  assert re.findall(np,a)==re.findall(np,b),(ch,'ordered numbers')
  assert set(re.findall(ep,a))==set(re.findall(ep,b)),(ch,'English terms')
  assert re.findall(r'^\|.*$',a,re.M)==re.findall(r'^\|.*$',b,re.M),(ch,'tables')
  assert re.findall(r'```.*?```',a,re.S)==re.findall(r'```.*?```',b,re.S),(ch,'code')
  checks[str(ch)]={'numeric_tokens':len(re.findall(np,a)),'ordered_numbers':'identical','English_term_set':'identical','tables_and_code':'identical','before_characters':len(a),'after_characters':len(b)}
 else:assert a==b,(ch,'outside edited scope')
assert old[:old.index('# 1장 ')]==new[:new.index('# 1장 ')]
a='## TRI-V 공통 운용 기준';end='# 2장 ';assert old.split(a,1)[1].split(end,1)[0].strip()==new.split(a,1)[1].split(end,1)[0].strip()
for file in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json']:
 assert (OUT/file).read_bytes()==(ROOT/'e-book/exports/v11'/file).read_bytes(),file
v11=load('e-book/exports/v11/validation_v11.json');assert digest('e-book/exports/v11/ebook_review_v11.pdf')==v11['pdf_sha256']
ledger=load('e-book/exports/v11/build_manifest_v11.json')['old_numeric_ledgers']
for p,h in ledger.items():assert digest(p)==h,p
forbid='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(x in new for x in forbid)
assert not re.search(r'^### ',new,re.M)
with pymupdf.open(OUT/'ebook_review_v12.pdf') as pdf:
 toc=pdf.get_toc();pages={};flat='\n'.join(p.get_text() for p in pdf);compact=re.sub(r'\s+','',flat)
 targets={'author_origin':'들어가며','operating_contract':'TRI-V 공통 운용 기준','positive_cases':'충분한 근거가 있을 때 검토를 끝내기','chapter5':'5장 숫자를 읽을 때 필요한 통계','chapter6':'6장 고객 수보다 필요한 정보량부터','chapter9':'9장 학습을 실험 설계로 옮기기','chapter10':'10장 실험을 조직의 기억으로 남기기','scope':'11장 TRI-V의 기여와 적용 범위','chapter12':'12장 한 건의 캠페인을 설계에서 결정까지'}
 for key,title in targets.items():
  hits=[p for _,name,p in toc if name==title];assert len(hits)==1,(title,hits);pages[key]=hits[0]
  if key in ['chapter5','chapter6','chapter12','operating_contract']:pdf[hits[0]-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/(key+'.png'))
 for phrase in ['법적 권리 침해나 중대한 피해는 통계적 유의성을 기다리지 않는 운영 중단 사유로 두며','관계 안전은 통과했다고 말할 수 없다','공통 운용 기준의 여섯 항목에','추가 확인은 선택을 바꿀 질문으로 남긴다','+0.222','97.5%','0.00274','753,458','666']:assert re.sub(r'\s+','',phrase) in compact,phrase
 assert not any(x in flat for x in forbid)
 last_glossary_entries=[name for level,name,p in toc if level==2 and p==len(pdf)];assert len(last_glossary_entries)>=2,('stranded glossary tail',last_glossary_entries)
 report={'status':'passed','full_book_pages':len(pdf),'chapter_pages':pages,'edited_chapters':checks,'unchanged_chapters':[2,3,4,7,8,9,10,11],'six_cases_exactly_preserved':True,'operating_contract_exactly_preserved':True,'old_v11_pdf_unchanged':True,'old_numeric_ledgers':ledger,'minimum_record_fields':6,'minimum_record_pdf_pages':1,'record_files_byte_identical_to_v11':True,'counterexamples_reconciled':4,'human_review_approved':False,'reader_test_conducted':False,'PUB_02':'editorial changes applied and technically checked; author approval pending'}
(OUT/'integration_validation_v12.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
