# -*- coding: utf-8 -*-
"""VERIFY: definitive per-part provenance for the 1,230 parts that carry a real family.

Sources of truth, in this order:
  * decision_44_final.csv   (44 appended)  -> description agreement
  * decision_164_final.csv  (162 filled)   -> description agreement
  * decision_orphans.csv    (43, route a)  -> EPC figure name through the wording rules
  * classified.csv aim_source_this_pass    -> EPC figure name | figure key unanimous
Read-only.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
B44 = ROOT / "01_data" / "91_build" / "export_aim_append_20260924"
B164 = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
B43 = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"
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


# ---------------------------------------------------------------- inputs
mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        mm[pn] = dict(pn=pn,
                      l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
                      l2=clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2")),
                      l3=clean(r.get("aim_l3")),
                      changed=clean(r.get("aim_changed")),
                      source=clean(r.get("aim_source")))


def load(path, key="pn"):
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            rows[clean(r.get(key)).upper()] = r
    return rows


d44 = load(B44 / "decision_44_final.csv")
d164 = load(B164 / "decision_164_final.csv")
d43 = load(B43 / "decision_orphans.csv")

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

d43_route = {}
for pn, r in d43.items():
    if clean(r.get("place")).lower() in ("true", "1"):
        d43_route[pn] = clean(r.get("route"))

# ---------------------------------------------------------------- provenance
ROUTE_RULE = "EPC figure name read through the wording rules"
ROUTE_KEY = "figure key that is unanimous on the master"
ROUTE_DESC = "exact description agreeing on the master"


def route_of(pn):
    m = mm.get(pn)
    if not m or not realv(m["l1"]):
        return "open"
    stamp = m["changed"]
    today = ("export_aim_eq_20260924" in stamp) or ("export_pr00_20260924" in stamp)
    if pn in d44 or pn in d164:
        return ROUTE_DESC
    if d43_route.get(pn) == "a":
        return ROUTE_RULE
    c = cls.get(pn)
    if c and c["src"] == "EPC figure name":
        return ROUTE_RULE
    if c and c["src"] == "figure key, unanimous on the master":
        return ROUTE_KEY
    if today:
        return ROUTE_RULE
    return "not placed today"


P("=" * 78)
P("PROVENANCE OF THE 1,230 PARTS THAT CARRY A REAL FAMILY")
P("=" * 78)
placed = [pn for pn in cls if mm.get(pn) and realv(mm[pn]["l1"])]
P("placed parts on the price list: %d" % len(placed))
P("")
rc = Counter(route_of(pn) for pn in placed)
ER = defaultdict(float)
for pn in placed:
    ER[route_of(pn)] += (cls[pn]["eur"] or 0.0)
for k, v in rc.most_common():
    P("  %5d parts  %12.0f EUR   %s" % (v, ER[k], k))
P("  %5d parts  %12.0f EUR   TOTAL" % (len(placed), sum(ER.values())))
P("")
P("overlap check - parts in two decision files at once: %d"
  % len(set(d44) & set(d164)))
P("  44-file placed: %d ; 164-file placed: %d"
  % (len(d44), sum(1 for r in d164.values() if clean(r.get("chosen_l1")))))
P("  43-file route a: %d" % sum(1 for v in d43_route.values() if v == "a"))
P("")

P("=" * 78)
P("THE FIVE BIGGEST FAMILIES BY LIST VALUE, WITH THEIR ROUTE MIX")
P("=" * 78)
fam = defaultdict(lambda: dict(n=0, eur=0.0, route=Counter()))
for pn in placed:
    f = fam[mm[pn]["l1"]]
    f["n"] += 1
    f["eur"] += (cls[pn]["eur"] or 0.0)
    f["route"][route_of(pn)] += 1
P("%-24s %5s %11s %8s %8s %6s" % ("family", "parts", "list EUR", "rule", "key", "desc"))
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["eur"])[:8]:
    P("%-24s %5d %11.0f %8d %8d %6d" % (
        k, v["n"], v["eur"],
        v["route"][ROUTE_RULE], v["route"][ROUTE_KEY], v["route"][ROUTE_DESC]))
P("")
P("all families, by part count:")
P("%-24s %5s %11s %8s %8s %6s" % ("family", "parts", "list EUR", "rule", "key", "desc"))
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["n"]):
    P("%-24s %5d %11.0f %8d %8d %6d" % (
        k, v["n"], v["eur"],
        v["route"][ROUTE_RULE], v["route"][ROUTE_KEY], v["route"][ROUTE_DESC]))
P("")

with (OUT / "provenance.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pn", "description", "list_eur", "family_l1", "family_l2", "family_l3", "route", "changed_stamp"])
    for pn in placed:
        m = mm[pn]
        w.writerow([pn, "", "%.2f" % (cls[pn]["eur"] or 0.0), m["l1"], m["l2"], m["l3"],
                    route_of(pn), m["changed"]])

(OUT / "provenance_report.txt").write_text("\n".join(REP), encoding="utf-8")
