import asyncio
import hashlib
import json
import math
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "episode.json").read_text(encoding="utf-8"))
test = DATA["experiment"]
a, b, n = (test[key] for key in ("conversions_a", "conversions_b", "visitors_per_group"))
joined = a + b
first_b, second_b = test["example_b"]
if not (0 <= a < b <= n and all(max(0, joined - n) <= count <= min(n, joined) for count in (first_b, second_b))):
    raise ValueError("두 그룹의 가입 완료 수 또는 재배정 예시를 확인하세요.")

probabilities = {
    2 * in_b - joined: math.comb(n, in_b) * math.comb(n, joined - in_b) / math.comb(2 * n, joined)
    for in_b in range(max(0, joined - n), min(n, joined) + 1)
}
tail = sum(p for gap, p in probabilities.items() if abs(gap) >= b - a)
if not math.isclose(sum(probabilities.values()), 1):
    raise ValueError("가능한 배정의 확률 합계가 1이 아닙니다.")

def number(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")

VALUES = dict(n=n, total=2*n, a=a, b=b, joined=joined, count_gap=b-a,
              rate_a=number(100*a/n), rate_b=number(100*b/n), gap=number(100*(b-a)/n),
              first_a=joined-first_b, first_b=first_b, second_a=joined-second_b,
              second_b=second_b, tail=round(tail*100))
CACHE = ROOT / ".voice-cache"
RATE = "-3%"
PITCH = {"A": "+0Hz", "B": "+14Hz", "해설": "-11Hz"}

def lines(version):
    return [(scene, speaker, template.format_map(VALUES)) for scene, speaker, template in DATA[version]]

def spoken(text):
    text = re.sub(r"\bA(?=[가-힣]|\b)", "에이", text)
    text = re.sub(r"\bB(?=[가-힣]|\b)", "비", text)
    text = text.replace("%포인트", " 퍼센트 포인트").replace("%", " 퍼센트")
    return " ".join(text.split())

def audio_path(speaker, text):
    key = hashlib.sha256(f"{DATA['voices'][speaker]}:{RATE}:{PITCH[speaker]}:{spoken(text)}".encode()).hexdigest()[:20]
    return CACHE / f"{key}.mp3"

async def synthesize(versions):
    await synthesize_lines(segment for version in versions for segment in lines(version))

async def synthesize_lines(segments):
    CACHE.mkdir(exist_ok=True)
    queue = {(speaker,text) for _, speaker,text in segments}
    limit = asyncio.Semaphore(4)

    async def save(speaker, text):
        out = audio_path(speaker, text)
        if out.exists() and out.stat().st_size > 1000:
            return
        async with limit:
            temp = out.with_suffix(".part")
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(spoken(text), DATA["voices"][speaker], rate=RATE, pitch=PITCH[speaker]).save(str(temp))
                    if temp.stat().st_size <= 1000:
                        raise RuntimeError("빈 음성 파일")
                    temp.replace(out)
                    return
                except Exception as error:
                    temp.unlink(missing_ok=True)
                    if attempt == 2:
                        raise RuntimeError(f"음성 생성 실패: {text}") from error
                    await asyncio.sleep(2 ** attempt)

    await asyncio.gather(*(save(speaker, text) for speaker, text in queue))
    print(f"음성 {len(queue)}개 확인", flush=True)

if __name__ == "__main__":
    asyncio.run(synthesize(("long", "short")))
