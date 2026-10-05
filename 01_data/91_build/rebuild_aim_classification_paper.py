"""Patch ISZE_AIM_Classification_Paper.html to today's AIM master / classification.

No historical builder existed for this hand-authored paper. This script refreshes
the snapshot counts and dates from live derived files so the hero matches
aim_master_v2.csv and the catalogue shape matches the classification release that
_releases/RELEASES.json marks APPROVED (resolved + sha256-checked through the release
guard; fail closed). Before 2026-10-01 it read the NOT_RELEASED live overlay
aim_pn_classification_20260920.csv; the catalogue shape is identical in both.

    python rebuild_aim_classification_paper.py            # patches the live page
    python rebuild_aim_classification_paper.py --staged   # writes ..._staged.html, live untouched
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
HTML = ISZE / "02_dashboards" / "sales" / "ISZE_AIM_Classification_Paper.html"
OPEN = ISZE / "02_dashboards" / "sales" / "OPEN_ISZE_AIM_Classification_Paper.cmd"
MASTER = D / "aim_master_v2.csv"
CLASS: Path  # set in main(): the APPROVED release, via 04_tools/_shared/classification_paths
sys.path.insert(0, str(ISZE / "04_tools" / "_shared"))


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
    global CLASS
    from classification_paths import approved_release

    CLASS, _rel = approved_release()  # raises unless APPROVED and hash equals the register
    print(f"catalogue shape from release {_rel['release_id']} {_rel['status']} "
          f"{_rel['sha256'][:12]}: {CLASS}")
    staged = "--staged" in sys.argv[1:]
    # staged copy one folder down: sync_to_deploys.ps1 does not walk sales/_staged/
    html_out = (HTML.parent / "_staged" / (HTML.stem + "_staged.html")) if staged else HTML
    html_out.parent.mkdir(exist_ok=True)
    master_n, gap, has_aim, aim_l1n, aim_l2n = count_master()
    class_n, c_l1, c_l2, c_l3 = count_class()
    print(f"master_rows={master_n} gap_auto={gap} has_aim={has_aim} aim_L1={aim_l1n} aim_L2={aim_l2n}")
    print(f"class_rows={class_n} catalog={c_l1}/{c_l2}/{c_l3}")

    t = HTML.read_text(encoding="utf-8")
    import re

    # Hero: classified part numbers = live master spine count
    t = re.sub(
        r"<b>[\d,]+</b>Classified part numbers",
        f"<b>{master_n:,}</b>Classified part numbers",
        t,
        count=1,
    )
    # Cover prepared date
    t = re.sub(
        r"<div><b>\d+ September 2026</b>Prepared for internal review</div>",
        "<div><b>20 September 2026</b>Prepared for internal review</div>",
        t,
        count=1,
    )
    # Price-list tree card: live catalogue classification shape (any prior N / N / N · N parts)
    new_shape = f"{c_l1} / {c_l2} / {c_l3} · {class_n:,} parts"
    t2, n_shape = re.subn(
        r"\d+\s*/\s*\d+\s*/\s*\d+\s*·\s*[\d,]+\s*parts",
        new_shape,
        t,
        count=1,
    )
    t = t2
    if n_shape == 0:
        print("WARN: catalogue shape string not found")
    # Category workbook card
    new_wb = (
        f"{aim_l1n} system names · {has_aim:,} parts with AIM labels"
        f" (incl. {gap:,} auto-gap fills)"
    )
    t2, n_wb = re.subn(
        r"\d+\s+system names\s*·\s*[\d,]+\s*parts with AIM labels[^<]*",
        new_wb,
        t,
        count=1,
    )
    t = t2
    if n_wb == 0:
        print("WARN: workbook shape string not found")
    # Live-as-of footer
    t = re.sub(
        r"Figures on the live classification as\n\s*of \d+ September 2026[^<]*</p>",
        "Figures on the live classification as\n    of 20 September 2026 "
        f"({master_n:,} part numbers on the AIM master spine).</p>",
        t,
        count=1,
    )

    html_out.write_text(t, encoding="utf-8", newline="\n")
    if staged:
        print(f"wrote {html_out} (staged; live page and opener untouched)")
        t2 = html_out.read_text(encoding="utf-8")
        assert f"{c_l1} / {c_l2} / {c_l3}" in t2 and f"{class_n:,} parts" in t2
        print("SANITY_OK (staged)")
        return 0
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
