"""Portable reader package with licensed font subsets, covers and simulated reviews."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v07'
guide='''# 허재혁의 CRM A/B 테스트 실무서 v0.7

먼저 ebook_review_v07.pdf를 여세요. 79쪽 검토본입니다. 브라우저 독서는 ebook_review_v07.html이며 assets 폴더를 같은 위치에 두세요. 편집 원고는 Markdown입니다. 본문의36개 키워드 색인과 목차를 이용할 수 있습니다.

cover_comparison_v07.png에서 세 표지를 비교할 수 있습니다. 본책은 A안을 추천안으로 사용했으며 최종 저자 승인 전입니다. cover_A.html, cover_B.html, cover_C.html은 수정 가능한 원본으로 글꼴은 함께 제공한 assets를 사용합니다.

PERSONA_REVIEW_v07.md는 네 가상 페르소나의 편집 평가와 수정 결과입니다. 실제 인터뷰, 지불 의사나 판매 검증이 아닙니다. REVIEW_v07.md는 분량 변화, 실제 반영 위치와 확인 범위입니다. decision_sheet_v07.md는 복사해 작성할 빈 양식이며 승인 도구가 아닙니다.

이 묶음은 PDF, HTML, 원고, 그림과 읽기 글꼴 및 편집 평가를 제공합니다. 원래 고객 DB와 전체 개발 환경, 과거 워크북과60개 카드 별책까지 포함한 묶음은 아닙니다. 계산의 DB와 코드에 접근할 권한이 있는 독자는 기존 비공개 저장소의 경로와 명세를 따릅니다.

이 묶음은 전체 재현 환경이 아닙니다. 새 작업 사본에서는 계획 JSON의LF 줄바꿈과 DB 기록의CRLF 바이트 해시가 달라지는 문제를 발견했습니다. CRLF 표현을 재구성한 해시는 DB 기록과 일치하지만 원본 바이트가 동일하다고 주장하지 않으며 계획이나 DB를 고쳐 맞추지 않았습니다. 세부 상태는 저장소의 PROJECT_STATUS.json에 기록합니다.

수치103항목의 원고 대조와12장SQL의읽기전용집계를 확인했지만 사람의 통계 및 OEM 검수와 실제 독자 시험, 판매처 규격과 최종 권리 및 저자 문체 확인은 남아 있습니다. 실제 OEM 성과나 새로운 통계 이론을 입증한 출간 승인본으로 사용하지 마세요.
'''
(OUT/'READER_README_v07.md').write_text(guide,encoding='utf-8')
files={p.name:p.read_bytes() for p in OUT.iterdir() if p.is_file() and (p.name.startswith('ebook_review_') or p.suffix=='.svg' or p.name in ['decision_sheet_v07.md','READER_README_v07.md','validation_v07.json','build_manifest_v07.json','numeric_text_validation_v07.json','chapter12_sql_validation_v07.json'])}
for p in (OUT/'assets').iterdir():files['assets/'+p.name]=p.read_bytes()
for name,src in [('PERSONA_REVIEW_v07.md','e-book/design/v07/PERSONA_REVIEW_v07.md'),('REVIEW_v07.md','e-book/design/v07/REVIEW.md'),('cover_comparison_v07.png','e-book/design/v07/covers/cover_comparison_v07.png')]:files[name]=(ROOT/src).read_bytes()
for key in ['A','B','C']:
 h=(ROOT/f'e-book/design/v07/covers/cover_{key}.html').read_text(encoding='utf-8').replace('file:///C:/Windows/Fonts/NotoSansKR-VF.ttf','assets/reader-sans.woff2').replace('file:///C:/Windows/Fonts/NotoSerifKR-VF.ttf','assets/reader-serif.woff2');files[f'cover_{key}.html']=h.encode('utf-8');files[f'cover_{key}.png']=(ROOT/f'e-book/design/v07/covers/cover_{key}.png').read_bytes()
hashes={name:hashlib.sha256(data).hexdigest() for name,data in files.items()};(OUT/'package_hashes_v07.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8');files['package_hashes_v07.json']=(OUT/'package_hashes_v07.json').read_bytes()
p=ROOT/'JH_CRM_ebook_reader_v07.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in files.items():z.writestr('JH_CRM_reader_v07/'+name,data)
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for name,digest in hashes.items():assert hashlib.sha256(z.read('JH_CRM_reader_v07/'+name)).hexdigest()==digest
 assert len(z.namelist())==len(files)
print(json.dumps({'path':str(p),'entries':len(files),'bytes':p.stat().st_size,'zip_integrity':'passed','file_hashes':'passed'},ensure_ascii=False,indent=2))
