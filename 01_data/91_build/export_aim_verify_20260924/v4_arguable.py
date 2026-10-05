# -*- coding: utf-8 -*-
"""VERIFY steps 3 and 4: the three arguable placements, and the connector claim.

Read-only.
"""
from __future__ import annotations

import csv
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

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def clean(s):
    s = "" if s is None or str(s).strip().lower() in ("nan", "none", "null") else str(s).strip()
    return s


master = []
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        l1 = clean(r.get("aim_l1")); l2 = clean(r.get("aim_l2")); l3 = clean(r.get("aim_l3"))
        f1 = clean(r.get("aim_l1_fixed")); f2 = clean(r.get("aim_l2_fixed"))
        eff1 = f1 if f1 not in PH else l1
        eff2 = f2 if f2 not in PH else l2
        master.append(dict(
            pn=clean(r.get("part_number")).upper(),
            desc=clean(r.get("description")),
            raw=(l1, l2, l3), eff=(eff1, eff2, l3),
            fig_key=clean(r.get("fig_key")), fig_no=clean(r.get("fig_no")),
            key_no=clean(r.get("key_no")), source=clean(r.get("aim_source")),
            real=bool(eff1 and eff1 not in PH),
        ))


def eff_path(m):
    return " > ".join(m["eff"]) if m["real"] else ""


# ---------------------------------------------------------------- step 3
def show_rule_firing(fig_name, label):
    P("--- %s" % label)
    P("    figure name: %r" % fig_name)
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    hits = []
    for i, (p, l1, l2, l3) in enumerate(RULES):
        if p in up:
            hits.append((i, p, l1, l2, l3))
    hits.sort(key=lambda h: (-len(h[1]), h[0]))
    for i, p, l1, l2, l3 in hits:
        P("      rule %-26r len %-3d doc#%-4d -> %s > %s > %s" % (p, len(p), i, l1, l2, l3))
    if hits:
        top_len = len(hits[0][1])
        tied = [h for h in hits if len(h[1]) == top_len]
        P("      longest phrase length: %d ; rules at that length: %d %s"
          % (top_len, len(tied), "TIE - document order decides" if len(tied) > 1 else ""))
    P("")


P("=" * 78)
P("STEP 3 - THE THREE ARGUABLE PLACEMENTS")
P("=" * 78)
P("")

# 3a oil filter
P("### (1) 7552062110  FILTER ASM; OIL  -> written Cooling > Radiator > Radiator Assembly")
show_rule_firing("0-50 - OIL COOLER AND OIL FILTER", "7552062110")
d = "FILTER ASM; OIL"
sup = Counter(eff_path(m) for m in master if m["desc"] == d and m["real"])
P("    master parts with description %r: %d" % (d, sum(sup.values())))
for k, v in sup.most_common():
    P("        %4d  %s" % (v, k))
P("    master parts on Cooling > Radiator > Radiator Assembly: %d"
  % sum(1 for m in master if eff_path(m) == "Cooling > Radiator > Radiator Assembly"))
P("    master parts on Maintenance Service > Oil Filter > Oil Filter Element: %d"
  % sum(1 for m in master if eff_path(m) == "Maintenance Service > Oil Filter > Oil Filter Element"))
P("    master parts on Maintenance Service > Filters > Filter: %d"
  % sum(1 for m in master if eff_path(m) == "Maintenance Service > Filters > Filter"))
P("    master parts whose description starts 'FILTER ASM; OIL': %d"
  % sum(1 for m in master if m["desc"].upper().startswith("FILTER ASM; OIL")))
oilf = Counter(eff_path(m) for m in master if m["desc"].upper().startswith("FILTER ASM; OIL") and m["real"])
for k, v in oilf.most_common(6):
    P("        %4d  %s" % (v, k))
P("")

# 3b pump kit
P("### (2) 7552710010  PUMP KIT  -> written Intake Exhaust Emission > DEF System > DEF Tank")
show_rule_firing("1-46 - DEF TANK AND PIPING", "7552710010")
d = "PUMP KIT"
sup = Counter(eff_path(m) for m in master if m["desc"] == d and m["real"])
P("    master parts with description %r: %d" % (d, sum(sup.values())))
for k, v in sup.most_common():
    P("        %4d  %s" % (v, k))
P("    master parts on Intake Exhaust Emission > DEF System > DEF Tank: %d"
  % sum(1 for m in master if eff_path(m) == "Intake Exhaust Emission > DEF System > DEF Tank"))
P("    master parts on Fuel System > Injection Pump > Fuel Pump: %d"
  % sum(1 for m in master if eff_path(m) == "Fuel System > Injection Pump > Fuel Pump"))
P("    master parts on Fuel System > Fuel Pump > Fuel Pump: %d"
  % sum(1 for m in master if eff_path(m) == "Fuel System > Fuel Pump > Fuel Pump"))
P("")

# 3c tray
P("### (3) 8974210030  TRAY; INST  -> written Cabin Interior > Dashboard & Controls > Knob")
show_rule_firing("7-40 - INSTRUMENT PANEL AND BOX", "8974210030")
d = "TRAY; INST"
sup = Counter(eff_path(m) for m in master if m["desc"] == d and m["real"])
P("    master parts with description %r: %d" % (d, sum(sup.values())))
for k, v in sup.most_common():
    P("        %4d  %s" % (v, k))
P("    master parts on Cabin Interior > Dashboard & Controls > Knob: %d"
  % sum(1 for m in master if eff_path(m) == "Cabin Interior > Dashboard & Controls > Knob"))
P("    master parts with description starting 'TRAY': %d"
  % sum(1 for m in master if m["desc"].upper().startswith("TRAY")))
tr = Counter(eff_path(m) for m in master if m["desc"].upper().startswith("TRAY") and m["real"])
for k, v in tr.most_common(10):
    P("        %4d  %s" % (v, k))
P("")

# how many parts share each of those three figure names
P("--- how crowded these three figure names are on the whole price list ---")
cls = list(csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")))
byname = Counter(clean(r["aim_note"]) for r in cls
                 if clean(r["aim_source_this_pass"]) == "EPC figure name")
for nm in ["0-50 - OIL COOLER AND OIL FILTER", "1-46 - DEF TANK AND PIPING",
           "7-40 - INSTRUMENT PANEL AND BOX"]:
    P("    %-38s %d price lines" % (nm, byname[nm]))
P("")

# ---------------------------------------------------------------- step 4
P("=" * 78)
P("STEP 4 - THE THREE CONNECTORS AND THE FIGURE-KEY CLAIM")
P("=" * 78)
P("")
conn = ["8943633640", "8980626220", "8980680830"]
P("--- what the master holds for their figure keys ---")
for fk in ["816-002", "816-090"]:
    rows = [m for m in master if m["fig_key"] == fk]
    P("    %s : %d master rows" % (fk, len(rows)))
    for m in rows:
        P("        %-12s %-34s family=%s" % (m["pn"], m["desc"][:34], eff_path(m) or "(blank)"))
P("")
P("--- every master row whose figure number is 816 ---")
rows = [m for m in master if m["fig_no"] == "816"]
P("    %d rows" % len(rows))
byl = Counter(eff_path(m) or "(blank)" for m in rows)
for k, v in byl.most_common():
    P("        %4d  %s" % (v, k))
P("    distinct families among them: %d" % len([k for k in byl if k != "(blank)"]))
P("")
P("--- what a whole-figure-number grouping would say (816 alone) ---")
P("    families present: %s" % [k for k in byl if k != "(blank)"])
P("")
P("--- would a bare CONNECTOR wording rule place them? ---")
conl1 = [m for m in master if m["desc"].upper().startswith("CONNECTOR")]
P("    master parts whose description starts CONNECTOR: %d" % len(conl1))
c = Counter(eff_path(m) or "(blank)" for m in conl1)
for k, v in c.most_common():
    P("        %4d  %s" % (v, k))
P("    -> on Electrical > Harness & Connectors > Connector: %d"
  % c.get("Electrical > Harness & Connectors > Connector", 0))
P("")
P("    the two exact texts, and what the master holds for each:")
for t in ["CONNECTOR; HEAD LAMP", "CONNECTOR; HARNESS (2P FEMAIL)"]:
    s = Counter(eff_path(m) or "(blank)" for m in master if m["desc"].upper() == t)
    P("      %-32r %d master parts %s" % (t, sum(s.values()), dict(s)))
P("")
# all CONNECTOR; HEAD LAMP master parts, by family, whatever the column
P("    every master row with description CONNECTOR; HEAD LAMP (any family state):")
for m in master:
    if m["desc"].upper() == "CONNECTOR; HEAD LAMP":
        P("        %-12s family=%s  source=%s" % (m["pn"], eff_path(m) or "(blank)", m["source"]))
P("")
P("--- the rule table itself ---")
P("    rules containing 'CONNECT': %s" % [r[0] for r in RULES if "CONNECT" in r[0].upper()])
P("    rules containing 'HARNESS': %s" % [r[0] for r in RULES if "HARNESS" in r[0].upper()])
P("    the HARNESS rule maps figure names that contain HARNESS to Electrical > Harness & Connectors > Terminal")
P("")
P("--- what the EPC returned for the three ---")
import json
recs = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        r = json.loads(line)
        recs[clean(r["pn"]).upper()] = r
for p in conn:
    P("    %s  %s" % (p, recs.get(p)))
P("")
sib = [m for m in master if m["desc"].upper().startswith("CONNECTOR; HARNESS") and m["real"]]
P("--- master parts with description starting 'CONNECTOR; HARNESS' that carry a family ---")
for m in sib:
    P("    %-12s %-34s %s" % (m["pn"], m["desc"][:34], eff_path(m)))
P("")

(OUT / "verify_steps_3_4.txt").write_text("\n".join(REP), encoding="utf-8")
