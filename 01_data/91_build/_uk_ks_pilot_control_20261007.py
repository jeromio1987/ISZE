# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from site_ks import parse, ParseError  # noqa: E402

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pilot_20261007"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

pn = "8974995480"
url = f"https://www.ks-international.com/catalogsearch/result/?q={pn}"
req = Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
with urlopen(req, timeout=45) as resp:
    data = resp.read()
path = OUT / f"_control_search_{pn}.html"
path.write_bytes(data)
html = data.decode("utf-8", errors="replace")
print("control bytes", len(data))
title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
print("title", re.sub(r"\s+", " ", title_m.group(1)) if title_m else None)
print("product-item substr", html.count("item product product-item"))
for pat in [
    r"We can.?t find products matching",
    r"Your search returned no results",
    r'class="message notice"',
    r"toolbar-number",
]:
    m = re.search(pat, html, re.I)
    print("pat", pat, "->", bool(m), (m.group(0)[:80] if m else ""))
try:
    rows = parse(html, source_url=url, observed_at="2026-10-07")
    print("ROWS", len(rows))
    for r in rows:
        print(r["match_method"], r["part_no"], r["price"], r.get("competitor_pn"), (r.get("description") or "")[:120])
except ParseError as e:
    print("PARSE", e)

p0 = (OUT / "search_5876150170.html").read_text(encoding="utf-8", errors="replace")
print("--- pilot0 empty markers ---")
for pat in [
    r"We can.?t find products matching",
    r"Your search returned no results",
    r'class="message notice"[^>]*>.*?</div>',
    r"toolbar-number",
]:
    m = re.search(pat, p0, re.I | re.S)
    print("pat", pat, "->", (m.group(0)[:160].replace("\n", " ") if m else None))
