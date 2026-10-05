# -*- coding: utf-8 -*-
"""What does the PUBLISHED table show, and can the brief's 67 open be reproduced?"""
from __future__ import annotations

import csv
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
    return "" if s is None or str(s).strip().lower() in ("nan", "none", "null") else str(s).strip()


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


q = list(dict.fromkeys(clean(r.get("pn")).upper()
                       for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))))
rows = list(csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig")))
qrow = {}
for r in rows:
    pn = clean(r.get("pn")).upper()
    if pn not in qrow:
        qrow[pn] = r

# candidate readings of the queue file's own recorded state
for col in ("cur_aim_l1", "cur_aim_l2", "cur_aim_l3"):
    real = unk = blank = 0
    for pn in q:
        v = clean(qrow[pn].get(col))
        if realv(v):
            real += 1
        elif v.lower().startswith("unknown"):
            unk += 1
        else:
            blank += 1
    P("queue.csv %-12s : real %4d | Unknown %4d | blank %4d | open %d"
      % (col, real, unk, blank, unk + blank))

# the master
mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        mm[clean(r.get("part_number")).upper()] = r
real = unk = blank = norow = 0
for pn in q:
    r = mm.get(pn)
    if not r:
        norow += 1
        continue
    v = clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1"))
    if realv(v):
        real += 1
    elif v.lower().startswith("unknown"):
        unk += 1
    else:
        blank += 1
P("aim_master_v2  : real %4d | Unknown %4d | blank %4d | no row %4d | open %d"
  % (real, unk, blank, norow, unk + blank + norow))

# the overlay
ov = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        ov.setdefault(clean(r.get("part_number")).upper(), r)
real = unk = blank = norow = 0
for pn in q:
    r = ov.get(pn)
    if not r:
        norow += 1
        continue
    v = clean(r.get("aim_l1_fixed"))
    if realv(v):
        real += 1
    elif v.lower().startswith("unknown"):
        unk += 1
    else:
        blank += 1
P("overlay        : real %4d | Unknown %4d | blank %4d | no row %4d | open %d"
  % (real, unk, blank, norow, unk + blank + norow))

# the published file
pub = {}
with (DER / "AIM_Master_PN_Categories_Figkey_20260924.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pub[clean(r.get("part_number")).upper()] = r
real = unk = blank = norow = 0
for pn in q:
    r = pub.get(pn)
    if not r:
        norow += 1
        continue
    v = clean(r.get("aim_level_1"))
    if realv(v):
        real += 1
    elif v.lower().startswith("unknown"):
        unk += 1
    else:
        blank += 1
P("PUBLISHED pair : real %4d | Unknown %4d | blank %4d | no row %4d | open %d"
  % (real, unk, blank, norow, unk + blank + norow))
P("")
P("the brief's 25 + 31 + 11 = 67 reading:")
# 25 marker rows "on the classification overlay" -- already measured 25
P("  overlay markers measured: %d" % unk)
P("  so 67 would need 25 markers + 31 wording rows + 11 no-row")
P("  measured overlay blank-with-a-row: %d" % blank)
P("  -> 25 + %d + 11 = %d" % (blank, 25 + blank + 11))
P("")
P("published-file family mix (what a person filtering the published table sees):")
c = Counter(clean(pub[pn]["aim_level_1"]) for pn in q if pn in pub and realv(clean(pub[pn]["aim_level_1"])))
P("  distinct families present: %d" % len(c))
for k, v in c.most_common():
    P("    %4d  %s" % (v, k))

(OUT / "verify_published.txt").write_text("\n".join(REP), encoding="utf-8")
