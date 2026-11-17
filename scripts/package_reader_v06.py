"""Package the portable v0.6 reader, not a vendor-source or data redistribution."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v06'
files=['ebook_review_v06.pdf','ebook_review_v06.html','ebook_review_v06.md','build_manifest_v06.json','validation_v06.json','numeric_text_validation_v06.json','figure_data_v06.json','winner_effect.svg','guardrail_effect.svg','tri_v_method.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']
info='''# 허재혁의 CRM A/B 테스트, 저자 검토본 v0.6

PDF는 50쪽 A4 읽기본입니다. HTML은 브라우저에서 열면 목차와 36개 키워드 색인을 사용할 수 있습니다. Markdown은 편집용 원고이며 그림 SVG와 같은 폴더에 둡니다.

방법론 제목 맥락항법: 비교의 근거에서 실행의 결론까지는 제안입니다. 기존 트리아타시스와 TRI-V 세 축을 유지합니다. 9장과 10장은 노션 학습을 교정하고 설계와 조직 기록으로 확장했으며 11장은 유효성과 한계를 평가합니다.

기존 사례 여섯 개와 수치 장부를 보존했습니다. 새 그래프는 같은 수치에서 생성했습니다. 기존 워크북과 카드 참조편은 이 묶음에 포함하지 않았으며 v0.4 자료가 그대로 남아 있습니다.

실제 OEM 성과, 방법론의 현장 우월성 또는 새 통계 이론을 입증한 책은 아닙니다. 저자와 사람의 기술 검토, 독자 테스트, 인용과 글꼴 및 판매 요건 확인 전입니다. 영상의 검증된 전사본이 아닌 사용자 학습 노트에서 출발했으며 연결 영상을 모두 시청했다고 주장하지 않습니다.

계산 코드와 데이터는 비공개 저장소 AB-Test의 기존 경로를 사용합니다. 이 읽기 묶음은 전체 개발 환경이 아닙니다.
'''
(OUT/'READER_README.md').write_text(info,encoding='utf-8');files.append('READER_README.md')
manifest={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in files}
(OUT/'package_hashes_v06.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append('package_hashes_v06.json')
p=ROOT/'JH_CRM_ebook_reader_v06.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(OUT/name,'JH_CRM_reader_v06/'+name)
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)
 for name,digest in manifest.items():assert hashlib.sha256(z.read('JH_CRM_reader_v06/'+name)).hexdigest()==digest
print(json.dumps({'package':str(p),'files':len(files),'bytes':p.stat().st_size,'zip_integrity':'passed','hashes':'all passed'},ensure_ascii=False,indent=2))
