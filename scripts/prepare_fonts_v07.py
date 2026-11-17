"""Subset installed OFL Noto fonts for the portable reader."""
from pathlib import Path
import urllib.request,json
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v07/assets';OUT.mkdir(parents=True,exist_ok=True)
texts=[]
for p in (ROOT/'e-book/manuscript').glob('*.md'):texts.append(p.read_text(encoding='utf-8'))
texts.append((ROOT/'e-book/exports/v06/ebook_review_v06.md').read_text(encoding='utf-8'))
texts.append('그래서, 이 캠페인 계속할까요? 차이를 발견하는 실험에서 실행을 결정하는 방법으로 CRM A/B 테스트 실무서 맥락항법 제안 허재혁 지음 저자 검토본 읽기 안내 목차 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz +-→[]()%pp')
if (ROOT/'e-book/exports/v07/ebook_review_v07.md').exists():texts.append((ROOT/'e-book/exports/v07/ebook_review_v07.md').read_text(encoding='utf-8'))
chars=''.join(texts);report=[]
for family,source,target,url in [('sans','NotoSansKR-VF.ttf','reader-sans.woff2','https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/OFL.txt'),('serif','NotoSerifKR-VF.ttf','reader-serif.woff2','https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifkr/OFL.txt')]:
 font=TTFont('C:/Windows/Fonts/'+source)
 license_entries=[n.toUnicode() for n in font['name'].names if n.nameID==13];assert any('Open Font License' in s for s in license_entries)
 options=subset.Options();options.name_IDs=['*'];options.name_languages=['*'];options.layout_features=['*'];options.recalc_bounds=True
 sub=subset.Subsetter(options=options);sub.populate(text=chars);sub.subset(font);font.flavor='woff2';font.save(OUT/target)
 raw=urllib.request.urlopen(url,timeout=25).read();license_text=raw.decode('utf-8');assert 'SIL OPEN FONT LICENSE' in license_text;(OUT/f'LICENSE-{family}.txt').write_text(license_text,encoding='utf-8');report.append({'family':family,'installed_source':source,'embedded_license':'SIL OFL1.1','file':target,'bytes':(OUT/target).stat().st_size,'license_url':url,'note':'Reading subset of installed Noto font; final distribution legal review remains separate.'})
(OUT/'fonts_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
