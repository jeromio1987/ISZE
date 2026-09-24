# -*- coding: utf-8 -*-
"""Read-only probe: pin down the exact set the brief calls "the 819".

Measures several candidate definitions of "carries the Unknown marker as its family"
on the master, for the 1,097 open part numbers, and prints each count so the set the
brief names can be matched rather than guessed.

Writes nothing outside its own folder.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_unknown_clear_20260924"

MASTER = DER / "aim_master_v2.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"

MARKERS = {"unknown", "unknown review", "to review", "unclassified"}

LOG = []


def say(*p):
    line = " ".join(str(x) for x in p)
    print(line)
    LOG.append(line)


def bl(s):
    return (s or "").strip()


def is_marker(s):
    t = bl(s).lower()
    return t in MARKERS or t.startswith("unknown")


def norm_pn(s):
    return bl(s).upper()


# ---------------------------------------------------------------- the open set
open_rows = []
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        open_rows.append(r)
open_pns = [norm_pn(r["pnk"]) for r in open_rows]
say("open part numbers from open_parts_classified.csv:", len(open_pns), "distinct:", len(set(open_pns)))
say("group counts there:", dict(Counter(r["group"] for r in open_rows)))

# ---------------------------------------------------------------- the master
master_rows = []
with MASTER.open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    hdr = rd.fieldnames
    for r in rd:
        master_rows.append(r)
say("")
say("master rows:", len(master_rows))
say("master columns:", len(hdr), hdr)
by_pn = {bl(r["part_number"]): r for r in master_rows}
say("distinct master part numbers:", len(by_pn))

on_master = [p for p in open_pns if p in by_pn]
say("of the open set, on the master:", len(on_master), "| not:", len(open_pns) - len(on_master))

# marker test on a single row
def m1(r):   return is_marker(r["aim_l1"])
def m1f(r):  return is_marker(r["aim_l1_fixed"])
def m2(r):   return is_marker(r["aim_l2"])
def m2f(r):  return is_marker(r["aim_l2_fixed"])
def m3(r):   return is_marker(r["aim_l3"])
def any_marker(r):
    return any(is_marker(r.get(c)) for c in
               ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed")
               if c in r)

say("")
say("CANDIDATE DEFINITIONS on the 1,097 open part numbers")
defs = {
    "aim_l1 is a marker": lambda r: m1(r),
    "aim_l1_fixed is a marker": lambda r: m1f(r),
    "aim_l1 AND aim_l1_fixed are markers": lambda r: m1(r) and m1f(r),
    "aim_l1 OR aim_l1_fixed is a marker": lambda r: m1(r) or m1f(r),
    "any of l1/l2/l3/l1f/l2f is a marker": any_marker,
    "aim_l1 OR aim_l2 OR aim_l3 is a marker": lambda r: m1(r) or m2(r) or m3(r),
    "aim_l1_fixed OR aim_l2_fixed is a marker": lambda r: m1f(r) or m2f(r),
}
counts = {}
for name, fn in defs.items():
    got = [p for p in on_master if fn(by_pn[p])]
    counts[name] = len(got)
    say(f"  {name:52s} {len(got):6d}")

# every exact marker value seen, and where
say("")
say("EXACT MARKER STRINGS SEEN (open set, master row)")
vals = Counter()
for p in on_master:
    r = by_pn[p]
    for c in ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"):
        if is_marker(r.get(c)):
            vals[(c, bl(r.get(c)))] += 1
for k in sorted(vals):
    say("  ", k[0], "=", repr(k[1]), "->", vals[k])

# the overlay
ov_rows = {}
with OVERLAY.open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    o_hdr = rd.fieldnames
    for r in rd:
        ov_rows.setdefault(norm_pn(r["part_number"]), r)
say("")
say("overlay rows (distinct part numbers):", len(ov_rows))
say("overlay columns:", len(o_hdr))
say("overlay carries aim_l1_fixed:", "aim_l1_fixed" in o_hdr,
    "| aim_l2_fixed:", "aim_l2_fixed" in o_hdr,
    "| aim_l3_fixed:", "aim_l3_fixed" in o_hdr)

ov_marker = [p for p in open_pns
             if p in ov_rows and any(is_marker(ov_rows[p].get(c)) for c in
                                     ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))]
say("open parts whose OVERLAY carries a marker in aim_l*_fixed:", len(ov_marker))
ov_appl = [p for p in ov_marker if p not in by_pn]
say("  of those with no master row:", len(ov_appl))

ov_vals = Counter()
for p in ov_marker:
    r = ov_rows[p]
    for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
        if is_marker(r.get(c)):
            ov_vals[(c, bl(r.get(c)))] += 1
for k in sorted(ov_vals):
    say("   overlay", k[0], "=", repr(k[1]), "->", ov_vals[k])

# reconcile: master-marker set + overlay-only-marker
say("")
say("RECONCILIATION ATTEMPTS")
both = [p for p in on_master if m1(by_pn[p]) and m1f(by_pn[p])]
say("  master l1 AND l1_fixed marker:", len(both))
say("  master l1 OR l1_fixed marker :", counts["aim_l1 OR aim_l1_fixed is a marker"])
union = set(both) | set(ov_marker)
say("  union(master both, overlay marker):", len(union))
only_ov = [p for p in ov_marker if p not in both]
say("  overlay marker but not master-both:", len(only_ov))

# the 1,097 split as the brief states it
say("")
say("THE BRIEF'S THREE-WAY SPLIT, MEASURED")
n_marker = counts["any of l1/l2/l3/l1f/l2f is a marker"]
n_norow = len(open_pns) - len(on_master)
n_blank = len(on_master) - n_marker
say("  819-style (marker in the AIM columns):", n_marker)
say("  master row but no marker at all  :", n_blank)
say("  no master row                    :", n_norow)
say("  sum                              :", n_marker + n_blank + n_norow)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "probe_819_run.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
(OUT / "probe_819_counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
say("")
say("wrote", OUT / "probe_819_run.txt")
