# -*- coding: utf-8 -*-
"""
Every competitor evidence source on disk, what it can and cannot be joined on,
and the honest coverage that follows.

This exists because a join was proposed that cannot be made. The point of the
file is to stop that happening again: for each source, state the key it carries
and the question it can therefore answer.

Run: python 01_data/91_build/build_competitor_evidence_inventory.py
Writes: 01_data/00_derived/competitor_evidence_inventory.csv
        01_data/00_derived/competitor_evidence_inventory_meta.json
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
SNAP = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper\_snapshots\2026-09-15"

PN10 = re.compile(r"\b\d{10}\b")


def say(m=""):
    print(m)
    sys.stdout.flush()


rows = []


def add(source, path, exists, pn_key, geography, vehicle, vintage, n_rows, n_pn,
        can_answer, cannot_answer, notes):
    rows.append({
        "source": source, "path": path, "on_disk": exists,
        "part_number_key": pn_key, "geography": geography, "vehicle_scope": vehicle,
        "vintage": vintage, "rows": n_rows, "part_numbers": n_pn,
        "can_answer": can_answer, "cannot_answer": cannot_answer, "notes": notes,
    })


say("=" * 84)
say("COMPETITOR EVIDENCE INVENTORY")
say("=" * 84)
say()

# ---- 1. the same-shop listings, which is what the panel is built on
ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
domains = sorted({u.split("/")[2] for u in ks["ks_url"].dropna()})
add("Same-shop listings (KS)", "01_data/00_derived/iam_ks_price_gap.csv", True,
    "YES - 10-digit part number", f"ONE source, {len(domains)} domain: {domains[0]}",
    "not stated in the file", "scraped 2026-08-10, FX 1.17 as of 2026-05-01",
    len(ks), ks["pn"].nunique(),
    "which part numbers we sit above a real competitor on, and by how much",
    "any market comparison - one UK source is fanned across 18 market rows; "
    "no vehicle split; 83% of rows rest on a single price",
    "the db column repeats the same three numbers per part number. 374 rows "
    "reduce to 43 distinct facts")
say(f"  Same-shop listings        : {len(ks)} rows, {ks['pn'].nunique()} PNs, "
    f"{len(domains)} domain")

# ---- 2. the Israeli street source
a3 = pd.read_csv(os.path.join(SNAP, "auto365_results.csv"))
a3_pn = int(a3.astype(str).agg(" ".join, axis=1).apply(lambda s: bool(PN10.search(s))).sum())
add("Israeli street prices (Auto365)", "04_tools/autodoc_scraper/_snapshots/"
    "2026-09-15/auto365_results.csv", True,
    "NO - Hebrew product name only, no part number anywhere",
    "Israel only", "not stated; the range is older models (Sumo, Rodeo, Trooper, "
    "D-Max 2007-2012)", "scraped 2026-09-07",
    len(a3), 0,
    "the level of Israeli retail prices for the items it lists, by name",
    "ANY join to our part-number data - there is no shared key. A name match from "
    "Hebrew retail titles to 10-digit numbers would be a guess",
    f"PMS_Category is empty on all {len(a3)} rows. Median listed price EUR 120. "
    "Mostly lamps and body parts")
say(f"  Israeli street (Auto365)  : {len(a3)} rows, {a3_pn} rows carrying a part number")

# ---- 3. the network benchmark
eu = pd.read_csv(os.path.join(D, "eucon_price_gap.csv"), dtype=str)
add("Network benchmark (Eucon/PartsPool)", "01_data/00_derived/eucon_price_gap.csv", True,
    "YES - part number", "network level, built from a UK and IL survey",
    "not stated", "2023-24 UK survey and a 2026-03-29 PartsPool batch",
    len(eu), eu["pn"].nunique(),
    "a network-level check on a small set of comparable part numbers",
    "market-level or vehicle-level splits",
    "44 part numbers. Two vintages mixed in one file - label before quoting")
say(f"  Network benchmark         : {len(eu)} rows, {eu['pn'].nunique()} PNs")

# ---- 4. the Autodoc risk file
au = pd.read_csv(os.path.join(D, "competitiveness_autodoc_risk.csv"), dtype=str)
bad = int((au["autodoc_min_eur"].astype(str).str.strip() == "2.34").sum())
add("Marketplace extract (Autodoc)", "01_data/00_derived/"
    "competitiveness_autodoc_risk.csv", True,
    "YES - part number and cheapest BRAND name", "not stated", "not stated",
    "scrape frozen 2026-05-30, Cloudflare-blocked since",
    len(au), au["part_number"].nunique(),
    "WHICH competing brand is present on a part number, and its name",
    "the competitor PRICE - unusable",
    f"{bad} of {len(au)} rows carry the identical value 2.34 in the price column, "
    "so the ratio column is meaningless. Brand names only")
say(f"  Marketplace extract       : {len(au)} rows, {au['part_number'].nunique()} PNs, "
    f"{bad} rows with a corrupt price")

# ---- 5. the other scrapes
for f, label in (("ks_results.csv", "KS raw results"),
                 ("mekonomen_results.csv", "Mekonomen"),
                 ("tmc_results.csv", "TMC"),
                 ("tranzparts_results.csv", "Tranzparts")):
    p = os.path.join(SNAP, f)
    if not os.path.exists(p):
        continue
    x = pd.read_csv(p)
    cols = list(x.columns)
    has_pn = any("part" in c.lower() and "number" in c.lower() for c in cols) or \
        bool(x.astype(str).agg(" ".join, axis=1).apply(
            lambda s: bool(PN10.search(s))).any())
    add(label, f"04_tools/autodoc_scraper/_snapshots/2026-09-15/{f}", True,
        "YES" if has_pn else "NO - no part number",
        "not stated", "not stated", "snapshot 2026-09-15",
        len(x), x.shape[1] and int(x[cols[0]].nunique()),
        "category-level price context where a category column exists",
        "a part-number join unless a part number is present",
        f"columns: {', '.join(cols[:6])}")
    say(f"  {label:<25}: {len(x)} rows, part number present: {has_pn}")

say()
inv = pd.DataFrame(rows)
say("=" * 84)
say("WHAT THE INVENTORY SAYS")
say("=" * 84)
pn_capable = inv[inv["part_number_key"].str.startswith("YES")]
say(f"  sources on disk                          : {len(inv)}")
say(f"  sources that carry a part number key     : {len(pn_capable)}")
say(f"  sources with a real geography split      : 0")
say(f"  sources with a vehicle split             : 0")
say()
say("  So: two questions cannot be answered by anything on disk today.")
say("    Israel against the UK      - no source prices the same part in both places.")
say("    CV against LCV             - no source says which vehicle a part fits.")
say()
say("  And one join that looked obvious does not exist:")
say("    Auto365 (Israeli street) carries NO part number. It cannot be joined to")
say("    the panel at all. Matching its Hebrew product titles to 10-digit numbers")
say("    would be a guess, and a guess is worse than a stated gap.")
say()

inv.to_csv(os.path.join(D, "competitor_evidence_inventory.csv"), index=False)
meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "purpose": "state, per source, the key it carries and the question it can answer",
    "headline": {
        "sources": int(len(inv)),
        "with_part_number": int(len(pn_capable)),
        "with_geography": 0,
        "with_vehicle_split": 0,
        "ks_domains": len(domains),
        "auto365_rows_with_pn": a3_pn,
        "autodoc_rows_with_corrupt_price": bad,
    },
    "blocked_questions": [
        "Israel vs UK: no source prices the same part in both markets.",
        "CV vs LCV: no source states which vehicle a part number fits.",
        "The Auto365 join is impossible - the file has no part number.",
    ],
    "what_would_unblock": [
        "A competitor price per market for the same part number (local scrapes).",
        "The vehicle application per part number (EPC or catalogue figure).",
        "More than one competing listing per part (83% of current rows rest on one).",
        "A market-differentiated list on our side for PR00 - our list price is global today.",
    ],
}
with open(os.path.join(D, "competitor_evidence_inventory_meta.json"), "w",
          encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say(f"wrote competitor_evidence_inventory.csv ({len(inv)} sources)")
say("BUILD_OK")
