#!/usr/bin/env python3
"""Check Benelux duplication and recompute ranks on a de-duplicated network."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "01_data/08_Distributor/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html"
t = DASH.read_text(encoding="utf-8", errors="replace")
seg = t[t.find('"dealers":'):]
dealers, _ = json.JSONDecoder().raw_decode(seg[seg.find("["):])

ben = {d["name"] for d in dealers if d["country"] == "Benelux"}
be = {d["name"] for d in dealers if d["country"] == "Belgium"}
nl = {d["name"] for d in dealers if d["country"] == "Netherlands"}
print("Benelux", len(ben), "Belgium", len(be), "NL", len(nl))
print("Benelux subset of BE+NL:", ben <= (be | nl), " overlap:", len(ben & (be | nl)))
print("Benelux-only names:", sorted(ben - (be | nl))[:10])

# treat every dealer id as unique but drop Benelux rows when the name also
# exists under Belgium / Netherlands
drop = {d["id"] for d in dealers if d["country"] == "Benelux" and d["name"] in (be | nl)}
dedup = [d for d in dealers if d["id"] not in drop]
print("rows", len(dealers), "-> dedup", len(dedup))
scored = [d for d in dedup if d.get("total_pct") is not None]
print("scored dedup", len(scored))
order = sorted(scored, key=lambda d: -d["total_pct"])
rank = {d["id"]: i for i, d in enumerate(order, 1)}
net_avg = sum(d["total_pct"] for d in scored) / len(scored)
print(f"network avg {net_avg*100:.2f}%")
for n in ["AUTO RENO PA\u00c7OS FERREIRA", "ROLMAX", "AUTO INDUSTRIAL LEIRIA"]:
    d = next(x for x in scored if x["country"] == "Portugal" and x["name"] == n)
    print(f"{n:<28} {d['total_pct']*100:5.2f}%  global {rank[d['id']]:>3}/{len(scored)}"
          f"  = top {100*rank[d['id']]/len(scored):.1f}%")
