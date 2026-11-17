from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/verify_ebook_v05_numbers.py').read_text(encoding='utf-8')
s=s.replace("e-book/exports/v05/ebook_review_v05.md","e-book/exports/v06/ebook_review_v06.md")
s=s.replace("case_source=(ROOT/'e-book/manuscript/winner_cases_456_v05.md').read_text(encoding='utf-8')","case_source=text")
s=s.replace("e-book/exports/v05/numeric_text_validation_v05.json","e-book/exports/v06/numeric_text_validation_v06.json")
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
