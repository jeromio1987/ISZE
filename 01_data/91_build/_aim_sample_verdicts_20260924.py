"""Fill the agreement verdicts into the accuracy sample. Read-only on sources.

The verdict for each row is the author's reading of the part's own billed
description against the assigned family, with the part's figure key and the
families its figure-key siblings carry used as an independent second read.
Nothing is adjusted anywhere; this only annotates the sample CSV.
"""
from __future__ import annotations

import csv
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_accuracy_sample_20260924.csv")

# pn -> (l1_agree, l2_agree, l3_agree, note)
V = {
    "7552348290": ("Y", "Y", "Y", ""),
    "8978808250": ("Y", "Y", "Y", ""),
    "8983767550": ("Y", "Y", "Y", ""),
    "8978808270": ("Y", "Y", "Y", ""),
    "7552752270": ("Y", "Y", "Y", ""),
    "8983682091": ("Y", "Y", "Y", ""),
    "8984890190": ("Y", "Y", "Y", ""),
    "8983300950": ("Y", "Y", "Y", ""),
    "8978279610": ("Y", "N", "N",
                   "figure key 302-133 is labelled 'Pad kit; disc BRK,w/o shim & clip' and six of "
                   "its seven siblings are on Brakes > Pads & Shoes > Brake Pad Kit; this row sits "
                   "on Discs & Drums > Brake Disc. Family right, leaf wrong."),
    "8975509392": ("Y", "Y", "Y", ""),
    "8976671380": ("Y", "Y", "Y", ""),
    "8978461152": ("Y", "Y", "Y", ""),
    "5876102320": ("Y", "Y", "Y", ""),
    "8975546610": ("Y", "Y", "Y", ""),
    "1876100934": ("Y", "Y", "Y", "L2 name 'Filters (unspecified)' is vague, leaf and family right."),
    "8978808260": ("Y", "Y", "Y", ""),
    "5878324001": ("Y", "Y", "Y", ""),
    "8974816300": ("Y", "Y", "Y", ""),
    "8982979331": ("Y", "Y", "Y", ""),
    "8981455011": ("N", "N", "Y",
                   "figure key 040-424 is labelled 'Pump' (22 parts). A supply-pump overhaul kit is "
                   "engine or fuel-system, not Transmission; the leaf 'Overhaul Kit' is defensible."),
    "8976880340": ("Y", "Y", "Y", ""),
    "8983937793": ("Y", "N", "Y",
                   "figure key 690-005 is labelled 'Bumper'; the part is a rear bumper support. "
                   "Family right; L2 'Panels' should be 'Bumpers'."),
    "5876102201": ("Y", "Y", "Y", ""),
    "8982753180": ("Y", "Y", "Y", ""),
    "8983882610": ("Y", "Y", "Y", ""),
    "8982330932": ("Y", "Y", "Y", ""),
    "8982488970": ("Y", "Y", "Y", ""),
    "7552283740": ("Y", "Y", "Y", "figure key 260-001 is 'Review needed'; family and leaf are plausible."),
    "8976547870": ("Y", "Y", "Y", ""),
    "8975512712": ("Y", "Y", "Y", ""),
    "8978486410": ("Y", "Y", "Y", ""),
    "8982403130": ("Y", "Y", "Y",
                   "a bracket for the rear disc brake; the figure key 306-006 is 'Brake disc' but "
                   "the master carries no bracket family, so Chassis Frame is the materiality call."),
    "8974882820": ("Y", "Y", "Y", ""),
    "8981649171": ("Y", "Y", "Y", ""),
    "8983716601": ("Y", "Y", "Y", ""),
    "8981600613": ("Y", "Y", "Y", ""),
    "8982473952": ("Y", "Y", "N",
                   "a throttle assembly on the leaf 'Air Duct'; the family and the intake group are "
                   "right, the leaf is wrong."),
    "8978258782": ("Y", "Y", "Y", ""),
    "5876150600": ("Y", "Y", "Y", ""),
    "8981028241": ("Y", "N", "N",
                   "figure key 871-001 is labelled 'A/C compressor' and holds 78 such parts; this "
                   "row's leaf is 'Radiator Assembly'. Family right, group and leaf wrong."),
    "8983039020": ("Y", "Y", "N",
                   "a front-axle knuckle on the leaf 'King Pin Kit'; the group 'Knuckle & King Pin' "
                   "is right, the leaf is not."),
    "8973665260": ("N", "N", "N",
                   "a 4th/overdrive mainshaft hub sleeve sits on Wheels Hub > Hub & Bearing > Hub. "
                   "figure key 226-524 is 'Review needed' and holds only two parts, so nothing "
                   "corroborates the wheel-hub reading."),
    "8978420540": ("Y", "Y", "N",
                   "an engine harness on the leaf 'Connector'; group right, leaf too coarse."),
    "8971725491": ("Y", "Y", "Y", ""),
    "8983307150": ("Y", "Y", "Y", ""),
    "8978354490": ("Y", "Y", "Y", ""),
    "8980317403": ("Y", "N", "N",
                   "a heater unit on the leaf 'Blower Filter' under HVAC Filters; family right, "
                   "group and leaf wrong."),
    "8980195192": ("Y", "Y", "Y", ""),
    "8980432054": ("N", "N", "N",
                   "a power-steering pump; figure key 436-001 is labelled 'Steering pump' (238 "
                   "parts) and the master's own siblings under it are stepped to Steering. Assigned "
                   "Fuel System > Injection Pump > Fuel Pump."),
    "8980080340": ("Y", "Y", "N",
                   "a brake-shoe hold-down pin on the leaf 'Brake Shoe'; group and family right, "
                   "leaf wrong."),
}

rows = list(csv.DictReader(P.open(encoding="utf-8", newline="")))
for r in rows:
    v = V.get(r["part_number"], ("", "", "", ""))
    r["agree_l1"], r["agree_l2"], r["agree_l3"], r["note"] = v

with P.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

n = len(rows)
for k in ("agree_l1", "agree_l2", "agree_l3"):
    yes = sum(1 for r in rows if r[k] == "Y")
    print(f"{k}: {yes}/{n} = {yes/n*100:.0f}%")
bad = [r["part_number"] for r in rows if r["agree_l1"] == "N"]
print("family disagreements:", bad)
