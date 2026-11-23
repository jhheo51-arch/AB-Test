"""Check rollout decisions against the normal local server in Chromium."""
import argparse
import json
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


def verify_saved_report(page, url):
    page.goto(url)
    page.locator("#rollout > summary").click()
    page.locator("#rollout-example").click()
    original = page.locator("#rollout-reasons li").all_text_contents()
    with page.expect_download() as download:
        page.locator("#save-project").click()
    saved = download.value.path().read_bytes()
    project = json.loads(saved)
    assert project["version"] == 8 and project["cells"] == []
    rollout = project["rollout"]
    assert rollout["source"] == "synthetic" and rollout["decision"] == "hold"
    assert rollout["input"] == {
        "total-a": 15482, "visit-a": 1416, "optout-a": 129,
        "total-b": 15603, "visit-b": 1597, "optout-b": 139,
        "visit-min": 0.5, "optout-max": 0.2, "comparison": "three",
        "capacity": "unknown", "cost": "unknown", "design-confirmed": True,
    }
    assert [f'보류 — {check["reason"]}' for check in rollout["reasons"]] == original

    page.reload()
    share = page.locator('nav [data-view="share"]')
    expect(share).to_be_disabled()
    page.locator("#project-file").set_input_files(
        {"name": "revisit.json", "mimeType": "application/json", "buffer": saved}
    )
    expect(page.locator("#rollout-decision")).to_have_text("확대 보류")
    expect(page.locator("#rollout-reasons li")).to_have_text(original)
    share.click()
    expect(page.locator("#csv-share-options")).to_be_hidden()
    preview = page.locator("#report-preview")
    for expected in [
        "확대 보류", "가상 정기점검 사례", "A군: 배정 15,482명, 방문 완료 1,416명, 수신 철회 129명",
        "B군: 배정 15,603명, 방문 완료 1,597명, 수신 철회 139명", *original,
    ]:
        expect(preview).to_contain_text(expected)
    page.locator("#share-confirm").check()
    with page.expect_download() as download:
        page.locator("#export-report").click()
    exported = download.value.path().read_text(encoding="utf-8")
    assert all(expected in exported for expected in ["확대 보류", "15,603명", *original])
    page.evaluate("window.print = () => {}")
    page.locator("#print-report").click()
    expect(page.locator("#print-area")).to_contain_text(original[0], use_inner_text=False)

    page.locator('nav [data-view="input"]').click()
    page.locator('[name="visit-b"]').fill("1680")
    share.click()
    expect(page.locator("#share-confirm")).not_to_be_checked()
    expect(page.locator("#export-report")).to_be_disabled()
    expect(preview).to_contain_text("+1.621%p")
    expect(preview).not_to_contain_text("+1.089%p")

    page.locator('nav [data-view="input"]').click()
    page.locator("#data-text").fill("arm,success,total\nA,12,100\nB,20,100")
    page.locator("#prepare").click()
    expect(page.locator("#analysis-options")).to_be_visible()
    for condition in ("randomized", "independent", "mature", "fixed-stop"):
        page.locator(f"#{condition}").select_option("yes")
    page.locator("#confirm-input").check()
    page.locator("#analyze").click()
    expect(page.locator("#results-view")).to_be_visible()
    share.click()
    expect(page.locator("#csv-share-options")).to_be_visible()
    expect(preview).to_contain_text("전체 결과")
    expect(preview).to_contain_text("별도로 입력한 집계")
    expect(preview).to_contain_text("+1.621%p")

    # Restoring an older project must clear the previous project's rollout state.
    project["version"] = 7
    del project["rollout"]
    page.locator("#project-file").set_input_files({
        "name": "legacy.json", "mimeType": "application/json",
        "buffer": json.dumps(project).encode(),
    })
    expect(share).to_be_disabled()
    expect(page.locator('[name="visit-b"]')).to_have_value("")


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
                    page = browser.new_page(viewport={"width": width, "height": 900}, accept_downloads=True)
                    verify(page, url)
                    verify_saved_report(page, url)
                    page.close()
                    print(f"PASS {width}px")
                browser.close()
        finally:
            server.terminate()
