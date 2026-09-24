# -*- coding: utf-8 -*-
"""Final provenance, restricted to the 1,303 price-list part numbers."""
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
B44 = ROOT / "01_data" / "91_build" / "export_aim_append_20260924" / "decision_44_final.csv"
B164 = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924" / "decision_164_final.csv"
B43 = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924" / "decision_orphans.csv"
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


q = list(dict.fromkeys(clean(r.get("pn")).upper()
                       for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))))
qset = set(q)
P("distinct part numbers in the queue: %d" % len(q))
mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        mm[pn] = dict(l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
                      ch=clean(r.get("aim_changed")))
eq = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        r = json.loads(line)
        eq[clean(r["pn"]).upper()] = clean(r.get("eq_fig_name")), clean(r.get("eq_status"))
cls = {}
for r in csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")):
    pn = clean(r.get("pn")).upper()
    e = num(r.get("Price"))
    rec = cls.setdefault(pn, dict(eur=None, desc=clean(r.get("Description")),
                                 src="", note=""))
    if e is not None and (rec["eur"] is None or e > rec["eur"]):
        rec["eur"] = e
    s = clean(r.get("aim_source_this_pass"))
    if s:
        rec["src"] = s
        rec["note"] = clean(r.get("aim_note"))
desc_pns = {clean(r.get("pn")).upper()
            for p in (B44, B164) for r in csv.DictReader(p.open(encoding="utf-8-sig"))
            if clean(r.get("chosen_l1"))}
route_a = {clean(r.get("pn")).upper()
           for r in csv.DictReader(B43.open(encoding="utf-8-sig"))
           if clean(r.get("place")).lower() in ("true", "1") and clean(r.get("route")) == "a"}

placed = [p for p in q if mm.get(p) and realv(mm[p]["l1"])]
P("placed on the 1,303: %d" % len(placed))

buckets = Counter()
eur = defaultdict(float)
for p in placed:
    name, status = eq.get(p, ("", "NO_RECORD"))
    has_name = bool(name)
    if p in route_a:
        b = "EPC figure name through the wording rules (orphan pass)"
    elif p in desc_pns and has_name:
        b = "description agreement; own figure name agrees too"
    elif p in desc_pns:
        b = "description agreement, no EPC figure name of its own"
    elif has_name or cls[p]["src"] == "EPC figure name":
        b = "EPC figure name through the wording rules"
    elif cls[p]["src"] == "figure key, unanimous on the master":
        b = "figure key unanimous on the master"
    else:
        b = "other / carry-over label"
    buckets[b] += 1
    eur[b] += (cls[p]["eur"] or 0)
P("")
for k, v in buckets.most_common():
    P("  %5d parts  %11.0f EUR   %s" % (v, eur[k], k))
P("  %5d parts  %11.0f EUR   TOTAL" % (sum(buckets.values()), sum(eur.values())))
P("")

# sanity: of the description-route placed parts, how many have a figure name that agrees
agree = tot = 0
import re
sys.path.insert(0, str(EQ))
from aim_rules import RULES
RULES = sorted(RULES, key=lambda r: -len(r[0]))
for p in placed:
    if p not in desc_pns:
        continue
    name = eq.get(p, ("", ""))[0]
    if not name:
        continue
    tot += 1
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", name.upper())
    hit = None
    for ph, a, b, c in RULES:
        if ph in up:
            hit = (a, b, c)
            break
    if hit == (mm[p]["l1"], "", "") or (hit and hit[0] == mm[p]["l1"]):
        agree += 1
P("description-route placed parts whose own figure name points at the same Level 1: %d of %d"
  % (agree, tot))
P("")

P("carry-over labels (not written today): %d" % sum(
    1 for p in placed if "20260924" not in mm[p]["ch"]))
P("")
P("--- the five biggest families by list value ---")
fam = defaultdict(lambda: dict(n=0, eur=0.0, b=Counter()))
for p in placed:
    f = fam[mm[p]["l1"]]
    f["n"] += 1
    f["eur"] += (cls[p]["eur"] or 0)
    name = eq.get(p, ("", ""))[0]
    if p in desc_pns:
        k = "description"
    elif p in route_a or name or cls[p]["src"] == "EPC figure name":
        k = "EPC name"
    else:
        k = "figure key"
    f["b"][k] += 1
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["eur"])[:5]:
    P("  %-24s %11.0f EUR  %3d parts  (EPC name %d | description %d | key %d)" % (
        k, v["eur"], v["n"], v["b"]["EPC name"], v["b"]["description"], v["b"]["figure key"]))
P("")
P("all families:")
for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["n"]):
    P("  %-24s %11.0f EUR  %3d parts  (EPC name %d | description %d | key %d)" % (
        k, v["eur"], v["n"], v["b"]["EPC name"], v["b"]["description"], v["b"]["figure key"]))

(OUT / "final_provenance.txt").write_text("\n".join(REP), encoding="utf-8")
