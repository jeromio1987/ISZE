# -*- coding: utf-8 -*-
"""VERIFY step 6 corrected: family rollup with a correct EU/US price parser.

Price shapes in EXPORT.XLSX: '99,99' (583) | '9,99' (495) | '999,99' (222) | '9 999.99' (18).
So the decimal separator is the LAST of ',' or '.'; spaces are thousands.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_verify_20260924"

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def clean(s):
    s = "" if s is None or str(s).strip().lower() in ("nan", "none", "null") else str(s).strip()
    return s


def num(s):
    s = clean(s).replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    has_c, has_d = "," in s, "." in s
    if has_c and has_d:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_c:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


# --------------------------------------------------------------- master
mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        f = clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1"))
        f2 = clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2"))
        mm[pn] = dict(pn=pn, l1=f, l2=f2, l3=clean(r.get("aim_l3")),
                      source=clean(r.get("aim_source")), changed=clean(r.get("aim_changed")))

# --------------------------------------------------------------- classified (source of each label + price)
cls = {}
with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("pn")).upper()
        e = num(r.get("Price"))
        rec = cls.setdefault(pn, dict(pn=pn, eur=None, src="", note="", lines=0))
        rec["lines"] += 1
        if e is not None and (rec["eur"] is None or e > rec["eur"]):
            rec["eur"] = e
        s = clean(r.get("aim_source_this_pass"))
        if s:
            rec["src"] = s
            rec["note"] = clean(r.get("aim_note"))

# --------------------------------------------------------------- published pair
pub = {}
with (DER / "AIM_Master_PN_Categories_Figkey_20260924.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pub[clean(r.get("part_number")).upper()] = r

# --------------------------------------------------------------- how each part got its label TODAY
# Aim source of the label, from the master's own stamp + the classified route.
def route_of(pn):
    c = cls.get(pn)
    m = mm.get(pn)
    stamp = m["changed"] if m else ""
    today = "export_aim_eq_20260924" in stamp or "export_pr00_20260924" in stamp
    if not today:
        return "not placed today"
    if c and c["src"] == "EPC figure name":
        return "wording rule on the EPC figure name"
    if c and c["src"] == "figure key, unanimous on the master":
        return "figure key unanimous on the master"
    # no EPC figure name recorded, yet placed -> the description-agreement route
    return "description agreement on the master"


P("=" * 78)
P("STEP 1 AGAIN - EURO ON THE PRICE LIST (correct parser)")
P("=" * 78)
P("price-list part numbers: %d" % len(cls))
tot = sum((c["eur"] or 0.0) for c in cls.values())
P("total list value of the price list: %.0f EUR" % tot)
P("")

groups = defaultdict(lambda: dict(n=0, eur=0.0))
for pn, c in cls.items():
    m = mm.get(pn)
    if not m:
        g = "no master row"
    elif realv(m["l1"]):
        g = "real family"
    elif clean(m["l1"]).lower().startswith("unknown"):
        g = "Unknown marker"
    else:
        g = "blank family"
    groups[g]["n"] += 1
    groups[g]["eur"] += (c["eur"] or 0.0)
P("%-18s %6s %14s" % ("group", "parts", "list EUR"))
for k, g in sorted(groups.items(), key=lambda kv: -kv[1]["eur"]):
    P("%-18s %6d %14.0f" % (k, g["n"], g["eur"]))
P("")

P("=" * 78)
P("STEP 6 - FAMILY VIEW")
P("=" * 78)
fam = defaultdict(lambda: dict(n=0, eur=0.0, route=Counter()))
for pn, c in cls.items():
    m = mm.get(pn)
    if not m or not realv(m["l1"]):
        continue
    f = fam[m["l1"]]
    f["n"] += 1
    f["eur"] += (c["eur"] or 0.0)
    f["route"][route_of(pn)] += 1

P("%-24s %6s %14s  %s" % ("family (Level 1)", "parts", "list EUR", "how placed"))
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["n"]):
    r = v["route"]
    P("%-24s %6d %14.0f  rule %d | key %d | desc %d | not today %d" % (
        k, v["n"], v["eur"],
        r["wording rule on the EPC figure name"],
        r["figure key unanimous on the master"],
        r["description agreement on the master"],
        r["not placed today"]))
P("")
P("--- biggest five by list value ---")
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["eur"])[:5]:
    r = v["route"]
    P("  %-24s %14.0f EUR over %3d parts   (rule %d | key %d | desc %d | not today %d)" % (
        k, v["eur"], v["n"],
        r["wording rule on the EPC figure name"],
        r["figure key unanimous on the master"],
        r["description agreement on the master"],
        r["not placed today"]))
P("")

P("--- the same five, split by whether the label was written today ---")
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["eur"])[:5]:
    new = sum(1 for pn, c in cls.items()
              if mm.get(pn) and realv(mm[pn]["l1"]) and mm[pn]["l1"] == k
              and ("export_aim_eq_20260924" in mm[pn]["changed"] or "export_pr00_20260924" in mm[pn]["changed"]))
    P("  %-24s %3d of %3d carry a label written today" % (k, new, v["n"]))
P("")

P("--- provenance of every part named today (%d parts) ---")
today = [pn for pn in cls if mm.get(pn) and (
    "export_aim_eq_20260924" in mm[pn]["changed"] or "export_pr00_20260924" in mm[pn]["changed"])]
P("parts carrying a today stamp: %d" % len(today))
rc = Counter(route_of(pn) for pn in today)
for k, v in rc.most_common():
    P("    %4d  %s" % (v, k))
P("")
eur_by_route = defaultdict(float)
for pn in today:
    eur_by_route[route_of(pn)] += (cls[pn]["eur"] or 0.0)
for k, v in sorted(eur_by_route.items(), key=lambda kv: -kv[1]):
    P("    %12.0f EUR  %s" % (v, k))
P("")

P("--- the 1,161 parts the EPC named, by route ---")
named = [pn for pn, c in cls.items() if c["src"] == "EPC figure name"]
P("parts with a recorded EPC figure name: %d" % len(named))
P("  of those, the figure name is an EPC name that the rules convert: %d" % len(named))
nonamed = [pn for pn, c in cls.items() if c["src"] != "EPC figure name"]
P("parts with NO EPC figure name recorded: %d" % len(nonamed))
nr = Counter(route_of(pn) for pn in nonamed)
for k, v in nr.most_common():
    P("    %4d  %s" % (v, k))
P("")

P("=" * 78)
P("STEP 7 - WHAT COULD NOT BE CHECKED WITHOUT THE EPC, IN PARTS AND EUROS")
P("=" * 78)
groups2 = defaultdict(lambda: dict(n=0, eur=0.0))
for pn, c in cls.items():
    m = mm.get(pn)
    if not m:
        g = "no master row (never placed)"
    elif not realv(m["l1"]):
        g = "open (marker or blank)"
    else:
        g = "placed"
    groups2[g]["n"] += 1
    groups2[g]["eur"] += (c["eur"] or 0.0)
for k, g in sorted(groups2.items(), key=lambda kv: -kv[1]["eur"]):
    P("%-30s %6d %14.0f EUR" % (k, g["n"], g["eur"]))
P("")
openp = [pn for pn, c in cls.items() if not (mm.get(pn) and realv(mm[pn]["l1"]))]
P("open parts: %d" % len(openp))
P("open list value: %.0f EUR  (%.1f%% of the list)" % (
    sum(cls[p]["eur"] or 0.0 for p in openp),
    100.0 * sum(cls[p]["eur"] or 0.0 for p in openp) / tot))
P("")
P("named open parts:")
for p in sorted(openp, key=lambda x: -(cls[x]["eur"] or 0.0)):
    m = mm.get(p)
    P("    %-12s %9.2f EUR  %-34s %s" % (
        p, cls[p]["eur"] or 0.0, clean(cls[p].get("note"))[:34] if False else "",
        ("no master row" if not m else ("marker" if clean(m["l1"]).lower().startswith("unknown") else "blank"))))

(OUT / "verify_family_euro.txt").write_text("\n".join(REP), encoding="utf-8")
