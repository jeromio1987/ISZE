# -*- coding: utf-8 -*-
"""Israel: prove HTML scrape yields structured notices with deadline."""
import re
import sys

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Live search filtered to vehicle keyword
url = "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&q=%D7%A8%D7%9B%D7%91"
r = s.get(url, timeout=60)
print("status", r.status_code, "bytes", len(r.content), "ct", r.headers.get("Content-Type"))
soup = BeautifulSoup(r.text, "html.parser")
print("title", soup.title.string if soup.title else None)

containers = soup.select(".result-container")
print("result-container count", len(containers))

notices = []
for box in containers:
    a = box.select_one("a[href*='/p/']")
    title = a.get_text(" ", strip=True) if a else ""
    href = a["href"] if a else ""
    if href.startswith("/"):
        href = "https://mr.gov.il" + href
    text = box.get_text("\n", strip=True)
    # deadline patterns
    deadline = None
    for pat in [
        r"מועד אחרון[^\n]*?(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"תאריך אחרון[^\n]*?(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"(\d{1,2}[./]\d{1,2}[./]\d{4})",
    ]:
        m = re.search(pat, text)
        if m:
            deadline = m.group(1) if m.lastindex else m.group(0)
            break
    # publish date near "פורסם"
    pub = None
    m = re.search(r"פורסם[^\n]*?(\d{1,2}[./]\d{1,2}[./]\d{2,4})", text)
    if m:
        pub = m.group(1)
    notices.append({"title": title, "link": href, "deadline": deadline, "pub": pub, "raw_head": text[:250]})

for n in notices[:5]:
    print(n)

# Also show structure of first container HTML
if containers:
    print("\nFIRST HTML:\n", str(containers[0])[:1500])

# Autocomplete JSON (partial structured source)
ac = s.get(
    "https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox",
    params={"term": "רכב"},
    timeout=30,
)
print("\nAC", ac.status_code, ac.headers.get("Content-Type"), len(ac.content))
j = ac.json()
print("suggestions", j.get("suggestions", [])[:5])
print("products sample", (j.get("products") or [])[:3])
