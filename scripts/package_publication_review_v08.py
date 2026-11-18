"""Package only prepared author-review documents, never actual participant records."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import csv,json,hashlib
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/reader_test_v01'
with (D/'OBSERVATION_TEMPLATE.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==[]
paths=[f'e-book/review/reader_test_v01/{name}' for name in ['PROTOCOL.md','PARTICIPANT_PACKET.md','FACILITATOR_KEY.md','OBSERVATION_TEMPLATE.csv','FIXTURE_CALCULATIONS.json','PREPARATION_VALIDATION.json']]+['e-book/review/publication/CLAIM_SCOPE_AND_SYNTHETIC_AUDIT.md','e-book/planning/PUBLICATION_BRIEF.md','e-book/planning/PUBLICATION_CHECKLIST.md','e-book/design/v08/REVIEW.md']
files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
dest=ROOT/'JH_CRM_publication_and_reader_test_v08_AUTHOR_ONLY.zip'
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in paths:z.write(ROOT/p,p)
 z.write(ROOT/'e-book/review/AUTHOR_REVIEW_START_HERE.md','START_HERE.md')
 z.writestr('FILE_MANIFEST.json',json.dumps({'scope':'Author review only. Do not share whole archive with participants. No real participant records or outcomes.','files':files},ensure_ascii=False,indent=2))
with ZipFile(dest) as z:
 assert z.testzip() is None
 for p,h in files.items():assert hashlib.sha256(z.read(p)).hexdigest()==h
 assert not list(csv.DictReader(z.read('e-book/review/reader_test_v01/OBSERVATION_TEMPLATE.csv').decode('utf-8-sig').splitlines()))
print(json.dumps({'archive':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'verified_file_count':len(files),'zip_integrity':'passed','exact_entry_bytes':'passed','real_participant_records':False,'author_only':True},ensure_ascii=False,indent=2))
