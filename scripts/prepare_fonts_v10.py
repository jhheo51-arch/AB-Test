from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/prepare_fonts_v07.py').read_text(encoding='utf-8').replace('e-book/exports/v07/assets','e-book/exports/v10/assets').replace('e-book/exports/v07/ebook_review_v07.md','e-book/exports/v10/ebook_review_v10.md')
s=s.replace("chars=''.join(texts);report=[]", "texts.extend(p.read_text(encoding='utf-8') for p in (ROOT/'e-book/exports/v10').glob('*.svg'))\nchars=''.join(texts);report=[]")
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
