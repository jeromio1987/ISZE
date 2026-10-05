# -*- coding: utf-8 -*-
"""VERIFY: full-set re-derivation + tie analysis + family/euro rollup.

Read-only. Builds:
  verify_all.csv        one row per distinct price-list part number with re-derived vs master
  tie_parts.csv         parts whose outcome depends on a rule-length TIE (document order)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
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

# Order of first appearance in the authored file, for tie reporting.
_authored = {}
import importlib.util
spec = importlib.util.spec_from_file_location("aim_rules_orig", EQ / "aim_rules.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}


def clean(s):
    if s is None:
        return ""
    s = str(s).strip()
    return "" if s.lower() in ("nan", "none", "null") else s


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


def hits_for(fig_name):
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    return [(i, p, l1, l2, l3) for i, (p, l1, l2, l3) in enumerate(RULES) if p in up]


def aim_from_fig_name(fig_name):
    hits = hits_for(fig_name)
    if not hits:
        return None, "", []
    _, p, l1, l2, l3 = hits[0]
    return (l1, l2, l3), p, hits


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


def master_path(m):
    l1, l2, l3 = m["dup_l1"], m["dup_l2"], m["dup_l3"]
    if m["f1"] not in PH:
        l1 = m["f1"]
    if m["f2"] not in PH:
        l2 = m["f2"]
    return l1, l2, l3


def main():
    live_l3 = {}
    master = {}
    with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = clean(r.get("part_number")).upper()
            l1 = clean(r.get("aim_l1")); l2 = clean(r.get("aim_l2")); l3 = clean(r.get("aim_l3"))
            if l1 and l2 and l3 and not l1.lower().startswith("unknown"):
                live_l3.setdefault((l1, l2), set()).add(l3)
            if pn in master:
                master[pn]["dup"] = True
            master[pn] = dict(
                pn=pn, desc=clean(r.get("description")),
                dup_l1=l1, dup_l2=l2, dup_l3=l3,
                f1=clean(r.get("aim_l1_fixed")), f2=clean(r.get("aim_l2_fixed")),
                source=clean(r.get("aim_source")), changed=clean(r.get("aim_changed")),
                fig_key=clean(r.get("fig_key")), l3=l3, l1=l1,
            )

    eq = {}
    for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            r = json.loads(line)
            if r.get("pn"):
                eq[clean(r["pn"]).upper()] = r

    q = {}
    with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = clean(r.get("pn")).upper()
            q.setdefault(pn, r)

    # price lines per pn (max list price, and all lines)
    prices = defaultdict(list)
    with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = clean(r.get("pn")).upper()
            prices[pn].append(r)

    rows = []
    for pn in sorted(q):
        m = master.get(pn)
        qr = q[pn]
        hit = eq.get(pn)
        fig_name = clean(hit.get("eq_fig_name")) if hit else ""
        trip, phrase, hits = aim_from_fig_name(fig_name)
        # tie: two rules with the SAME phrase length both fire
        if hits:
            top_len = len(hits[0][1])
            tied = [h for h in hits if len(h[1]) == top_len]
            tie = len(tied) > 1
            tie_phrases = " | ".join(h[1] for h in tied)
        else:
            tie, tie_phrases = False, ""
        aligned = ""
        if trip:
            l3a = align_l3(trip[0], trip[1], trip[2], live_l3)
            aligned = "%s > %s > %s" % (trip[0], trip[1], l3a) if l3a else ""
        mp = master_path(m) if m else ("", "", "")
        # list price for the pn (first line)
        def num(s):
            s = clean(s).replace(" ", "").replace("\u00a0", "").replace(".", "").replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None
        pls = [num(x.get("Price")) for x in prices.get(pn, [])]
        pls = [p for p in pls if p is not None]
        rows.append(dict(
            pn=pn, desc=clean(qr.get("Description")),
            list_eur=max(pls) if pls else "",
            fig_key=clean(qr.get("fig_key")),
            eq_status=clean(hit.get("eq_status")) if hit else "NO_LOOKUP",
            eq_fig_name=fig_name,
            rule_phrase=phrase, rule_triple=" > ".join(trip) if trip else "",
            aligned_triple=aligned, tie=tie, tie_phrases=tie_phrases,
            on_master=bool(m),
            master_triple=" > ".join(mp),
            master_l3=mp[2],
            master_source=m["source"] if m else "",
            master_changed=m["changed"] if m else "",
            master_f1=m["f1"] if m else "", master_f2=m["f2"] if m else "",
        ))

    with (OUT / "verify_all.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with (OUT / "tie_parts.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        tw = [r for r in rows if r["tie"]]
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(tw)

    rep = []
    def P(s=""):
        print(s); rep.append(s)

    P("parts on the price list: %d" % len(rows))
    P("with a returned EPC figure name: %d" % sum(1 for r in rows if r["eq_fig_name"]))
    P("EPC figure name that a rule converts: %d" % sum(1 for r in rows if r["rule_triple"]))
    P("EPC figure name no rule converts: %d" % sum(1 for r in rows if r["eq_fig_name"] and not r["rule_triple"]))
    P("parts whose rule outcome depends on a LENGTH TIE (document order decides): %d" % sum(1 for r in rows if r["tie"]))
    P("")
    P("=== tie breakdown (phrase pair that ties) ===")
    tt = Counter(r["tie_phrases"] for r in rows if r["tie"])
    for k, v in tt.most_common():
        P("  %-40s %d" % (k, v))
    P("")
    P("=== rule triple vs master triple, all parts with a rule ===")
    withrule = [r for r in rows if r["rule_triple"]]
    ok = [r for r in withrule if r["rule_triple"] == r["master_triple"]]
    okal = [r for r in withrule if r["aligned_triple"] == r["master_triple"]]
    P("  raw rule triple == master:      %d of %d" % (len(ok), len(withrule)))
    P("  aligned rule triple == master:  %d of %d" % (len(okal), len(withrule)))
    bad = [r for r in withrule if r["aligned_triple"] != r["master_triple"]]
    P("  disagreements: %d" % len(bad))
    for r in bad:
        P("    %s %-30s rule=%s  master=%s" % (r["pn"], r["desc"][:30], r["aligned_triple"], r["master_triple"]))

    (OUT / "verify_all_report.txt").write_text("\n".join(rep), encoding="utf-8")


if __name__ == "__main__":
    main()
