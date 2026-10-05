# -*- coding: utf-8 -*-
"""Verify the specific claims made in VERIFY.md."""
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
from aim_rules import RULES

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def clean(s):
    return "" if s is None or str(s).strip().lower() in ("nan", "none", "null") else str(s).strip()


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


def num(s):
    s = clean(s).replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        mm[clean(r.get("part_number")).upper()] = dict(
            l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
            l2=clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2")),
            l3=clean(r.get("aim_l3")), ch=clean(r.get("aim_changed")))

eq = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        r = json.loads(line)
        eq[clean(r["pn"]).upper()] = (clean(r.get("eq_status")), clean(r.get("eq_fig_name")))

cls = {}
for r in csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")):
    pn = clean(r.get("pn")).upper()
    e = num(r.get("Price"))
    rec = cls.setdefault(pn, dict(eur=None, src="", desc=clean(r.get("Description"))))
    if e is not None and (rec["eur"] is None or e > rec["eur"]):
        rec["eur"] = e
    s = clean(r.get("aim_source_this_pass"))
    if s:
        rec["src"] = s

q = list(dict.fromkeys(clean(r.get("pn")).upper()
                       for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))))
placed = [p for p in q if mm.get(p) and realv(mm[p]["l1"])]

P("placed on the 1,303: %d" % len(placed))
P("placed value: %.0f EUR" % sum(cls[p]["eur"] or 0 for p in placed))
P("")

# --- by route, restricted to the 1,303, using classified source as the split
named = [p for p in placed if cls[p]["src"] == "EPC figure name"]
keyed = [p for p in placed if cls[p]["src"] == "figure key, unanimous on the master"]
other = [p for p in placed if p not in set(named) | set(keyed)]
P("EPC figure name route: %d parts  %.0f EUR" % (len(named), sum(cls[p]["eur"] or 0 for p in named)))
P("figure key route     : %d parts  %.0f EUR" % (len(keyed), sum(cls[p]["eur"] or 0 for p in keyed)))
P("no EPC name recorded : %d parts  %.0f EUR" % (len(other), sum(cls[p]["eur"] or 0 for p in other)))
P("")
of_other = [p for p in other if clean(eq.get(p, ("", ""))[1])]
of_other_none = [p for p in other if not clean(eq.get(p, ("", ""))[1])]
P("  of those, own figure name agrees anyway (description route): %d parts  %.0f EUR"
  % (len(of_other), sum(cls[p]["eur"] or 0 for p in of_other)))
P("  of those, no figure name at all (description route):          %d parts  %.0f EUR"
  % (len(of_other_none), sum(cls[p]["eur"] or 0 for p in of_other_none)))
P("")

# --- how many parts sit on a different system from their own figure name
P("=== parts whose system differs between their own figure name and their written family ===")
desc_pns = set(of_other) | set(of_other_none)
diff = []
for p in placed:
    fn = clean(eq.get(p, ("", ""))[1])
    if not fn:
        continue
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", fn.upper())
    hit = None
    for ph, a, b, c in sorted(RULES, key=lambda r: -len(r[0])):
        if ph in up:
            hit = (a, b, c)
            break
    if hit and hit[0] != mm[p]["l1"]:
        diff.append((p, cls[p]["desc"], fn, "%s > %s > %s" % (mm[p]["l1"], mm[p]["l2"], mm[p]["l3"]), hit))
P("parts where the family now on the master differs from the family their own figure name gives: %d" % len(diff))
P("  of those, placed by the description route: %d" % sum(1 for d in diff if d[0] in desc_pns))
P("  of those, placed by the figure name anyway: %d" % sum(1 for d in diff if d[0] not in desc_pns))
P("")
P("  their list value: %.0f EUR" % sum(cls[d[0]]["eur"] or 0 for d in diff))
diffs_fam = Counter((d[4][0], d[3].split(" > ")[0]) for d in diff)
P("  the family shifts involved:")
for k, v in diffs_fam.most_common(12):
    P("     %3d  figure says %-24s -> master says %s" % (v, k[0], k[1]))
P("")
P("  named exceptions (not on the figure name route):")
for d in diff:
    if d[0] not in desc_pns:
        P("     %-12s %-28s fig %-38s master %s" % (d[0], d[1][:28], d[2][:38], d[3]))
P("")

# --- Maintenance Service specifics
ms = [p for p in placed if cls[p]["src"] == "EPC figure name" and mm[p]["l1"] == "Maintenance Service"]
ms_shift = [d for d in diff if d[0] in set(ms)]
P("parts on Maintenance Service filed from a figure name: %d" % len(ms))
P("  of those, whose own figure name gives a DIFFERENT family: %d" % len(ms_shift))
for d in ms_shift:
    P("     %-12s %-26s %-38s master %s" % (d[0], d[1][:26], d[2][:38], d[3]))
P("")

# --- connector rule support
def con_support(phrases):
    n = 0
    for r in mm.values():
        if not realv(r["l1"]):
            continue
        d = ""
        n += 0
    # need descriptions; reload
    return None


desc_by_pn = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        desc_by_pn[clean(r.get("part_number")).upper()] = clean(r.get("description"))

for phrases in (["CONNECTOR; HEAD LAMP"], ["CONNECTOR; HEAD LAMP", "CONNECTOR; HARNESS"]):
    n = 0
    for pn, r in mm.items():
        if not realv(r["l1"]):
            continue
        d = desc_by_pn.get(pn, "").upper()
        if any(d.startswith(ph) for ph in phrases):
            n += 1
    P("parts on the Connector leaf whose description starts %s : %d" % (phrases, n))
P("")

# --- three connectors' value
v = sum(cls[p]["eur"] or 0 for p in ["8943633640", "8980626220", "8980680830"] if p in cls)
P("the three connectors together: %.2f EUR" % v)
P("")

# --- price extract parts never queued
allpn = {}
for r in csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")):
    pn = clean(r.get("pn")).upper()
    e = num(r.get("Price"))
    if pn not in allpn or (e is not None and e > (allpn[pn] or 0)):
        allpn[pn] = e
never = sorted(set(allpn) - set(q))
P("extract part numbers never queued: %d  %.0f EUR" % (len(never), sum(allpn[p] or 0 for p in never)))
for p in never:
    P("   %-12s %9.2f  %s" % (p, allpn[p] or 0, clean(mm.get(p, {}).get("l1", ""))))
P("")

# --- fastener share on the 1,303
words = ("GASKET", "NUT", "BOLT", "BRACKET", "CLIP", "HOSE", "PIN", "SCREW", "WASHER",
         "STUD", "RING", "COLLAR", "BAND", "CLAMP", "SPACER", "PLATE", "PLUG", "SEAL",
         "CAP", "STOPPER", "FASTENER", "TIE", "KEY", "SHIM", "COVER-BOLT", "DOWEL")
small = [p for p in placed if any(w in cls[p]["desc"].upper() for w in words)]
P("fastener/small parts among the 1,224: %d (%.1f%%)  %.0f EUR (%.1f%% of placed value)"
  % (len(small), 100 * len(small) / len(placed),
     sum(cls[p]["eur"] or 0 for p in small),
     100 * sum(cls[p]["eur"] or 0 for p in small) / sum(cls[p]["eur"] or 0 for p in placed)))
P("")

# --- Value vs Price
rows = list(csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")))
vp = 0
for r in rows:
    a, b = num(r.get("Value")), num(r.get("Price"))
    if a is not None and b is not None and a < b:
        vp += 1
P("lines where Value < Price : %d of %d" % (vp, len(rows)))
P("")

# --- 8982909802
p = "8982909802"
fn = clean(eq.get(p, ("", ""))[1])
P("%s on the master: %s ; EPC figure name: %r ; is it in the queue? %s"
  % (p, "%s > %s > %s" % (mm[p]["l1"], mm[p]["l2"], mm[p]["l3"]) if p in mm else "no row",
     fn, p in q))

(OUT / "verify_claims.txt").write_text("\n".join(REP), encoding="utf-8")
