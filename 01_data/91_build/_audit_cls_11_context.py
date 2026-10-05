#!/usr/bin/env python3
"""Audit step 11: put euro + family + fleet on the air-filtration finding, and
check what EQ / peer-catalogue evidence is already on disk."""
from __future__ import annotations
import collections, csv, re
from pathlib import Path
import pandas as pd

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

# ---------------- customer code -> distributor label + fleet
lab, fleet = {}, {}
for r in csv.DictReader((D / "price_bp_weighted_compare_pn.csv").open(encoding="utf-8-sig", newline="")):
    c = (r.get("customer_code") or "").strip()
    if c:
        lab[c] = (r.get("gps_db_label") or r.get("distributor_code") or "").strip()
for r in csv.DictReader((D / "gps_spu_by_distributor.csv").open(encoding="utf-8-sig", newline="")):
    if (r.get("year") or "").strip() == "2025":
        dc = (r.get("distributor_code") or "").strip()
        try:
            fleet[dc] = float(r.get("uio_units") or 0)
        except ValueError:
            pass

rows = list(csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")))
AIRPAT = [r"\bFILTER; ?ACL\b", r"\bELEMENT; ?A[CI]L\b", r"ELEMENT; ?AIR CLEANER",
          r"FILTER; ?AIR CLEANER", r"\bAIR CLEANER ELEMENT\b", r"ELEMENT ASM; ?AIR"]
NOT = [r"\bCASE\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bBOLT\b", r"\bSEAL\b",
       r"\bGASKET\b", r"\bCLAMP\b", r"\bDUCT\b", r"\bHOSE\b", r"\bBODY\b", r"\bIND\b"]
air, mis = set(), set()
for r in rows:
    if r["node_present"] != "1" or not r["description"]:
        continue
    if any(re.search(p, r["description"]) for p in AIRPAT) and \
       not any(re.search(p, r["description"]) for p in NOT):
        air.add(r["pn"])
        if r["l3"] != "Air filter":
            mis.add(r["pn"])

df = pd.read_parquet(D / "sales_fact.parquet",
                     columns=["billing_date", "part_number", "sold_to_sap", "sold_to",
                              "net_sales_value", "billed_qty"])
dt = pd.to_datetime(df["billing_date"], errors="coerce")
w = df[(dt >= "2025-01-01") & (dt <= "2026-06-30")].copy()
w["pn"] = w["part_number"].astype(str).str.zfill(10)
w["code"] = w["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True)
sub = w[w["pn"].isin(air)].copy()
sub["mis"] = sub["pn"].isin(mis)

print("ENGINE AIR FILTRATION - euro, family and fleet together")
print("window 2025-01-01..2026-06-30 (18 months). Family = engine air-cleaner element.")
print(f"\n   {'market':<16} {'fleet 2025':>10} {'billed EUR':>12} {'units':>8} "
      f"{'EUR/truck':>10} {'units/truck':>12} {'misfiled %':>11}")
agg = sub.groupby("code").agg(
    eur=("net_sales_value", "sum"), units=("billed_qty", "sum")).reset_index()
agg["mis_eur"] = sub[sub["mis"]].groupby("code")["net_sales_value"].sum().reindex(agg["code"]).fillna(0).values
agg["label"] = agg["code"].map(lab).fillna("")
agg = agg.sort_values("eur", ascending=False)
tot_e = tot_u = 0.0
for _, r in agg.head(20).iterrows():
    dlab = r["label"] or r["code"]
    fl = fleet.get(dlab, 0)
    ept = f"{r['eur']/fl:.1f}" if fl else "no fleet"
    upt = f"{r['units']/fl:.3f}" if fl else "no fleet"
    print(f"   {dlab[:16]:<16} {(f'{fl:,.0f}' if fl else 'UNKNOWN'):>10} "
          f"{r['eur']:>12,.0f} {r['units']:>8,.0f} {ept:>10} {upt:>12} "
          f"{100*r['mis_eur']/r['eur']:>10.0f}%")
    tot_e += r["eur"]; tot_u += r["units"]
print(f"   {'NETWORK (top 20)':<16} {'163,459':>10} {tot_e:>12,.0f} {tot_u:>8,.0f} "
      f"{tot_e/163459:>10.1f} {tot_u/163459:>12.3f}")
print(f"\n   full window total: EUR {sub['net_sales_value'].sum():,.0f} on "
      f"{sub['billed_qty'].sum():,.0f} units across {sub['code'].nunique()} customers")
print(f"   of which misfiled out of the Filters family: EUR "
      f"{sub.loc[sub['mis'],'net_sales_value'].sum():,.0f} on "
      f"{sub.loc[sub['mis'],'billed_qty'].sum():,.0f} units")

# --------------------------------------------------- EQ / peer evidence on disk
print("\n" + "=" * 78)
print("EQ / PEER-CATALOGUE EVIDENCE ALREADY ON DISK")
p = D / "aim_gap_suggestions_20260702.csv"
g = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
print(f"\n  {p.name}: {len(g)} rows")
print(f"  eq_hit values: {dict(collections.Counter((r.get('eq_hit') or '').strip() for r in g))}")
print(f"  validated    : {dict(collections.Counter((r.get('validated') or '').strip() for r in g))}")
print(f"  confidence   : {dict(collections.Counter((r.get('confidence') or '').strip() for r in g))}")
print("\n  sample rows with an eq_hit:")
for r in [x for x in g if (x.get("eq_hit") or "").strip() not in ("", "0", "FALSE", "False")][:10]:
    print(f"    {r['pn']}  {r['description'][:34]:<34} eq_hit={r['eq_hit']!r:<8} "
          f"cur={r['current_l1']!r} -> sug={r['sug1_l1']!r}/{r['sug1_l2']!r} conf={r['confidence']}")

for name in ["competitiveness_autodoc_risk.csv", "iam_ks_price_gap.csv",
             "iam_mekonomen_price_gap.csv"]:
    q = D / name
    if not q.is_file():
        continue
    rr = list(csv.DictReader(q.open(encoding="utf-8-sig", newline="")))
    print(f"\n  {name}: {len(rr)} rows  cols={list(rr[0].keys())[:9]}")
