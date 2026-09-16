#!/usr/bin/env python3
"""Fail-closed QA gate for DB Sales Review packs (UMI 2026-08-12 retro)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # ISZE/
SYS_TOOLS = ROOT / "04_tools" / "db_sales_review"
if str(SYS_TOOLS) not in sys.path:
    sys.path.insert(0, str(SYS_TOOLS))

import common as C  # noqa: E402

SATY_BANNED = re.compile(
    r"sold[\s-]?to|export|blank|NaN|\bnan\b|payer.?name|pipeline",
    re.I,
)


def check_saty(profile: dict, fails: list[str]) -> None:
    note = profile.get("saty_note") or (profile.get("deck") or {}).get("saty_note") or ""
    if not note:
        return
    if SATY_BANNED.search(note):
        fails.append(f"saty_note has Mode B / export jargon: {note[:140]!r}")
    if "%" in note and "SOR" not in note.upper() and "VOR" not in note.upper():
        fails.append("saty_note has % but no SOR/VOR coded-mix framing")


def check_sold_to(profile: dict, fails: list[str]) -> None:
    st = profile.get("sold_to")
    if st is None:
        return
    key = profile.get("key", "")
    if str(int(st)) == "1797" and key != "UMI":
        fails.append(f"sold_to 1797 is UMI — profile key is {key}")
    if str(int(st)) == "1799":
        fails.append("sold_to 1799 is UTI — never build an IDS-Israel / UMI Mode A from UTI")


def check_exclude(profile: dict, fails: list[str]) -> None:
    deck = profile.get("deck") or {}
    excl = deck.get("exclude_movers_cats") or []
    if excl and not deck.get("exclude_movers_jerome_ok"):
        fails.append(
            f"exclude_movers_cats={excl} without deck.exclude_movers_jerome_ok: true "
            "(do not copy IBX Body exclude to another DB)"
        )


def check_summary_fresh(profile: dict, fails: list[str]) -> None:
    out = C.OUT_ROOT / f"{profile['key']}_Sales_Review_2026" / "_summary.json"
    if not out.exists():
        fails.append(f"_summary.json missing — run build_parts_analysis first ({out})")
        return
    common = SYS_TOOLS / "common.py"
    if common.exists() and out.stat().st_mtime < common.stat().st_mtime:
        fails.append(
            f"_summary.json older than common.py — re-run build_parts_analysis ({out})"
        )


def check_pbi_align(profile: dict, fails: list[str]) -> None:
    pbi = profile.get("pbi") or {}
    if not pbi:
        return
    months = pbi.get("months") or []
    sales = pbi.get("sales") or []
    if not months or not sales or len(months) != len(sales):
        fails.append("pbi.months / pbi.sales missing or length mismatch")
        return
    try:
        df = C.load_sales(profile)
    except Exception as e:
        fails.append(f"load_sales failed: {e}")
        return
    if df is None or df.empty:
        fails.append("load_sales returned empty")
        return
    if "Billing Date" not in df.columns:
        fails.append(f"load_sales missing Billing Date; cols={list(df.columns)[:15]}")
        return
    val_col = "net_eur" if "net_eur" in df.columns else None
    if not val_col:
        fails.append("load_sales missing net_eur")
        return

    df = df.copy()
    cur_label = profile["defaults"]["window_label_current"]
    if "period" in df.columns:
        df = df[df["period"] == cur_label]
    if df.empty:
        fails.append(f"load_sales has no rows for period={cur_label}")
        return
    df["_ym"] = C._dates(df["Billing Date"]).dt.strftime("%Y-%m")
    # Map PBI month labels to current FY window year (Apr+ → same calendar year as window start)
    win_start = str(profile["defaults"]["window_current"][0])  # e.g. 2026-01-01
    year = int(win_start[:4])
    mon_num = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    for mon, pbi_val in zip(months, sales):
        if pbi_val is None:
            continue
        n = mon_num.get(str(mon))
        if not n:
            fails.append(f"unknown pbi month label {mon!r}")
            continue
        ym = f"{year}-{n:02d}"
        sap_rows = df[df["_ym"] == ym]
        if sap_rows.empty:
            if mon == "Jul":
                continue  # export lag OK
            fails.append(f"PBI month {mon}={pbi_val:,.0f} but SAP has 0 rows in {ym}")
            continue
        sap = float(sap_rows[val_col].sum())
        diff = abs(sap - float(pbi_val))
        # Jul: soft — skip hard fail if SAP much lower (lag)
        if mon == "Jul" and sap < float(pbi_val) * 0.5:
            continue
        if diff > 2000:
            fails.append(
                f"PBI vs SAP {mon} ({ym}): PBI={float(pbi_val):,.0f} SAP={sap:,.0f} diff={diff:,.0f} (>€2k)"
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    profile = C.load_profile(args.db)
    fails: list[str] = []
    check_sold_to(profile, fails)
    check_saty(profile, fails)
    check_exclude(profile, fails)
    check_summary_fresh(profile, fails)
    check_pbi_align(profile, fails)

    key = profile["key"]
    if fails:
        print(f"QA GATE FAIL — {key}")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"QA GATE PASS — {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
