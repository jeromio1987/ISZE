# -*- coding: utf-8 -*-
"""Tick-3: Duncan margin/support nuance on MD-track + light feasibility/other-DB fix."""
from __future__ import annotations

import re
import runpy
from pathlib import Path

STRAT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")


def patch_feasibility_md() -> None:
    feas = STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.md"
    t = feas.read_text(encoding="utf-8")
    pat = r"\| Median unit support[^\n]+\n\| Average unit support[^\n]+\n"
    repl = (
        "| Median unit support (DN − offer) | **£86** | Measured |\n"
        "| Average unit support | **£172** | Measured — skew vs median |\n"
        "| Normal margin on dealer price (before offer) | **~47%** | Measured |\n"
    )
    t2, n = re.subn(pat, repl, t, count=1)
    if n != 1:
        raise SystemExit(f"feas median/avg replace failed n={n}")
    if "| Lines below cost |" not in t2:
        t2 = t2.replace(
            "| Average retained margin on offer | **~41%** | Measured |\n",
            "| Average retained margin on offer | **~41%** | Measured |\n"
            "| Retained margin band (median) | **~41–43%** | Measured |\n"
            "| Lines below cost | **None** | Measured |\n",
        )
    anchor = "| Lines below cost | **None** | Measured |\n"
    if "Duncan regional nuance" not in t2 and anchor in t2:
        note = (
            anchor
            + "\n"
            + "**Duncan regional nuance (Measured):** normal margin on dealer price before the offer ~**47%**; "
            "after the offer retained ~**41–43%** median. Nothing below cost. "
            "Support skew: median ~**£86** vs average ~**£172** on the **£54,922 / 218-case** register.\n"
        )
        t2 = t2.replace(anchor, note, 1)
    feas.write_text(t2, encoding="utf-8")
    print("feas MD patched")


def patch_other_live() -> None:
    other_md = STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md"
    om = other_md.read_text(encoding="utf-8")
    patterns = [
        (
            r"(After the offer it is \*\*)(\d{1,2}(?:\.\d+)?%)(\*\*\. No line is sold below cost\.)",
            r"\g<1>~41–43% median\g<3> (euro-weighted pool was ~34%; large discounts weigh more). "
            r"Normal margin before offer ~47%.",
        ),
        (
            r"(ITUK keeps )(\d{1,2}(?:\.\d+)?%)( on the offer, so it can\.)",
            r"\g<1>about 41–43% median\g<3>",
        ),
        (
            r"(ITUK keeps )(\d{1,2}(?:\.\d+)?%)( after the offer and might fund it anyway)",
            r"\g<1>~41–43% median\g<3>",
        ),
        (
            r"keeps 34% margin on the offer",
            "keeps ~41–43% median margin on the offer (~47% before)",
        ),
        (
            r"ITUK never sells below cost\*\* and keeps 34% after the offer",
            "ITUK never sells below cost** and keeps about **41–43% median** after the offer (~47% normal before)",
        ),
        (
            r"ITUK never sells below cost and keeps 34% after the offer",
            "ITUK never sells below cost and keeps about 41–43% median after the offer (~47% normal before)",
        ),
    ]
    om2 = om
    changed = 0
    for a, b in patterns:
        om2, c = re.subn(a, b, om2)
        changed += c
    other_md.write_text(om2, encoding="utf-8")
    print("other MD change ops", changed)

    other_html = STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html"
    oh = other_html.read_text(encoding="utf-8")
    oh2 = oh.replace(
        "ITUK keeps 34% margin on the offer, so it can fund much of it itself.",
        "ITUK keeps ~41–43% median margin on the offer (~47% before), so it can fund much of it itself.",
    )
    oh2 = oh2.replace(
        "keeps 34% after the offer",
        "keeps about 41–43% median after the offer",
    )
    other_html.write_text(oh2, encoding="utf-8")
    print("other HTML patched", oh != oh2)


def rebuild() -> None:
    runpy.run_path(
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_build_md_track_business_plan_20261008.py",
        run_name="__main__",
    )
    print("md-track rebuilt")
    runpy.run_path(
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_build_dlod_feasibility_html_20261008.py",
        run_name="__main__",
    )
    print("feas HTML rebuilt")


def verify() -> None:
    md = (STRAT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md").read_text(encoding="utf-8")
    html = (STRAT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html").read_text(encoding="utf-8")
    feas = (STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.md").read_text(encoding="utf-8")
    feas_html = (STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.html").read_text(encoding="utf-8")
    other = (STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md").read_text(encoding="utf-8")
    checks = {
        "md_47": "~47%" in md,
        "md_41_43": "41–43%" in md,
        "md_172": "£172" in md,
        "md_below": "below cost" in md.lower() and "None" in md,
        "md_tick3": "| 3 |" in md,
        "html_47": "~47%" in html,
        "html_41_43": "41–43%" in html,
        "html_card": "Duncan regional lines" in html,
        "feas_47": "~47%" in feas,
        "feas_below": "Lines below cost" in feas,
        "feas_html_47": "~47%" in feas_html,
        "other_no_bare_34_keep": "keeps 34% after the offer" not in other
        and "keeps 34% margin on the offer" not in other,
    }
    print(checks)
    if not all(checks.values()):
        bad = [k for k, v in checks.items() if not v]
        raise SystemExit(f"verify failed: {bad}")
    print("OK")


if __name__ == "__main__":
    patch_feasibility_md()
    patch_other_live()
    rebuild()
    verify()
