from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_ebook_v07_numbers.py').read_text(encoding='utf-8').replace('e-book/exports/v07/ebook_review_v07.md','e-book/exports/v11/ebook_review_v11.md').replace('e-book/exports/v07/numeric_text_validation_v07.json','e-book/exports/v11/numeric_text_validation_v11.json').replace('e-book/exports/v07/chapter12_sql_validation_v07.json','e-book/exports/v11/chapter12_sql_validation_v11.json')
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
