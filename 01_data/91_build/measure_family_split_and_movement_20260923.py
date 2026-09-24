"""Two measurements behind the 2026-09-23 receipt corrections. Both read the artefacts directly.

SECTION A - family splittability, per clock, before and after.
The page publishes one verdict per service family per clock. `pooled` is a refusal ("not comparable
by band"); `thin` and `ok` both mean the family IS split, `thin` carrying a caveat. So the count of
families the page will split by tonnage is the count of verdicts that are neither `pooled` nor
`none`, and the count refused is the `pooled` count. Those two are easily swapped, so this prints
both, and the family names behind each.

SECTION B - the page file's own movement, decomposed.
143 -> 180 on tonnage_capable_part_numbers.csv. The pieces are: rows that left the file, rows that
entered it, rows whose n_bands moved, and whether any of them carries a quarantined code. The
52-row gap between this file and vehicle_band_applicability.csv is a DIFFERENT population and is
reported separately so the two cannot be conflated.

Run:
    python 01_data/91_build/measure_family_split_and_movement_20260923.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
BEFORE = (ROOT / "02_dashboards" / "sales" / "_qa_family_evolution"
          / "before_rebase_20260923" / "ISZE_PMS_Family_Evolution_v2.before_rebase_20260923.html")
BAK = (ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
       / "tonnage_capable_part_numbers.csv.bak_pre_rebase")

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def payload(p: Path) -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                p.read_text(encoding="utf-8"), re.S).group(1))


def section_a() -> None:
    print("=" * 100)
    print("SECTION A - FAMILY SPLITTABILITY BY TONNAGE, AS THE PAGE PUBLISHES IT")
    print("=" * 100)
    before, after = payload(BEFORE), payload(HTML)
    for clock in ("CY", "FY"):
        print()
        print(f"  {clock} clock")
        for tag, d in (("before", before), ("after ", after)):
            comp = (d.get("comparability") or {}).get(clock) or {}
            cats = {c["key"]: c["label"] for c in d.get("cats", [])}
            live = {k: v for k, v in comp.items() if v.get("verdict") != "none"}
            split = sorted(k for k, v in live.items() if v.get("verdict") in ("ok", "thin"))
            refused = sorted(k for k, v in live.items() if v.get("verdict") == "pooled")
            none = sorted(k for k, v in comp.items() if v.get("verdict") == "none")
            print(f"    {tag}: {len(live)} families carry euro | SPLIT {len(split)} | "
                  f"refused {len(refused)} | no euro {len(none)}")
            print(f"        split   : " + ", ".join(
                f"{cats.get(k, k)} ({live[k]['verdict']})" for k in split))
            print(f"        refused : " + ", ".join(cats.get(k, k) for k in refused))
            if none:
                print(f"        no euro : " + ", ".join(cats.get(k, k) for k in none))


def section_b() -> None:
    print()
    print("=" * 100)
    print("SECTION B - THE PAGE FILE'S OWN MOVEMENT, DECOMPOSED")
    print("=" * 100)
    old = pd.read_csv(BAK, dtype=str, low_memory=False).fillna("")
    new = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    for d in (old, new):
        d["k"] = d.pn.map(n)
        d["nb"] = d.n_bands.astype(int)
        d["park"] = d.parked_codes.astype(str).str.strip() != ""
    print(f"  old {len(old)} rows / {int((old.nb == 1).sum())} single-band   "
          f"new {len(new)} rows / {int((new.nb == 1).sum())} single-band   "
          f"movement {int((new.nb == 1).sum()) - int((old.nb == 1).sum()):+d}")

    gone = old[~old.k.isin(set(new.k))]
    came = new[~new.k.isin(set(old.k))]
    both = old.merge(new, on="k", suffixes=("_o", "_n"))
    up = both[(both.nb_o != 1) & (both.nb_n == 1)]
    down = both[(both.nb_o == 1) & (both.nb_n != 1)]
    print()
    print("  pieces:")
    print(f"    rows that entered the file            : {len(came):4d}  "
          f"single-band among them {int((came.nb == 1).sum()):4d}  "
          f"carrying a quarantined code {int(came.park.sum()):3d}")
    print(f"    rows that left the file               : {len(gone):4d}  "
          f"single-band among them {int((gone.nb == 1).sum()):4d}  "
          f"carrying a quarantined code {int(gone.park.sum()):3d}")
    print(f"    in both, flipped to single-band       : {len(up):4d}  "
          f"carrying a quarantined code {int(up.park_n.sum()):3d}")
    print(f"    in both, flipped away from single-band: {len(down):4d}  "
          f"carrying a quarantined code {int(down.park_o.sum()):3d}")
    net = (int((came.nb == 1).sum()) - int((gone.nb == 1).sum()) + len(up) - len(down))
    print(f"    arithmetic: {int((came.nb == 1).sum()):+d} new  "
          f"{-int((gone.nb == 1).sum()):+d} dropped  {len(up):+d} flipped in  "
          f"{-len(down):+d} flipped out  = {net:+d}")
    moved = set(came.k) | set(gone.k) | set(up.k) | set(down.k)
    print()
    print(f"  rows involved in any part of the movement: {len(moved)}")
    parked_moved = [r.k for r in came.itertuples() if r.park] \
        + [r.k for r in gone.itertuples() if r.park] \
        + [r.k for r in up.itertuples() if r.park_n] \
        + [r.k for r in down.itertuples() if r.park_o]
    print(f"  of those, carrying a quarantined code    : {len(parked_moved)}")
    for p in parked_moved:
        o = old[old.k == p]
        nn = new[new.k == p]
        print(f"      {p:>12s} old {o.band_list.iloc[0] if len(o) else '(absent)'}"
              f" n={o.n_bands.iloc[0] if len(o) else '-'}"
              f"   ->   new {nn.band_list.iloc[0] if len(nn) else '(absent)'}"
              f" n={nn.n_bands.iloc[0] if len(nn) else '-'}"
              f"   parked {(nn.parked_codes.iloc[0] if len(nn) else o.parked_codes.iloc[0])!r}")
    print()
    print("  single-band rows split by quarantined code:")
    print(f"      old: parked {int(old[old.nb == 1].park.sum()):3d}  "
          f"not parked {int((~old[old.nb == 1].park).sum()):3d}")
    print(f"      new: parked {int(new[new.nb == 1].park.sum()):3d}  "
          f"not parked {int((~new[new.nb == 1].park).sum()):3d}")

    print()
    print("  THE OTHER POPULATION, for contrast - the gap between the two files:")
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    app["k"] = app.pn.map(n)
    app = app[app.n_series_bands != ""].copy()
    app["nb"] = app.n_series_bands.str.count(r"\|") + 1
    # the page file's rule, recomputed on the same rows, so the two are compared like for like
    from sys import path as _p
    _p.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
    from modules.vehicle_bands import N_SERIES_BANDS, UNRESOLVED, band_for
    page_nb = {}
    for r in app.itertuples():
        bands = {b for b in str(r.n_series_bands).split("|") if b}
        for c in str(r.parked_codes).split(";"):
            c = c.strip()
            if c and band_for(c) in N_SERIES_BANDS:
                bands.add(band_for(c))
        page_nb[r.k] = len(bands)
    app["page_nb"] = app.k.map(page_nb)
    print(f"      neutral file, one rung           : {int((app.nb == 1).sum())}")
    print(f"      page-file rule, one rung         : {int((app.page_nb == 1).sum())}")
    gap = app[(app.nb == 1) & (app.page_nb != 1)]
    print(f"      the gap                          : {len(gap)}  "
          f"quarantined among them {int((gap.parked_codes.astype(str).str.strip() != '').sum())}")


if __name__ == "__main__":
    section_a()
    section_b()
