# 전자책과 데이터 실행 안내

저장소 루트에서 실행합니다. 결과에 포함된 95쪽 PDF와 읽기 ZIP을 확인할 때는 상태 확인 명령부터 실행합니다.

~~~powershell
python scripts/refresh_project_status.py
~~~

v0.19 재생성에는 Python과 Markdown, Pillow, PyMuPDF, Playwright 및 Google Chrome이 필요합니다. 글꼴을 새로 만들 때는 기존 글꼴 설정과 라이선스를 확인합니다. 기존 PDF를 보관하려면 별도 작업 사본에서 아래 명령을 실행합니다.

~~~powershell
python scripts/build_visuals_v19.py
python scripts/build_ebook_v19.py
python scripts/render_verify_v19.py
python scripts/verify_ebook_v19_numbers.py
python scripts/verify_visual_geometry_v19.py
python scripts/verify_v19_integration.py
python scripts/package_reader_v19.py
python scripts/refresh_project_status.py
~~~

수치 검사는 원래 장부와 읽기 전용 SQL을 사용합니다. [합성 데이터 실행 안내](../e-book/virtual-data/v03/README.md)와 [교정 사본](../e-book/virtual-data/v13/README.md)에서 데이터별 경로를 확인할 수 있습니다. 이전 판의 배포와 검수에 쓰인 스크립트는 당시 파일과 함께 [정리 직전 Git 기록](https://github.com/jhheo51-arch/AB-Test/tree/c8cd72253f4b11131f71405e0ab4d26b3f0b46b0/scripts)에 있습니다.
