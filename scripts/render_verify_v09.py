"""Render and verify the integrated v0.9 reading edition."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/render_verify_v07.py').read_text(encoding='utf-8')
s=s.replace("OUT=ROOT/'e-book/exports/v07'","OUT=ROOT/'e-book/exports/v09'").replace("REVIEW=ROOT/'e-book/design/v07/review'","REVIEW=ROOT/'e-book/design/v09/review'")
for a,b in [('ebook_review_v07.html','ebook_review_v09.html'),('ebook_review_v07.pdf','ebook_review_v09.pdf'),('build_manifest_v07.json','build_manifest_v09.json'),('validation_v07.json','validation_v09.json')]:s=s.replace(a,b)
s=s.replace("for version in ['v06','v07']:","for version in ['v06','v09']:").replace("ctrl=OUT/'content_control_A4_v07.html'","ctrl=OUT/'content_control_A4_v09.html'")
s=s.replace('0.7 author review','0.9 author review').replace('저자 검토본0.7','저자 검토본0.9')
s=s.replace("for term in ['허재혁'", "assert flat.count('트리아타시스')==1 and flat.count('Tri-Ataxis')==1\n for term in ['허재혁'",1)
s=s.replace("for term in ['허재혁',", "for term in ['TRI-V 공통 운용 기준','최소 경로','변경 전 값과 변경 후 값','확인 기한','허재혁',",1)
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
