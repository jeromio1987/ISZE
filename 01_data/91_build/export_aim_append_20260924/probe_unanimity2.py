# -*- coding: utf-8 -*-
"""Read-only: unanimity of every attribute I would mirror, plus billing/jp-cache membership."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

PMS_L2 = {
    "Filters", "Brake parts", "Clutch parts", "Suspension", "Steering",
    "Cooling", "Exhaust", "Belts", "Fuel system", "Air system",
    "Starter / alternator", "Injectors", "Turbo",
    "Hydraulic / mechanical", "Transmission parts", "Engine parts",
}

pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in pns:
            info[r["pn"]] = r

# --- billing membership in sales_fact.parquet ---
import pandas as pd  # noqa: E402

sf = pd.read_parquet(D / "sales_fact.parquet", columns=["part_number"])
sfp = set(sf["part_number"].astype(str).str.strip())
print("sales_fact distinct PNs:", len(sfp))
print("of the 44 that appear in sales_fact:", sorted(set(pns) & sfp))

# --- jp cache membership ---
jp = {}
jp_path = D / "jp_codes_cache_20260920.csv"
if jp_path.exists():
    with jp_path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            jp[str(r.get("pn") or "").strip()] = r
print("jp cache PNs:", len(jp), "| of the 44 present:", sorted(set(pns) & set(jp)))

# --- catalogue-leaf unanimity per description from the classification overlay ---
C_cat = defaultdict(Counter)
C_dt = defaultdict(Counter)
C_core = defaultdict(Counter)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        dn = (r.get("description_norm") or "").strip()
        c = ((r.get("catalog_l1") or "").strip(), (r.get("catalog_l2") or "").strip(),
             (r.get("catalog_l3") or "").strip())
        if all(c):
            C_cat[dn][c] += 1
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        dn = (r.get("description") or "").strip()
        dt = (r.get("aim_demand_type") or "").strip()
        co = (r.get("aim_core_noncore") or "").strip()
        if dt and dt not in PH:
            C_dt[dn][dt] += 1
        if co and co not in PH:
            C_core[dn][co] += 1

print("\n--- per PN: is the catalogue leaf, demand type and core unanimous? ---")
not_uni = []
for pn in pns:
    desc = (info[pn]["Description"] or "").strip()
    cat = C_cat.get(desc, Counter())
    dt = C_dt.get(desc, Counter())
    co = C_core.get(desc, Counter())
    okc = len(cat) == 1 and sum(cat.values()) >= 3
    okd = len(dt) == 1 and sum(dt.values()) >= 3
    oko = len(co) == 1 and sum(co.values()) >= 3
    flag = "" if (okc and okd and oko) else "  <-- NOT UNANIMOUS"
    if flag:
        not_uni.append(pn)
    print(f"{pn} | {desc[:30]:30} | cat={cat.most_common(2)} dt={dt.most_common(2)} core={co.most_common(2)}{flag}")
print("\nnot unanimous:", not_uni)

print("\n--- fig_no/key_no from the row's own price extract, master convention check ---")
for pn in pns:
    fk = (info[pn]["fig_key"] or "").strip()
    fig_no, _, key_no = fk.partition("-")
    conv = f"{fig_no}-{key_no}" if key_no.isdigit() else ""
    print(f"{pn} | given fig_key {fk:8} -> fig_no {fig_no:4} key_no {key_no:5} -> master-convention fig_key {conv!r}")
