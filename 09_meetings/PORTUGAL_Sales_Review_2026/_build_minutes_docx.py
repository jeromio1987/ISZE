"""Build Word minutes for ISZE / Astara Portugal 2026-07-29."""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = Path(__file__).with_name("MINUTES_ISZE_Astara_Portugal_2026-07-29.docx")


def set_cell_shading(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def style_runs(paragraph, *, size=10, bold=False, italic=False, color=None, name="Calibri"):
    for run in paragraph.runs:
        run.font.size = Pt(size)
        run.font.name = name
        run.bold = bold
        run.italic = italic
        if color is not None:
            run.font.color.rgb = color


def add_para(doc, text, *, bold=False, italic=False, size=10, color=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    if color is not None:
        run.font.color.rgb = color
    return p


def add_heading_styled(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    return p


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        set_cell_shading(cell, "1F4E79")
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.name = "Calibri"
                run.font.color.rgb = RGBColor(255, 255, 255)
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                for run in p.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Calibri"
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return table


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(item, style="List Bullet")
        style_runs(p, size=10)


def main():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(4)

    title = doc.add_paragraph()
    run = title.add_run("Meeting minutes — ISZE / Astara Portugal")
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    run.font.name = "Calibri"

    add_para(
        doc,
        "Minutes based on incomplete/auto transcript — please confirm actions.",
        italic=True,
        size=9,
        color=RGBColor(0xC0, 0x39, 0x2B),
    )

    add_heading_styled(doc, "1. Meeting header", 1)
    add_table(
        doc,
        ["Field", "Detail"],
        [
            ["Title", "ISZE – Astara Portugal meeting"],
            ["Date / time", "29 July 2026, ~14:03 (duration ~1h 21m)"],
            ["Location", "Microsoft Teams"],
            ["Chair / organiser", "Jerome Van Der Pluym (ISZE)"],
            ["Recording", "ISZE - Astara Portugal meeting-20260729_160312-Meeting Recording"],
        ],
        [1.6, 5.2],
    )

    add_para(doc, "Attendees (from transcript)", bold=True)
    add_table(
        doc,
        ["Name", "Company / role"],
        [
            ["Jerome Van Der Pluym", "ISZE"],
            ["Bart Symons", "ISZE"],
            ["Hadewijch Tibos", "ISZE"],
            ["Koen Matheussen", "ISZE"],
            ["Nuno Machado", "Astara Portugal"],
        ],
        [2.5, 4.3],
    )
    add_para(
        doc,
        'Also addressed / referenced on the call (speaking role [UNCLEAR] from auto-transcript): '
        'Luis (Astara); "Nunu" (likely Nuno / aftersales colleague — [UNCLEAR]).',
        italic=True,
        size=9,
    )
    add_para(doc, "Apologies / absent: Not recorded in the transcript.")

    add_heading_styled(doc, "2. Purpose", 1)
    add_para(
        doc,
        "Review FY parts sales performance vs last year and plan; discuss genuine parts share / PMS view, "
        "dealer standards (IDS), UIO and extended sales target; align on SPA, R&M contracts, monthly "
        "sales/stock data, EDI/IT capabilities, BCS brackets, and obsolete stock.",
    )

    add_heading_styled(doc, "3. Key decisions", 1)
    add_bullets(
        doc,
        [
            "Brake-parts drop vs last year attributed mainly to prior-year campaign stock build — not treated as current aftermarket leakage; no further concern raised in the meeting.",
            "Combined ISZE + Astara dealer visit timing agreed in principle for second half of September to first half of October 2026 (avoid last week of October due to Japan competition / GP1).",
            "New dealer joining the network this quarter: not to be added to current IDS pack; include in next IDS cycle (expected around end Q1 / spring).",
            "Monthly sales-to-dealer data (invoice date, part number, quantity; optionally stock snapshot) — Astara agreed in principle to provide once extraction method is confirmed.",
            "Extended parts target (UIO growth + genuine share stretch + possible second incentive) presented as ambitious / extended; incentive not confirmed pending Japan approval (expected ~end August). Astara asked ISZE to revisit the genuine-share stretch.",
            "BCS / radar brackets: N-series adjustable solution exists; F-series fixed brackets need follow-up — Astara prefers an adjustable single-PN approach for stock/body-width practicality.",
            "Obsolete / scrap-risk stock: ISZE will not repurchase as a central buyer; Astara may send a list for manual cross-distributor matching (former Parts Locator approach).",
        ],
    )

    add_heading_styled(doc, "4. Action items", 1)
    add_table(
        doc,
        ["#", "Action", "Owner", "Due date", "Status"],
        [
            ["1", "Check clutch sales pattern (kits vs individual parts) and comment on ~20% drop drivers", "Nuno Machado (Astara)", "Next meeting / ASAP", "Open"],
            ["2", "Share completed IDS / dealer-standards tool, heat map, dealer fiches and documentation once finalised", "Jerome Van Der Pluym (ISZE)", "When tool complete (near-ready)", "Open"],
            ["3", "Propose dates for combined Astara–ISZE dealer visits (mid-Sep to mid-Oct); confirm ISZE/IMG/(vehicle) participants", "Jerome + Nuno", "Target window mid-Sep–mid-Oct 2026", "Open"],
            ["4", "Complete aftersales hours questionnaire", "Nuno Machado (Astara)", "31 July 2026", "Open"],
            ["5", "Send detailed figures for extended parts target; revisit genuine-share stretch after Astara feedback", "Jerome Van Der Pluym (ISZE)", "Follow-up email", "Open"],
            ["6", "Confirm second incentive / extended-target incentive once Japan approves", "ISZE management / Jerome", "~end August 2026", "Open"],
            ["7", "Prepare SPA part proposals (parts where better price can raise volume)", "Astara (Nuno / parts team)", "When ready; contact Jerome", "Open"],
            ["8", "Email main R&M / Allianz (Alliance) issues for ISZE escalation to Allianz International", "Nuno Machado (Astara)", "ASAP (after Bart's email)", "Open"],
            ["9", 'Share Real Garant (Zurich-backed) contact details as alternative R&M partner', "Bart Symons (ISZE)", 'Stated "will do"', "Open"],
            ["10", "Flag sizeable tenders where R&M parts pricing could matter — ISZE may seek management support", "Astara → Jerome / Bart", "Ongoing", "Open"],
            ["11", "Confirm how to extract & share monthly dealer sales (invoice date, PN, qty) and optional stock snapshot", "Astara (Nuno) + Jerome", "Next step after minutes", "Open"],
            ["12", "Send EDI / system capabilities overview (PDF); check with ISZE IT (Jimmy) what Astara already uses; align requirements meeting", "Bart Symons (ISZE) + Astara", "IT check next week; then meeting", "Open"],
            ["13", "Email Jerome + Bart with exact IT / parts-data requirements (PN ↔ N/F-series, etc.)", "Astara (Nuno)", "ASAP", "Open"],
            ["14", "Share BCS bracket part numbers / stock; check F-series adjustable option with warehouse / Japan / technical", "Bart + Jerome + technical", "Follow-up (not same-day)", "Open"],
            ["15", "Send obsolete / high scrap-risk stock list (PN + qty) for ISZE cross-DB demand check", "Astara (Nuno)", "ASAP", "Open"],
            ["16", "Issue formal minutes of this meeting", "Jerome Van Der Pluym (ISZE)", "After meeting", "In progress"],
        ],
        [0.35, 2.8, 1.5, 1.3, 0.85],
    )

    add_heading_styled(doc, "5. Open points / parking lot", 1)
    add_bullets(
        doc,
        [
            "GPS / genuine parts share ~63% of theoretical max spend: Astara views this as likely high vs market reality; Nuno's qualitative view ≈ >50% of parc not regularly in the official network. Model still assumption-heavy (Europe-wide €/UIO; warranty not fully separated — mid-50%s if warranty excluded [indicative]).",
            "Multi-site dealers (e.g. Évora/Beja, Astara Retail Lisbon + Cascais, Auto Reno Minho multi-workshop): secondary sites may show weak stock metrics because of central warehouse + internal redistribution — IDS/parts reading needs care.",
            "CV R&M: in-house at Astara risk; Allianz not interested at current volume; pricing often uncompetitive. Active contracts cited: ~12 CV, ~29 LCV.",
            "CV warranty 2 years vs many tenders requiring minimum 3 years — ongoing tender competitiveness issue.",
            "LCV: Chinese / KGM-type price competition; leasing tenders more winnable (residual value); direct-purchase tenders difficult; leasing often bundles R&M → fewer Astara R&M opportunities.",
            "Extended target: 9% UIO growth, +1.8% genuine share, on top of March ~5% price increase and FY dealer sales base ~€4,047,000 — ambitious; Astara sceptical on further genuine-share lift.",
            "Parts Locator tool no longer live — only manual broker matching possible.",
            "Exact Allianz International contact name spelling [UNCLEAR] in transcript.",
        ],
    )

    add_heading_styled(doc, "6. Discussion highlights", 1)
    add_bullets(
        doc,
        [
            "FY parts vs LY: ~+5%; vs plan: ~−2% gap (still feasible). May strongest; April/June softer. Filters and transmissions up; sensors partly warranty-driven (PM / NOx).",
            "BVP used deliberately on service contracts and older vehicles to protect TCO / workshop loyalty; quality experience broadly acceptable.",
            "New 3½-tonne BVP brake pad (~30% cheaper) flagged as useful genuine alternative.",
            "Portugal IDS self-audit: country average 86 vs full-network average; overall Portugal strong vs Europe. Tool (compare / heat map / map / dealer sheets) nearly ready to share.",
            "Astara UIO view: 10-year registrations/sales; ISZE scrap-rate model ≈ 7,909 units — directional alignment discussed, not a formal sign-off.",
            "SPA framed as tailored alternative to broad campaigns under new management rules.",
            "EDI: Astara Central Warehouse already connected but not using full feature set; three-party follow-up (Astara + ISZE parts + IT) proposed.",
        ],
    )

    add_heading_styled(doc, "7. Next meeting", 1)
    add_table(
        doc,
        ["Item", "Detail"],
        [
            [
                "Date",
                "TBC — dealer-visit week in mid-September to mid-October 2026; separate EDI/IT alignment after Astara requirements email",
            ],
            [
                "Proposed agenda",
                "(1) Confirm extended target / incentive status; (2) SPA proposals; (3) Monthly sales/stock feed go-live; "
                "(4) EDI/IT scope; (5) R&M Allianz / Real Garant progress; (6) BCS F-series brackets; "
                "(7) Obsolete-stock matching; (8) Dealer visit plan",
            ],
        ],
        [1.4, 5.4],
    )

    add_heading_styled(doc, "Chair check (before circulating)", 1)
    checks = [
        'Confirm attendee list — was Luis present, and is "Nunu" Nuno or a second Astara colleague?',
        "Confirm locked Portugal GPS figure for packs: transcript ~63% vs prior locked 63.3% — which number to use in follow-up materials?",
        "Confirm Allianz International contact name/spelling and whether Bart's escalation email already went out.",
        "Confirm whether Astara commits to stock snapshot monthly, or only invoice lines (date / PN / qty).",
        "Confirm F-series BCS action owner and whether Japan check is required vs local warehouse only.",
    ]
    for i, c in enumerate(checks, 1):
        add_para(doc, f"{i}. {c}")

    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
