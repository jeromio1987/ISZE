import json
from pathlib import Path
from bs4 import BeautifulSoup

p = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings"
    r"\IML_ITUK_PMS\mp\JEROME_ONLY\KS_PMS_Parts_Overview_20260818.html"
)
html = p.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")
out = {
    "cover_n": len(soup.select("#conclusions ol li")),
    "cover0": soup.select_one("#conclusions ol li").get_text(" ", strip=True),
    "compare_n": len(soup.select("#compare tbody tr")),
    "ituk_only": len(soup.select(".gapcard.ituk .misslist li")),
    "isze_stack": len(soup.select(".gapcard.isze .misslist li")),
    "both": len(soup.select(".gapcard.both .chips a")),
    "fetch": "fetch(" in html,
    "rows": [],
}
for tr in soup.select("#compare tbody tr"):
    tds = tr.find_all("td")
    hrefs = [a.get("href") for a in tr.select("a[href]")]
    out["rows"].append({
        "fam": tds[0].get_text(strip=True),
        "eng": tds[1].get_text(strip=True),
        "offer": tds[2].get_text(" ", strip=True),
        "ks_g": tds[5].get_text(" ", strip=True),
        "ks_iam": tds[6].get_text(" ", strip=True),
        "n_href": len(hrefs),
        "hrefs_ok": all(h and h.startswith("https://www.ks-international.com") for h in hrefs),
    })
Path(__file__).with_name("_qa_overview.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("ok", out["cover_n"], out["compare_n"], out["ituk_only"], out["both"])
