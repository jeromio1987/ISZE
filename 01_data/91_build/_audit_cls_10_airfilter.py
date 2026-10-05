#!/usr/bin/env python3
"""Audit step 10: what the air-filtration misfile actually costs us in reporting.

Two questions:
  1. How big is engine air filtration really, against the EUR 28,469 that the
     shipped catalogue note published as the whole network air-filter figure?
  2. Separate the genuinely WRONG (part is in the wrong system) from the merely
     INCONSISTENT (part is filed under the system it serves rather than under
     its object type). Those need different fixes and must not be added up.
"""
from __future__ import annotations
import collections, csv, re
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
rows = list(csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")))
for r in rows:
    r["eur"] = float(r["eur"] or 0)
    r["qty"] = float(r["qty"] or 0)
live = [r for r in rows if r["node_present"] == "1"]

print("=" * 78)
print("1. ENGINE AIR FILTRATION - WHERE IT ACTUALLY SITS")
print("   (18-month window 2025-01-01..2026-06-30, gross billed)")

# every part whose text says it is an air-cleaner element / engine air filter
AIRPAT = [r"\bFILTER; ?ACL\b", r"\bELEMENT; ?A[CI]L\b", r"ELEMENT; ?AIR CLEANER",
          r"FILTER; ?AIR CLEANER", r"\bAIR CLEANER ELEMENT\b", r"ELEMENT ASM; ?AIR"]
NOT = [r"\bCASE\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bBOLT\b", r"\bSEAL\b",
       r"\bGASKET\b", r"\bCLAMP\b", r"\bDUCT\b", r"\bHOSE\b", r"\bBODY\b", r"\bIND\b"]
air = [r for r in live
       if any(re.search(p, r["description"]) for p in AIRPAT)
       and not any(re.search(p, r["description"]) for p in NOT)]

g = collections.defaultdict(lambda: [0, 0.0, 0.0])
for r in air:
    k = f"{r['l1']} > {r['l2']} > {r['l3']}"
    g[k][0] += 1; g[k][1] += r["eur"]; g[k][2] += r["qty"]
print(f"\n   {len(air)} part numbers read as an engine air-cleaner element. They sit in:")
print(f"   {'node':<56} {'PNs':>5} {'billed EUR':>12} {'units':>9}")
for k, (n, e, q) in sorted(g.items(), key=lambda kv: -kv[1][1]):
    print(f"   {k:<56} {n:>5} {e:>12,.0f} {q:>9,.0f}")
te = sum(r["eur"] for r in air)
tq = sum(r["qty"] for r in air)
print(f"   {'TOTAL engine air filtration':<56} {len(air):>5} {te:>12,.0f} {tq:>9,.0f}")

inside = sum(e for k, (n, e, q) in g.items() if k.endswith("Air filter"))
print(f"\n   inside Competitive parts > Filters > Air filter : EUR {inside:,.0f}")
print(f"   outside it                                      : EUR {te-inside:,.0f}"
      f"  ({100*(te-inside)/te:.1f}% of engine air filtration)")
print(f"   -> the published network air-filter figure captures roughly "
      f"{100*inside/te:.0f}% of the category")

# cabin filters, for honesty: these genuinely belong to A/C
CAB = [r"FILTER; ?BLOWER", r"\bCABIN\b", r"FILTER; ?A/?C", r"POLLEN"]
cab = [r for r in live if any(re.search(p, r["description"]) for p in CAB)]
print(f"\n   for contrast, cabin / blower filtration (legitimately A/C): "
      f"{len(cab)} PNs, EUR {sum(r['eur'] for r in cab):,.0f}")

# per-market split of the misfiled air filtration
print("\n" + "=" * 78)
print("2. HOW THE MISFILE SPLITS BY DISTRIBUTOR  (needs the sales grain)")
import pandas as pd
sf = D / "sales_fact.parquet"
df = pd.read_parquet(sf, columns=["billing_date", "part_number", "sold_to", "net_sales_value", "billed_qty"])
dt = pd.to_datetime(df["billing_date"], errors="coerce")
w = df[(dt >= "2025-01-01") & (dt <= "2026-06-30")].copy()
w["pn"] = w["part_number"].astype(str).str.zfill(10)
airset = {r["pn"] for r in air}
misset = {r["pn"] for r in air if not f"{r['l1']} > {r['l2']} > {r['l3']}".endswith("Air filter")}
sub = w[w["pn"].isin(airset)].copy()
sub["misfiled"] = sub["pn"].isin(misset)
agg = sub.groupby("sold_to").apply(
    lambda x: pd.Series({
        "air_eur": x["net_sales_value"].sum(),
        "air_units": x["billed_qty"].sum(),
        "misfiled_eur": x.loc[x["misfiled"], "net_sales_value"].sum(),
    }), include_groups=False).sort_values("air_eur", ascending=False)
print(f"\n   {'customer':<44} {'air filt EUR':>13} {'units':>8} {'misfiled EUR':>13} {'%':>6}")
for k, r in agg.head(22).iterrows():
    pct = 100 * r["misfiled_eur"] / r["air_eur"] if r["air_eur"] else 0
    print(f"   {str(k)[:44]:<44} {r['air_eur']:>13,.0f} {r['air_units']:>8,.0f} "
          f"{r['misfiled_eur']:>13,.0f} {pct:>5.0f}%")

# ---------------------------------------------------------------- 3. classes
print("\n" + "=" * 78)
print("3. TWO DIFFERENT DEFECTS, NOT ONE NUMBER")
v = list(csv.DictReader((D / "_audit_cls_description_violations.csv").open(encoding="utf-8", newline="")))
WRONG_SYSTEM = {"air_filtration", "window_regulator", "king_pin", "ball_joint_arm",
                "steering_core", "bumper"}
OBJ_VS_SYS = {"gasket", "harness", "silencer", "brake_friction", "clutch_core",
              "turbo", "radiator_water_pump", "oil_filter", "fuel_filter", "lamp",
              "mirror", "injector", "shock_leaf", "starter_alt", "driveline", "ac_core"}
a = [x for x in v if x["rule"] in WRONG_SYSTEM]
b = [x for x in v if x["rule"] in OBJ_VS_SYS]
ea = sum(float(x["l12m_eur"]) for x in a)
eb = sum(float(x["l12m_eur"]) for x in b)
print(f"\n   (a) WRONG SYSTEM - the part is in a family it has no physical relation to")
print(f"       {len({x['part_number'] for x in a}):,} part numbers, EUR {ea:,.0f} billed")
for rid in sorted({x["rule"] for x in a}):
    s = [x for x in a if x["rule"] == rid]
    print(f"         {rid:<18} {len(s):>4} PNs  EUR {sum(float(x['l12m_eur']) for x in s):>10,.0f}")
print(f"\n   (b) OBJECT TYPE vs SYSTEM OF USE - defensible either way, but applied")
print(f"       inconsistently across the same tree")
print(f"       {len({x['part_number'] for x in b}):,} part numbers, EUR {eb:,.0f} billed")
for rid in sorted({x["rule"] for x in b}):
    s = [x for x in b if x["rule"] == rid]
    if s:
        print(f"         {rid:<18} {len(s):>4} PNs  EUR {sum(float(x['l12m_eur']) for x in s):>10,.0f}")
