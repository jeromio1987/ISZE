#!/usr/bin/env python3
"""List the parts of the 26 wrong move groups in release 2026-10-15, with their 11 Oct labels.

Claude's check of brief R2 (2026-10-15) found 26 of the 102 move groups wrong: the R2 builder
matched keywords instead of reading the description (every SHAFT to Steering > Sector Shaft,
door lock cylinders to Engine > Cylinder Liner, door trim pads to Brakes > Brake Pad, ...).
Jerome 2026-10-15: revert the 26 wrong groups to their 11 Oct labels, keep the other 76.

Input only for the fix release (brief R3). Writes one CSV; touches no release, master or overlay.

    python 01_data/91_build/build_revert_list_wrong_moves_20261015.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
REL = ISZE / "01_data" / "00_derived" / "_releases"
PARTS = REL / "next_release_proposal_wrong_labels_2026-10-15.csv"
R1011 = REL / "aim_pn_classification_release_2026-10-11.csv"
R1015 = REL / "aim_pn_classification_release_2026-10-15.csv"
OUT = REL / "revert_list_wrong_moves_2026-10-15.csv"
AIM = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "aim_source"]

# (description key, 11 Oct L3 label) -> why the move was wrong
WRONG = {
    ("CYLINDER SET;CAR LOCK", "Door"): "door lock key cylinder, not an engine cylinder liner",
    ("PAD;TRIM", "Door"): "door trim pad, not a brake pad",
    ("SHAFT;TOP GEAR", "Gear"): "gearbox shaft, not steering",
    ("VALVE;EXH BRAKE", "Valve"): "exhaust (engine) brake valve, not a service brake valve",
    ("PIPE;OIL", "Steering Gear"): "power steering oil pipe on the steering gear, not an engine oil pipe",
    ("SHAFT ASM;FRT DRIVE", "Motor"): "front drive shaft, not steering",
    ("CYLINDER ASM;W/KEY", "Door"): "lock cylinder with key, not an engine cylinder liner",
    ("CYLINDER ASM;DOOR LOCK", "Door"): "door lock cylinder, not an engine cylinder liner",
    ("SHAFT;MAIN", "Gear"): "gearbox main shaft, not steering",
    ("CARRIER;CAM SHAFT", "Carrier"): "engine camshaft carrier, not steering",
    ("BEARING;MAINSHAFT END", "Gear"): "gearbox bearing, not a clutch release bearing",
    ("PIPE;CHILLER", "HVAC"): "air conditioning pipe, not an oil pipe",
    ("DAMPER ASM;CLU OIL", "Damper"): "clutch hydraulic damper, not an oil pipe",
    ("SHAFT;AXLE", "Motor"): "axle shaft, not steering",
    ("SHAFT;IDLE GEAR", "Gear"): "gearbox idle gear shaft, not steering",
    ("FLANGE;FRT WHEEL HUB", "Hub"): "wheel hub flange, not a wheel rim",
    ("BEARING;NEEDLE", "Gear"): "gearbox needle bearing, not a clutch release bearing",
    ("SHAFT;GEAR", "Gear"): "gearbox shaft, not steering",
    ("PIPE ASM;A/C", "HVAC"): "air conditioning pipe, not a chassis frame hose",
    ("CLAMP;EXH PIPE", "Lamp"): "exhaust clamp, not an oil pipe",
    ("BAND;BRAKE", "Clutch Kit"): "band brake, not a brake caliper",
    ("CONNECTOR;JOINT", "Connector"): "electrical joint connector, not a ball joint",
    ("RETAINER;RR WINDOW", "Windshield"): "rear window retainer, not a window motor",
    ("STUD;LEAD PIPE", "Turbocharger"): "stud, not an oil pipe",
    ("SHAFT;ROCKER ARM", "Rocker Arm"): "engine rocker arm shaft; the 11 Oct label was right",
    ("STUD;AXLE SHAFT TO HUB", "Hub"): "hub stud, not steering",
}


def desc_key(d: str) -> str:  # same rule as build_next_release_proposal_wrong_labels_20261015.py
    d = re.sub(r"\s+", " ", (d or "").upper().strip())
    if ";" in d:
        head, rest = d.split(";", 1)
        return f"{head.strip()};{rest.split(',', 1)[0].strip()}"
    return d.split(",", 1)[0].strip()


def main() -> None:
    p = pd.read_csv(PARTS, dtype=str, keep_default_na=False)
    p = p[p.verdict.eq("move")].copy()
    p["description_key"] = p.description.map(desc_key)
    p["why_wrong"] = [WRONG.get((k, l3), "") for k, l3 in zip(p.description_key, p.current_aim_l3)]
    p = p[p.why_wrong.ne("")]
    found = set(zip(p.description_key, p.current_aim_l3))
    assert found == set(WRONG), sorted(set(WRONG) - found)

    a = pd.read_csv(R1011, dtype=str, keep_default_na=False).set_index("part_number")[AIM]
    b = pd.read_csv(R1015, dtype=str, keep_default_na=False).set_index("part_number")[AIM]
    assert a.index.is_unique and b.index.is_unique
    pn = p.part_number
    out = pd.DataFrame({
        "part_number": pn.values,
        "description": p.description.values,
        "description_key": p.description_key.values,
        "eur_fy2026": p.eur_fy2026.astype(float).round(2).values,
        "revert_to_aim_l1": a.loc[pn, "aim_l1_fixed"].values,
        "revert_to_aim_l2": a.loc[pn, "aim_l2_fixed"].values,
        "revert_to_aim_l3": a.loc[pn, "aim_l3_fixed"].values,
        "revert_to_aim_source": a.loc[pn, "aim_source"].values,
        "now_aim_l1": b.loc[pn, "aim_l1_fixed"].values,
        "now_aim_l2": b.loc[pn, "aim_l2_fixed"].values,
        "now_aim_l3": b.loc[pn, "aim_l3_fixed"].values,
        "now_aim_source": b.loc[pn, "aim_source"].values,
        "why_wrong": p.why_wrong.values,
    }).sort_values(["eur_fy2026", "part_number"], ascending=[False, True])

    # the 11 Oct label must equal the proposal's "current" label, and 15 Oct must differ from it
    cur = p.set_index("part_number").loc[out.part_number, ["current_aim_l1", "current_aim_l2", "current_aim_l3"]].values
    assert (out[["revert_to_aim_l1", "revert_to_aim_l2", "revert_to_aim_l3"]].values == cur).all()
    assert (out[["revert_to_aim_l1", "revert_to_aim_l2", "revert_to_aim_l3"]].values
            != out[["now_aim_l1", "now_aim_l2", "now_aim_l3"]].values).any(axis=1).all()

    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"{OUT.name}: {len(out)} parts, {out.part_number.nunique()} distinct, "
          f"{len(found)} groups, EUR {out.eur_fy2026.sum():,.2f} FY2026")


if __name__ == "__main__":
    main()
