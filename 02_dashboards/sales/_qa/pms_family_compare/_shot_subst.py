import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_PMS_Family_Compare.html")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa\pms_family_compare")
t = html.read_text(encoding="utf-8")
P = json.loads(re.search(r'id="payload">(.*?)</script>', t, re.S).group(1))
s = P["bvp_subst"]
print("CY net", [(x["label"], round(x["share"] * 100, 1) if x["share"] else None) for x in s["cy"]["network"]])
print("FY net", [(x["label"], round(x["share"] * 100, 1) if x["share"] else None) for x in s["fy"]["network"]])
print("FY dbs", len(s["fy"]["by_db"]), "CY dbs", len(s["cy"]["by_db"]))
print("UMI FY", s["fy"]["by_db"].get("UMI"))

chrome = Path(r"C:\Users\jerom\AppData\Local\Google\Chrome\Application\chrome.exe")
if not chrome.exists():
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=str(chrome), headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 1600})
    page.goto(html.as_uri(), wait_until="domcontentloaded")
    page.wait_for_timeout(400)
    page.select_option("#q", "bvp_subst")
    page.wait_for_timeout(350)
    page.screenshot(path=str(qa / "q_bvp_subst_net_cy.png"), full_page=False)
    page.select_option("#substDb", "ITUK")
    page.wait_for_timeout(300)
    page.screenshot(path=str(qa / "q_bvp_subst_ituk_cy.png"), full_page=False)
    page.select_option("#substPer", "fy")
    page.wait_for_timeout(300)
    page.screenshot(path=str(qa / "q_bvp_subst_ituk_fy.png"), full_page=False)
    page.select_option("#substDb", "NETWORK")
    page.wait_for_timeout(300)
    page.screenshot(path=str(qa / "q_bvp_subst_net_fy.png"), full_page=False)
    b.close()
print("shots ok")
