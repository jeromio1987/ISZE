# -*- coding: utf-8 -*-
"""Where could '47 supporting parts' come from? Test the plausible readings."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

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
            rows.append(dict(pn=clean(r.get("part_number")), desc=clean(r.get("description")).upper(),
                             l1=l1, l2=l2, l3=clean(r.get("aim_l3")),
                             ch=clean(r.get("aim_changed")), fk=clean(r.get("fig_key"))))
    return rows


now = load(DER / "aim_master_v2.csv")
before = load(DER / "aim_master_v2.csv.bak_pre_export_append_20260924_135923")

CONN = ("Electrical", "Harness & Connectors", "Connector")


def n(rows, pred):
    return sum(1 for r in rows if pred(r) and realv(r["l1"]))


tests = [
    ("starts CONNECTOR, on the Connector leaf (NOW)", now, lambda r: r["desc"].startswith("CONNECTOR") and (r["l1"], r["l2"], r["l3"]) == CONN),
    ("starts CONNECTOR, on the Connector leaf (BEFORE today)", before, lambda r: r["desc"].startswith("CONNECTOR") and (r["l1"], r["l2"], r["l3"]) == CONN),
    ("text exactly 'CONNECTOR', anywhere (BEFORE)", before, lambda r: r["desc"] == "CONNECTOR"),
    ("text exactly 'CONNECTOR', on the Connector leaf (BEFORE)", before, lambda r: r["desc"] == "CONNECTOR" and (r["l1"], r["l2"], r["l3"]) == CONN),
    ("contains CONNECTOR, on the Connector leaf (NOW)", now, lambda r: "CONNECTOR" in r["desc"] and (r["l1"], r["l2"], r["l3"]) == CONN),
    ("contains CONNECTOR, on the Connector leaf (BEFORE)", before, lambda r: "CONNECTOR" in r["desc"] and (r["l1"], r["l2"], r["l3"]) == CONN),
    ("starts CONNECTOR, not on fig 816, on the Connector leaf (NOW)", now, lambda r: r["desc"].startswith("CONNECTOR") and (r["l1"], r["l2"], r["l3"]) == CONN and not r["fk"].startswith("816")),
    ("starts CONNECTOR, on the Connector leaf, fig 377 family (NOW)", now, lambda r: r["desc"].startswith("CONNECTOR") and (r["l1"], r["l2"], r["l3"]) == CONN and r["fk"].startswith("377")),
    ("whole Connector leaf (NOW)", now, lambda r: (r["l1"], r["l2"], r["l3"]) == CONN),
]
for label, rows, pred in tests:
    print("%-64s %4d" % (label, n(rows, pred)))

print()
print("fig keys present among master rows whose description starts CONNECTOR, on the leaf:")
c = Counter((r["fk"][:3]) for r in now if r["desc"].startswith("CONNECTOR") and (r["l1"], r["l2"], r["l3"]) == CONN)
for k, v in c.most_common():
    print("    fig %s : %d" % (k, v))
