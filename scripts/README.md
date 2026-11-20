# 전자책과 데이터 실행 안내

저장소 루트에서 실행합니다. 결과에 포함된 97쪽 PDF와 읽기 ZIP을 확인할 때는 상태 확인 명령부터 실행합니다.

~~~bash
python scripts/refresh_project_status.py
~~~

v0.22는 본문 개발을 종료하고 검수에서 확인한 오류와 읽기 장애만 고친 저자 검토본입니다. 재생성에는 Python, uv, Markdown, fonttools, brotli, Pillow, PyMuPDF, Playwright와 설치된 Google Chrome 및 Noto KR 글꼴이 필요합니다. 현재 PDF를 보존하려면 별도 작업 사본에서 실행합니다.

~~~bash
uv run --with markdown python scripts/build_ebook_v22.py
uv run --with fonttools --with brotli python scripts/prepare_fonts_v22.py
uv run --with playwright --with pymupdf --with pillow python scripts/render_verify_v22.py
python scripts/verify_ebook_v22_numbers.py
uv run --with playwright python scripts/verify_visual_geometry_v22.py
uv run --with playwright python scripts/verify_reader_features_v22.py
uv run --with playwright --with pymupdf python scripts/verify_record_print_v22.py
uv run --with pymupdf python scripts/verify_v22_integration.py
uv run --with pymupdf python scripts/review_v22_corrections.py
TMPDIR="${TMPDIR:?사용할 임시 폴더의 전체 경로를 TMPDIR에 먼저 설정하세요}" uv run --with playwright --with pymupdf python scripts/package_reader_v22.py
python scripts/refresh_project_status.py
~~~

읽기 ZIP은 `e-book/packages/JH_CRM_ebook_reader_v22.zip`에 생성됩니다. 패키지 검사는 `TMPDIR`의 실제 존재하는 폴더에 임시 압축을 해제합니다. Hermes에서는 프로필에 설정된 scratch 경로를 사용합니다. 글꼴 재생성은 설치된 Noto KR 파일과 보존된 OFL 라이선스를 사용합니다.

v20~v22와 그 검수 기록을 함께 보존합니다. 최초 동결 장부는 바꾸지 않고, 이전 폴더 정리로 이동한 v20의 입력은 [경로 대응표](../e-book/manuscript/development_v20/BASELINE_RELOCATION.json)로 확인합니다. `frozen_v19`의 사본은 당시 바이트 검증용이며 실행용 옛 스크립트가 아닙니다. 새 판에 필요한 SVG와 이전 원고는 저장소에 이미 보존되어 있습니다. `prepare_v21_pipeline.py`와 `prepare_v22_pipeline.py`는 제작 코드 자체를 재생성할 때만 쓰며, 위의 일반 재조판 명령과 구분합니다.

수치 검사는 기존 장부와 읽기 전용 SQL을 사용합니다. [합성 데이터 실행 안내](../e-book/virtual-data/v03/README.md)와 [교정 사본](../e-book/virtual-data/v13/README.md)에서 데이터별 경로를 확인할 수 있습니다. 과거 정리 이전의 실행 코드와 배포 이력은 [정리 직전 Git 기록](https://github.com/jhheo51-arch/AB-Test/tree/c8cd72253f4b11131f71405e0ab4d26b3f0b46b0/scripts)에도 남아 있습니다.
