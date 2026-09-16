#!/usr/bin/env python3
"""Parse AT USP tenderlist HTML + offenevergaben downloads for a free feed path."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
}
KEYWORDS_AT = [
    "lkw", "nkw", "nutzfahrzeug", "pritsche", "fahrgestell", "pickup", "pick-up",
    "transporter", "kastenwagen", "fahrzeug", "flotte", "instandhaltung",
    "reparatur", "ersatzteil", "werkstatt", "kipper", "lastwagen", "isuzu",
    "d-max", "dienstwagen", "betriebsfahrzeug",
]
# Transporter/Kastenwagen kept for keyword scan only — not-for-us gate drops panel vans later.

s = requests.Session()
s.headers.update(UA)
out = {"probed_at": datetime.now(timezone.utc).isoformat()}

url = "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist"
r = s.get(url, timeout=40)
print("tenderlist", r.status_code, len(r.content))
soup = BeautifulSoup(r.text, "html.parser")

# DataTables often embeds JSON in a script or loads via ajax — find ajax url
ajax_urls = re.findall(r"ajax\s*:\s*[\"']([^\"']+)[\"']", r.text, flags=re.I)
dt_urls = re.findall(r"[\"']([^\"']*tender[^\"']*)[\"']", r.text, flags=re.I)
out["ajax"] = list(dict.fromkeys(ajax_urls))[:20]
out["tender_refs"] = list(dict.fromkeys(dt_urls))[:40]
print("ajax", out["ajax"][:10])
print("tender_refs sample", out["tender_refs"][:15])

# Try POST/GET common DataTables endpoints
for path in out["ajax"][:5]:
    full = path if path.startswith("http") else "https://ausschreibungen.usp.gv.at" + (
        path if path.startswith("/") else "/" + path
    )
    try:
        rr = s.get(full, timeout=25)
        print(" ajax GET", rr.status_code, len(rr.content), full[:90], rr.headers.get("content-type", "")[:40])
        if "json" in (rr.headers.get("content-type") or ""):
            out["ajax_hit"] = {"url": full, "http": rr.status_code, "snip": rr.text[:300]}
    except Exception as e:
        print(" ajax ERR", e)

# Table rows on page (may be empty if JS-rendered)
rows = []
for tr in soup.select("table tbody tr"):
    cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
    if not cells:
        continue
    blob = " ".join(cells).lower()
    hit = any(k in blob for k in KEYWORDS_AT)
    link = None
    a = tr.find("a", href=True)
    if a:
        link = a["href"]
    rows.append({"cells": cells[:6], "hit": hit, "href": link})

out["html_rows"] = len(rows)
out["html_hits"] = sum(1 for x in rows if x["hit"])
print("html rows", len(rows), "keyword hits", out["html_hits"])
for x in rows[:5]:
    print(" ", x["hit"], (x["cells"][0] if x["cells"] else "")[:80])

# offenevergaben downloads
r2 = s.get("https://offenevergaben.at/downloads", timeout=30)
soup2 = BeautifulSoup(r2.text, "html.parser")
links = []
for a in soup2.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(" ", strip=True)
    if re.search(r"csv|json|zip|xml|download|export|tsv", href + " " + text, re.I):
        links.append({"href": href, "text": text[:80]})
out["ov_download_links"] = links
print("offenevergaben download links", len(links))
for L in links[:15]:
    print(" ", L)

# If CSV link, HEAD it
for L in links[:5]:
    href = L["href"]
    full = href if href.startswith("http") else "https://offenevergaben.at" + (
        href if href.startswith("/") else "/" + href
    )
    try:
        h = s.head(full, timeout=20, allow_redirects=True)
        print(" HEAD", h.status_code, h.headers.get("content-type"), h.headers.get("content-length"), full[:100])
    except Exception as e:
        # some servers reject HEAD
        try:
            g = s.get(full, timeout=20, stream=True)
            print(" GET", g.status_code, g.headers.get("content-type"), g.headers.get("content-length"), full[:100])
            g.close()
        except Exception as e2:
            print(" ERR", full[:80], e2)

Path("_overnight_at_tenderlist_parse.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_at_tenderlist_parse.json")
