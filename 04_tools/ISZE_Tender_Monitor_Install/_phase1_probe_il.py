# -*- coding: utf-8 -*-
"""Israel: confirm datastore freshness + HTML scrape last-resort selectors."""
import json
import re
import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = "ISZE-Discovery/1.0"

RID = "7038b3e6-a74d-442e-b16b-466c8196124a"
url = "https://data.gov.il/api/3/action/datastore_search"

# SQL max date
sql = f'SELECT MAX("תאריך פרסום") as max_pub, MAX(_id) as max_id, COUNT(*) as n FROM "{RID}"'
r = s.get(
    "https://data.gov.il/api/3/action/datastore_search_sql",
    params={"sql": sql},
    timeout=60,
)
print("SQL aggregate", r.status_code)
print(json.dumps(r.json(), ensure_ascii=False)[:800])

sql2 = f'SELECT "סטטוס", COUNT(*) as n FROM "{RID}" GROUP BY "סטטוס" ORDER BY n DESC'
r = s.get(
    "https://data.gov.il/api/3/action/datastore_search_sql",
    params={"sql": sql2},
    timeout=60,
)
print("status counts", json.dumps(r.json(), ensure_ascii=False)[:1000])

# filters published + vehicle-ish
r = s.get(
    url,
    params={
        "resource_id": RID,
        "q": "רכב",
        "filters": json.dumps({"סטטוס": "פורסם"}, ensure_ascii=False),
        "limit": 5,
        "sort": "_id desc",
    },
    timeout=60,
)
j = r.json()["result"]
print("vehicle+published total", j["total"])
for rec in j["records"]:
    print(
        {
            "title": rec.get("שם הליך"),
            "link_hint": f"https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&q={rec.get('מספר פרסום')}",
            "deadline": rec.get("תאריך אחרון להגשת השגות"),
            "pub": rec.get("תאריך פרסום"),
            "status": rec.get("סטטוס"),
            "pub_no": rec.get("מספר פרסום"),
        }
    )

# HTML last resort
html_url = "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER"
r = s.get(html_url, timeout=60)
html = r.text
soup = BeautifulSoup(html, "html.parser")
print("\nHTML bytes", len(r.content), "title", soup.title.string if soup.title else None)

# candidate product containers
for sel in [
    ".product-item",
    ".product",
    ".search-result",
    ".tender",
    "li.product__list--item",
    ".product__list--item",
    "[class*=product]",
    ".searchPage",
    "#resultsList",
    ".results",
]:
    found = soup.select(sel)
    if found:
        print(f"SEL {sel}: {len(found)}")

# list all class names that look like product/result
classes = Counter()
for tag in soup.find_all(True):
    for c in tag.get("class") or []:
        if any(x in c.lower() for x in ("product", "result", "tender", "search", "item", "list")):
            classes[c] += 1
print("top classes", classes.most_common(30))

# links that look like tender detail
links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(" ", strip=True)
    if "/p/" in href or "tender" in href.lower() or "product" in href.lower():
        links.append((text[:80], href[:120]))
print("product-ish links", len(links))
for t, h in links[:8]:
    print(" ", t, "->", h)

# embedded JSON in script tags
for i, script in enumerate(soup.find_all("script")):
    txt = script.string or ""
    if not txt:
        continue
    if "tender" in txt.lower() or "product" in txt.lower() or "searchResult" in txt or "ACC" in txt:
        if len(txt) > 80:
            print(f"script[{i}] len={len(txt)} preview={txt[:200].replace(chr(10),' ')}")

# ACC / hybris search API common pattern
for api in [
    "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&q=%3A&pageSize=20&page=0",
    "https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox?term=%D7%A8%D7%9B%D7%91",
    "https://mr.gov.il/ilgstorefront/he/search/results?s=TENDER&q=%3Arelevance%3A",
]:
    rr = s.get(api, timeout=45, headers={"Accept": "application/json, text/html"})
    print("API try", api[-50:], rr.status_code, rr.headers.get("content-type"), len(rr.content), rr.text[:120].replace("\n", " "))
