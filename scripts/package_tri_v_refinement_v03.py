"""Package only the refined review files and verified supporting sources."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/methodology/tri_v_refinement_v03'
names=['README.md','MINIMUM_RECORD.md','MINIMUM_RECORD.html','MINIMUM_RECORD.pdf','MINIMUM_RECORD_WORKED.md','COUNTEREXAMPLES.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json','EXPERIENCE_AND_ACCEPTANCE.md','SOURCE_EVIDENCE.md','AUTHOR_EVIDENCE.json','SOURCE_IMAGE.png','VALIDATION.json']
files=[D/name for name in names]+[ROOT/'e-book/manuscript/tri_v_author_origin_v03.md',ROOT/'scripts/build_tri_v_refinement_v03.py',Path(__file__),ROOT/'e-book/review/methodology/tri_v_sharpening_v02/DECISION_RECORD_TEMPLATE.md']
assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
author=json.loads((D/'AUTHOR_EVIDENCE.json').read_text(encoding='utf-8'));assert hashlib.sha256((D/'SOURCE_IMAGE.png').read_bytes()).hexdigest()==author['image_sha256']
v=json.loads((D/'VALIDATION.json').read_text(encoding='utf-8'));assert v['pdf_pages']==1 and v['input_count']==6 and v['minimum_text_pt']>=11.9
assert v['fixture_sha256']==hashlib.sha256((D/'counterexample_fixture.json').read_bytes()).hexdigest()
for p in files:
 if p.suffix in ['.md','.json','.html']:
  text=p.read_text(encoding='utf-8')
  assert not any(c in text for c in ['\u00b7','\u2022','\u2027','\u318d','\u22c5','\u30fb']),p.name
archive=ROOT/'TRI_V_practical_v03_AUTHOR_REVIEW.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;assert len(z.namelist())==len(files)
 assert json.loads(z.read('e-book/review/methodology/tri_v_refinement_v03/VALIDATION.json'))['pdf_pages']==1
checks={'path':str(archive),'file_count':len(files),'zip_crc':'passed','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'audience':'저자 검토용. 답안과 제공 이미지 포함. 참여자에게 전체 전송하지 않음','book':'v0.10 전체 읽기본은 변경하지 않음','effectiveness':'경험과 프로젝트 기록을 반영. 누락과 시간 감소의 비교 효과를 입증한 것은 아님'}
(D/'PACKAGE_CHECK.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
