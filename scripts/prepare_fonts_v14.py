"""Subset the existing OFL Noto faces for the integrated v0.14 reader."""
from pathlib import Path
import json,shutil
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'e-book/exports/v14';OUT=BASE/'assets';OUT.mkdir(parents=True,exist_ok=True)
texts=[(BASE/'ebook_review_v14.md').read_text(encoding='utf-8'),(ROOT/'e-book/design/v07/covers/selected_cover.html').read_text(encoding='utf-8'),'TRI-V 허재혁 읽기 안내 목차 저자 검토본 0.14 CHAPTER 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz +-→[]()%pp']
texts.extend(p.read_text(encoding='utf-8') for p in BASE.glob('*.svg'));chars=''.join(texts);report=[]
for family,source,target in [('sans','NotoSansKR-VF.ttf','reader-sans.woff2'),('serif','NotoSerifKR-VF.ttf','reader-serif.woff2')]:
 font=TTFont('C:/Windows/Fonts/'+source);licenses=[n.toUnicode() for n in font['name'].names if n.nameID==13];assert any('Open Font License' in x for x in licenses)
 options=subset.Options();options.name_IDs=['*'];options.name_languages=['*'];options.layout_features=['*'];options.recalc_bounds=True
 sub=subset.Subsetter(options=options);sub.populate(text=chars);sub.subset(font);font.flavor='woff2';font.save(OUT/target)
 previous=ROOT/'e-book/exports/v10/assets'/f'LICENSE-{family}.txt';license_text=previous.read_text(encoding='utf-8');assert 'SIL OPEN FONT LICENSE' in license_text;shutil.copyfile(previous,OUT/previous.name)
 report.append({'family':family,'installed_source':source,'file':target,'bytes':(OUT/target).stat().st_size,'embedded_license':'SIL OFL1.1','license_copy':'Preserved v0.10 upstream OFL file for the same Noto family','final_distribution_review':'pending'})
(OUT/'fonts_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False))
