#!/usr/bin/env python3
"""Global standing for the three Portugal visit dealers, computed from the
2026-09-17 dealer-compare payload (all countries in one file)."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "01_data/08_Distributor/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html"

t = DASH.read_text(encoding="utf-8", errors="replace")
seg = t[t.find('"dealers":'):]
dealers, _ = json.JSONDecoder().raw_decode(seg[seg.find("["):])

print("dealers in payload:", len(dealers))
print("per country:", dict(Counter(d["country"] for d in dealers)))
scored = [d for d in dealers if d.get("total_pct") is not None]
print("scored:", len(scored), " totals_only:", sum(1 for d in scored if d.get("totals_only")))
print("built:", t[:2000][t[:2000].find("built_at"):][:60] if "built_at" in t[:4000] else "n/a")

order = sorted(scored, key=lambda d: -d["total_pct"])
for i, d in enumerate(order, 1):
    d["_rank"] = i
by_id = {d["id"]: d for d in order}

targets = [
    ("Portugal", "AUTO RENO PA\u00c7OS FERREIRA"),
    ("Portugal", "ROLMAX"),
    ("Portugal", "AUTO INDUSTRIAL LEIRIA"),
]
pt = [d for d in scored if d["country"] == "Portugal"]
pt.sort(key=lambda d: -d["total_pct"])
ptrank = {d["id"]: i for i, d in enumerate(pt, 1)}
pt_avg = sum(d["total_pct"] for d in pt) / len(pt)
net_avg = sum(d["total_pct"] for d in scored) / len(scored)

print(f"\nnetwork avg {net_avg*100:.2f}%   Portugal avg {pt_avg*100:.2f}%   N={len(scored)}")
for c, n in targets:
    d = by_id[f"{c}::{n}"]
    print(
        f"{n:<28} total {d['total_pct']*100:5.2f}%  global {d['_rank']:>3}/{len(scored)}"
        f"  country {ptrank[d['id']]:>2}/16  vs network {(d['total_pct']-net_avg)*100:+5.1f}pp"
        f"  vs Portugal {(d['total_pct']-pt_avg)*100:+5.1f}pp"
    )

print("\n=== neighbours around each (global order) ===")
for c, n in targets:
    d = by_id[f"{c}::{n}"]
    i = d["_rank"]
    print(f"--- {n}: #{i} {d['total_pct']*100:.2f}%")
    for j in range(max(1, i - 3), min(len(order), i + 3) + 1):
        x = order[j - 1]
        mark = "  <<<" if x["id"] == d["id"] else ""
        print(f"   {j:>3} {x['name'][:38]:<38} {x['total_pct']*100:5.2f}%  {x['country']}{mark}")

print("\n=== full Portugal order (17 Sep scores) ===")
for i, d in enumerate(pt, 1):
    g = d["_rank"]
    print(f"  {i:>2}. {d['name'][:30]:<30} {d['total_pct']*100:5.2f}%  global {g:>3}/{len(scored)}")
