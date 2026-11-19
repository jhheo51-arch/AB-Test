# A/B 실험노트 영상 제작

A/B 테스트를 처음 배우는 시청자를 위해 가상 실험 하나를 질문, 도표, 대사 순서로 풀어냅니다. 이 폴더에서 1~10화의 최신 대본과 도표, 가로 롱폼과 세로 숏폼을 만드는 코드를 관리합니다. 사례의 방문자, 가입률, 실험 결과는 교육용 가상 데이터입니다.

## 대본에서 영상까지

1. 회차의 데이터와 장면을 작성합니다. 각 장면에는 화자, 대사, 제목, 도표나 숫자 카드, 강조할 단어가 있습니다. 같은 데이터와 계산을 롱폼과 숏폼에서 함께 쓰고, 설명 길이는 형식에 맞춥니다.
2. 한국어 대사를 Edge TTS로 합성합니다. 2~10화는 단어의 시작 시각을 받아 대사에 지정한 강조 단어를 찾습니다. 1화의 강조 시각은 재배정 애니메이션과 함께 대본에서 지정합니다. 음성과 단어 시각은 로컬 캐시를 재사용합니다.
3. Pillow가 도표와 자막을 장면에 그립니다. 대사에 맞는 수치나 도형을 강조하고, 주요 도표의 단위와 기준선은 강조가 바뀌어도 읽을 수 있게 유지합니다. 숏폼은 첫 1.2초에 표지를 표시하고 그 위에서 첫 대사가 시작합니다.
4. FFmpeg가 장면과 음성을 H.264/AAC MP4로 합칩니다. 롱폼은 1920×1080, 숏폼은 1080×1920입니다. 내장 자막 외에 SRT 파일과 장면 및 강조 시각 JSON도 같은 출력 폴더에 생성합니다.

| 바꿀 내용 | 파일 |
| --- | --- |
| 1화 데이터, 대본, 강조 시각 | [episode.json](episode.json), [episode_data.py](episode_data.py) |
| 2~3화 대본과 장면, 숏폼 표지 | [storyboards.py](storyboards.py), [make_shorts.py](make_shorts.py) |
| 4~5화 대본과 도표 | [storyboards_04_05.py](storyboards_04_05.py), [figures_04_05.py](figures_04_05.py) |
| 6~10화 대본과 도표 | [storyboards_06_10.py](storyboards_06_10.py), [figures_06_10.py](figures_06_10.py) |
| 음성 시각, 화면 조립, 영상 출력 | [make_videos.py](make_videos.py), [render.py](render.py) |

## Windows에서 재렌더링

Windows에서 Python과 FFmpeg를 준비하고 ffmpeg와 ffprobe가 PATH에서 실행되는지 확인합니다. 한글은 설치된 Noto Sans KR 가변 글꼴을 우선 사용하고 맑은 고딕을 기본 대체 글꼴로 씁니다. 캐시에 없는 음성은 Edge TTS 서비스에 대사를 보내 생성하므로 인터넷 연결이 필요합니다.

~~~powershell
cd video-production
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

.\.venv\Scripts\python render.py --version both --output renders-review-v01
.\.venv\Scripts\python make_videos.py renders-review-v01 2-3
.\.venv\Scripts\python make_videos.py renders-review-v01 4-5
.\.venv\Scripts\python make_videos.py renders-review-v01 6-10
~~~

예를 들어 7화 숏폼만 만들려면 아래 명령을 실행합니다. 다시 렌더링할 때는 새 폴더 이름을 지정합니다.

~~~powershell
.\.venv\Scripts\python make_videos.py renders-ep07-review-v02 6-10 7 --short-only
~~~

기본 렌더링은 A/B 글자로 표시합니다. 기존 캐릭터를 사용하려면 두 원본 파일 A_soft.png와 B_soft.png가 있는 폴더를 지정한 뒤 같은 명령을 실행합니다.

~~~powershell
$env:VIDEO_MASCOT_DIR = 'C:\path\to\character-assets'
~~~

## 검수와 보관

- ffprobe로 크기와 오디오를 확인하고, MP4와 자막 SRT, 장면 JSON을 대조합니다. 휴대폰 폭에서 제목, 축 단위, 기준선, 자막을 확인하고 숏폼 표지 1.2초 동안 첫 대사가 들리는지 확인합니다.
- 렌더링 결과와 음성 캐시는 로컬에 생성됩니다. 승인한 영상은 기존 비공개 Drive 보관함에서 관리합니다. 이 코드의 실행 범위는 로컬 파일 생성까지입니다.
- Git 기록은 제작 코드를 다룹니다. 기존 영상의 완성 MP4, 음성 캐시, 캐릭터 원본, Drive 주소는 각 보관 위치에서 관리합니다.
