#!/usr/bin/env python3
"""SPENT one-shot: IDS English labels + Jerome 2026-07-28 naming (applied 2026-07-28).

DO NOT RE-RUN. This script rewrites whole SOURCES / TOTAL_SOURCES / TOTALS_ONLY
blocks with hardcoded UK labels, and the ones baked in here are the swapped pair
(IUK->"UK CV", ITUK->"UK LCV") that was corrected on 2026-07-29. Re-running would
silently reintroduce the swap across the whole builder chain.

Source of truth for country labels is ids_paths.COUNTRY_LABELS. Kept for history.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

_SPENT = (
    "_patch_jerome_labels.py is a spent one-shot from 2026-07-28 and encodes the\n"
    "swapped UK mapping (IUK->UK CV, ITUK->UK LCV) fixed on 2026-07-29.\n"
    "Edit ids_paths.COUNTRY_LABELS instead. Refusing to run."
)


def patch_ids_paths() -> None:
    p = ROOT / "ids_paths.py"
    t = p.read_text(encoding="utf-8")
    t = t.replace('"IUK": "UK (IUK)"', '"IUK": "UK CV"')
    t = t.replace('"ITUK": "UK (ITUK)"', '"ITUK": "UK LCV"')
    # COUNTRY_LABELS: ensure Israel folder maps to Israel LCV
    if '"Israel": "Israel LCV"' not in t.split("COUNTRY_LABELS", 1)[1].split("}", 1)[0]:
        t = t.replace(
            '"ITUK": "UK LCV",\n}',
            '"ITUK": "UK LCV",\n    "Israel": "Israel LCV",\n}',
            1,
        )
    extras = {
        '"UK (IUK)": "UK CV",': True,
        '"UK (ITUK)": "UK LCV",': True,
        '"UK CV": "UK CV",': True,
        '"UK LCV": "UK LCV",': True,
        '"Israel": "Israel LCV",': True,
        '"Israel LCV": "Israel LCV",': True,
        '"ISRAEL": "Israel LCV",': True,
    }
    # Insert alias lines after ITUK alias if missing
    anchor = '"ITUK": "UK LCV",\n'
    insert = (
        '"ITUK": "UK LCV",\n'
        '    "UK (IUK)": "UK CV",\n'
        '    "UK (ITUK)": "UK LCV",\n'
        '    "UK CV": "UK CV",\n'
        '    "UK LCV": "UK LCV",\n'
        '    "Israel": "Israel LCV",\n'
        '    "Israel LCV": "Israel LCV",\n'
    )
    if '"UK CV": "UK CV"' not in t:
        # Only in aliases block — replace first ITUK alias occurrence inside aliases
        parts = t.split("COUNTRY_DISPLAY_ALIASES", 1)
        if len(parts) == 2:
            head, rest = parts
            rest = rest.replace(anchor, insert, 1)
            rest = rest.replace('"ISRAEL": "Israel"', '"ISRAEL": "Israel LCV"')
            t = head + "COUNTRY_DISPLAY_ALIASES" + rest
    else:
        t = t.replace('"ISRAEL": "Israel"', '"ISRAEL": "Israel LCV"')
    p.write_text(t, encoding="utf-8")
    print("ids_paths labels updated")


def patch_combine_sources() -> None:
    ranking = ROOT / "combine_all_rankings.py"
    t = ranking.read_text(encoding="utf-8")
    sources = '''# (source filename, English tab name) — main total ranking sheet only
SOURCES = (
    ("BE_dealer_ranking.xlsx", "Belgium"),
    ("NL_dealer_ranking.xlsx", "Netherlands"),
    ("LUX_dealer_ranking.xlsx", "Luxembourg"),
    ("Denmark_dealer_ranking.xlsx", "Denmark"),
    ("Poland_dealer_ranking.xlsx", "Poland"),
    ("Petros_dealer_ranking.xlsx", "Greece"),
    ("RSA_dealer_ranking.xlsx", "Norway"),
    ("IUK_dealer_ranking.xlsx", "UK CV"),
    ("ITUK_dealer_ranking.xlsx", "UK LCV"),
    ("France_dealer_ranking.xlsx", "France"),
    ("Italy_dealer_ranking.xlsx", "Italy"),
    ("Switzerland_dealer_ranking.xlsx", "Switzerland"),
    ("Spain_dealer_ranking.xlsx", "Spain"),
    ("MIDI_FR_dealer_ranking.xlsx", "France"),
    ("MIDI_IT_dealer_ranking.xlsx", "Italy"),
    ("MIDI_CH_dealer_ranking.xlsx", "Switzerland"),
    ("MIDI_ES_dealer_ranking.xlsx", "Spain"),
    ("Israel_dealer_ranking.xlsx", "Israel LCV"),
    ("Romania_dealer_ranking.xlsx", "Romania"),
    ("Portugal_dealer_ranking.xlsx", "Portugal"),
    ("Hungary_dealer_ranking.xlsx", "Hungary"),
    ("Malta_dealer_ranking.xlsx", "Malta"),
    ("Cyprus_dealer_ranking.xlsx", "Cyprus"),
)
'''
    import re

    t2, n = re.subn(
        r"# \(source filename.*?SOURCES = \(.*?\n\)\n",
        sources,
        t,
        count=1,
        flags=re.S,
    )
    if n:
        ranking.write_text(t2, encoding="utf-8")
        print("combine_all_rankings ok")
    else:
        print("combine_all_rankings: SOURCES block not replaced")

    # Prefer first tab (skip duplicates)
    if "if tab_name in out_wb.sheetnames:\n            continue" not in t2 if n else t:
        old = """        if tab_name in out_wb.sheetnames:
            del out_wb[tab_name]
        tgt_ws = out_wb.create_sheet(tab_name)"""
        new = """        if tab_name in out_wb.sheetnames:
            continue
        tgt_ws = out_wb.create_sheet(tab_name)"""
        cur = ranking.read_text(encoding="utf-8")
        if old in cur:
            ranking.write_text(cur.replace(old, new), encoding="utf-8")

    eval_c = ROOT / "combine_evaluation_result_reports.py"
    et = eval_c.read_text(encoding="utf-8")
    countries = '''COUNTRIES = (
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "Benelux",
    "Denmark",
    "Poland",
    "Greece",
    "Norway",
    "UK CV",
    "UK LCV",
    "Israel LCV",
    "Malta",
    "Cyprus",
    "Romania",
    "Portugal",
    "Hungary",
    "France",
    "Italy",
    "Switzerland",
    "Spain",
)
'''
    et2, n2 = re.subn(
        r"COUNTRIES = \(.*?\n\)\n",
        countries,
        et,
        count=1,
        flags=re.S,
    )
    if n2:
        eval_c.write_text(et2, encoding="utf-8")
        print("combine_evaluation ok")
    else:
        print("combine_evaluation: COUNTRIES not replaced")

    globf = ROOT / "build_global_ranking_files.py"
    gt = globf.read_text(encoding="utf-8")
    total = sources.replace("SOURCES = (", "TOTAL_SOURCES = (")
    gt2, n3 = re.subn(
        r"TOTAL_SOURCES = \(.*?\n\)\n",
        total + "\n",
        gt,
        count=1,
        flags=re.S,
    )
    if n3:
        globf.write_text(gt2, encoding="utf-8")
        print("build_global_ranking ok")
    else:
        print("build_global_ranking: TOTAL_SOURCES not replaced")


def patch_ituk_qa() -> None:
    ituk = ROOT / "build_ituk_ranking.py"
    t = ituk.read_text(encoding="utf-8")
    t = t.replace('write_ranking_workbook(\n        "ITUK",', 'write_ranking_workbook(\n        "UK LCV",')
    t = t.replace('write_ranking_workbook(\n        "UK (ITUK)",', 'write_ranking_workbook(\n        "UK LCV",')
    ituk.write_text(t, encoding="utf-8")
    qa = ROOT / "ids_dashboard_qa.py"
    qt = qa.read_text(encoding="utf-8")
    qt = qt.replace(
        'TOTALS_ONLY_COUNTRIES = frozenset({"ITUK"})',
        'TOTALS_ONLY_COUNTRIES = frozenset({"ITUK", "UK LCV", "UK (ITUK)"})',
    )
    qt = qt.replace(
        'TOTALS_ONLY_COUNTRIES = frozenset({"ITUK", "UK (ITUK)"})',
        'TOTALS_ONLY_COUNTRIES = frozenset({"ITUK", "UK LCV", "UK (ITUK)"})',
    )
    qa.write_text(qt, encoding="utf-8")
    print("ituk/qa ok")


def main() -> None:
    patch_ids_paths()
    patch_combine_sources()
    patch_ituk_qa()
    from ids_paths import COUNTRY_LABELS, country_display_name

    print("LABELS", COUNTRY_LABELS)
    for x in ["IUK", "ITUK", "Israel", "ISRAEL", "UK (IUK)", "RSA", "MIDI_CH", "LUX"]:
        print(x, "->", country_display_name(x))


if __name__ == "__main__":
    sys.exit(_SPENT)
