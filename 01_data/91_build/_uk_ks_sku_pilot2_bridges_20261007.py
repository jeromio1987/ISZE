# -*- coding: utf-8 -*-
"""Pick up to 20 untried competitor SKUs for KS SKU pilot2. No invent."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_sku_pilot2_20261007"
OUT.mkdir(parents=True, exist_ok=True)

EXCL_PNS = {
    "5876150170",
    "1876100934",
    "1876101132",
    "8975488420",
    "8975425390",
    "8982120690",
    "8975056801",
    "8978279610",
}
TIER_RANK = {
    "confirmed": 0,
    "likely": 1,
    "doubtful": 2,
    "reject": 3,
    "ungraded": 4,
    "unknown": 5,
}


def norm(s: str | None) -> str:
    return (s or "").strip()


def compact(s: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s or "").upper()


def is_own(brand: str) -> bool:
    b = brand.upper()
    return (
        "OUR OWN" in b
        or b in {"ISUZU", "ISUZU (OUR OWN NUMBER)", "OUR OWN NUMBER"}
        or b.startswith("ISUZU")
    )


def fam_ok(text: str) -> bool:
    t = (text or "").lower()
    return any(
        k in t
        for k in (
            "filter",
            "clutch",
            "exhaust",
            "muffler",
            "silencer",
            "pipe; exh",
            "tail pipe",
            "pipe exh",
        )
    )


tried: set[str] = set()
q1 = ROOT / "01_data/90_INBOX/_uk_ks_sku_pilot_20261007/sku_search_queue_20261007.csv"
with q1.open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = compact(r["sku"])
        if c:
            tried.add(c)

fs = ROOT / "01_data/90_INBOX/_uk_ks_sku_pilot_20261007/sku_pilot_fetch_summary_20261007.json"
if fs.exists():
    d = json.loads(fs.read_text(encoding="utf-8"))
    for r in d.get("results", []):
        c = compact(r.get("sku"))
        if c:
            tried.add(c)

pn_meta: dict[str, dict] = {}
h2 = json.loads(
    (
        ROOT
        / "01_data/90_INBOX/_uk_ks_filter_clutch_harvest2_20261007/harvest2_pn_queue_20261007.json"
    ).read_text(encoding="utf-8")
)
for i, r in enumerate(h2):
    pn = r["part_no"]
    if pn in EXCL_PNS:
        continue
    pn_meta[pn] = {
        "family": r["family"],
        "eur": float(r.get("eur_all_billed") or 0),
        "prio": i,
    }

exh = ROOT / "01_data/90_INBOX/_uk_ks_exhaust_harvest_20261007/shortlist_exhaust_20261007.csv"
with exh.open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pn = norm(r["part_number"])
        if not pn or pn in EXCL_PNS:
            continue
        if pn not in pn_meta:
            pn_meta[pn] = {
                "family": "exhaust",
                "eur": float(r.get("eur_proxy") or 0),
                "prio": 100 + int(r.get("rank") or 99),
                "description": norm(r.get("description")),
            }

fam_map: dict[str, str] = {}
iam = ROOT / "01_data/00_derived/iam_ks_price_gap.csv"
if iam.exists():
    with iam.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = norm(r.get("pn"))
            desc = norm(r.get("description"))
            if pn and pn not in EXCL_PNS and fam_ok(desc):
                if pn not in pn_meta:
                    pn_meta[pn] = {
                        "family": desc[:48],
                        "eur": float(r.get("isze_price_eur") or 0),
                        "prio": 500,
                    }
                fam_map[pn] = desc

bridges: dict[str, list[dict]] = defaultdict(list)
with (ROOT / "04_tools/aftermarket_intelligence/state/crossref_graded.csv").open(
    encoding="utf-8", newline=""
) as f:
    for r in csv.DictReader(f):
        pn = norm(r.get("part_no"))
        if not pn or pn in EXCL_PNS:
            continue
        cpn = norm(r.get("competitor_pn"))
        brand = norm(r.get("competitor_brand"))
        if not cpn or compact(cpn) in tried or is_own(brand):
            continue
        if compact(cpn) == compact(pn):
            continue
        bridges[pn].append(
            {
                "source": "crossref_graded",
                "tier": norm(r.get("tier")) or "unknown",
                "brand": brand,
                "sku": cpn,
            }
        )

spn = ROOT / "04_tools/aftermarket_intelligence/state/crossref_spareto_new_edges.csv"
if spn.exists():
    with spn.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = norm(r.get("part_no"))
            if not pn or pn in EXCL_PNS:
                continue
            cpn = norm(r.get("competitor_pn"))
            brand = norm(r.get("competitor_brand"))
            if not cpn or compact(cpn) in tried or is_own(brand):
                continue
            bridges[pn].append(
                {
                    "source": "crossref_spareto_new_edges",
                    "tier": norm(r.get("tier")) or "doubtful",
                    "brand": brand,
                    "sku": cpn,
                }
            )

with (ROOT / "04_tools/aftermarket_intelligence/state/crossref_edges.csv").open(
    encoding="utf-8", newline=""
) as f:
    for r in csv.DictReader(f):
        pn = norm(r.get("part_no"))
        if not pn or pn in EXCL_PNS:
            continue
        if bridges.get(pn):
            continue
        cpn = norm(r.get("competitor_pn"))
        brand = norm(r.get("competitor_brand"))
        if not cpn or compact(cpn) in tried or is_own(brand):
            continue
        bridges[pn].append(
            {
                "source": "crossref_edges_ungraded",
                "tier": "ungraded",
                "brand": brand,
                "sku": cpn,
            }
        )

cand: list[dict] = []
for pn, rows in bridges.items():
    meta = pn_meta.get(pn)
    if not meta:
        continue
    if not fam_ok(meta["family"]) and not fam_ok(fam_map.get(pn, "")) and not fam_ok(
        meta.get("description", "")
    ):
        continue
    by: dict[str, dict] = {}
    for r in rows:
        c = compact(r["sku"])
        if not c or c in tried:
            continue
        prev = by.get(c)
        if prev is None or TIER_RANK.get(r["tier"], 9) < TIER_RANK.get(prev["tier"], 9):
            by[c] = {
                **r,
                "part_no": pn,
                "family": meta["family"],
                "eur": meta["eur"],
                "prio": meta["prio"],
            }
    usable = [v for v in by.values() if v["tier"] in ("confirmed", "likely")]
    fallback = sorted(by.values(), key=lambda x: TIER_RANK.get(x["tier"], 9))
    pool = usable if usable else fallback[:5]
    cand.extend(pool)

cand.sort(key=lambda x: (TIER_RANK.get(x["tier"], 9), x["prio"], -x["eur"]))
pick: list[dict] = []
seen: set[str] = set()
pn_n: dict[str, int] = defaultdict(int)
for r in cand:
    c = compact(r["sku"])
    if c in seen:
        continue
    if pn_n[r["part_no"]] >= 2:
        continue
    seen.add(c)
    pn_n[r["part_no"]] += 1
    pick.append(r)
    if len(pick) >= 20:
        break
if len(pick) < 20:
    for r in cand:
        c = compact(r["sku"])
        if c in seen:
            continue
        if pn_n[r["part_no"]] >= 4:
            continue
        seen.add(c)
        pn_n[r["part_no"]] += 1
        pick.append(r)
        if len(pick) >= 20:
            break
if len(pick) < 20:
    for r in cand:
        c = compact(r["sku"])
        if c in seen:
            continue
        seen.add(c)
        pick.append(r)
        if len(pick) >= 20:
            break

queue = [
    {
        "part_no": p["part_no"],
        "family": p["family"],
        "sku": p["sku"],
        "brand": p["brand"],
        "tier": p["tier"],
        "source": p["source"],
        "eur": p["eur"],
    }
    for p in pick
]
out = {
    "excl_pilot1_pns": sorted(EXCL_PNS),
    "tried_compact_skus_pilot1": len(tried),
    "n_candidate_rows": len(cand),
    "n_picked": len(pick),
    "search_queue": queue,
    "by_pn": {pn: n for pn, n in sorted(pn_n.items())},
}
(OUT / "sku_bridges_pilot2_20261007.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
with (OUT / "sku_search_queue_pilot2_20261007.csv").open(
    "w", encoding="utf-8", newline=""
) as f:
    w = csv.DictWriter(
        f, fieldnames=["part_no", "family", "sku", "brand", "tier", "source", "eur"]
    )
    w.writeheader()
    w.writerows(queue)

print("tried_pilot1", len(tried))
print("pn_meta", len(pn_meta), "bridges_pns", len(bridges), "cand", len(cand))
print("PICK", len(pick))
for p in pick:
    print(
        p["part_no"],
        p["family"],
        p["tier"],
        p["brand"],
        p["sku"],
        p["source"],
        round(p["eur"]),
    )
print("wrote", OUT)
