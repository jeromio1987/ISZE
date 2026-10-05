# -*- coding: utf-8 -*-
"""Read-only probe 2: explain the difference between 845 (master marker rows) and
819 (overlay marker rows) so the set the brief names can be identified exactly.

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
PAIR = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"

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


open_rows = []
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    open_rows = list(csv.DictReader(fh))
open_pns = [norm_pn(r["pnk"]) for r in open_rows]

master = {}
with MASTER.open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        master[bl(r["part_number"])] = r

ov_all = {}
ov_dupes = Counter()
with OVERLAY.open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        k = norm_pn(r["part_number"])
        ov_dupes[k] += 1
        ov_all.setdefault(k, []).append(r)
say("overlay part numbers:", len(ov_all), "| with more than one row:", sum(1 for v in ov_dupes.values() if v > 1))

master_marker = [p for p in open_pns if p in master and any(
    is_marker(master[p].get(c)) for c in ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"))]
overlay_marker = [p for p in open_pns if p in ov_all and any(
    any(is_marker(x.get(c)) for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))
    for x in ov_all[p])]
say("")
say("master marker:", len(master_marker), "| overlay marker:", len(overlay_marker))
diff = sorted(set(master_marker) - set(overlay_marker))
say("in master-marker but NOT overlay-marker:", len(diff))
say("in overlay-marker but NOT master-marker:", len(set(overlay_marker) - set(master_marker)))

say("")
say("THE DIFFERENCE ROWS — every aim column on the master, then the overlay")
for p in diff:
    m = master[p]
    say(f"  {p}  desc={bl(m['description'])[:34]:34}")
    say(f"      master : l1={bl(m['aim_l1'])!r} l2={bl(m['aim_l2'])!r} l3={bl(m['aim_l3'])!r} "
        f"l1f={bl(m['aim_l1_fixed'])!r} l2f={bl(m['aim_l2_fixed'])!r} "
        f"src={bl(m['aim_source'])!r} has_aim={bl(m['has_aim'])!r}")
    if p in ov_all:
        for x in ov_all[p]:
            say(f"      overlay: l1f={bl(x.get('aim_l1_fixed'))!r} l2f={bl(x.get('aim_l2_fixed'))!r} "
                f"l3f={bl(x.get('aim_l3_fixed'))!r} catalog={bl(x.get('catalog_l1'))!r}/"
                f"{bl(x.get('catalog_l2'))!r}/{bl(x.get('catalog_l3'))!r} "
                f"aim_src={bl(x.get('aim_source'))!r} line_kind={bl(x.get('line_kind'))!r}")
    else:
        say("      overlay: NO ROW")

# what does the published pair print for the difference rows?
pair = {}
with PAIR.open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pair.setdefault(norm_pn(r["part_number"]), r)
say("")
say("WHAT THE PUBLISHED PAIR PRINTS")
say("  pair rows:", len(pair))
say("  master-marker rows whose pair label is a marker:",
    sum(1 for p in master_marker if p in pair and is_marker(pair[p]["aim_level_1"])))
say("  master-marker rows whose pair label is blank:",
    sum(1 for p in master_marker if p in pair and bl(pair[p]["aim_level_1"]) == ""))
say("  master-marker rows absent from the pair:",
    sum(1 for p in master_marker if p not in pair))
say("  master-marker rows whose pair label is a REAL family:",
    sum(1 for p in master_marker if p in pair and bl(pair[p]["aim_level_1"]) != ""
        and not is_marker(pair[p]["aim_level_1"])))

# and: which parts does the PAIR actually show a marker for, among the open set
pair_marker = [p for p in open_pns if p in pair and is_marker(pair[p]["aim_level_1"])]
say("  open parts the pair shows a marker for:", len(pair_marker))
say("  open parts the pair shows blank:", sum(1 for p in open_pns if p in pair and bl(pair[p]["aim_level_1"]) == ""))
say("  open parts absent from the pair:", sum(1 for p in open_pns if p not in pair))

# the 235 / 209 candidates
blank_aim = [p for p in open_pns if p in master and not any(
    is_marker(master[p].get(c)) for c in ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"))]
say("")
say("THE 'BLANK FAMILY' GROUP")
say("  on the master with no marker anywhere:", len(blank_aim))
say("  of those, aim_l1 AND aim_l1_fixed both blank:",
    sum(1 for p in blank_aim if bl(master[p]['aim_l1']) == "" and bl(master[p]['aim_l1_fixed']) == ""))
say("  of those, has_aim=0:", sum(1 for p in blank_aim if bl(master[p]['has_aim']) == "0"))
say("  of those, in the overlay:", sum(1 for p in blank_aim if p in ov_all))
say("  of those, overlay carries a real family:",
    sum(1 for p in blank_aim if p in ov_all and any(
        bl(x.get('aim_l1_fixed')) and not is_marker(x.get('aim_l1_fixed')) for x in ov_all[p])))
say("  no master row at all:", sum(1 for p in open_pns if p not in master))
say("")
say("  845 + 209 + 43 =", 845 + 209 + 43)
say("  819 + 235 + 43 =", 819 + 235 + 43)
say("  (235 - 209) =", 235 - 209, " which equals the difference rows:", len(diff))

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "probe_819_diff_run.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
say("")
say("wrote", OUT / "probe_819_diff_run.txt")
