# -*- coding: utf-8 -*-
"""VERIFY step 2: re-derive the 32 placed orphans from classified.csv + aim_rules.py.

Independent re-implementation of the reading. Read-only.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_verify_20260924"

sys.path.insert(0, str(EQ))
from aim_rules import RULES  # noqa: E402

RULES = sorted(RULES, key=lambda r: -len(r[0]))

L3_HINTS = [
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


def aim_from_fig_name(fig_name):
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    hits = [(p, l1, l2, l3) for p, l1, l2, l3 in RULES if p in up]
    if not hits:
        return None, "", []
    p, l1, l2, l3 = hits[0]
    return (l1, l2, l3), p, hits


def load_master():
    mm = {}
    live_l3 = {}
    out = []
    with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = (r.get("part_number") or "").strip().upper()
            l1 = (r.get("aim_l1") or "").strip()
            l2 = (r.get("aim_l2") or "").strip()
            l3 = (r.get("aim_l3") or "").strip()
            f1 = (r.get("aim_l1_fixed") or "").strip()
            f2 = (r.get("aim_l2_fixed") or "").strip()
            rec = dict(pn=pn, desc=(r.get("description") or "").strip(),
                       raw=(l1, l2, l3), fixed=(f1, f2),
                       source=(r.get("aim_source") or "").strip(),
                       changed=(r.get("aim_changed") or "").strip(),
                       fig_key=(r.get("fig_key") or "").strip())
            mm[pn] = rec
            out.append(rec)
            if l1 and l2 and l3 and not l1.lower().startswith("unknown"):
                live_l3.setdefault((l1, l2), set()).add(l3)
    return mm, live_l3, out


def align_l3(l1, l2, l3, live):
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
    if len(leaves) == 1:
        return next(iter(leaves))
    return ""


def main():
    mm, live_l3, master_rows = load_master()

    orphans = []
    with (EQ / "orphans_43.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            orphans.append(r)
    pns = [r["part_number"].strip().upper() for r in orphans]

    cls = {}
    with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            k = (r.get("pn") or "").strip().upper()
            if k in pns and k not in cls:
                cls[k] = r

    rows = []
    for o in orphans:
        pn = o["part_number"].strip().upper()
        c = cls[pn]
        src = (c.get("aim_source_this_pass") or "").strip()
        note = (c.get("aim_note") or "").strip()
        fig_name = note if src == "EPC figure name" else ""
        trip, phrase, hits = aim_from_fig_name(fig_name)
        contested = len({h[1:] for h in hits}) > 1
        aligned = ""
        if trip:
            a, b, cc = trip
            l3a = align_l3(a, b, cc, live_l3)
            aligned = "%s > %s > %s" % (a, b, l3a) if l3a else ""
        cls_triple = " > ".join([c.get("aim_level_1") or "",
                                 c.get("aim_level_2") or "",
                                 c.get("aim_level_3") or ""])
        m = mm.get(pn)
        mstr = " > ".join(m["raw"]) if m else ""
        rows.append(dict(
            pn=pn, desc=(o.get("Description") or "").strip(),
            list_eur=o.get("list_eur", ""), fig_key=(o.get("fig_key") or "").strip(),
            classified_source=src, epc_fig_name=fig_name, rule_phrase=phrase,
            rule_triple=" > ".join(trip) if trip else "",
            aligned_triple=aligned, contested=contested,
            classified_triple=cls_triple, on_master=bool(m),
            master_triple=mstr,
            master_source=m["source"] if m else "",
            master_changed=m["changed"] if m else "",
        ))

    with (OUT / "orphan_rederive.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    placed = [r for r in rows if r["rule_triple"]]
    rep = []
    def P(s=""):
        print(s); rep.append(s)

    P("orphans: %d   re-derived by a rule (route a): %d" % (len(rows), len(placed)))
    P("no rule match (should be the 11 unplaced): %d" % (len(rows) - len(placed)))
    P("")
    P("=== re-derived rule vs what is on the master now ===")
    match = [r for r in placed if r["rule_triple"] == r["master_triple"]]
    mismatch = [r for r in placed if r["rule_triple"] != r["master_triple"]]
    P("  exact match (raw rule triple == master triple): %d of %d" % (len(match), len(placed)))
    for r in mismatch:
        P("  MISMATCH %s %s" % (r["pn"], r["desc"][:28]))
        P("      rule     : %s" % r["rule_triple"])
        P("      master   : %s" % r["master_triple"])
    P("")
    P("=== re-derived rule vs what classified.csv recorded ===")
    m2 = sum(1 for r in placed if r["rule_triple"] == r["classified_triple"])
    m3 = sum(1 for r in placed if r["aligned_triple"] == r["classified_triple"])
    P("  raw rule triple == classified triple      : %d of %d" % (m2, len(placed)))
    P("  aligned rule triple == classified triple  : %d of %d" % (m3, len(placed)))
    for r in placed:
        if r["aligned_triple"] != r["classified_triple"]:
            P("  DIFF %s aligned=%r classified=%r" % (r["pn"], r["aligned_triple"], r["classified_triple"]))
    P("")
    P("=== rule triples where alignment changed the Level 3 ===")
    for r in placed:
        if r["rule_triple"] != r["aligned_triple"]:
            P("  %s %-28s raw=%-55s aligned=%s" % (r["pn"], r["desc"][:28], r["rule_triple"], r["aligned_triple"]))
    P("")
    P("=== contested figure names (more than one rule matched; first wins) ===")
    for r in placed:
        if r["contested"]:
            P("  %s %-28s %r -> %r" % (r["pn"], r["desc"][:28], r["epc_fig_name"], r["rule_phrase"]))
    P("")
    P("=== unplaced (no rule match) ===")
    for r in rows:
        if not r["rule_triple"]:
            P("  %s %-34s src=%-42r fig_name=%r master=%r" % (
                r["pn"], r["desc"][:34], r["classified_source"], r["epc_fig_name"], r["master_triple"]))

    (OUT / "orphan_rederive_report.txt").write_text("\n".join(rep), encoding="utf-8")


if __name__ == "__main__":
    main()
