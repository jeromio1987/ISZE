# -*- coding: utf-8 -*-
"""First loop pass: harden MD-track plan markdown + refresh HTML via builder."""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
BUILDER = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_build_md_track_business_plan_20261008.py"
)
MD_PATH = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md"
HTML_PATH = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html"


def patch_md(md: str) -> str:
    if "## 4.5 Board measurement definition" not in md:
        insert = """
---

## 4.5 Board measurement definition (Proposed)

**Save-rate** = supported cases marked *won* ÷ supported cases with a known outcome (won or lost). Cases left *unknown* stay disclosed separately — do not pretend they were wins.

**Return numerator (Proposed):** on won cases, ISZE billed euros on the linked order (or the supported lines if the full order cannot be tied), times ISZE margin on those lines when margin is known; otherwise report billed euros and label margin Unknown.

**Evidence fill rate:** share of *new* cases after the harden date with Competitor Price or a typed reason code. Target for Q1 FY27 gate: **>80%**.

**What we will not claim:** a loyalty euro, a full-book ROI, or a promotion timeline.

"""
        md = md.replace("## 5. Operating model", insert + "## 5. Operating model")

    if "## 3.5 Pilot stack (paste into opex meeting)" not in md and "### 3.5 Pilot stack" not in md:
        insert2 = """
### 3.5 Pilot stack (paste into opex meeting)

| Line | EUR | Status |
|---|---:|---|
| ITUK Don't Lose the Deal FY27 | 30,000 | Confirm continuity (already in budget) |
| IUK pilot at ~0.5% of FY2026 billed | ~30,200 | Proposed new |
| Ireland *or* Portugal third pot | ~5,700–9,300 | Proposed / optional |
| **Pilot envelope total** | **~70,000–80,000** | Proposed ask |
| Full-book 0.5% (18 DBs) | ~162,900 | Later — not this ask |

"""
        md = md.replace("### 3.3 Case register", insert2 + "### 3.3 Case register")

    if "Loop tick log" not in md:
        md = md.rstrip() + """

---

## Loop tick log

| Tick | When | What hardened |
|---|---|---|
| 0 | 2026-10-08 (build) | First pack from DLOD feasibility + other-DB honesty |
| 1 | 2026-10-08 (first pass) | Board measurement definition (save-rate / evidence fill); pilot stack table for opex meeting; loop log |
"""
    elif "| 1 |" not in md:
        md = md.rstrip() + "\n| 1 | 2026-10-08 (first pass) | Board measurement definition; pilot stack table; loop log |\n"
    return md


def patch_html(html: str) -> str:
    """Inject measurement + pilot stack cards if missing."""
    if "Board measurement" in html:
        return html

    block = """
<div class="grid g2">
  <div class="card">
    <h2>Pilot stack for next week</h2>
    <p class="q">Paste into the opex conversation — cap, not a spend promise</p>
    <table>
      <thead><tr><th>Line</th><th>EUR</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td>ITUK FY27 Don't Lose the Deal</td><td>€30,000</td><td>Confirm continuity</td></tr>
        <tr><td>IUK pilot (~0.5% FY billed)</td><td>~€30,200</td><td>Proposed</td></tr>
        <tr><td>Ireland or Portugal</td><td>~€5.7–9.3k</td><td>Optional third</td></tr>
        <tr><td><b>Pilot total</b></td><td><b>~€70–80k</b></td><td>Proposed ask</td></tr>
        <tr><td>Full-book 0.5% later</td><td>~€163k</td><td>Not this ask</td></tr>
      </tbody>
    </table>
  </div>
  <div class="card">
    <h2>Board measurement</h2>
    <p class="q">How return will be counted — Unknowns stay labelled</p>
    <ul class="clean">
      <li><b>Save-rate</b> = won ÷ (won + lost). Unknown outcomes disclosed separately.</li>
      <li><b>Return</b> = ISZE billed € on won linked orders × margin when known.</li>
      <li><b>Evidence fill</b> on new cases — Q1 gate &gt;80% with competitor price or reason code.</li>
      <li>No loyalty euro, no fake full-book ROI, no promotion timeline in the pack.</li>
    </ul>
  </div>
</div>
"""
    # insert before kill criteria card
    marker = '<div class="card" style="margin-bottom:18px">\n  <h2>Kill criteria</h2>'
    if marker in html:
        html = html.replace(marker, block + "\n" + marker)
    else:
        html = html.replace('<div class="ask">', block + '\n<div class="ask">')

    # soften footnote CDN false positive wording already ok; ensure bar-row count stays
    return html


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    MD_PATH.write_text(patch_md(md), encoding="utf-8")

    # Re-run builder for clean HTML baseline, then enrich
    import runpy

    runpy.run_path(str(BUILDER), run_name="__main__")
    html = HTML_PATH.read_text(encoding="utf-8")
    html2 = patch_html(html)
    HTML_PATH.write_text(html2, encoding="utf-8")

    html2 = HTML_PATH.read_text(encoding="utf-8")
    checks = {
        "bar_rows": html2.count("bar-row"),
        "kpi": html2.count("class=\"kpi"),
        "pilot_stack": "Pilot stack for next week" in html2,
        "measurement": "Board measurement" in html2,
        "payload": 'id="payload"' in html2,
        "no_script_src": "<script src=" not in html2.lower(),
        "md_has_45": "## 4.5 Board measurement definition" in MD_PATH.read_text(encoding="utf-8"),
        "md_has_35": "### 3.5 Pilot stack" in MD_PATH.read_text(encoding="utf-8"),
    }
    print(json.dumps(checks, indent=2))
    if checks["bar_rows"] < 5 or not checks["pilot_stack"] or not checks["md_has_45"]:
        raise SystemExit("pass1 incomplete")


if __name__ == "__main__":
    main()
