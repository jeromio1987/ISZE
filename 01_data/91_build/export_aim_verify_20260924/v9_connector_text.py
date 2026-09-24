# -*- coding: utf-8 -*-
"""VERIFY: the bare 'CONNECTOR' placements - where did the 14 vs the 4 come from?"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "91_build" / "export_aim_verify_20260924"

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def clean(s):
    return "" if s is None or str(s).strip().lower() in ("nan", "none") else str(s).strip()


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


def load(p):
    rows = []
    with p.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            l1 = clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1"))
            l2 = clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2"))
            rows.append(dict(pn=clean(r.get("part_number")), desc=clean(r.get("description")),
                             l1=l1, l2=l2, l3=clean(r.get("aim_l3")),
                             ch=clean(r.get("aim_changed")),
                             src=clean(r.get("aim_source"))))
    return rows


now = load(DER / "aim_master_v2.csv")
before = load(DER / "aim_master_v2.csv.bak_pre_export_append_20260924_135923")

P("=== master rows with description exactly 'CONNECTOR' ===")
for label, rows in [("BEFORE today's run", before), ("NOW", now)]:
    c = [(r["pn"], r["l1"], r["l2"], r["l3"]) for r in rows if r["desc"].upper() == "CONNECTOR"]
    placed = [x for x in c if realv(x[1])]
    P("-- %s : %d rows, %d placed" % (label, len(c), len(placed)))
    for k, v in Counter((x[1], x[2], x[3]) for x in placed).most_common():
        P("      %4d  %s > %s > %s" % (v, k[0], k[1], k[2]))
P("")
P("=== the parts labelled TODAY (any description) whose text is exactly 'CONNECTOR' ===")
for r in sorted(now, key=lambda x: x["pn"]):
    if r["desc"].upper() == "CONNECTOR" and "20260924" in r["ch"]:
        P("    %-12s %-46s [%s]" % (r["pn"], "%s > %s > %s" % (r["l1"], r["l2"], r["l3"]), r["ch"]))
P("")
P("=== what the classified.csv route said for those ===")
cls = {}
with (ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "classified.csv").open(
        encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        cls[clean(r.get("pn")).upper()] = r
for r in sorted(now, key=lambda x: x["pn"]):
    if r["desc"].upper() == "CONNECTOR":
        c = cls.get(r["pn"])
        if c:
            P("    %-12s src=%-40r note=%-34r classified=%s" % (
                r["pn"], clean(c.get("aim_source_this_pass")), clean(c.get("aim_note"))[:34],
                "%s > %s > %s" % (clean(c.get("aim_level_1")), clean(c.get("aim_level_2")),
                                  clean(c.get("aim_level_3")))))

(OUT / "verify_connector_text.txt").write_text("\n".join(REP), encoding="utf-8")
