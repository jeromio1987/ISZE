"""Classify the EXPORT.XLSX part numbers into the AIM family tree.

Two sources, strongest first:

  1. The EQ-Hit EPC lookup result (eq_fig_name), read against the AIM family
     vocabulary that is actually in use on aim_master_v2.csv. This is the part's
     own figure name from Isuzu's catalogue, so it beats every inferred source.
  2. A figure-key -> AIM path map learned from the master, but ONLY where every
     part number sharing that figure key already carries the same AIM path.

Anything else is left blank and exported as "needs a person". Nothing is guessed.

Output (this folder):
  classified.csv       one row per price line, with the AIM fill and its source
  still_unknown.csv    the rows that could not be filled, with the reason
  summary.json         counts

Run:  python 01_data/91_build/export_aim_eq_20260924/classify.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
DER = ROOT / "01_data" / "00_derived"
EXPORT = ROOT / "01_data" / "EXPORT.XLSX"
EQ_JSONL = OUT / "eq_results.jsonl"


def real(s: pd.Series) -> pd.Series:
    v = s.fillna("")
    return (v != "") & (~v.str.lower().str.startswith("unknown"))


def fig_key_of(df: pd.DataFrame) -> pd.Series:
    n = pd.to_numeric(df["Fig No."], errors="coerce")
    k = df["Key No."].fillna("").astype(str).str.strip().str.upper()
    return n.map(lambda v: f"{int(v):03d}" if pd.notna(v) else "") + "-" + k


# ---------------------------------------------------------------- EPC -> AIM
# The wording rules live in aim_rules.py so they can be validated on their own.
from aim_rules import RULES  # noqa: E402

RULES = sorted(RULES, key=lambda r: -len(r[0]))
RULES.sort(key=lambda r: -len(r[0]))

# Words that decide which live Level-3 leaf a figure-name phrase belongs to.
L3_HINTS: list[tuple[str, str]] = [
    ("Clutch Kit", "Kit"), ("Disc", "Disc"), ("Release System", "Slave"),
    ("Bumpers", "Bumper Assembly"), ("Trim", "Trim"), ("Glass", "Windshield"),
    ("Wiper & Washer", "Wiper Blade"), ("Lighting", "Lamp"),
    ("Instruments", "Instrument Cluster"), ("Sensors", "Sensor"),
    ("Harness & Connectors", "Harness"), ("Starting & Charging", "Battery"),
    ("Charging", "Alternator/Generator"), ("Control Units", "Control Unit"),
    ("Hydraulic", "Brake Pipe"), ("Caliper", "Brake Caliper"),
    ("Pads & Shoes", "Brake Pad"), ("Disc & Drum", "Brake Disc"),
    ("Discs & Drums", "Brake Rotor"), ("Actuation", "Brake Assembly"),
    ("Booster & Control", "Brake Valve"), ("ABS Control", "ABS Sensor"),
    ("Case", "Case Cover"), ("Geartrain", "Gear"), ("Shift Mechanism", "Shift Fork"),
    ("Repair Kits", "Overhaul Kit"), ("Bearings & Seals", "Gasket"),
    ("Cylinder Head", "Head Cover"), ("Block & Structure", "Cylinder Block"),
    ("Internal Rotating", "Engine Internal"), ("Valve Train", "Camshaft"),
    ("Timing Drive", "Timing Gear"), ("Mounting", "Engine Mount"),
    ("Gasket & Sealing", "Gasket"), ("Complete Assembly", "Engine Assembly"),
    ("Turbo", "Turbocharger"), ("Air Intake", "Air Duct"), ("EGR", "EGR Component"),
    ("Exhaust", "Exhaust Pipe"), ("Emission Control", "Catalyst"),
    ("DEF System", "DEF Component"), ("Radiator", "Radiator Assembly"),
    ("Water Pump", "Water Pump"), ("Thermostat & Control", "Thermostat"),
    ("Cooling Hoses & Pipes", "Water Pipe"),
    ("Steering Gear", "Steering Gear"), ("Gear", "Steering Gear"),
    ("Column", "Steering Shaft"), ("Linkage", "Tie Rod"),
    ("Knuckle & King Pin", "King Pin"), ("Control & Sensors", "Steering Sensor"),
    ("Leaf Springs", "Leaf Spring Asm"), ("Shock Absorber", "Damper"),
    ("Suspension Arm", "Ball Joint"), ("Bush & Mount", "Bushing"),
    ("Bushings", "Bushing"), ("Stabilizer", "Stabilizer Bar"),
    ("Axle Shaft", "Axle Shaft"), ("Differential", "Differential"),
    ("Final Drive", "Final Drive Asm"), ("Hub & Bearing", "Hub"),
    ("Hub Seals", "Hub Seal"), ("Wheel Rim", "Rim"),
    ("Tank & Supply", "Fuel Tank"), ("Fuel Lines & Hoses", "Fuel Pipe"),
    ("Injection", "Injection Pipe"), ("Fuel Rail", "Fuel Rail"),
    ("Fuel Pump", "Fuel Pump"), ("Filtration", "Sedimenter"),
    ("Filtration", "Fuel Filter"), ("Fuel Control", "Injection Pump"),
    ("Oil Filter System", "Oil Filter"), ("Oil Pump", "Oil Pump"),
    ("Sump & Sealing", "Oil Pan"), ("Lubrication Lines", "Oil Pipe"),
    ("Breather & Vent", "Breather"),
    ("Air Filter", "Air Cleaner Filter"), ("Oil Filter", "Oil Filter Element"),
    ("Belts", "Drive Belt"), ("Filters", "Filter"), ("Ignition & Tune-Up", "Spark Plug"),
    ("HVAC Filters", "HVAC"), ("Interior Trim", "Trim"), ("Dashboard & Controls", "Dashboard"),
    ("Seat", "Seat Cushion"), ("Pedals & Controls", "Pedal"),
    ("Panels", "Panel"), ("Locks & Handles", "Handle"), ("Mirrors", "Mirror"),
    ("Rear Gate", "Rear Gate Assembly"), ("Roof", "Roof"),
    ("Crossmember & Brackets", "Bracket"), ("Side Rail & Crossmember", "Frame"),
    ("Mounting Hardware", "Bolt"), ("Underbody Protection", "Mud Guard"),
    ("Workshop Tools", "Tool"), ("Coolant", "Coolant"), ("Lubricants", "Lubricant"),
    ("Grease", "Grease"), ("Cleaning Chemicals", "Cleaner"),
    ("Transmission Fluid", "Transmission Fluid"), ("Manuals", "Manual"),
    ("Packaging", "Packaging"), ("Audio", "Speaker"),
]


def align_l3(l1: str, l2: str, l3: str, live: dict[tuple[str, str], set[str]]) -> str:
    """Return a Level-3 that actually exists on the master under this L1/L2.

    The classifier's own wording is kept when the master already carries it;
    otherwise the closest live leaf for the pair is used. Nothing is invented —
    if the pair has no leaves at all, the Level 3 stays blank.
    """
    leaves = live.get((l1, l2))
    if not leaves:
        return ""
    if l3 in leaves:
        return l3
    low = l3.lower()
    for hint, leaf in L3_HINTS:
        if hint.lower() in low and leaf in leaves:
            return leaf
    for leaf in sorted(leaves):
        if leaf.lower() in low or low in leaf.lower():
            return leaf
    # a single-leaf pair is unambiguous
    if len(leaves) == 1:
        return next(iter(leaves))
    return ""



def aim_from_fig_name(fig_name: str) -> tuple[str, str, str] | None:
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    for phrase, l1, l2, l3 in RULES:
        if phrase in up:
            return l1, l2, l3
    return None


def main() -> None:
    x = pd.read_excel(EXPORT)
    x["pn"] = x["Newest P/N"].fillna("").astype(str).str.strip().str.upper()
    x["fk"] = fig_key_of(x)
    x["descN"] = x["Description"].fillna("").astype(str).str.strip().str.upper()

    m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
    m["pn"] = m["part_number"].fillna("").astype(str).str.strip().str.upper()
    m["fk"] = m["fig_key"].fillna("").astype(str).str.strip()
    m["l1"] = m["aim_l1"].fillna("").str.strip()
    m["l2"] = m["aim_l2"].fillna("").str.strip()
    m["l3"] = m["aim_l3"].fillna("").str.strip()

    # The Level-3 leaves that exist under each L1/L2 pair on the live master.
    live_l3: dict[tuple[str, str], set[str]] = {}
    for a, b, c in zip(m["l1"], m["l2"], m["l3"]):
        if a and b and c and not a.lower().startswith("unknown"):
            live_l3.setdefault((a, b), set()).add(c)

    # Reference 1 — figure-key -> AIM path, only where the master is unanimous.
    known = m[real(m["aim_l1"])].copy()
    known["path"] = (known["aim_l1"] + " > " + known["aim_l2"].fillna("")
                     + " > " + known["aim_l3"].fillna(""))
    pk = known[known["fk"] != ""]
    uniq = pk.groupby("fk")["path"].nunique()
    fk_map = (pk[pk["fk"].isin(uniq[uniq == 1].index)]
              .drop_duplicates("fk").set_index("fk")["path"])

    # Reference 2 — the EPC lookups.
    eq: dict[str, dict] = {}
    if EQ_JSONL.exists():
        for line in EQ_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("pn"):
                    eq[str(r["pn"]).strip().upper()] = r

    l1, l2, l3, src, note = [], [], [], [], []
    for _, r in x.iterrows():
        hit = eq.get(r["pn"])
        if hit and hit.get("eq_fig_name"):
            got = aim_from_fig_name(hit["eq_fig_name"])
            if got:
                a, b = got[0], got[1]
                c = align_l3(a, b, got[2], live_l3)
                if not c:
                    l1.append(""); l2.append(""); l3.append("")
                    src.append("")
                    note.append(f"{a} > {b} has no Level-3 leaf on the master yet; "
                                f"EPC said: {hit['eq_fig_name']}")
                    continue
                l1.append(a); l2.append(b); l3.append(c)
                src.append("EPC figure name")
                note.append(str(hit["eq_fig_name"]))
                continue
            l1.append(""); l2.append(""); l3.append("")
            src.append("")
            note.append("EPC found but the figure name has no AIM rule yet: "
                        + str(hit["eq_fig_name"]))
            continue

        path = fk_map.get(r["fk"], "")
        if path:
            a, b, c = (list(path.split(" > ")) + ["", ""])[:3]
            l1.append(a.strip()); l2.append(b.strip()); l3.append(c.strip())
            src.append("figure key, unanimous on the master")
            note.append(str(r["fk"]))
            continue

        l1.append(""); l2.append(""); l3.append("")
        src.append("")
        if hit and hit.get("eq_status") == "NOT_FOUND":
            note.append("not in the EPC")
        elif hit and hit.get("eq_status") == "ERROR":
            note.append("lookup failed: " + str(hit.get("error")))
        elif not hit:
            note.append("not looked up")
        else:
            note.append("figure key is not unanimous on the master")

    x["aim_level_1"] = l1
    x["aim_level_2"] = l2
    x["aim_level_3"] = l3
    x["aim_source_this_pass"] = src
    x["aim_note"] = note

    cols = ["pn", "P/N", "Newest P/N", "Description", "Sales Org", "Fig No.", "Key No.",
            "fk", "ABC Code", "Price", "Currency", "Value",
            "aim_level_1", "aim_level_2", "aim_level_3",
            "aim_source_this_pass", "aim_note"]
    out = x[cols].copy()
    out.to_csv(OUT / "classified.csv", index=False, encoding="utf-8-sig")

    miss = out[out["aim_level_1"] == ""]
    miss.to_csv(OUT / "still_unknown.csv", index=False, encoding="utf-8-sig")

    summary = {
        "price_lines": int(len(out)),
        "filled": int((out["aim_level_1"] != "").sum()),
        "still_blank": int(len(miss)),
        "by_source": out.loc[out["aim_level_1"] != "", "aim_source_this_pass"]
                        .value_counts().to_dict(),
        "blank_reasons": miss["aim_note"].value_counts().head(15).to_dict(),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
