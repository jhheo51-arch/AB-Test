# 현재 앱 실제 조작 시연

현재 도움말은 **160.16초, H.264 1280×900 25fps, 무음 한국어 자막 26구간**의 실제 Chrome 녹화입니다. UI는 다시 그리지 않았고 1280×800 실제 앱 아래 100px 자막 영역만 합성했습니다. 재생 파일은 단일 경로 `../app/help/walkthrough.mp4`에 있으며 [자막](../app/help/walkthrough.ko.srt)과 [실제 타임라인](../app/help/walkthrough.timeline.json)을 함께 제공합니다.

## 내용과 한계

약 00:08 상황·목적, 00:16 고정 질문·후보와 편집 계획, 00:33 계획 JSON 저장·새 페이지 복원, 00:46 CSV 업로드, 00:52 열과 A=control/B=treatment, 01:04 모름 조건의 기술통계, 01:17 합성 네 조건 가정, 01:32 집단 사전성 모름, 01:38 실제 결과·계산 근거·탐색 집단, 02:03 판단·프로젝트/HTML/PDF 공유 범위, 02:26 근거 변경 무효화입니다. 정확한 구간은 실제 타임라인을 따릅니다.

모든 입력은 합성입니다. 설계 안내는 로컬 고정 질문·후보이지 의미 해석 AI가 아닙니다. **네 핵심 조건의 확인됨은 시연에서만 둔 합성 가정인 사용자 진술이며 실제 실험 인증이 아닙니다. 실제 자료의 모르는 조건은 모름으로 둡니다.** 사람 관찰 0건, live LLM 0건이며 사용성·학습 효과·실제 CRM 성과·전반적 접근성 인증은 없습니다. 장면 단위 자막이며 프레임 단위 동기 보장은 아닙니다. 모바일에서 영상 내 작은 글자의 가독성을 인증하지 않습니다.

실제 합성 결과는 A 130/1000, B 150/1000, 관측 +2.00pp, p=0.22074876980310534, 승패 보류입니다. 집단 사전성 모름으로 집단 p값은 없으며 사업·보호 조건은 미확인입니다. 근거는 프로젝트 JSON에 남지만 공개 HTML/PDF·최소 모델 정보에서는 제외됩니다. 프로젝트 자체가 익명화되는 것은 아닙니다.

## 원래 녹화 근거와 현재 통합 검사

`EVIDENCE.json`과 `evidence/`는 **원래 녹화 당시의 역사적 기록**을 선택 보관했습니다. 그 안의 `runtime/` 경로와 `current_app_source_sha256` 이름은 녹화 시 고정 스냅샷을 가리키며 현재 소스 검증으로 재해석하지 않습니다. 원본 제작 스크립트 해시·미포함 원시 파일의 해시도 역사적 기록입니다. 현재 이 폴더의 스크립트는 이식성을 위해 수정했으므로 그 역사적 스크립트 해시와 다릅니다. 원본 staging 자료는 변경하지 않았습니다.

통합은 도움말 제목·설명과 자막 다운로드용 서버의 좁은 GET 허용목록만 바꿨습니다. 앱 JS·통계·개인정보·조건 상태 구현은 유지했습니다. 이전 동영상 바이트를 보존했다는 주장은 하지 않습니다. 현재 영상 SHA-256은 `ffe7cd998e4a875b44ef45130e12a4d931b12d542c06b0276abfe5aa0978eabd`입니다. 현재 소스 해시는 `../app/verification.json`, 실제 Chrome 재생/닫기/상태 보존은 `../app/interface_verification.json`, 새 전체 FFmpeg 디코드는 `../app/evidence/tutorial_media_validation.json`에서 확인합니다. 원래 녹화 16단언과 원래 검증 41단언은 통합 25개 스크립트 검사 합계에 더하지 않습니다.

실제 다운로드 JSON·HTML·3쪽 Chromium PDF, 엔진 JSON, ffprobe/전체 decode, 표본 프레임만 선택 보관합니다. 의존 패키지·글꼴 변환본·원시 WebM·중간 동영상·자막 PNG는 배포하지 않습니다. 원래 영상의 OFL Pretendard는 앱의 `fonts/LICENSE.txt` 고지를 따릅니다.

## 재현 (원본 앱과 녹화 자료에 쓰지 않음)

Python, uv, 설치된 Chrome, FFmpeg/ffprobe가 필요합니다. 일반 앱 사용에는 제작 의존성이 필요하지 않습니다. Windows Bash 예:

```bash
export TMPDIR='C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch'
export TEMP="$TMPDIR" TMP="$TMPDIR"
uv venv "$TMPDIR/tutorial-venv"
uv pip install --python "$TMPDIR/tutorial-venv/Scripts/python.exe" playwright PyMuPDF Pillow fonttools Brotli
PY="$TMPDIR/tutorial-venv/Scripts/python.exe"
OUT="$TMPDIR/ab_walkthrough_reproduction"
"$PY" record_walkthrough.py --app-dir ../app --output-dir "$OUT" --quick
"$PY" record_walkthrough.py --app-dir ../app --output-dir "$OUT"
"$PY" render_walkthrough.py --app-dir ../app --output-dir "$OUT"
"$PY" verify_walkthrough.py --app-dir ../app --output-dir "$OUT"
"$PY" finalize_evidence.py --app-dir ../app --output-dir "$OUT"
```

`--app-dir` 기본값은 스크립트와 나란한 현재 `app/`, `--output-dir` 기본값은 TMPDIR 아래 scratch입니다. 다른 OS에서는 venv의 `bin/python`을 사용합니다. 출력은 앱/이 폴더 바깥이어야 하며 새 녹화 시간·바이트는 원본과 달라질 수 있습니다. WOFF2는 앱의 상대경로에서 읽고 TTF와 OFL 고지는 출력 폴더에만 만듭니다. 모든 서버는 loopback 임의 포트를 사용하고 종료하며 외부/모델 요청은 차단합니다. 새 출력 영상은 자동으로 정식 도움말을 덮어쓰지 않습니다.
