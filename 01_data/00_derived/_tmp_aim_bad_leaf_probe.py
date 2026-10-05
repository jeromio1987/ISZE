# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

root = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
m = pd.read_csv(root / "aim_master_v2.csv", dtype=str, keep_default_na=False)
hp = pd.read_csv(root / "aim_gap_high_conf_patch_20260918.csv", dtype=str, keep_default_na=False)
hp_pns = set(hp["part_number"])

mark = m[m["aim_changed"] == "gap_auto_20260918"].copy()
extra = mark[~mark["part_number"].isin(hp_pns)]
print("=== EXTRA 12 ===")
for _, r in extra.iterrows():
    print(
        "|".join(
            [
                r["part_number"],
                r["description"],
                r["aim_l1"],
                r["aim_l2"],
                r["aim_l3"],
                "src=" + r["aim_source"][:80],
            ]
        )
    )

bad_pns = [
    "8978708710",
    "8978708720",
    "8980603820",
    "1884055560",
    "7552816560",
    "8974993681",
    "8980094180",
]
print("\n=== BAD TARGETS CURRENT ===")
for pn in bad_pns:
    rows = m[m["part_number"] == pn]
    for _, r in rows.iterrows():
        print(
            "|".join(
                [
                    pn,
                    r["description"],
                    r["aim_l1"],
                    r["aim_l2"],
                    r["aim_l3"],
                    "changed=" + r["aim_changed"],
                ]
            )
        )

non = m[m["aim_changed"] != "gap_auto_20260918"]
non = non[(non["aim_l1"] != "") & (non["aim_l2"] != "") & (non["aim_l3"] != "")]


def find_triples(kw_l1=None, kw_l2=None, kw_l3=None, desc_kw=None, limit=15):
    df = non
    if kw_l1:
        df = df[df["aim_l1"].str.contains(kw_l1, case=False, na=False)]
    if kw_l2:
        df = df[df["aim_l2"].str.contains(kw_l2, case=False, na=False)]
    if kw_l3:
        df = df[df["aim_l3"].str.contains(kw_l3, case=False, na=False)]
    if desc_kw:
        df = df[df["description"].str.contains(desc_kw, case=False, na=False)]
    triples = df.groupby(["aim_l1", "aim_l2", "aim_l3"]).size().sort_values(ascending=False)
    print(triples.head(limit).to_string())
    return triples


print("\n=== HEADLAMP / LIGHTING / NOZZLE ===")
find_triples(desc_kw="HEADLAMP")
print("--- Lighting L2 ---")
find_triples(kw_l1="Electrical", kw_l2="Light")
print("--- washer / nozzle ---")
find_triples(desc_kw="WASHER")
find_triples(desc_kw="NOZZLE")

print("\n=== BOLT / FASTENER / ATF PIPE ===")
find_triples(desc_kw="BOLT; EYE")
find_triples(kw_l2="Fastener")
find_triples(kw_l3="Bolt")
find_triples(desc_kw="ATF PIPE")

print("\n=== BRAKE FLUID ===")
find_triples(desc_kw="BRAKE FLUID")
find_triples(kw_l1="Fluids", kw_l2="Brake")
find_triples(kw_l1="Fluids", kw_l3="Brake")
find_triples(kw_l1="Fluids")

print("\n=== HV / BATTERY ===")
find_triples(desc_kw="HIGH VOLTAGE")
find_triples(kw_l1="Electrical", kw_l2="Charg")
find_triples(kw_l3="Battery")
find_triples(kw_l2="Starting")

print("\n=== TIRE SENSOR ===")
find_triples(desc_kw="TIRE")
find_triples(kw_l3="Tire")
find_triples(desc_kw="INFLAT")
find_triples(kw_l2="Sensor")

print("\n=== MAP SENSOR ===")
find_triples(desc_kw="SENSOR; MAP")
find_triples(kw_l3="MAP")
find_triples(kw_l3="Pressure")
find_triples(desc_kw="MANIFOLD ABS")
find_triples(desc_kw="MAP")
