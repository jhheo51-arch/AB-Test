from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/render_verify_v07.py').read_text(encoding='utf-8')
s=s.replace("OUT=ROOT/'e-book/exports/v07'","OUT=ROOT/'e-book/exports/v08'").replace("REVIEW=ROOT/'e-book/design/v07/review'","REVIEW=ROOT/'e-book/design/v08/review'")
for a,b in [('ebook_review_v07.html','ebook_review_v08.html'),('ebook_review_v07.pdf','ebook_review_v08.pdf'),('build_manifest_v07.json','build_manifest_v08.json'),('validation_v07.json','validation_v08.json')]:s=s.replace(a,b)
s=s.replace("for version in ['v06','v07']:","for version in ['v06','v08']:")
s=s.replace("ctrl=OUT/'content_control_A4_v07.html'","ctrl=OUT/'content_control_A4_v08.html'")
s=s.replace('0.7 author review','0.8 author review').replace('저자 검토본0.7','저자 검토본0.8')
s=s.replace("for term in ['허재혁'", "assert flat.count('트리아타시스')==1 and flat.count('Tri-Ataxis')==1\n for term in ['허재혁'",1)
exec(compile(s,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
