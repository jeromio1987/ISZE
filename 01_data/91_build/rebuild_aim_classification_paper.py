"""Patch ISZE_AIM_Classification_Paper.html to today's AIM master / classification.

No historical builder existed for this hand-authored paper. This script refreshes
the snapshot counts and dates from live derived files so the hero matches
aim_master_v2.csv and the catalogue shape matches aim_pn_classification_v2.csv.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
HTML = ISZE / "02_dashboards" / "sales" / "ISZE_AIM_Classification_Paper.html"
OPEN = ISZE / "02_dashboards" / "sales" / "OPEN_ISZE_AIM_Classification_Paper.cmd"
MASTER = D / "aim_master_v2.csv"
CLASS = D / "aim_pn_classification_v2.csv"


def count_master() -> tuple[int, int, int, int, int]:
    n = gap = has_aim = 0
    l1s: set[str] = set()
    l2s: set[str] = set()
    with MASTER.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            n += 1
            ac = row.get("aim_changed") or ""
            if "gap_auto_20260918" in ac:
                gap += 1
            if (row.get("has_aim") or "").strip() == "1":
                has_aim += 1
                l1 = (row.get("aim_l1") or "").strip()
                l2 = (row.get("aim_l2") or "").strip()
                if l1:
                    l1s.add(l1)
                if l2:
                    l2s.add(l2)
    return n, gap, has_aim, len(l1s), len(l2s)


def count_class() -> tuple[int, int, int, int]:
    n = 0
    l1s: set[str] = set()
    l2s: set[str] = set()
    l3s: set[str] = set()
    with CLASS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            n += 1
            for col, bucket in (
                ("catalog_l1", l1s),
                ("catalog_l2", l2s),
                ("catalog_l3", l3s),
            ):
                v = (row.get(col) or "").strip()
                if v:
                    bucket.add(v)
    return n, len(l1s), len(l2s), len(l3s)


def main() -> int:
    master_n, gap, has_aim, aim_l1n, aim_l2n = count_master()
    class_n, c_l1, c_l2, c_l3 = count_class()
    print(f"master_rows={master_n} gap_auto={gap} has_aim={has_aim} aim_L1={aim_l1n} aim_L2={aim_l2n}")
    print(f"class_rows={class_n} catalog={c_l1}/{c_l2}/{c_l3}")

    t = HTML.read_text(encoding="utf-8")
    # Hero: classified part numbers = live master spine count (Jerome's 18 Sep extract).
    t = t.replace("<b>164,667</b>Classified part numbers",
                  f"<b>{master_n:,}</b>Classified part numbers")
    # Cover prepared date (snapshot), keep decision lock wording on 17 Sep elsewhere.
    t = t.replace("<div><b>17 September 2026</b>Prepared for internal review</div>",
                  "<div><b>18 September 2026</b>Prepared for internal review</div>")
    # Price-list tree card: live catalogue classification shape.
    old_shape = "7 / 25 / 171 · 164,667 parts"
    new_shape = f"{c_l1} / {c_l2} / {c_l3} · {class_n:,} parts"
    if old_shape not in t:
        # tolerate already-partial patches
        print("WARN: old catalogue shape string not found")
    else:
        t = t.replace(old_shape, new_shape)
    # Category workbook card: live AIM-labelled PN count on master.
    old_wb = "21 system names · 16,499 parts, ~79% of euro"
    new_wb = (f"{aim_l1n} system names · {has_aim:,} parts with AIM labels"
              f" (incl. {gap:,} auto-gap fills on 18 Sep)")
    if old_wb in t:
        t = t.replace(old_wb, new_wb)
    else:
        print("WARN: old workbook shape string not found")
    # Live-as-of footer for the classification cut.
    t = t.replace(
        "Figures on the live classification as\n    of 17 September 2026.</p>",
        "Figures on the live classification as\n    of 18 September 2026 "
        f"({master_n:,} part numbers on the AIM master spine).</p>",
    )

    HTML.write_text(t, encoding="utf-8", newline="\n")
    OPEN.write_bytes(
        b'@echo off\r\nstart "" "%~dp0ISZE_AIM_Classification_Paper.html"\r\n'
    )
    print(f"wrote {HTML}")
    print(f"mtime {datetime.fromtimestamp(HTML.stat().st_mtime):%Y-%m-%d %H:%M:%S}")
    print(f"launcher {OPEN} size={OPEN.stat().st_size}")
    # sanity — hero must track the master; catalogue card may still show class_n
    t2 = HTML.read_text(encoding="utf-8")
    assert f"<b>{master_n:,}</b>Classified part numbers" in t2
    assert "164,667</b>Classified" not in t2
    assert f"{c_l1} / {c_l2} / {c_l3} · {class_n:,} parts" in t2 or (
        f"{c_l1} / {c_l2} / {c_l3}" in t2 and f"{class_n:,} parts" in t2
    )
    assert f"{has_aim:,} parts with AIM labels" in t2
    assert "Friction" not in t2
    assert "Mode A" not in t2 and "Mode B" not in t2
    assert "sell-out" not in t2 and "street" not in t2 and "wallet" not in t2
    print("SANITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
