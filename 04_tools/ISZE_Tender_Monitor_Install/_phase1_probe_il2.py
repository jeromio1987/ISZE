# -*- coding: utf-8 -*-
"""Israel HTML last-resort analysis (no SQL)."""
import json
import re
import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

RID = "7038b3e6-a74d-442e-b16b-466c8196124a"
# working datastore (confirmed earlier)
r = s.get(
    "https://data.gov.il/api/3/action/datastore_search",
    params={
        "resource_id": RID,
        "q": "רכב",
        "filters": json.dumps({"סטטוס": "פורסם"}, ensure_ascii=False),
        "limit": 3,
        "sort": "_id desc",
    },
    timeout=60,
)
print("CKAN vehicle+published", r.status_code, r.headers.get("content-type"), len(r.content))
j = r.json()["result"]
print("total", j["total"])
for rec in j["records"]:
    print(
        json.dumps(
            {
                "title": rec.get("שם הליך"),
                "deadline": rec.get("תאריך אחרון להגשת השגות"),
                "pub": rec.get("תאריך פרסום"),
                "status": rec.get("סטטוס"),
                "pub_no": rec.get("מספר פרסום"),
                "ministry": rec.get("שם המשרד"),
            },
            ensure_ascii=False,
        )
    )

html_url = "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER"
r = s.get(html_url, timeout=60)
html = r.text
soup = BeautifulSoup(html, "html.parser")
print("\nHTML", r.status_code, len(r.content), "title=", (soup.title.string if soup.title else None))

classes = Counter()
for tag in soup.find_all(True):
    for c in tag.get("class") or []:
        if any(x in c.lower() for x in ("product", "result", "tender", "search", "item", "list", "card")):
            classes[c] += 1
print("top classes", classes.most_common(40))

for sel in [
    ".product-item",
    ".product",
    "li.product__list--item",
    ".product__list--item",
    ".search-results",
    "#results-list",
    ".results-list",
    "[class*='product']",
    ".item__list--item",
]:
    n = len(soup.select(sel))
    if n:
        print(f"SEL {sel}: {n}")
        el = soup.select(sel)[0]
        print("  sample classes", el.get("class"))
        print("  text", el.get_text(" ", strip=True)[:160])
        a = el.find("a", href=True)
        if a:
            print("  href", a["href"][:120], "a_text", a.get_text(" ", strip=True)[:80])

# Hybris often embeds ACC.product or search results JSON
for script in soup.find_all("script"):
    txt = script.string or script.get_text() or ""
    if len(txt) < 40:
        continue
    if any(k in txt for k in ("ACC.", "searchResult", "productData", "tenders", "pagination", "results")):
        print("SCRIPT hit len", len(txt), "preview", txt[:220].replace("\n", " "))

# Try facet search URL patterns used by SAP Commerce
candidates = [
    "https://mr.gov.il/ilgstorefront/he/search/results?q=%3Arelevance%3A&s=TENDER&page=0",
    "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&q=%D7%A8%D7%9B%D7%91&page=0",
    "https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox?term=%D7%A8%D7%9B%D7%91",
]
for url in candidates:
    rr = s.get(url, timeout=45, headers={"Accept": "application/json, text/html, */*", "X-Requested-With": "XMLHttpRequest"})
    print("TRY", url[-70:], rr.status_code, rr.headers.get("content-type"), len(rr.content))
    print("  ", rr.text[:150].replace("\n", " "))

# Look for product detail URL pattern from HTML
links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(" ", strip=True)
    if "/p/" in href or "/tender" in href.lower():
        links.append((text[:100], href))
print("detail links", len(links))
for t, h in links[:10]:
    print(" ", t, "->", h)
