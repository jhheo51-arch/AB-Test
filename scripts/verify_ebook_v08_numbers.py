from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_ebook_v07_numbers.py').read_text(encoding='utf-8').replace('e-book/exports/v07/ebook_review_v07.md','e-book/exports/v08/ebook_review_v08.md').replace('e-book/exports/v07/numeric_text_validation_v07.json','e-book/exports/v08/numeric_text_validation_v08.json').replace('e-book/exports/v07/chapter12_sql_validation_v07.json','e-book/exports/v08/chapter12_sql_validation_v08.json')
# The inherited runner rewrites the v05 validation output to v07; redirect that literal as well.
s=s.replace("'e-book/exports/v07/numeric_text_validation_v07.json'","'e-book/exports/v08/numeric_text_validation_v08.json'")
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
