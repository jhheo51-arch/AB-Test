from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_ebook_v07_numbers.py').read_text(encoding='utf-8').replace('e-book/exports/v07/ebook_review_v07.md','e-book/exports/v13/ebook_review_v13.md').replace('e-book/exports/v07/numeric_text_validation_v07.json','e-book/exports/v13/numeric_text_validation_v13.json').replace('e-book/exports/v07/chapter12_sql_validation_v07.json','e-book/exports/v13/chapter12_sql_validation_v13.json')
s=s.replace('e-book/virtual-data/v03/data/jh_motors_v03.sqlite','e-book/virtual-data/v13/data/jh_motors_v13.sqlite')
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})