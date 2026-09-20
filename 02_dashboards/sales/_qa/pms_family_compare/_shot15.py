from pathlib import Path
import json
import re
from playwright.sync_api import sync_playwright

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_PMS_Family_Compare.html")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa\pms_family_compare")
qa.mkdir(parents=True, exist_ok=True)
print("html", html.stat().st_size)
t = html.read_text(encoding="utf-8")
assert "cdn.jsdelivr" not in t.lower()
assert "NaN" not in t
assert "bar-row" in t
m = re.search(r'id="payload">(.*?)</script>', t, re.S)
P = json.loads(m.group(1))
print("questions", len(P["questions"]), [q["id"] for q in P["questions"]])
chrome = Path(r"C:\Users\jerom\AppData\Local\Google\Chrome\Application\chrome.exe")
if not chrome.exists():
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
shots = ["spend_pu", "residual", "fleet", "basket", "bvp_two", "bvp_contest", "warranty"]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=str(chrome), headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1600})
    page.goto(html.as_uri(), wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.screenshot(path=str(qa / "full_1440.png"), full_page=False)
    for qid in shots:
        page.select_option("#q", qid)
        page.wait_for_timeout(300)
        page.screenshot(path=str(qa / f"q_{qid}.png"), full_page=False)
    page.set_viewport_size({"width": 390, "height": 2000})
    page.select_option("#q", "spend_pu")
    page.wait_for_timeout(250)
    page.screenshot(path=str(qa / "full_390.png"), full_page=False)
    page.set_viewport_size({"width": 1024, "height": 1600})
    page.screenshot(path=str(qa / "full_1024.png"), full_page=False)
    browser.close()
print("shots ok")
