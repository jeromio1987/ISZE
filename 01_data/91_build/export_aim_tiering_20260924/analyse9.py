"""Hand-audit pass: the ENGINE ASM case, a contradiction scan, and 20 manual checks."""
from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np, re

pd.set_option("display.width", 320); pd.set_option("display.max_rows", 600)
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
CLSWB = ROOT / "01_data" / "01_Pricing" / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"

log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)

q = pd.read_csv(OUT / "queue_strict_tiered.csv", dtype=str, encoding="utf-8-sig")
for c in ("pr00", "list", "d_n", "f_n"):
    q[c] = pd.to_numeric(q[c], errors="coerce")
q["strict"] = q["strict"] == "True"
m = pd.read_csv(MASTER, dtype=str, low_memory=False)

say("=" * 78)
say("1. THE 'ENGINE ASM' ROW JEROME NAMED")
row = q[q["desc_norm"].astype(str).str.strip() == "ENGINE ASM"]
say(f"  queue rows named ENGINE ASM: {len(row)}")
for _, r in row.iterrows():
    say(f"    pn={r['pn']} fk={r['fk']} list={r['list']:,.2f} pr00={r['pr00']:,.2f}")
    say(f"      d_l1={r['d_l1']} (master parts={r['d_n']})  f_l1={r['f_l1']} (parts={r['f_n']})")
    say(f"      strict Tier A = {r['strict']}")
mm = m[m["description"].fillna("").str.strip().str.upper() == "ENGINE ASM"]
say(f"  master rows with that exact description: {len(mm)}")
if len(mm):
    say(f"    their aim_l1: {dict(mm['aim_l1'].value_counts())}")
    say(f"    their fig_keys: {dict(mm['fig_key'].value_counts().head(5))}")
    for _, r in mm.head(6).iterrows():
        say(f"      {r['part_number']}  {str(r['description'])[:26]:26s} -> {r['aim_l1']} > {r['aim_l2']} > {r['aim_l3']}  src={r['aim_source']}")

say("")
say("=" * 78)
say("2. CONTRADICTION SCAN INSIDE STRICT TIER A")
# keyword -> the family that keyword implies; if the row's family is a DIFFERENT
# system family, flag it.
KW = {
    "SUSP": {"Suspension"},
    "SPRING ASM; LEAF": {"Suspension"},
    "SHOCK": {"Suspension"},
    "STRG": {"Steering"}, "STEERING": {"Steering"},
    "CLU": {"Clutch"}, "CLUTCH": {"Clutch"},
    "BRK": {"Brakes"}, "BRAKE": {"Brakes"},
    "EXH": {"Intake Exhaust Emission"}, "EXHAUST": {"Intake Exhaust Emission"},
    "TURBO": {"Intake Exhaust Emission"},
    "TRANS": {"Transmission"}, "TRANSMISSION": {"Transmission"},
    "FUEL": {"Fuel System"},
    "COOL": {"Cooling"}, "RAD": {"Cooling"}, "WATER": {"Cooling"}, "THERMO": {"Cooling"},
    "HARNESS": {"Electrical"}, "SENSOR": {"Electrical"}, "SWITCH": {"Electrical"},
    "STARTER": {"Electrical"}, "ALTERNATOR": {"Electrical"}, "CONTROL UNIT": {"Electrical"},
    "LAMP": {"Electrical", "Accident & Body"}, "MIRROR": {"Accident & Body"},
    "BUMPER": {"Accident & Body"}, "DOOR": {"Accident & Body"}, "FENDER": {"Accident & Body"},
    "GRILLE": {"Accident & Body"}, "WIPER": {"Accident & Body"},
    "SEAT": {"Cabin Interior"}, "AIR BAG": {"Cabin Interior"},
    "WHEEL": {"Wheels Hub"}, "HUB": {"Wheels Hub"},
    "AXLE": {"Driveline Axle", "Chassis Frame"}, "DIFF": {"Driveline Axle"},
    "PISTON": {"Engine"}, "CYL": {"Engine"}, "CRANKSHAFT": {"Engine"}, "CAM": {"Engine"},
    "OIL": {"Lubrication", "Maintenance Service", "Engine"},
    "FILTER": {"Maintenance Service"},
    "DEF": {"Intake Exhaust Emission"}, "DPD": {"Intake Exhaust Emission"},
    "A/C": {"Cabin Interior", "Cooling"}, "HEATER": {"Cabin Interior", "Cooling"},
}
A = q[q["strict"]].copy()
hits = []
for _, r in A.iterrows():
    d = str(r["desc_norm"]).upper(); fam = str(r["d_l1"])
    for kw, allowed in KW.items():
        if kw in d and fam not in allowed:
            hits.append({"pn": r["pn"], "desc": d, "family": fam, "keyword": kw,
                         "expected": " / ".join(sorted(allowed)), "fk": r["fk"],
                         "list": r["list"], "pr00": r["pr00"], "d_n": r["d_n"], "f_n": r["f_n"]})
            break
h = pd.DataFrame(hits)
say(f"  strict Tier A rows: {len(A)}")
say(f"  rows where a system word points at a different family: {len(h)}")
if len(h):
    say(f"  euro on those rows: PR00 {h['pr00'].sum():,.2f}  list {h['list'].sum():,.2f}")
    for _, r in h.sort_values("pr00", ascending=False).iterrows():
        say(f"    {r['pn']}  {r['desc'][:38]:38s} fk={r['fk']:9s} -> {r['family'][:22]:22s} "
            f"(word '{r['keyword']}' implies {r['expected']}) list={r['list']:9,.2f} pr00={r['pr00']:9,.2f}")

say("")
say("=" * 78)
say("3. TWENTY STRICT TIER A ROWS CHECKED BY HAND")
A_s = A.sort_values("pr00", ascending=False)
picks = list(A_s.head(10).index) + list(A_s.iloc[len(A_s)//2: len(A_s)//2 + 5].index) + list(A_s.tail(5).index)
for i, ix in enumerate(picks, 1):
    r = q.loc[ix]
    say(f"  {i:2d}. {r['pn']}  {str(r['desc_norm'])[:34]:34s}")
    say(f"      queue says list EUR {r['list']:,.2f}, PR00 value EUR {r['pr00']:,.2f}, fig key {r['fk']}")
    say(f"      rule assigns {r['d_l1']}   (master: {int(r['d_n'])} parts share this exact description, "
        f"{int(r['f_n'])} sit on this fig key, all the same family)")

(OUT / "handcheck.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE9")
