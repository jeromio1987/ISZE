# -*- coding: utf-8 -*-
"""The length ties: which parts depend on document order, and where did they land?"""
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
        eq[clean(r["pn"]).upper()] = clean(r.get("eq_fig_name"))

queue = list(csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig")))
qrow = {}
for r in queue:
    qrow.setdefault(clean(r.get("pn")).upper(), r)

ordered = sorted(enumerate(RULES), key=lambda t: (-len(t[1][0]), t[0]))


def hits(fig):
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig or "").upper())
    return [(i, p, l1, l2, l3) for i, (p, l1, l2, l3) in enumerate(RULES) if p in up]


P("=" * 78)
P("PARTS WHOSE LABEL DEPENDS ON A LENGTH TIE (document order decides)")
P("=" * 78)
tie_parts = []
for pn, fig in sorted(eq.items()):
    h = hits(fig)
    if not h:
        continue
    top = len(h[0][1])
    tied = [x for x in h if len(x[1]) == top]
    if len(tied) < 2:
        continue
    rest = sorted(tied, key=lambda x: x[0])
    tie_parts.append((pn, fig, rest[0], rest[1]))
P("parts affected: %d" % len(tie_parts))
P("")
bypair = defaultdict(list)
for pn, fig, a, b in tie_parts:
    bypair[(a, b)].append(pn)
for (a, b), pns in sorted(bypair.items(), key=lambda kv: -len(kv[1])):
    P("--- tie: %r (doc#%d -> %s > %s > %s)  vs  %r (doc#%d -> %s > %s > %s)"
      % (a[1], a[0], a[2], a[3], a[4], b[1], b[0], b[2], b[3], b[4]))
    P("    %d parts on the price list fall on a figure name carrying both" % len(pns))
    for pn in pns:
        m = mm.get(pn, {})
        fig = eq[pn]
        P("      %-12s %-34s fig=%-42s now %s" % (
            pn, (clean(qrow.get(pn, {}).get("Description")) or "")[:34], fig[:42],
            ("%s > %s > %s" % (m.get("l1", ""), m.get("l2", ""), m.get("l3", ""))) if m and realv(m.get("l1", "")) else "(open)"))
    P("")
P("")
P("every part on figure name containing 'INSTRUMENT PANEL' and its leaf:")
c = Counter()
for pn, fig in eq.items():
    if "INSTRUMENT PANEL" in fig.upper():
        m = mm.get(pn)
        c[("%s > %s > %s" % (m["l1"], m["l2"], m["l3"])) if m and realv(m["l1"]) else "(open)"] += 1
for k, v in c.most_common():
    P("    %4d  %s" % (v, k))
P("")
P("every part on figure name containing 'OIL COOLER' and its leaf:")
c = Counter()
for pn, fig in eq.items():
    if "OIL COOLER" in fig.upper():
        m = mm.get(pn)
        c[("%s > %s > %s" % (m["l1"], m["l2"], m["l3"])) if m and realv(m["l1"]) else "(open)"] += 1
for k, v in c.most_common():
    P("    %4d  %s" % (v, k))
P("")
P("every part on figure name containing 'FUEL FILTER' and its leaf:")
c = Counter()
for pn, fig in eq.items():
    if "FUEL FILTER" in fig.upper():
        m = mm.get(pn)
        c[("%s > %s > %s" % (m["l1"], m["l2"], m["l3"])) if m and realv(m["l1"]) else "(open)"] += 1
for k, v in c.most_common():
    P("    %4d  %s" % (v, k))
P("")
P("every part on figure name containing 'DEF TANK' and its leaf:")
c = Counter()
for pn, fig in eq.items():
    if "DEF TANK" in fig.upper():
        m = mm.get(pn)
        c[("%s > %s > %s" % (m["l1"], m["l2"], m["l3"])) if m and realv(m["l1"]) else "(open)"] += 1
for k, v in c.most_common():
    P("    %4d  %s" % (v, k))
P("")
m = mm.get("8974210030")
P("8974210030 now: %s > %s > %s" % (m["l1"], m["l2"], m["l3"]) if m else "not on master")
P("parts on Cabin Interior > Dashboard & Controls > Knob: %d"
  % sum(1 for x in mm.values() if realv(x["l1"]) and (x["l1"], x["l2"], x["l3"]) == ("Cabin Interior", "Dashboard & Controls", "Knob")))

(OUT / "verify_ties.txt").write_text("\n".join(REP), encoding="utf-8")
