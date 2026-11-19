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

## 새 회차 만들기 예시 (11화)

예제 질문은 **클릭률이 오르면 가입률도 오를까?**입니다. 그룹당 방문자 20명에서 A는 6명이 클릭하고 4명이 가입했고, B는 8명이 클릭하고 3명이 가입했다고 가정합니다. 클릭률과 가입률은 모두 전체 방문자를 분모로 계산합니다.

### 1. 대본과 도표 데이터 추가

이 폴더에 `storyboards_11_plus.py`를 만들고 아래 코드를 붙여 넣습니다. `comparison()`에서 같은 분모로 비율과 숫자 카드를 만들고, `dots=...`로 20개의 점 중 클릭한 사람 또는 가입한 사람을 채웁니다. 가로와 세로 화면에는 기존 렌더러가 같은 데이터로 카드와 점을 그립니다. 숏폼에서 두 카드에 점을 표시하려면 그룹당 20개 이하로 둡니다.

~~~python
from storyboards import card, one, shot

VISITORS = 20
CLICKS = (6, 8)
SIGNUPS = (4, 3)


def comparison(metric, counts):
    rates = tuple(f"{count / VISITORS:.0%}" for count in counts)
    cards = [
        card(screen, rate, f"방문자 {VISITORS}명 중 {count}명")
        for screen, rate, count in zip(("기존 화면 A", "새 화면 B"), rates, counts, strict=True)
    ]
    return shot(
        "해설", f"{metric}은 기존 화면이 {rates[0]}, 새 화면은 {rates[1]}예요.",
        f"방문자 기준 {metric}", cards,
        cues=(("", "first"), ("새 화면은", "second")),
        dots=tuple((VISITORS, count) for count in counts),
    )


def lessons():
    question = shot(
        "B", "클릭률이 오른 새 화면에서 가입률도 올랐을까요?",
        "클릭이 늘면 가입도 늘까?",
        one("클릭한 사람과 가입한 사람", "두 비율 비교", "전체 방문자가 두 비율의 분모입니다"),
        cues=(("", "value"),),
    )
    denominator = shot(
        "해설", f"두 화면에 방문자가 {VISITORS}명씩 있었어요. 두 비율 모두 전체 방문자로 나눠요.",
        "두 비율의 분모",
        one("그룹마다", f"방문자 {VISITORS}명", "클릭률과 가입률에 같은 분모를 사용"),
        cues=(("", "value"),),
    )
    clicks = comparison("클릭률", CLICKS)
    signups = comparison("가입률", SIGNUPS)
    takeaway = shot(
        "A", "클릭은 늘었지만 가입은 줄었어요. 목표가 가입이라면 가입률까지 확인하세요.",
        "목표에 맞는 결과 확인",
        one("이 실험의 목표", "가입 완료", "클릭률은 중간 과정에 대한 단서"),
        cues=(("", "value"),),
    )
    short = [question, clicks, signups, takeaway]
    long = [question, denominator, clicks, signups, takeaway]
    yield 11, ("클릭이 늘면", "가입도 늘까?"), short, long
~~~

`yield`에는 **회차 번호, 숏폼 표지 두 줄, 숏폼 장면, 롱폼 장면**을 순서대로 넣습니다. `("", "first")`는 장면 시작에 첫 카드를 강조하고 `("새 화면은", "second")`는 음성이 그 문구에 도달할 때 두 번째 카드를 강조합니다. 강조 문구는 실제 대사에 있어야 하며, 같은 장면에서는 말하는 순서대로 둡니다.

점 도표는 이 예제처럼 대본 파일에서 데이터를 지정합니다. 축, 구간, 기준선이 필요한 새 도표는 [figures_06_10.py](figures_06_10.py)의 `plot()`과 `KINDS`를 참고해 도형을 추가하고, 대본의 `chart(..., kind, ...)`에 같은 이름을 넣습니다. `plot()`이 호출하는 도표 함수가 반환하는 강조 영역 이름은 대본의 강조 이름과 일치해야 합니다. 배치와 단위는 가로와 세로 모두에서 확인합니다.

### 2. 새 회차 묶음 등록

[make_videos.py](make_videos.py) 상단의 다른 회차 가져오기 옆에 아래 한 줄을 추가합니다.

~~~python
from storyboards_11_plus import lessons as later_lessons
~~~

같은 파일의 `main()`에서 `batches = ...`와 바로 뒤의 회차 검사 부분을 다음 코드로 바꿉니다.

~~~python
    batches = {"2-3": episodes, "4-5": next_episodes, "6-10": lessons, "11+": later_lessons}
    if selection not in batches:
        raise ValueError(f"회차 묶음은 {', '.join(batches)} 중 하나로 지정하세요.")
~~~

나중에 12화부터는 같은 `storyboards_11_plus.py`의 `lessons()`에 새 `yield`를 추가하고 아래 명령에서 회차 번호를 바꿉니다.

### 3. 롱폼과 숏폼 렌더링

앞 절에서 설치를 마친 뒤 `video-production/`에서 실행합니다.

~~~powershell
.\.venv\Scripts\python make_videos.py renders-ep11-review-v01 '11+' 11
~~~

`renders-ep11-review-v01/`에 `ep11-long.mp4`와 `ep11-short.mp4`가 생성됩니다. 각각 같은 이름의 `.srt`와 `.json`으로 자막과 강조 시각을 확인할 수 있습니다. 숏폼만 다시 만들 때는 새 출력 폴더 이름을 쓰고 명령 끝에 `--short-only`를 붙입니다. 첫 1.2초 표지 위에서 B의 질문이 들리는지, 클릭률과 가입률을 말할 때 해당 카드가 강조되는지 확인합니다.

## 검수와 보관

- ffprobe로 크기와 오디오를 확인하고, MP4와 자막 SRT, 장면 JSON을 대조합니다. 휴대폰 폭에서 제목, 축 단위, 기준선, 자막을 확인하고 숏폼 표지 1.2초 동안 첫 대사가 들리는지 확인합니다.
- 렌더링 결과와 음성 캐시는 로컬에 생성됩니다. 승인한 영상은 기존 비공개 Drive 보관함에서 관리합니다. 이 코드의 실행 범위는 로컬 파일 생성까지입니다.
- Git 기록은 제작 코드를 다룹니다. 기존 영상의 완성 MP4, 음성 캐시, 캐릭터 원본, Drive 주소는 각 보관 위치에서 관리합니다.
