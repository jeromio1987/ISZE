# -*- coding: utf-8 -*-
"""Parse saved KS search HTML for the 8-PN pilot. Read-only on ledger."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from site_ks import parse, ParseError  # noqa: E402

OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pilot_20261007"
PNS = [
    ("5876150170", "fuel_filter"),
    ("1876100934", "fuel_filter"),
    ("1876101132", "air_filter"),
    ("8975488420", "blower_filter"),
    ("8975425390", "fuel_filter"),
    ("8982120690", "clutch_disc"),
    ("8975056801", "brake_pad"),
    ("8978279610", "brake_pad"),
]

results = []
hashes: dict[str, list[str]] = {}
for pn, fam in PNS:
    path = OUT / f"search_{pn}.html"
    raw = path.read_bytes()
    h = hashlib.sha1(raw).hexdigest()[:12]
    hashes.setdefault(h, []).append(pn)
    html = raw.decode("utf-8", errors="replace")
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else "?"
    entry = {
        "part_no": pn,
        "family": fam,
        "bytes": len(raw),
        "sha1_12": h,
        "title": title[:160],
        "parse_error": None,
        "rows": [],
    }
    url = f"https://www.ks-international.com/catalogsearch/result/?q={pn}"
    try:
        rows = parse(html, source_url=url, observed_at="2026-10-07")
        for r in rows:
            entry["rows"].append(
                {
                    "match_method": r.get("match_method"),
                    "part_no": r.get("part_no"),
                    "price": r.get("price"),
                    "vat": r.get("vat"),
                    "competitor_pn": r.get("competitor_pn"),
                    "price_type": r.get("price_type"),
                    "stock": r.get("stock"),
                    "description": (r.get("description") or "")[:240],
                    "source_url": r.get("source_url"),
                }
            )
    except ParseError as e:
        entry["parse_error"] = str(e)
    results.append(entry)
    print("=" * 72)
    print(pn, fam, "bytes", len(raw), "hash", h)
    print(" title:", title[:120])
    if entry["parse_error"]:
        print(" PARSE:", entry["parse_error"])
    for r in entry["rows"]:
        print(
            " ROW",
            r["match_method"],
            "pn=",
            r["part_no"],
            "£",
            r["price"],
            "sku=",
            r["competitor_pn"],
        )
        print("  ", r["description"][:160])

print()
print("unique page hashes:", {k: v for k, v in hashes.items()})
accepted = [
    e
    for e in results
    if any(r["match_method"] == "exact_oem" for r in e["rows"])
]
rejected = [e for e in results if e not in accepted]
print("accepted_exact_oem_pns", len(accepted), [e["part_no"] for e in accepted])
print("rejected_pns", len(rejected), [e["part_no"] for e in rejected])

out_json = OUT / "pilot_parse_summary.json"
out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
print("wrote", out_json)
