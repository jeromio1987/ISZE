import pandas as pd
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
m = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False)
m["eur"] = pd.to_numeric(m["l12m_billed_eur"], errors="coerce").fillna(0)
a = m[m["has_aim"] == "1"]

print("=" * 86)
print("FULL AIM TAXONOMY AUDIT - every L1 with its L2 children, by euro")
print("=" * 86)
for l1, g in a.groupby("aim_l1"):
    tot = g["eur"].sum()
    print(f"\n### {l1}   EUR {tot:,.0f}   ({g['part_number'].nunique()} PNs)")
    kids = (g.groupby("aim_l2").agg(pn=("part_number", "nunique"), eur=("eur", "sum"))
              .sort_values("eur", ascending=False))
    for l2, r in kids.iterrows():
        flag = ""
        key = str(l2).strip().lower()
        # defect heuristics
        if key in ("filters", "filter"):
            flag = "  <== PARENT-AS-SIBLING?"
        if key in ("review needed", "to review", "unknown", "unclassified", "unclassified / review"):
            flag = "  <== UNRESOLVED"
        print(f"    {str(l2)[:38]:<38} {r['eur']:>12,.0f}  {int(r['pn']):>5} PN{flag}")

print()
print("=" * 86)
print("DEFECT SCAN")
print("=" * 86)

# 1. near-duplicate L2 names
names = sorted({str(x).strip() for x in a["aim_l2"].dropna()})
print("\n1. NEAR-DUPLICATE L2 NAMES (case/punctuation/singular)")
import re
norm = {}
for n in names:
    k = re.sub(r"[^a-z]", "", n.lower())
    k = k.rstrip("s")
    norm.setdefault(k, []).append(n)
for k, v in norm.items():
    if len(v) > 1:
        e = a[a["aim_l2"].isin(v)]["eur"].sum()
        print(f"   {v}  -> EUR {e:,.0f}")

# 2. parent sitting as sibling
print("\n2. PARENT SITTING BESIDE ITS OWN CHILDREN")
for parent, children in {
    "Filters": ["Air Filter", "Oil Filter", "Fuel Filter", "Cabin Filter", "HVAC Filters"],
    "Brakes": ["Pads & Shoes", "Discs & Drums", "Disc & Drum"],
}.items():
    p = a[a["aim_l2"] == parent]
    ch = a[a["aim_l2"].isin(children)]
    if len(p):
        print(f"   L2 '{parent}' EUR {p['eur'].sum():,.0f}   vs children {children} EUR {ch['eur'].sum():,.0f}")

# 3. unresolved labels at any level
print("\n3. UNRESOLVED LABELS (any level)")
BAD = {"review needed", "to review", "unknown", "unclassified", "review", "??", "tbd"}
for lv in ("aim_l1", "aim_l2", "aim_l3"):
    hit = a[a[lv].fillna("").str.strip().str.lower().isin(BAD)]
    if len(hit):
        print(f"   {lv}: {len(hit)} rows, EUR {hit['eur'].sum():,.0f}, values {sorted(set(hit[lv]))}")

# 4. Lighting inside Accident & Body
print("\n4. SERVICE BUSINESS INSIDE A CRASH CLASS")
for combo in [("Accident & Body", "Lamps"), ("Electrical", "Lighting")]:
    h = a[(a["aim_l1"] == combo[0]) & (a["aim_l2"] == combo[1])]
    if len(h):
        print(f"   {combo[0]} > {combo[1]}: EUR {h['eur'].sum():,.0f} ({h['part_number'].nunique()} PN)")
print("   -> lamps total across both homes:")
lm = a[a["aim_l2"].isin(["Lamps", "Lighting"])]
print(f"      EUR {lm['eur'].sum():,.0f}")

# 5. bumpers
print("\n5. BUMPERS SPLIT ACROSS HOMES")
bp = a[a["aim_l2"].isin(["Bumpers", "Panels"]) & a["description"].fillna("").str.contains("BUMPER", case=False)]
print(bp.groupby("aim_l2")["eur"].agg(["sum", "size"]).round(0).to_string())
