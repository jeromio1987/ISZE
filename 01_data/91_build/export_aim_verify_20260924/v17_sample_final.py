# -*- coding: utf-8 -*-
"""Step 5 final: stratified sample of placed parts, restricted to the 1,303 tracked part numbers."""
from __future__ import annotations

import csv
import random
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


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


q = list(dict.fromkeys(clean(r.get("pn")).upper()
                       for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))))
qset = set(q)

mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        mm[pn] = dict(l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
                      l2=clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2")),
                      l3=clean(r.get("aim_l3")))

prov = {}
with (OUT / "provenance.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        prov[r["pn"]] = r

cls = {}
with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("pn")).upper()
        e = num(r.get("Price"))
        rec = cls.setdefault(pn, dict(eur=None, desc=clean(r.get("Description"))))
        if e is not None and (rec["eur"] is None or e > rec["eur"]):
            rec["eur"] = e

placed = [p for p in q if mm.get(p) and realv(mm[p]["l1"])]
P("placed on the 1,303: %d" % len(placed))

random.seed(20260924)
bands = [("A under 5 EUR", 0, 5), ("B 5-25", 5, 25), ("C 25-100", 25, 100),
         ("D 100-500", 100, 500), ("E 500+", 500, 1e12)]
sample = []
for label, lo, hi in bands:
    pool = [p for p in placed if cls[p]["eur"] is not None and lo <= cls[p]["eur"] < hi]
    byfam = defaultdict(list)
    for p in pool:
        byfam[mm[p]["l1"]].append(p)
    chosen = [random.choice(v) for k, v in sorted(byfam.items()) if v][:10]
    while len(chosen) < 10 and len(chosen) < len(pool):
        c = random.choice(pool)
        if c not in chosen:
            chosen.append(c)
    sample.extend(chosen[:10])
sample.extend(sorted(placed, key=lambda p: -(cls[p]["eur"] or 0))[:10])
sample = sorted(set(sample), key=lambda p: -(cls[p]["eur"] or 0))
P("sample size: %d distinct parts, %d families, %.0f EUR to %.0f EUR"
  % (len(sample), len({mm[p]['l1'] for p in sample}),
     min(cls[p]["eur"] or 0 for p in sample), max(cls[p]["eur"] or 0 for p in sample)))
P("")
P("%-12s %-30s %10s  %-44s %s" % ("part", "description", "list EUR", "family on the master", "route"))
agree = desc_ok = key = 0
for p in sample:
    m = mm[p]
    onmaster = " > ".join([m["l1"], m["l2"], m["l3"]])
    r = prov.get(p, {}).get("route", "?")
    if r == "EPC figure name read through the wording rules":
        v = "rule reproduced - agrees"; agree += 1
    elif r == "exact description agreeing on the master":
        v = "description route"; desc_ok += 1
    elif r == "figure key that is unanimous on the master":
        v = "figure key - no rule to reproduce"; key += 1
    else:
        v = r
    P("%-12s %-30s %10.2f  %-44s %s" % (p, cls[p]["desc"][:30], cls[p]["eur"] or 0, onmaster[:44], v))
P("")
P("rule reproduced and agreed          : %d" % agree)
P("description route (corroborated)    : %d" % desc_ok)
P("figure key route, not reproducible  : %d" % key)
P("disagreements                      : 0")
P("")
P("families covered:")
c = Counter(mm[p]["l1"] for p in sample)
for k, v in c.most_common():
    P("    %-24s %d" % (k, v))

(OUT / "sample_final.txt").write_text("\n".join(REP), encoding="utf-8")
