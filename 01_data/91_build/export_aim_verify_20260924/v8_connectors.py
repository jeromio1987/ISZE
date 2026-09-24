# -*- coding: utf-8 -*-
"""VERIFY step 4 (final): CONNECTOR support and the three connectors' fig keys."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_verify_20260924")

REP = []
def P(s=""):
    print(s)
    REP.append(s)


def clean(s):
    return "" if s is None or str(s).strip().lower() in ("nan", "none") else str(s).strip()


def realv(v):
    v = clean(v)
    return bool(v) and not v.lower().startswith("unknown")


rows = []
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        l1 = clean(r.get("aim_l1_fixed")) or clean(r.get("aim_l1"))
        l2 = clean(r.get("aim_l2_fixed")) or clean(r.get("aim_l2"))
        l3 = clean(r.get("aim_l3"))
        rows.append(dict(pn=clean(r.get("part_number")), desc=clean(r.get("description")),
                         l1=l1, l2=l2, l3=l3, ch=clean(r.get("aim_changed")),
                         fk=clean(r.get("fig_key"))))
placed = [r for r in rows if realv(r["l1"])]
P("master rows with a real family: %d" % len(placed))

con = [r for r in placed if r["desc"].upper().startswith("CONNECTOR")]
P("of those, description starts CONNECTOR: %d" % len(con))
target = [r for r in con if r["l3"] == "Connector" and r["l2"] == "Harness & Connectors"]
P("  on Electrical > Harness & Connectors > Connector: %d" % len(target))
P("")
P("their exact descriptions and the leaf they sit on:")
c = Counter((r["desc"], r["l1"], r["l2"], r["l3"]) for r in con)
for k, v in c.most_common():
    P("   %4d  %-40s  %s > %s > %s" % (v, k[0][:40], k[1], k[2], k[3]))
P("")
exact = sum(v for k, v in c.items() if k[0].upper() == "CONNECTOR" and k[3] == "Connector")
P("description exactly 'CONNECTOR' on that leaf: %d" % exact)
P("")
P("parts starting CONNECTOR that were labelled TODAY:")
for r in sorted(con, key=lambda x: x["desc"]):
    if "20260924" in r["ch"]:
        P("    %-12s %-34s %s > %s > %s  [%s]" % (r["pn"], r["desc"][:34], r["l1"], r["l2"], r["l3"], r["ch"]))
P("")
P("fig keys of the three unplaced connectors:")
for pn in ["8943633640", "8980626220", "8980680830"]:
    ir = [r for r in rows if r["pn"] == pn]
    P("    %s -> %s" % (pn, ir[0]["fk"] if ir else "(no row)"))
P("")
P("master rows sharing those keys / that figure number:")
for fk in ["816-002", "816-090"]:
    s = [r for r in rows if r["fk"] == fk]
    P("    %-8s : %d master rows" % (fk, len(s)))
    for r in s:
        P("        %-12s %-30s family=%s" % (r["pn"], r["desc"][:30], "%s > %s > %s" % (r["l1"], r["l2"], r["l3"]) if realv(r["l1"]) else "(blank)"))
s816 = [r for r in rows if r["fk"].startswith("816")]
P("    figure number 816 (all keys): %d master rows, %d carrying a family" % (
    len(s816), sum(1 for r in s816 if realv(r["l1"]))))
for r in s816:
    P("        %-12s %-30s %s" % (r["pn"], r["desc"][:30], "%s > %s > %s" % (r["l1"], r["l2"], r["l3"]) if realv(r["l1"]) else "(blank)"))

(OUT / "verify_connectors.txt").write_text("\n".join(REP), encoding="utf-8")
