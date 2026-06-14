#!/usr/bin/env python3
"""Generate critical PDF audit of ISUZU Dealer Standards Evaluation Sheet (2026)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ids_paths import DATA_ROOT, RSA_TEMPLATE

OUTPUT = DATA_ROOT / "reports" / "ISUZU_Dealer_Standards_Audit_Report_2026.pdf"
SAMPLE_TEMPLATE = RSA_TEMPLATE

# A4 with 2 cm margins → 17 cm content width
CONTENT_WIDTH = 17 * cm


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=14,
            textColor=colors.HexColor("#1a1a1a"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#c00000"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            leftIndent=12,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.grey,
        ),
        "th": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "td": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            alignment=TA_LEFT,
        ),
        "td_c": ParagraphStyle(
            "TableCellCenter",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
        ),
    }


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _make_table(
    st,
    rows: list[list[str]],
    col_widths: list[float],
    *,
    header_bg: str = "#404040",
    header_text: str = "#ffffff",
    zebra: bool = True,
    center_cols: set[int] | None = None,
) -> Table:
    """Build a table with Paragraph cells so long text wraps inside columns."""
    center_cols = center_cols or set()
    table_data: list[list] = []
    for r_idx, row in enumerate(rows):
        out_row = []
        for c_idx, cell in enumerate(row):
            text = _esc(cell)
            if r_idx == 0:
                para = Paragraph(text, st["th"])
            elif c_idx in center_cols:
                para = Paragraph(text, st["td_c"])
            else:
                para = Paragraph(text, st["td"])
            out_row.append(para)
        table_data.append(out_row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(header_text)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]
    if zebra and len(rows) > 1:
        style_commands.append(
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")])
        )
    tbl.setStyle(TableStyle(style_commands))
    return tbl


def _bullets(st, items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(i, st["bullet"])) for i in items],
        bulletType="bullet",
        start="•",
    )


def build_story(st) -> list:
    today = date.today().strftime("%d %B %Y")
    s: list = []

    s.append(Paragraph("Independent Audit Report", st["title"]))
    s.append(
        Paragraph(
            "<b>ISUZU Dealer Standards Evaluation Sheet — Version 2026</b><br/>"
            "Operational, service, and compliance requirements for authorised dealers",
            st["body"],
        )
    )
    s.append(
        Paragraph(
            f"<b>Report date:</b> {today}<br/>"
            "<b>Prepared for:</b> ISZE / IBX programme management<br/>"
            "<b>Basis of review:</b> Consolidated analysis of deployed Excel templates "
            f"(representative master: <i>{SAMPLE_TEMPLATE.name}</i>) and aligned market "
            "submissions (BE, IUK, ITUK, NL, Poland, Petros, RSA).<br/>"
            "<b>Classification:</b> Internal — management use",
            st["meta"],
        )
    )
    s.append(Spacer(1, 0.4 * cm))

    # Executive summary
    s.append(Paragraph("1. Executive summary", st["h1"]))
    s.append(
        Paragraph(
            "This audit assesses the <b>2026 ISUZU Dealer Standards Evaluation Sheet</b> as an "
            "operating instrument for self-assessment, field audit, and cross-market benchmarking. "
            "The template is structurally mature: it segments requirements into logical domains "
            "(premises, organisation, service, parts, sales, marketing, KPIs), assigns traceable "
            "item numbers, and links to a quantitative scorecard. However, as a <i>compliance and "
            "governance</i> document it exhibits material weaknesses that undermine audit defensibility, "
            "dealer comprehension, and regulatory alignment.",
            st["body"],
        )
    )
    s.append(
        Paragraph(
            "<b>Overall rating (critical view):</b> "
            "<font color='#c00000'><b>Adequate for internal benchmarking; not yet fit for "
            "formal compliance certification without remediation.</b></font>",
            st["body"],
        )
    )

    rating_data = [
        ["Dimension", "Score (1–5)", "Auditor comment"],
        ["Clarity of language", "2.5", "Heavy compound questions; inconsistent terms; typos in live template"],
        ["Cohesion & structure", "3.5", "Strong category tree; weak governance layer and version control"],
        ["Auditability / evidence", "2.0", "Reference column largely unused; method labels inconsistent"],
        ["Regulatory alignment", "2.5", "GDPR and H&S referenced ad hoc; no explicit legal mapping"],
        ["OEM benchmark position", "3.0", "Breadth comparable to premium CV OEMs; depth of evidence trails below best practice"],
    ]
    s.append(
        _make_table(
            st,
            rating_data,
            [4.2 * cm, 2.3 * cm, 10.5 * cm],
            center_cols={1},
        )
    )
    s.append(Spacer(1, 0.3 * cm))

    s.append(
        Paragraph(
            "<b>Key findings:</b> (1) ~196 auditable line items create scoring granularity but "
            "overload dealers and auditors; (2) priority weighting (1–5) is not consistently reflected "
            "in point values; (3) mandatory brand graphics rules (I.VIS / I.BIS) are repeated with "
            "conditional carve-outs that invite subjective scoring; (4) self-evaluation bias is evident "
            "in submitted files (high YES rates without populated evidence references); (5) multilingual "
            "deployments (EN/FR/NL) risk divergent legal meaning without a controlled translation register.",
            st["body"],
        )
    )

    s.append(PageBreak())

    # Scope
    s.append(Paragraph("2. Scope and methodology", st["h1"]))
    s.append(
        Paragraph(
            "The evaluation workbook reviewed comprises four primary tabs: <i>Cover Page</i> "
            "(dealer metadata), <i>Evaluation Sheet_English</i> (~225 rows × 16 columns), "
            "<i>2023–2025 Comparison</i>, and <i>Score Card</i> (category roll-up to total "
            "percentage and items scored). Market packs mirror this structure with translated "
            "sheet names (e.g. <i>Scorekaart</i>, <i>Fiche de résultats</i>). Quantitative "
            "sampling on the RSA master template identified <b>196 scored questions</b>, with "
            "priority distribution: P1 (94), P2 (57), P3 (32), P4 (12), P5 (1).",
            st["body"],
        )
    )
    s.append(
        Paragraph(
            "This review applies professional scepticism: language critique, control design, "
            "comparative OEM practice (commercial vehicle and passenger OEM dealer audit frameworks), "
            "and EU/UK regulatory context relevant to Isuzu’s European dealer base. It is not a "
            "field audit of individual dealer performance.",
            st["body"],
        )
    )

    # Clarity
    s.append(Paragraph("3. Clarity of language", st["h1"]))
    s.append(Paragraph("3.1 Strengths", st["h2"]))
    s.append(
        _bullets(
            st,
            [
                "Numbering scheme (A.1-1, E.2-2) supports traceability and workshop discussion.",
                "Four-level scoring rubrics (Point 0–3) reduce binary pass/fail where graduated criteria exist.",
                "Explicit reference to distributor brand policies (main brand co-location) acknowledges real-world dealer structures.",
                "Update column (New / Modified / Carry over) supports change management versus 2022 baseline.",
            ],
        )
    )
    s.append(Paragraph("3.2 Critical weaknesses", st["h2"]))
    s.append(
        _bullets(
            st,
            [
                "<b>Compound and overloaded questions</b> — 43 items exceed 140 characters; many bundle multiple obligations "
                "(e.g. parking separation, marking, and night-time illumination in one criterion). This violates audit "
                "best practice: one control = one testable assertion.",
                "<b>Ambiguous modals</b> — Frequent use of “must”, “should”, and “do you” without distinguishing legal "
                "mandate vs. recommended practice. Dealers cannot know consequences of non-compliance.",
                "<b>Undefined acronyms</b> — I.VIS, I.BIS, I-TEC, 5S, and “IMG/ISZE Evaluation” are used without a "
                "glossary on the Cover Page or a linked standards manual.",
                "<b>Inconsistent evaluation methods</b> — 16+ method labels (e.g. “Related Document” vs “Related document”, "
                "“Interview / Related Document” split across lines) prevent reliable auditor training and sampling plans.",
                "<b>Template quality defects</b> — Live text includes spelling errors (“unncecessary”, “seperate”) which "
                "erode authority in a document positioned as a contractual standard.",
                "<b>Conditional footnotes in-line</b> — Parentheticals such as “Check if main Brand allow…” convert objective "
                "standards into negotiable interpretations at audit time.",
            ],
        )
    )
    s.append(
        Paragraph(
            "<b>Illustrative excerpt (category E — sales):</b> Questions on lead-response systems, conversion tracking, "
            "and post-sale follow-up are directionally sound but blend <i>CRM process existence</i> with "
            "<i>effectiveness</i> without defining minimum KPI thresholds (e.g. response within 24h). "
            "A dealer answering “YES” in Self Evaluation provides no probative value without the empty "
            "Reference column being mandatory.",
            st["body"],
        )
    )

    s.append(PageBreak())

    # Cohesion
    s.append(Paragraph("4. Cohesion and structure", st["h1"]))
    s.append(Paragraph("4.1 Logical architecture", st["h2"]))
    s.append(
        Paragraph(
            "The A→H category model (Premises; Organisation; Service; Parts; Sales; Marketing; "
            "Standards review; KPIs) aligns with established CV dealer audit frameworks and supports "
            "balanced scorecard reporting on the Score Card tab. Roll-up from subcategory to total "
            "points (max ~280) and dual metrics (<i>Points achieved %</i> and <i>Items scored %</i>) "
            "allows ranking while exposing partial completion — a design strength used successfully "
            "in IBX country league tables.",
            st["body"],
        )
    )
    s.append(Paragraph("4.2 Structural gaps", st["h2"]))
    s.append(
        _bullets(
            st,
            [
                "<b>No hierarchy of consequences</b> — The workbook scores compliance but does not map item failures to "
                "remedial timelines, dealer agreement clauses, or withdrawal of incentives.",
                "<b>Cover Page vs. Evaluation misalignment</b> — Mechanic headcount, GDPR opt-outs, and model lists sit "
                "adjacent to qualitative standards without validation rules (e.g. York Van Centre variant lacks Score Card).",
                "<b>Comparison tab under-specified</b> — 2023–2025 Comparison exists but governance for when year-on-year "
                "regression triggers action is not documented in-sheet.",
                "<b>ITUK consolidated format divergence</b> — UK operating companies use a multi-dealer matrix (Sheet2) "
                "inconsistent with per-dealer files elsewhere; increases operational risk of formula/version drift.",
                "<b>Priority–points misalignment</b> — Priority 4 items do not consistently carry higher point weight; "
                "undermines risk-based auditing.",
            ],
        )
    )

    # Comparative
    s.append(Paragraph("5. Comparative OEM benchmark", st["h1"]))
    s.append(
        Paragraph(
            "Benchmarking is qualitative, based on published and industry practice for leading OEM dealer "
            "standards programmes (Volvo Trucks / Renault Trucks dealer standards, Mercedes-Benz Truck "
            "Outlet Standards, TRATON-group audit tools, Toyota dealer assessment, and VWG commercial "
            "network reviews).",
            st["body"],
        )
    )
    comp_data = [
        ["Criterion", "ISUZU 2026", "Typical best-in-class CV OEM"],
        ["Category breadth", "Comprehensive (196 items)", "Comparable"],
        ["Evidence trail", "Optional Reference column", "Mandatory evidence upload / audit trail ID"],
        ["Scoring model", "0–3 rubric + self-assessment", "Often independent auditor only for tier status"],
        ["Legal integration", "Implicit", "Explicit matrix to ISO 9001 / ISO 14001 / local law"],
        ["Digital channel", "Limited (few website items)", "Dedicated digital retail & data privacy section"],
        ["Remedial workflow", "Not in template", "Corrective action plan (CAP) with deadlines"],
        ["Translation control", "Per-market files", "Master English + certified translations"],
    ]
    s.append(
        _make_table(
            st,
            comp_data,
            [4.5 * cm, 5.5 * cm, 7.0 * cm],
            zebra=False,
        )
    )
    s.append(Spacer(1, 0.2 * cm))
    s.append(
        Paragraph(
            "<b>Strengths vs. peers:</b> Isuzu's standard is notably strong on <i>physical retail "
            "and workshop presentation</i> (signage, customer journey, waiting facilities) and "
            "<i>aftersales process</i> (5S, customer handling). <b>Weaknesses vs. peers:</b> weaker "
            "on <i>data governance</i>, <i>CRM KPI enforcement</i>, and <i>closed-loop corrective "
            "action</i>. Premium OEMs increasingly treat dealer audits as part of ISO-aligned "
            "management systems; Isuzu's Excel-centric model will not scale without a document "
            "control layer.",
            st["body"],
        )
    )

    s.append(PageBreak())

    # Compliance
    s.append(Paragraph("6. Compliance and risk implications", st["h1"]))
    s.append(
        _bullets(
            st,
            [
                "<b>GDPR / UK GDPR</b> — Cover Page collects mechanic names with optional blanking but lacks purpose, "
                "retention, and DPA role clarity. Evaluation items on customer data handling are not mapped to "
                "Articles 5–32 GDPR; risk of unlawful processing if dealers store lead data without documented legal basis.",
                "<b>Health & safety</b> — Workshop, 5S, and employee facility items touch H&S but do not reference "
                "national regulations (UK HSE, EU framework Directive 89/391). Auditors may score YES while statutory "
                "risk remains (e.g. inadequate risk assessment).",
                "<b>Consumer protection / mis-selling</b> — Sales and marketing items (warranty extension, maintenance "
                "packages) intersect with consumer rights directives; template does not require disclosure standards "
                "or record retention for offers made at point of sale.",
                "<b>Environmental claims</b> — Environmental / 5S criteria lack alignment with environmental permitting "
                "or waste-oil handling rules; “green” appearance risk if marketing items scored without substance.",
                "<b>Competition / multi-brand</b> — Repeated “check main Brand allow” caveats may conflict with "
                "competition law constraints on exclusive branding in multi-franchise sites — legal review advised.",
                "<b>Audit defensibility</b> — Heavy reliance on Self Evaluation without mandatory evidence exposes "
                "distributor to challenge if rankings inform incentives (EU competition-sensitive state aid character).",
            ],
        )
    )

    # Recommendations
    s.append(Paragraph("7. Recommendations (prioritised)", st["h1"]))
    rec_data = [
        ["P", "Action", "Owner", "Target"],
        [
            "1",
            "Publish Dealer Standards Manual (PDF) with glossary, legal mapping, and I.VIS/I.BIS extracts",
            "IBX Programme",
            "Q3 2026",
        ],
        [
            "1",
            "Split compound questions; cap at one auditable outcome per row",
            "Standards owner",
            "Rev 2026.1",
        ],
        [
            "1",
            "Make Reference column mandatory for any Self Evaluation = YES",
            "Audit protocol",
            "Immediate",
        ],
        [
            "2",
            "Harmonise evaluation method taxonomy (6 methods or fewer)",
            "Template admin",
            "Rev 2026.1",
        ],
        [
            "2",
            "Align Priority 1–5 to minimum point weights or remove priority column",
            "Analytics",
            "Rev 2026.1",
        ],
        [
            "2",
            "Introduce CAP tab: finding, owner, due date, verification",
            "Field audit",
            "Q4 2026",
        ],
        [
            "3",
            "Certified translation register for FR/NL/Nordic sheets",
            "Local markets",
            "Ongoing",
        ],
        [
            "3",
            "Reject non-standard workbook variants from rankings (template validation)",
            "ISZE analytics",
            "Immediate",
        ],
        [
            "3",
            "Digital evidence portal (photo / doc upload per item ID)",
            "IT / IBX",
            "2027 roadmap",
        ],
    ]
    s.append(
        _make_table(
            st,
            rec_data,
            [0.9 * cm, 8.8 * cm, 3.6 * cm, 3.7 * cm],
            header_bg="#c00000",
            zebra=True,
            center_cols={0, 3},
        )
    )

    s.append(Spacer(1, 0.4 * cm))
    s.append(Paragraph("8. Conclusion", st["h1"]))
    s.append(
        Paragraph(
            "The 2026 ISUZU Dealer Standards Evaluation Sheet is a <b>substantive operational audit tool</b> "
            "suitable for internal ranking and dealer development conversations. It is <b>not yet</b> a "
            "precision compliance instrument. Without language remediation, evidence controls, and "
            "regulatory mapping, distributors risk over-relying on league-table outcomes that reflect "
            "self-attestation more than verified conformity. Implementing the Priority 1 recommendations "
            "would materially improve defensibility before linking scores to contractual remedies or "
            "financial programmes.",
            st["body"],
        )
    )
    s.append(Spacer(1, 0.6 * cm))
    s.append(
        Paragraph(
            "<i>This report was generated from template analytics and professional audit judgement. "
            "It does not constitute legal advice. Legal and competition review should validate "
            "branding requirements and incentive linkage.</i>",
            st["meta"],
        )
    )

    return s


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    st = _styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="ISUZU Dealer Standards Audit 2026",
        author="ISZE Compliance Review",
    )
    doc.build(build_story(st))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
