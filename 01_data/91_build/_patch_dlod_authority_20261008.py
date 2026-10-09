# -*- coding: utf-8 -*-
"""Authority pass: MOA + Yoshimoto ~50% layer split + 20% modelling-only."""
from __future__ import annotations

import re
import runpy
from pathlib import Path

STRAT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build")
MOA_PATH = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\FY26_ITUK_DLOD_2026-03.docx.pdf"

AUTHORITY_MD = f"""
### 4.1a Authority sources (do not blend)

| Layer | What it says | Source | Label |
|---|---|---|---|
| Signed MOA | ISZE pays ITUK **EUR 30,000** for Don't Lose the Deal **if ITUK provides the activity record**. **No margin, %GM, dealer keep-rate, or Japan per-case clause** in the agreement. | `{MOA_PATH}` (DocuSign completed 26 Mar 2026; Yoshimoto / Peter Murphy; effective 1 Apr 2025) | Measured |
| ISZE GP on programme deals | About **~50%** ISZE gross profit on the deals covered by the €30k (turnover / cost / GP figures in Jerome → Yoshimoto reply) | Mar 2026 DocuSign / DLAD mail thread | Measured |
| ITUK retained on offer | **~47%** normal margin on dealer price before offer; **~41–43% median** retained after; none below cost; support skew ~£86 median vs ~£172 average | Duncan deal file (218 regional lines) | Measured |

**Do not blend:** Yoshimoto-mail **~50%** is **ISZE** margin on those deals. Duncan **~41–43%** is **ITUK** retained after the offer (~47% before). The MOA sets only the EUR 30k + activity-record condition — it does **not** set either margin figure.
"""

FEAS_MOA_ROW = (
    "| **Signed MOA** `FY26_ITUK_DLOD_2026-03.docx.pdf` | ISZE pays ITUK **EUR 30,000** for Don't Lose the Deal if ITUK provides the **activity record**. "
    "**No margin / %GM / dealer keep-rate** in the agreement (Yoshimoto / Peter Murphy; effective 1 Apr 2025; DocuSign 26 Mar 2026) | Measured |\n"
)

FEAS_LAYERS = """
### 1.2a Margin layers (do not blend)

| Layer | Figure | Source | Label |
|---|---|---|---|
| ISZE GP on programme deals | **~50%** | Jerome → Yoshimoto, Mar 2026 DocuSign / DLAD thread (study numbers on deals covered by the €30k) | Measured |
| ITUK normal margin before offer | **~47%** | Duncan deal file | Measured |
| ITUK retained after offer | **~41–43% median** (avg ~41%) | Duncan deal file | Measured |

The signed MOA (`C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\90_INBOX\\FY26_ITUK_DLOD_2026-03.docx.pdf`) does **not** set any of these percentages — only EUR 30,000 against the activity record.
"""


def patch_md_track_builder() -> None:
    p = BUILD / "_build_md_track_business_plan_20261008.py"
    t = p.read_text(encoding="utf-8")

    # Insert authority block after Duncan nuance in MD template
    duncan_note = (
        "**Duncan regional nuance (Measured):** ITUK's normal margin on dealer price before the offer is about **47%**. "
        "After the offer, retained margin sits at about **41–43% median**. Nothing on the register is sold below cost. "
        "Support is skewed — median about **£86** versus average about **£172** on the **£54,922 / 218-case** register — "
        "so a few large lines pull the mean; the typical case is the median."
    )
    if "### 4.1a Authority sources" not in t:
        if duncan_note not in t:
            raise SystemExit("duncan note missing in builder MD")
        t = t.replace(duncan_note, duncan_note + "\n" + AUTHORITY_MD.rstrip() + "\n", 1)

    # Situation bullet: cite MOA
    old_bullet = (
        "- ISZE already funds ITUK via round **EUR 30,000** credit notes tagged DLOD / DLAD; "
        "that figure is also an intentional **FY27 budget** line and sits on the VPACC action plan "
        "and in the Pricing P&L DLOD reserve. *(Measured / Confirmed)*"
    )
    new_bullet = (
        "- Signed **MOA** (Mar 2026 DocuSign): ISZE pays ITUK **EUR 30,000** for Don't Lose the Deal "
        "if ITUK provides the **activity record** — **no margin / %GM** in the agreement "
        f"(`FY26_ITUK_DLOD_2026-03.docx.pdf`). Same EUR 30k appears as credit notes and as the intentional "
        "**FY27 budget** / VPACC / Pricing P&L DLOD reserve line. *(Measured / Confirmed)*"
    )
    if old_bullet in t:
        t = t.replace(old_bullet, new_bullet, 1)
    elif "Signed **MOA**" not in t:
        raise SystemExit("could not patch situation bullet")

    # Revision + loop tick
    if "MOA + Yoshimoto ~50%" not in t:
        t = t.replace(
            "| 2026-10-08 | Loop tick: Duncan margin/support nuance (47% → 41–43% retained; £86 vs £172 skew; none below cost). |\n",
            "| 2026-10-08 | Loop tick: Duncan margin/support nuance (47% → 41–43% retained; £86 vs £172 skew; none below cost). |\n"
            "| 2026-10-08 | Authority pass: signed MOA (EUR 30k + activity record; no margin/%GM); ISZE ~50% (Yoshimoto mail) vs ITUK 41–43%/47% (Duncan) layers separated. |\n",
            1,
        )
        t = t.replace(
            "| 3 | 2026-10-08 (loop) | Duncan regional margin nuance + support skew (£86 median vs £172 avg); none below cost |\n",
            "| 3 | 2026-10-08 (loop) | Duncan regional margin nuance + support skew (£86 median vs £172 avg); none below cost |\n"
            "| 4 | 2026-10-08 (loop) | MOA cited; Yoshimoto ~50% ISZE GP separated from Duncan ITUK retained; 20% floor not treated as agreement |\n",
            1,
        )

    # KPI tip for EUR 30k
    old_tip = (
        '"tip": "Intentional FY27 opex / budget line for ITUK Don\'t Lose the Deal, also seen as ~€30k credit notes.",'
    )
    new_tip = (
        '"tip": "Signed MOA: ISZE pays ITUK EUR 30,000 if ITUK provides the activity record — '
        'no margin/%GM in the agreement. Same figure is the FY27 budget / credit-note line.",'
    )
    if old_tip in t:
        t = t.replace(old_tip, new_tip, 1)

    # HTML card: expand Duncan card with authority layers
    old_card = """<div class="card" style="margin-bottom:18px">
  <h2>Duncan regional lines — margin and support (Measured)</h2>
  <p class="q">UK proof detail from the deal register — do not confuse with ISZE %GM on the list</p>
  <table>
    <thead><tr><th>Fact</th><th>Figure</th></tr></thead>
    <tbody>
      <tr><td>Normal margin on dealer price (before offer)</td><td>~47%</td></tr>
      <tr><td>Retained margin after offer</td><td>~41–43% median (avg ~41%)</td></tr>
      <tr><td>Lines below cost</td><td>None</td></tr>
      <tr><td>Unit support</td><td>Median ~£86 · average ~£172 (skew)</td></tr>
      <tr><td>Register money</td><td>£54,922 support · 218 regional cases</td></tr>
    </tbody>
  </table>
  <p class="q" style="margin-top:10px">A few large lines pull the average; the typical case is the median. Support is margin given up, not a loss.</p>
</div>"""

    new_card = """<div class="card" style="margin-bottom:18px">
  <h2>Authority sources — money and margin layers</h2>
  <p class="q">Signed agreement vs ISZE mail vs Duncan register — do not blend</p>
  <table>
    <thead><tr><th>Layer</th><th>Figure / rule</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Signed MOA</td><td>EUR 30,000 if ITUK provides the activity record. <b>No margin / %GM</b> in the agreement.</td><td>FY26_ITUK_DLOD_2026-03.docx.pdf</td></tr>
      <tr><td>ISZE GP on programme deals</td><td>~50%</td><td>Jerome → Yoshimoto (Mar 2026 DocuSign thread)</td></tr>
      <tr><td>ITUK normal margin (before offer)</td><td>~47%</td><td>Duncan deal file</td></tr>
      <tr><td>ITUK retained (after offer)</td><td>~41–43% median (avg ~41%); none below cost</td><td>Duncan deal file</td></tr>
      <tr><td>Unit support skew</td><td>Median ~£86 · average ~£172 on £54,922 / 218 cases</td><td>Duncan deal file</td></tr>
    </tbody>
  </table>
  <p class="q" style="margin-top:10px">Yoshimoto-mail ~50% is ISZE margin. Duncan ~41–43% is ITUK retained after the offer. The MOA sets only the EUR 30k + activity-record condition.</p>
</div>"""

    if "Authority sources — money and margin layers" not in t:
        if old_card not in t:
            raise SystemExit("old Duncan HTML card not found in builder")
        t = t.replace(old_card, new_card, 1)

    p.write_text(t, encoding="utf-8")
    print("md-track builder patched")


def patch_feasibility_md() -> None:
    feas = STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.md"
    t = feas.read_text(encoding="utf-8")

    # Add MOA row in §1.4 table if missing
    if "FY26_ITUK_DLOD_2026-03.docx.pdf" not in t:
        anchor = "| **Pricing P&L model - DLOD reserve across DBs** |"
        # try unicode dash variants
        for a in [
            "| **Pricing P&L model - DLOD reserve across DBs** | Finance model already contemplates a Don't Lose the Deal reserve beyond a single market | Confirmed |\n",
            "| **Pricing P&L model – DLOD reserve across DBs** | Finance model already contemplates a Don't Lose the Deal reserve beyond a single market | Confirmed |\n",
            "| **Pricing P&L model — DLOD reserve across DBs** | Finance model already contemplates a Don't Lose the Deal reserve beyond a single market | Confirmed |\n",
        ]:
            if a in t:
                t = t.replace(a, a + FEAS_MOA_ROW, 1)
                break
        else:
            # insert before DLAD vs DLOD paragraph
            marker = "**DLAD vs DLOD:**"
            if marker not in t:
                raise SystemExit("feas: cannot find insert point for MOA row")
            t = t.replace(marker, FEAS_MOA_ROW + "\n" + marker, 1)

    # Layers section after who-funds
    if "### 1.2a Margin layers" not in t:
        marker = "### 1.3 Deal file fields"
        if marker not in t:
            raise SystemExit("feas: missing 1.3")
        t = t.replace(marker, FEAS_LAYERS.strip() + "\n\n" + marker, 1)

    # Fix unknowns line
    t = t.replace(
        "memorandum text on disk (not re-found); ",
        "MOA now on disk (EUR 30k + activity record; no margin/%GM); ",
    )

    # Files section
    if "FY26_ITUK_DLOD_2026-03.docx.pdf" not in t.split("## 10. Files to open")[-1]:
        t = t.replace(
            "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\90_INBOX\\ituk_std_mail_hunt_20260903\\pulled_attachments\\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx\n",
            "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\90_INBOX\\FY26_ITUK_DLOD_2026-03.docx.pdf\n"
            "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\90_INBOX\\ituk_std_mail_hunt_20260903\\pulled_attachments\\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx\n",
            1,
        )

    if "Authority pass: signed MOA" not in t:
        t = t.replace(
            "| 2026-10-08 | Full feasibility study. Corrects Sep 23 zero-cases. Adds Duncan evidence, 0.5% envelopes, FY27/VPACC/P&L corroboration, readiness scorecard, return and non-money sections. |\n",
            "| 2026-10-08 | Full feasibility study. Corrects Sep 23 zero-cases. Adds Duncan evidence, 0.5% envelopes, FY27/VPACC/P&L corroboration, readiness scorecard, return and non-money sections. |\n"
            "| 2026-10-08 | Authority pass: signed MOA (EUR 30k + activity record; no margin/%GM); ISZE ~50% vs ITUK retained layers separated. |\n",
            1,
        )

    feas.write_text(t, encoding="utf-8")
    print("feas MD patched")


def patch_feasibility_html_builder() -> None:
    p = BUILD / "_build_dlod_feasibility_html_20261008.py"
    t = p.read_text(encoding="utf-8")

    # Add authority fields to PAYLOAD if missing
    if '"moa_path"' not in t:
        insert = '''    "moa_path": r"C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\90_INBOX\\FY26_ITUK_DLOD_2026-03.docx.pdf",
    "moa_summary": "ISZE pays ITUK EUR 30,000 for Don't Lose the Deal if ITUK provides the activity record. No margin/%GM in the agreement.",
    "isze_gp_pct_yoshimoto": 50,
    "ituk_normal_margin_pct": 47,
    "ituk_retained_margin_band": "41-43",
'''
        # insert after programme key
        t = t.replace(
            '"programme": "Don\'t Lose the Deal",\n',
            '"programme": "Don\'t Lose the Deal",\n' + insert,
            1,
        )

    # Inject banner HTML near verdict if template has a marker
    if "Authority sources" not in t and "FY26_ITUK_DLOD" not in t.split("PAYLOAD", 1)[-1][:5000]:
        pass  # payload fields added; template may need HTML block

    # Find a place in HTML template string for authority card
    # Look for an existing banner or kpi section
    markers = [
        '<div class="banner">',
        "Honest correction",
        "Sep 23",
    ]
    # We'll add a static card after opening wrap if we can find duncan table in HTML
    if "Authority — MOA and margin layers" not in t:
        # try insert before Japan / Yoshimoto section or after hero
        needle = None
        for cand in [
            '<h2>Who funds what</h2>',
            "<h2>Who funds what</h2>",
            "Who funds what",
            "Measured UK evidence",
        ]:
            if cand in t:
                needle = cand
                break
        if needle:
            card = """
<div class="card" style="margin-bottom:18px">
  <h2>Authority — MOA and margin layers</h2>
  <p class="q">Signed agreement vs mail vs Duncan register — do not blend</p>
  <table>
    <thead><tr><th>Layer</th><th>Figure / rule</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Signed MOA</td><td>EUR 30,000 if ITUK provides the activity record. <b>No margin / %GM</b> in the agreement.</td><td>FY26_ITUK_DLOD_2026-03.docx.pdf</td></tr>
      <tr><td>ISZE GP on programme deals</td><td>~50%</td><td>Jerome → Yoshimoto (Mar 2026)</td></tr>
      <tr><td>ITUK before / after offer</td><td>~47% normal · ~41–43% median retained</td><td>Duncan deal file</td></tr>
    </tbody>
  </table>
</div>
"""
            # insert before needle occurrence in HTML template (last occurrence likely in template)
            # Prefer inserting before Measured UK evidence heading in HTML
            html_marker = ">Measured UK evidence<"
            if html_marker in t:
                # find h2 containing it
                m = re.search(r"<h2[^>]*>Measured UK evidence</h2>", t)
                if m:
                    t = t[: m.start()] + card + t[m.start() :]
            elif "Who funds what" in t:
                m = re.search(r"<h2[^>]*>Who funds what</h2>", t)
                if m:
                    t = t[: m.start()] + card + t[m.start() :]
            else:
                # append after body wrap start - fragile; use payload-driven note in footer instead
                t = t.replace(
                    '<div class="foot">',
                    '<div class="card" style="margin-bottom:18px"><h2>Authority — MOA and margin layers</h2>'
                    "<p>Signed MOA: EUR 30,000 against the activity record; no margin/%GM. "
                    "ISZE ~50% GP (Yoshimoto mail) is a different layer from ITUK ~41–43% retained (Duncan). "
                    "Path: FY26_ITUK_DLOD_2026-03.docx.pdf</p></div>\n<div class=\"foot\">",
                    1,
                )

    p.write_text(t, encoding="utf-8")
    print("feas HTML builder patched")


def patch_other_study() -> None:
    other_md = STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md"
    om = other_md.read_text(encoding="utf-8")

    # Strengthen 20% framing
    old_note = "*Proposed: 20% as the margin a distributor needs to keep. Mechanics: support = 17.6% of the normal dealer price, as measured at ITUK.*"
    new_note = (
        "*Proposed modelling only — **not** in the signed MOA and **not** in Jerome's mail. "
        "The MOA is EUR 30,000 + activity record only (no margin/%GM). "
        "The 20% leave-distributor floor is a sensitivity assumption in this model, not programme policy or agreement. "
        "Mechanics: support = 17.6% of the normal dealer price, as measured at ITUK.*"
    )
    if old_note in om:
        om = om.replace(old_note, new_note, 1)
    elif "Proposed modelling only" not in om:
        # broader replace on the 20% caption
        om = om.replace(
            "Share of the discount ISZE must fund to leave the distributor 20% margin",
            "Share of the discount ISZE must fund to leave the distributor 20% margin *(Proposed modelling only — not MOA/mail)*",
            1,
        )

    # Design rule 4
    old_rule = "4. **ISZE funds a share, not all.** The share is the lower of a half or what is needed to leave the distributor 20% margin."
    new_rule = (
        "4. **ISZE funds a share, not all.** *(Proposed modelling only — not MOA / not mail.)* "
        "In this model the share is the lower of a half or what is needed to leave the distributor 20% margin. "
        "That 20% floor is **not** programme policy or agreement."
    )
    if old_rule in om:
        om = om.replace(old_rule, new_rule, 1)

    # Add layers + MOA near section 3 if missing
    if "Yoshimoto" not in om or "FY26_ITUK_DLOD" not in om:
        insert = (
            "\n**Authority layers (do not blend).** Signed MOA (`01_data\\90_INBOX\\FY26_ITUK_DLOD_2026-03.docx.pdf`): "
            "ISZE pays ITUK EUR 30,000 if ITUK provides the activity record — **no margin/%GM** in the agreement. "
            "Jerome → Yoshimoto (Mar 2026): ISZE GP on the covered deals about **~50%**. "
            "Duncan register: ITUK retained after offer **~41–43% median** (~47% before). "
            "These are three different layers.\n"
        )
        if "FY26_ITUK_DLOD" not in om:
            marker = "## 3. How the money works for ISZE"
            if marker in om:
                om = om.replace(marker, marker + insert, 1)

    if "FY26_ITUK_DLOD_2026-03.docx.pdf" not in om:
        om = om.replace(
            "- `01_data\\90_INBOX\\ituk_std_mail_hunt_20260903\\pulled_attachments\\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx`\n",
            "- `01_data\\90_INBOX\\FY26_ITUK_DLOD_2026-03.docx.pdf` (signed MOA: EUR 30k + activity record; no margin/%GM)\n"
            "- `01_data\\90_INBOX\\ituk_std_mail_hunt_20260903\\pulled_attachments\\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx`\n",
            1,
        )

    if "Authority pass" not in om:
        om = om.replace(
            "| 2026-10-08 | First version. New study on the 17 other distributors. Does not overwrite the 8 Oct feasibility study or the 23 Sep rollout note. |\n",
            "| 2026-10-08 | First version. New study on the 17 other distributors. Does not overwrite the 8 Oct feasibility study or the 23 Sep rollout note. |\n"
            "| 2026-10-08 | Authority pass: MOA cited; Yoshimoto ~50% vs Duncan retained separated; 20% floor labelled Proposed modelling only. |\n",
            1,
        )

    other_md.write_text(om, encoding="utf-8")
    print("other MD patched")

    # HTML light patches
    oh_path = STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html"
    oh = oh_path.read_text(encoding="utf-8")
    oh2 = oh
    oh2 = oh2.replace(
        "leave the distributor 20% margin",
        "leave the distributor 20% margin (Proposed modelling only — not MOA/mail)",
    )
    # only first if many
    if oh2 == oh:
        # try without replacement already done
        pass
    if "FY26_ITUK_DLOD" not in oh2:
        oh2 = oh2.replace(
            "</body>",
            '<div class="card" style="margin:18px"><h2>Authority</h2>'
            "<p>Signed MOA: EUR 30,000 + activity record; no margin/%GM "
            "(FY26_ITUK_DLOD_2026-03.docx.pdf). ISZE ~50% GP (Yoshimoto mail) ≠ "
            "ITUK ~41–43% retained (Duncan). The 20% leave-distributor floor in this study "
            "is Proposed modelling only — not agreement.</p></div>\n</body>",
            1,
        )
    elif "Proposed modelling only" not in oh2:
        oh2 = oh2.replace(
            "20% margin",
            "20% margin (Proposed modelling only)",
            1,
        )
    oh_path.write_text(oh2, encoding="utf-8")
    print("other HTML patched", oh != oh2)


def rebuild() -> None:
    runpy.run_path(str(BUILD / "_build_md_track_business_plan_20261008.py"), run_name="__main__")
    print("md-track rebuilt")
    runpy.run_path(str(BUILD / "_build_dlod_feasibility_html_20261008.py"), run_name="__main__")
    print("feas HTML rebuilt")


def verify() -> None:
    files = {
        "md": STRAT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md",
        "md_html": STRAT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html",
        "feas": STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.md",
        "feas_html": STRAT / "DLOD_NETWORK_FEASIBILITY_2026-10-08.html",
        "other": STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md",
        "other_html": STRAT / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html",
    }
    texts = {k: p.read_text(encoding="utf-8") for k, p in files.items()}

    checks = {
        "1_moa_md": "FY26_ITUK_DLOD_2026-03.docx.pdf" in texts["md"] and "activity record" in texts["md"].lower(),
        "1_moa_no_margin_md": "no margin" in texts["md"].lower() or "No margin" in texts["md"],
        "1_moa_feas": "FY26_ITUK_DLOD_2026-03.docx.pdf" in texts["feas"] and "activity record" in texts["feas"].lower(),
        "1_moa_html": "FY26_ITUK_DLOD" in texts["md_html"] and "activity record" in texts["md_html"].lower(),
        "1_moa_feas_html": "FY26_ITUK_DLOD" in texts["feas_html"] or "Authority — MOA" in texts["feas_html"],
        "2_isze_50_md": "~50%" in texts["md"] and "Yoshimoto" in texts["md"],
        "2_layers_md": "Do not blend" in texts["md"] or "do not blend" in texts["md"].lower(),
        "2_isze_50_html": "~50%" in texts["md_html"] and "Yoshimoto" in texts["md_html"],
        "2_duncan_md": "~47%" in texts["md"] and "41–43%" in texts["md"],
        "3_20_other_modelling": (
            "Proposed modelling only" in texts["other"]
            and ("not programme policy" in texts["other"].lower() or "not in the signed MOA" in texts["other"].lower()
                 or "not MOA" in texts["other"])
        ),
        "3_20_not_bare_policy": not re.search(
            r"(?i)agreement.{0,40}leave the distributor 20%|leave the distributor 20%.{0,40}(policy|agreement|MOA)",
            texts["other"],
        ),
        "4_duncan_md_track": "~47%" in texts["md"] and "41–43%" in texts["md"] and ("£172" in texts["md"] or "172" in texts["md"]),
        "4_duncan_html": "~47%" in texts["md_html"] and "41–43%" in texts["md_html"],
        "5_no_cdn_md": not re.search(r"(?i)cdn\.|unpkg|jsdelivr|googleapis", texts["md_html"]),
        "5_no_cdn_feas": not re.search(r"(?i)cdn\.|unpkg|jsdelivr|googleapis", texts["feas_html"]),
        "5_no_cdn_other": not re.search(r"(?i)cdn\.|unpkg|jsdelivr|googleapis", texts["other_html"]),
        "5_paints_md": "bar-row" in texts["md_html"] or "<tbody>" in texts["md_html"],
        "5_paints_feas": "bar-row" in texts["feas_html"] or "Chart" in texts["feas_html"],
    }
    print(checks)
    bad = [k for k, v in checks.items() if not v]
    if bad:
        raise SystemExit(f"VERIFY FAIL: {bad}")
    print("VERIFY PASS")


if __name__ == "__main__":
    patch_md_track_builder()
    patch_feasibility_md()
    patch_feasibility_html_builder()
    patch_other_study()
    rebuild()
    verify()
