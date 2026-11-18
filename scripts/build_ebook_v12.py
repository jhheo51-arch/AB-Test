"""Build the next full reader from bounded, evidence-preserving chapter edits."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v12';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v11/ebook_review_v11.md');text=base
for ch in [1,5,6,12]:
 start=text.index(f'# {ch}장 ');end=text.find('\n# ',start+1);end=len(text) if end<0 else end
 text=text[:start]+read(f'e-book/manuscript/editorial_v12/ch{ch:02d}.md').strip()+'\n\n'+text[end:].lstrip('\n')
# Build commands refer to this edition; editing does not rerun original inference.
text=text.replace('uv run --with statsmodels --with scipy --with playwright --with pymupdf python scripts/build_tri_v_record_v11.py','python scripts/edit_ebook_v12.py')
text=text.replace('scripts/build_ebook_v11.py','scripts/build_ebook_v12.py').replace('scripts/render_verify_v11.py','scripts/render_verify_v12.py').replace('scripts/prepare_fonts_v11.py','scripts/prepare_fonts_v12.py').replace('scripts/verify_ebook_v11_numbers.py','scripts/verify_ebook_v12_numbers.py').replace('scripts/verify_v11_integration.py','scripts/verify_v12_integration.py')
(OUT/'ebook_review_v12.md').write_text(text,encoding='utf-8',newline='\n')
for p in (ROOT/'e-book/exports/v11').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json']:
 shutil.copyfile(ROOT/'e-book/exports/v11'/name,OUT/name)
shutil.copytree(ROOT/'e-book/exports/v11/assets',OUT/'assets',dirs_exist_ok=True)
# Reuse the already exercised layout implementation, not a new visual redesign.
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden)
s=read('scripts/build_ebook_v11.py');s=s[s.index("s=read('scripts/build_ebook_v07.py')"):s.index("m=json.loads((OUT/")]
s=s.replace('v11','v12').replace('0.11','0.12')
s=s.replace("exec(compile(s,__file__,'exec'),globals())", "s=s.replace('.glossary h2{font-size:15pt;margin:5mm 0 3mm}', '.glossary h2{font-size:15pt;margin:3.5mm 0 2mm}')\nexec(compile(s,__file__,'exec'),globals())")
exec(compile(s,__file__,'exec'),globals())
m=json.loads((OUT/'build_manifest_v12.json').read_text(encoding='utf-8'));m.update({'previous_v11_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'methodology_name':'TRI-V','fixed_axes':True,'record_fields':6,'publication_stage':'PUB-02 prose editing applied; author approval and independent human review pending','new_content':['Bounded prose editing in chapters1,5,6,12; original chapter9/10 editing retained','All ordered evidence numbers, English-term sets, tables and code preserved within edited chapters','Decision follow-up connected to six existing fields without a second mandatory form'],'field_effect_or_reader_learning_proven':False,'old_v11_preserved':True})
(OUT/'build_manifest_v12.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'edition':'v0.12','source_characters':len(text),'previous_v11_characters':len(base),'original_data_rebuilt':False},ensure_ascii=False))
