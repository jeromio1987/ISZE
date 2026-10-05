# -*- coding: utf-8 -*-
"""VERIFY final consolidation: the numbers that go into VERIFY.md."""
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


# ---- price lines (the 1,318) and the distinct list (1,310 Newest / 1,303 queue)
lines = list(csv.DictReader((EQ / "classified.csv").open(encoding="utf-8-sig")))
P("price lines in classified.csv: %d" % len(lines))
pn_line = {}
for r in lines:
    pn = clean(r.get("pn")).upper()
    e = num(r.get("Price"))
    rec = pn_line.setdefault(pn, dict(pn=pn, eur=None, lines=0))
    rec["lines"] += 1
    if e is not None and (rec["eur"] is None or e > rec["eur"]):
        rec["eur"] = e
P("distinct part numbers (Newest P/N): %d" % len(pn_line))
P("total list value over those: %.0f EUR" % sum((v["eur"] or 0) for v in pn_line.values()))
P("")

q = {clean(r.get("pn")).upper() for r in csv.DictReader((EQ / "queue.csv").open(encoding="utf-8-sig"))}
P("distinct part numbers in queue.csv: %d" % len(q))
outside = sorted(set(pn_line) - q)
P("in the price extract but never queued: %d  %s" % (len(outside), outside))
P("")

# ---- eq outcomes
eq = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        r = json.loads(line)
        eq[clean(r["pn"]).upper()] = r

# ---- master
mm = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = clean(r.get("part_number")).upper()
        mm[pn] = dict(pn=pn, l1=clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1")),
                      l2=clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2")),
                      l3=clean(r.get("aim_l3")), ch=clean(r.get("aim_changed")),
                      src=clean(r.get("aim_source")))

P("=" * 78)
P("STEP 7 - WHAT A FRESH EPC LOOKUP WOULD STILL BE NEEDED FOR")
P("=" * 78)
noeq, err = 0, 0
for pn in q:
    r = eq.get(pn)
    if not r:
        noeq += 1
    elif r.get("eq_status") == "NOT_FOUND":
        noeq += 1
    elif r.get("eq_status") == "ERROR":
        err += 1
P("part numbers where the EPC returned nothing (NOT_FOUND or no record): %d" % noeq)
P("part numbers where the lookup errored: %d" % err)
placed_no_epc = [pn for pn in q if (not eq.get(pn) or eq[pn].get("eq_status") != "FOUND")
                 and mm.get(pn) and realv(mm[pn]["l1"])]
eur_pne = sum((pn_line[pn]["eur"] or 0) for pn in placed_no_epc if pn in pn_line)
P("of those, now carrying a family (so the label came from something other than an EPC name): %d"
  % len(placed_no_epc))
P("their list value: %.0f EUR" % eur_pne)
P("")
errored = [pn for pn in q if eq.get(pn) and eq[pn].get("eq_status") == "ERROR"]
P("the errored one: %s" % errored)
for pn in errored:
    P("   description: %s ; master: %s" % (clean(mm.get(pn, {}).get("l1", "")),
                                           "not on master" if pn not in mm else clean(mm[pn]["l1"])))
found_empty_names = [pn for pn in q if eq.get(pn) and eq[pn].get("eq_status") == "FOUND"
                     and not clean(eq[pn].get("eq_fig_name"))]
P("FOUND but with no figure name recorded: %d" % len(found_empty_names))
fe_placed = [p for p in found_empty_names if mm.get(p) and realv(mm[p]["l1"])]
P("   placed anyway (figure key or description): %d" % len(fe_placed))
P("   still open: %d" % (len(found_empty_names) - len(fe_placed)))
P("")
P("parts placed TODAY but with NO EPC figure name of their own:")
today = [pn for pn in q if mm.get(pn) and "20260924" in mm[pn]["ch"] and realv(mm[pn]["l1"])]
today_named = [pn for pn in today if clean(eq.get(pn, {}).get("eq_fig_name"))]
P("   placed today: %d ; of those with their own EPC figure name: %d" % (len(today), len(today_named)))
P("   placed today WITHOUT a figure name: %d" % (len(today) - len(today_named)))
eur_no_name = sum((pn_line[pn]["eur"] or 0) for pn in today if pn not in set(today_named) and pn in pn_line)
P("   their list value: %.0f EUR" % eur_no_name)
P("")

P("=" * 78)
P("HEADLINE NUMBERS")
P("=" * 78)
real = sum(1 for pn in q if pn in mm and realv(mm[pn]["l1"]))
unk = sum(1 for pn in q if pn in mm and clean(mm[pn]["l1"]).lower().startswith("unknown"))
blank = sum(1 for pn in q if pn in mm and not realv(mm[pn]["l1"]) and not clean(mm[pn]["l1"]).lower().startswith("unknown"))
norow = sum(1 for pn in q if pn not in mm)
P("price-list part numbers          : %d" % len(q))
P("  real family                    : %d" % real)
P("  Unknown marker                 : %d" % unk)
P("  blank family                   : %d" % blank)
P("  no master row                  : %d" % norow)
P("  sum                            : %d" % (real + unk + blank + norow))
P("")

placed = [pn for pn in q if mm.get(pn) and realv(mm[pn]["l1"])]
tot = sum((pn_line[pn]["eur"] or 0) for pn in q)
P("total list value of the 1,303   : %.0f EUR" % tot)
P("on parts with a real family     : %.0f EUR (%.1f%%)" % (
    sum((pn_line[pn]["eur"] or 0) for pn in placed),
    100 * sum((pn_line[pn]["eur"] or 0) for pn in placed) / tot))
P("on open parts                   : %.0f EUR (%.1f%%)" % (
    sum((pn_line[pn]["eur"] or 0) for pn in q if pn not in placed),
    100 * sum((pn_line[pn]["eur"] or 0) for pn in q if pn not in placed) / tot))
P("")
P("largest open part: %s %.0f EUR" % (
    max((p for p in q if p not in placed), key=lambda p: pn_line[p]["eur"] or 0),
    max((pn_line[p]["eur"] or 0) for p in q if p not in placed)))

(OUT / "final_numbers.txt").write_text("\n".join(REP), encoding="utf-8")
