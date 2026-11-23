"""Check rollout decisions against the normal local server in Chromium."""
import argparse
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import expect, sync_playwright


def verify(page, url):
    response = page.goto(url)
    assert response.ok
    page.locator("#rollout > summary").click()
    decision = page.locator("#rollout-decision")
    reasons = page.locator("#rollout-reasons")
    expect(decision).to_have_text("확대 보류")
    page.locator("#rollout-example").click()

    expect(decision).to_have_text("확대 보류")
    expect(reasons).to_contain_text("차이 +1.089%p, 보정 하한 +0.286%p / 최소 개선폭 +0.500%p")
    expect(reasons).to_contain_text("차이 +0.058%p, 95% 신뢰구간 상한 +0.265%p / 허용 상한 +0.200%p")
    expect(reasons).to_contain_text("센터 수용량 미확인")
    expect(reasons).to_contain_text("비용 미확인")

    visit = page.locator('[name="visit-b"]')
    optout = page.locator('[name="optout-b"]')
    capacity = page.locator('[name="capacity"]')
    cost = page.locator('[name="cost"]')
    visit.fill("1680")
    expect(reasons.locator("li").nth(0)).to_have_text(
        "충족 — 방문 완료율 차이 +1.621%p, 보정 하한 +0.808%p / 최소 개선폭 +0.500%p"
    )
    optout.fill("120")
    expect(reasons.locator("li").nth(1)).to_have_text(
        "충족 — 수신 철회율 차이 -0.064%p, 95% 신뢰구간 상한 +0.135%p / 허용 상한 +0.200%p"
    )
    expect(decision).to_have_text("확대 보류")
    capacity.select_option("ready")
    expect(decision).to_have_text("확대 보류")
    cost.select_option("ready")
    expect(decision).to_have_text("확대 검토 가능")
    capacity.select_option("unknown")
    expect(decision).to_have_text("확대 보류")
    capacity.select_option("blocked")
    expect(reasons).to_contain_text("센터 수용량 조건 미충족")
    capacity.select_option("ready")
    page.locator('[name="design-confirmed"]').uncheck()
    expect(decision).to_have_text("확대 보류")
    page.locator('[name="design-confirmed"]').check()

    for selector, invalid, valid in [
        ('[name="visit-min"]', "0.90", "0.50"),
        ('[name="optout-max"]', "0.10", "0.20"),
        ('[name="visit-b"]', "15604", "1680"),
        ('[name="optout-b"]', "", "120"),
    ]:
        field = page.locator(selector)
        field.fill(invalid)
        expect(decision).to_have_text("확대 보류")
        field.fill(valid)
        expect(decision).to_have_text("확대 검토 가능")

    visit.fill("1450")
    expect(decision).to_have_text("확대 보류")
    expect(reasons).to_contain_text("차이 +0.147%p, 보정 하한 -0.639%p")
    page.locator('[name="comparison"]').select_option("single")
    expect(reasons).to_contain_text("95% 신뢰구간 하한")
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--browser")
    args = parser.parse_args()
    with subprocess.Popen(
        [sys.executable, str(args.app.resolve() / "server.py")],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ) as server:
        try:
            startup = server.stdout.readline().strip()
            assert startup.startswith("AB_LOCAL_URL="), startup
            url = startup.split("=", 1)[1]
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.browser)
                for width in (1440, 375):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    verify(page, url)
                    page.close()
                    print(f"PASS {width}px")
                browser.close()
        finally:
            server.terminate()
