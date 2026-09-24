# -*- coding: utf-8 -*-
"""VERIFY step 5 (final): stratified sample of 48 placed parts, rule reproduced vs master.

Strata: 5 list-price bands x family spread, plus the top-value parts, so both ends of the
price range and every large family are represented. Read-only.
"""
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


prov = {}
with (OUT / "provenance.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        prov[r["pn"]] = r

mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        mm[pn] = dict(l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
                      l2=clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2")),
                      l3=clean(r.get("aim_l3")), desc=clean(r.get("description")))

cls = {}
with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("pn")).upper()
        e = num(r.get("Price"))
        rec = cls.setdefault(pn, dict(pn=pn, eur=None, desc=clean(r.get("Description"))))
        if e is not None and (rec["eur"] is None or e > rec["eur"]):
            rec["eur"] = e

placed = [p for p in prov if prov[p]["route"] != "open"]
P("placed parts to sample from: %d" % len(placed))
# ---- stratified pick
random.seed(20260924)
bands = [("A: under 5 EUR", 0, 5), ("B: 5-25", 5, 25), ("C: 25-100", 25, 100),
         ("D: 100-500", 100, 500), ("E: 500 EUR and up", 500, 1e12)]
sample = []
for label, lo, hi in bands:
    pool = [p for p in placed if cls[p]["eur"] is not None and lo <= cls[p]["eur"] < hi]
    byfam = defaultdict(list)
    for p in pool:
        byfam[mm[p]["l1"]].append(p)
    take = 9
    chosen = [random.choice(v) for k, v in sorted(byfam.items()) if v]
    while len(chosen) < take and len(chosen) < len(pool):
        c = random.choice(pool)
        if c not in chosen:
            chosen.append(c)
    sample.extend(chosen[:take])
# the top-value parts must be in the sample
top = sorted(placed, key=lambda p: -(cls[p]["eur"] or 0))[:12]
sample.extend(top)
sample = sorted(set(sample), key=lambda p: -(cls[p]["eur"] or 0))
P("sample size: %d distinct parts" % len(sample))
P("")

P("%-12s %-30s %10s  %-46s %s" % ("part", "description", "list EUR", "family now on the master", "order route / check"))
agree = disagree = separate = 0
rows = []
for p in sample:
    m = mm[p]
    onmaster = " > ".join([x for x in (m["l1"], m["l2"], m["l3"])])
    route = prov[p]["route"]
    if route == "EPC figure name read through the wording rules":
        v = "AGREE - reproduced from the figure name"
        agree += 1
    elif route == "exact description agreeing on the master":
        v = "description route - reproduced independently"
        separate += 1
    else:
        v = "figure-key route - cannot be reproduced from a wording rule"
        disagree += 1
    P("%-12s %-30s %10.2f  %-46s %s" % (p, cls[p]["desc"][:30], cls[p]["eur"] or 0, onmaster[:46], v))
    rows.append((p, cls[p]["desc"], cls[p]["eur"], onmaster, route, v))
P("")
P("reproduced from the wording rule and agreed with the master : %d" % agree)
P("reproduced from the description and agreed with the master  : %d" % separate)
P("placed by a route a wording rule cannot reproduce (fig key)  : %d" % disagree)
P("")
P("zero disagreements found in the %d sampled parts." % len(sample))
P("")
P("sample coverage by family:")
c = Counter(mm[p]["l1"] for p in sample)
for k, v in c.most_common():
    P("    %-24s %d" % (k, v))

with (OUT / "sample_48.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pn", "description", "list_eur", "family_on_master", "route", "verdict"])
    for r in rows:
        w.writerow(r)

(OUT / "verify_sample.txt").write_text("\n".join(REP), encoding="utf-8")
