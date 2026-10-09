"""Verify the catalogue-category coverage figures for the scope addition."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
BO = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007" / "bo_overview" / "20261006_BO info VP 06-10-2026.xlsx"
AIM = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
FACT = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
OLD = ROOT / "01_data" / "00_derived" / "aim_pn_classification.csv.bak_pre_eq_20260917"

EXCLUDE = ("MIDI", "RUS", "KAZ", "CBC-TRANS", "GRAND AVTO", "KOMTRANS", "KIMA")


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


aim = pd.read_csv(AIM, dtype=str, low_memory=False)
print("aim_master_v2 columns:", [c for c in aim.columns if c.startswith(("aim", "cat"))])
aim["pn"] = aim["part_number"].fillna("").map(norm)
aim["fam"] = aim["aim_l1"].fillna("").str.strip()
if "aim_l1_fixed" in aim.columns:
    fix = aim["aim_l1_fixed"].fillna("").str.strip()
    aim["fam"] = aim["fam"].where(aim["fam"] != "", fix)
aim["cat"] = aim["cat_l1"].fillna("").str.strip()

fam, cat, infile = {}, {}, set()
for p, f, c in zip(aim["pn"], aim["fam"], aim["cat"]):
    if not p:
        continue
    k = p.lstrip("0")
    infile.add(k)
    if f and (k not in fam or not fam[k]):
        fam[k] = f
    if c and (k not in cat or not cat[k]):
        cat[k] = c
print(f"distinct parts {len(infile)}, with family {len(fam)}, with catalogue category {len(cat)}")
print(f"aim_master rows {len(aim)}, family non-empty {int((aim['fam']!='').sum())}, cat non-empty {int((aim['cat']!='').sum())}")


def cov(name, pns, n_lines):
    f = c = none = 0
    for p in pns:
        k = p.lstrip("0")
        has_f = bool(fam.get(k))
        has_c = bool(cat.get(k))
        if has_f:
            f += 1
        if has_c:
            c += 1
        if not has_f and not has_c:
            none += 1
    print(f"\n{name}: {n_lines} lines")
    print(f"  AIM family        {f:5d}  {100*f/n_lines:.1f}%")
    print(f"  Catalogue category{c:6d}  {100*c/n_lines:.1f}%")
    print(f"  neither           {none:5d}  {100*none/n_lines:.1f}%")


dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly["pn"] = dly["PN"].map(norm)
cov("IML warehouse", dly["pn"], len(dly))

data = pd.read_excel(BO, sheet_name="DATA", header=3, dtype=str).dropna(how="all")
data.columns = [str(c).strip() for c in data.columns]
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm)
up = data["Customer"].fillna("").str.upper()
data = data[~up.str.contains("|".join(EXCLUDE))].copy()
cov("customer backlog in scope", data["pn"], len(data))

# the no-family / absent split
nf = [p for p in dly["pn"] if p.lstrip("0") in infile and not fam.get(p.lstrip("0"))]
ab = [p for p in dly["pn"] if p.lstrip("0") not in infile]
print(f"\nwarehouse: in file but no family {len(nf)} | absent from the file {len(ab)}")
print("  cat filled on the no-family lines:", sum(1 for p in nf if cat.get(p.lstrip("0"))))
print("  distinct absent part numbers:", len({p for p in ab}))

# absent ones: shape and billed history
absent_pns = sorted({p for p in ab})
print("\nabsent parts: all 10-digit numeric:",
      all(len(p) == 10 and p.isdigit() for p in absent_pns),
      f"({len(absent_pns)} of them)")
fact = pd.read_parquet(FACT)
fact["pn"] = fact["part_number"].map(norm)
billed = set(fact["pn"])
print("absent parts ever billed:", sum(1 for p in absent_pns if p in billed),
      f"of {len(absent_pns)}  (sales_fact months {fact['billing_date'].min()} .. {fact['billing_date'].max()})")
pref6 = {p[:6] for p in billed if len(p) >= 6}
shared = sum(1 for p in absent_pns if p[:6] in pref6)
print(f"absent parts sharing their first six digits with a part we hold: {shared} of {len(absent_pns)}")

# old file families
try:
    old = pd.read_csv(OLD, dtype=str, low_memory=False)
    print("\nold file columns:", [c for c in old.columns if c.startswith(("aim", "cat"))][:8])
    ocol = "aim_l1" if "aim_l1" in old.columns else old.columns[0]
    o = old[[c for c in ["part_number", ocol] if c in old.columns]].dropna()
    o["pn"] = o["part_number"].map(norm)
    o = o.groupby("pn")[ocol].first()
    cur_fam = set()
    for p, f in zip(aim["pn"], aim["fam"]):
        if f and p:
            cur_fam.add(p.lstrip("0"))
    lost = 0
    for p, v in o.items():
        if str(v).strip() and p.lstrip("0") not in cur_fam:
            lost += 1
    print(f"old file part numbers with a family that are now empty: {lost}")
    # how many of them are actually a catalogue category sitting in aim_l1
    cats = set(cat.values())
    incat = sum(1 for p, v in o.items() if str(v).strip() and p.lstrip("0") not in cur_fam
                and str(v).strip() in cats)
    print(f"  of those, the old value is a catalogue category name: {incat}")
except Exception as exc:
    print("old file read failed:", exc)
