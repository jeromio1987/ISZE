# -*- coding: utf-8 -*-
"""Extract competitor/OE SKU bridges for the 8-PN KS SKU pilot. No invent."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_sku_pilot_20261007"
OUT.mkdir(parents=True, exist_ok=True)

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
OWN = {p for p, _ in PNS}
TIER_RANK = {"confirmed": 0, "likely": 1, "doubtful": 2, "reject": 3}


def norm(s: str | None) -> str:
    return (s or "").strip()


def is_own_brand(brand: str) -> bool:
    b = brand.upper()
    return (
        "OUR OWN" in b
        or b in {"ISUZU", "ISUZU (OUR OWN NUMBER)", "OUR OWN NUMBER"}
        or b.startswith("ISUZU")
    )


bridges: dict[str, list[dict]] = defaultdict(list)

# 1) graded edges
graded = ROOT / "04_tools/aftermarket_intelligence/state/crossref_graded.csv"
with graded.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = norm(r.get("part_no"))
        if pn not in OWN:
            continue
        cpn = norm(r.get("competitor_pn"))
        brand = norm(r.get("competitor_brand"))
        if not cpn or cpn in OWN or is_own_brand(brand):
            continue
        bridges[pn].append(
            {
                "source": "crossref_graded",
                "tier": norm(r.get("tier")) or "unknown",
                "brand": brand,
                "sku": cpn,
                "edge_origin": norm(r.get("edge_origin")),
                "spareto_pair": norm(r.get("spareto_pair")),
            }
        )

# 2) spareto new edges (if any of our PNs)
spareto_new = ROOT / "04_tools/aftermarket_intelligence/state/crossref_spareto_new_edges.csv"
if spareto_new.exists():
    with spareto_new.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = norm(r.get("part_no"))
            if pn not in OWN:
                continue
            cpn = norm(r.get("competitor_pn"))
            brand = norm(r.get("competitor_brand"))
            if not cpn or cpn in OWN or is_own_brand(brand):
                continue
            bridges[pn].append(
                {
                    "source": "crossref_spareto_new_edges",
                    "tier": norm(r.get("tier")) or "doubtful",
                    "brand": brand,
                    "sku": cpn,
                    "edge_origin": "spareto_only",
                    "spareto_pair": "True",
                }
            )

# 3) spareto_crossref.csv — column names vary; collect any hit
spareto = ROOT / "04_tools/aftermarket_intelligence/state/spareto_crossref.csv"
spareto_cols: list[str] = []
if spareto.exists():
    with spareto.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        spareto_cols = list(reader.fieldnames or [])
        pn_keys = [k for k in spareto_cols if k.lower() in ("part_no", "oe_pn", "isuzu_pn", "oem_pn")]
        sku_keys = [
            k
            for k in spareto_cols
            if k.lower()
            in ("competitor_pn", "iam_pn", "sku", "brand_pn", "replacement_pn", "alt_pn")
        ]
        brand_keys = [k for k in spareto_cols if "brand" in k.lower()]
        for r in reader:
            pn = ""
            for k in pn_keys:
                pn = norm(r.get(k))
                if pn:
                    break
            if pn not in OWN:
                # also scan all values for exact PN match as OE
                vals = [norm(v) for v in r.values()]
                if not any(v in OWN for v in vals):
                    continue
                for v in vals:
                    if v in OWN:
                        pn = v
                        break
            cpn = ""
            for k in sku_keys:
                cpn = norm(r.get(k))
                if cpn and cpn not in OWN:
                    break
            if not cpn:
                continue
            brand = ""
            for k in brand_keys:
                brand = norm(r.get(k))
                if brand:
                    break
            if is_own_brand(brand):
                continue
            bridges[pn].append(
                {
                    "source": "spareto_crossref",
                    "tier": "doubtful",
                    "brand": brand,
                    "sku": cpn,
                    "edge_origin": "spareto",
                    "spareto_pair": "True",
                }
            )

# 4) oe_bridge_coverage — note presence only
oe_hits: dict[str, dict] = {}
oe = ROOT / "01_data/00_derived/oe_bridge_coverage.csv"
if oe.exists():
    with oe.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = norm(r.get("part_no") or r.get("pn"))
            if pn in OWN:
                oe_hits[pn] = dict(r)

# 5) iam_ks — note if PN appears (SKU columns if any)
iam_hits: dict[str, list[dict]] = defaultdict(list)
iam = ROOT / "01_data/00_derived/iam_ks_price_gap.csv"
if iam.exists():
    with iam.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = norm(r.get("part_no") or r.get("pn"))
            if pn in OWN:
                iam_hits[pn].append({k: r[k] for k in list(r)[:12]})

# 6) edges.csv fallback (ungraded) — only if graded empty for a PN
edges = ROOT / "04_tools/aftermarket_intelligence/state/crossref_edges.csv"
with edges.open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        pn = norm(r.get("part_no"))
        if pn not in OWN:
            continue
        if bridges.get(pn):
            continue  # already have graded
        cpn = norm(r.get("competitor_pn"))
        brand = norm(r.get("competitor_brand"))
        if not cpn or cpn in OWN or is_own_brand(brand):
            continue
        bridges[pn].append(
            {
                "source": "crossref_edges_ungraded",
                "tier": "ungraded",
                "brand": brand,
                "sku": cpn,
                "edge_origin": "eucon_edge",
                "spareto_pair": "",
            }
        )

summary = []
search_queue = []  # (isuzu_pn, family, sku, brand, tier, source)

for pn, fam in PNS:
    rows = bridges.get(pn, [])
    by_sku: dict[str, dict] = {}
    for r in rows:
        sku = r["sku"]
        prev = by_sku.get(sku)
        rank = TIER_RANK.get(r["tier"], 9)
        if prev is None or rank < TIER_RANK.get(prev["tier"], 9):
            by_sku[sku] = r

    usable = [v for v in by_sku.values() if v["tier"] in ("confirmed", "likely")]
    # Prefer usable; if none, still record all but do NOT invent — for KS we try
    # confirmed/likely first; if only doubtful, try up to 5 distinct SKUs so the
    # pilot can honestly say "bridge on disk, KS miss" vs "no bridge".
    candidates = usable if usable else sorted(
        by_sku.values(), key=lambda x: TIER_RANK.get(x["tier"], 9)
    )[:5]

    entry = {
        "part_no": pn,
        "family": fam,
        "n_unique_skus": len(by_sku),
        "n_usable_confirmed_likely": len(usable),
        "oe_bridge_row": pn in oe_hits,
        "iam_ks_rows": len(iam_hits.get(pn, [])),
        "bridge_status": "no_SKU_bridge" if not by_sku else "has_bridge",
        "skus": [
            {
                "sku": v["sku"],
                "brand": v["brand"],
                "tier": v["tier"],
                "source": v["source"],
                "edge_origin": v["edge_origin"],
            }
            for v in sorted(by_sku.values(), key=lambda x: TIER_RANK.get(x["tier"], 9))
        ],
        "ks_search_candidates": [
            {
                "sku": v["sku"],
                "brand": v["brand"],
                "tier": v["tier"],
                "source": v["source"],
            }
            for v in candidates
        ],
    }
    summary.append(entry)

    for v in candidates:
        search_queue.append(
            {
                "part_no": pn,
                "family": fam,
                "sku": v["sku"],
                "brand": v["brand"],
                "tier": v["tier"],
                "source": v["source"],
            }
        )

out_json = OUT / "sku_bridges_20261007.json"
out_json.write_text(json.dumps({"summary": summary, "search_queue": search_queue}, indent=2), encoding="utf-8")

# flat CSV of search queue
qpath = OUT / "sku_search_queue_20261007.csv"
with qpath.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["part_no", "family", "sku", "brand", "tier", "source"])
    w.writeheader()
    for row in search_queue:
        w.writerow(row)

print("spareto_cols", spareto_cols[:25])
print("search_queue_n", len(search_queue))
for e in summary:
    print(
        e["part_no"],
        e["family"],
        e["bridge_status"],
        "unique",
        e["n_unique_skus"],
        "usable",
        e["n_usable_confirmed_likely"],
        "candidates",
        len(e["ks_search_candidates"]),
    )
    for c in e["ks_search_candidates"][:8]:
        print("   ", c["tier"], c["brand"], c["sku"])
print("wrote", out_json)
print("wrote", qpath)
