from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/render_verify_v07.py').read_text(encoding='utf-8')
s=s.replace("OUT=ROOT/'e-book/exports/v07'","OUT=ROOT/'e-book/exports/v10'").replace("REVIEW=ROOT/'e-book/design/v07/review'","REVIEW=ROOT/'e-book/design/v10/review'")
for a,b in [('ebook_review_v07.html','ebook_review_v10.html'),('ebook_review_v07.pdf','ebook_review_v10.pdf'),('build_manifest_v07.json','build_manifest_v10.json'),('validation_v07.json','validation_v10.json')]:s=s.replace(a,b)
s=s.replace("for version in ['v06','v07']:","for version in ['v06','v10']:").replace("ctrl=OUT/'content_control_A4_v07.html'","ctrl=OUT/'content_control_A4_v10.html'")
s=s.replace('0.7 author review','0.10 author review').replace('저자 검토본0.7','저자 검토본0.10').replace('CRM,A/B,TRI-V,맥락항법,JH Motors','CRM,A/B,TRI-V,JH Motors')
s=s.replace("for term in ['허재혁'", "assert flat.count('트리아타시스')==1 and flat.count('Tri-Ataxis')==1\n for term in ['허재혁'",1)
s=s.replace("for term in ['허재혁',", "for term in ['시승 안내로 먼저 이해하기','출발점과 적용 범위','공통 운용 기준','허재혁',",1)
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
