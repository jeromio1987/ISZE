# -*- coding: utf-8 -*-
"""Definitive route table on the 1,303, built from the decision files + raw names."""
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
D44 = ROOT / "01_data" / "91_build" / "export_aim_append_20260924" / "decision_44_final.csv"
D164 = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924" / "decision_164_final.csv"
D43 = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924" / "decision_orphans.csv"

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
            l3=clean(r.get("aim_l3")), ch=clean(r.get("aim_changed")),
            desc=clean(r.get("description")))

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
    rec = cls.setdefault(pn, dict(eur=None, desc=clean(r.get("Description")), src=""))
    if e is not None and (rec["eur"] is None or e > rec["eur"]):
        rec["eur"] = e
    s = clean(r.get("aim_source_this_pass"))
    if s:
        rec["src"] = s

q = list(dict.fromkeys(clean(r.get("pn")).upper()
                       for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))))
placed = [p for p in q if mm.get(p) and realv(mm[p]["l1"])]


def decision_pns(path):
    out = set()
    for r in csv.DictReader(path.open(encoding="utf-8-sig")):
        if clean(r.get("chosen_l1")):
            out.add(clean(r.get("pn")).upper())
    return out


desc_route = decision_pns(D44) | decision_pns(D164)
orphan_route = {clean(r.get("pn")).upper() for r in csv.DictReader(D43.open(encoding="utf-8-sig"))
                if clean(r.get("place")).lower() in ("true", "1") and clean(r.get("route")) == "a"}

P("=== FINAL ROUTE TABLE (distinct part numbers on the 1,303) ===")
P("placed: %d   placed value: %.0f EUR" % (len(placed), sum(cls[p]["eur"] or 0 for p in placed)))
P("")
table = defaultdict(lambda: dict(n=0, eur=0.0, named=0))
for p in placed:
    status, name = eq.get(p, ("NO_RECORD", ""))
    hasname = bool(name)
    if p in desc_route:
        b = "description route (own figure name agrees)" if hasname else "description route (no figure name of its own)"
    elif p in orphan_route or (hasname and cls[p]["src"] == "EPC figure name"):
        b = "wording rule on the EPC figure name"
    elif cls[p]["src"] == "figure key, unanimous on the master":
        b = "figure key, unanimous on the master"
    else:
        b = "other"
    table[b]["n"] += 1
    table[b]["eur"] += (cls[p]["eur"] or 0)
    table[b]["named"] += 1 if hasname else 0
for k, v in sorted(table.items(), key=lambda kv: -kv[1]["n"]):
    P("  %5d parts  %11.0f EUR   %s" % (v["n"], v["eur"], k))
P("  %5d parts  %11.0f EUR   TOTAL" % (sum(v["n"] for v in table.values()),
                                        sum(v["eur"] for v in table.values())))
P("")
P("parts with a recorded EPC figure name: %d ; without: %d"
  % (sum(1 for p in placed if clean(eq.get(p, ('', ''))[1])),
     sum(1 for p in placed if not clean(eq.get(p, ('', ''))[1]))))
P("")
P("=== is the rule-on-name consistent with the master for the description-route parts? ===")
R = sorted(RULES, key=lambda r: -len(r[0]))


def rule_of(fn):
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fn or "").upper())
    for ph, a, b, c in R:
        if ph in up:
            return a
    return None


same = diff = noname = 0
for p in placed:
    if p not in desc_route:
        continue
    name = clean(eq.get(p, ("", ""))[1])
    if not name:
        noname += 1
        continue
    if rule_of(name) == mm[p]["l1"]:
        same += 1
    else:
        diff += 1
        P("   DIFF %s  fig %r -> %s ; master %s" % (p, name, rule_of(name), mm[p]["l1"]))
P("  description-route parts where the figure name agrees at Level 1: %d" % same)
P("  description-route parts where it does not: %d" % diff)
P("  description-route parts with no figure name: %d" % noname)
P("  their value: %.0f EUR" % sum(cls[p]["eur"] or 0 for p in desc_route
                                  if not clean(eq.get(p, ("", ""))[1])))
P("")

P("=== where does the fastener share land ===")
words = ("GASKET", "NUT", "BOLT", "BRACKET", "CLIP", "HOSE", "PIN", "SCREW", "WASHER", "STUD",
         "RING", "COLLAR", "BAND", "CLAMP", "SPACER", "PLATE", "PLUG", "SEAL", "CAP",
         "STOPPER", "FASTENER", "TIE", "KEY", "SHIM", "DOWEL", "ORIFICE")
small = [p for p in placed if any(w in cls[p]["desc"].upper() for w in words)]
P("  %d of %d = %.1f%% ; %.0f EUR = %.1f%% of placed value"
  % (len(small), len(placed), 100 * len(small) / len(placed),
     sum(cls[p]["eur"] or 0 for p in small),
     100 * sum(cls[p]["eur"] or 0 for p in small) / sum(cls[p]["eur"] or 0 for p in placed)))
P("")

P("=== the CONNECTOR rule support, measured narrowly ===")
leaf = ("Electrical", "Harness & Connectors", "Connector")
on_leaf = [pn for pn, r in mm.items() if realv(r["l1"]) and (r["l1"], r["l2"], r["l3"]) == leaf]
P("  master parts on the Connector leaf: %d" % len(on_leaf))
start = Counter()
for pn in on_leaf:
    d = mm[pn]["desc"].upper()
    if d.startswith("CONNECTOR"):
        start[d] += 1
P("  of those, description starts CONNECTOR: %d" % sum(start.values()))
for k, v in start.most_common():
    P("      %3d  %r" % (v, k))
nn = sum(v for k, v in start.items() if k.startswith("CONNECTOR; HARNESS"))
onh = sum(v for k, v in start.items() if k.startswith("CONNECTOR; HEAD LAMP"))
P("  exact-ish siblings for the three parts: CONNECTOR; HARNESS* = %d ; CONNECTOR; HEAD LAMP* = %d"
  % (nn, onh))
P("")

P("=== the 7 extract part numbers never queued, described properly ===")
allpn = {}
for r in csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")):
    pn = clean(r.get("pn")).upper()
    e = num(r.get("Price"))
    if pn not in allpn or (e is not None and e > (allpn[pn] or 0)):
        allpn[pn] = e
never = sorted(set(allpn) - set(q))
for p in never:
    m = mm.get(p)
    pub = clean(m["l1"]) if m else ""
    P("  %-12s %9.2f EUR  fixed=%r  published=%s"
      % (p, allpn[p] or 0, pub, "real family" if realv(pub) else "OPEN"))
P("  total %.0f EUR" % sum(allpn[p] or 0 for p in never))
P("")

P("=== Value vs Price ===")
rows = list(csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")))
lt = sum(1 for r in rows if (num(r.get("Value")) or 0) < (num(r.get("Price")) or 0))
P("  lines where Value < Price: %d of %d" % (lt, len(rows)))

(OUT / "definitive.txt").write_text("\n".join(REP), encoding="utf-8")
